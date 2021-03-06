# -*- coding: utf8 -*-
import json
import urllib
import urlparse

from django.http import QueryDict
from django.test import client

from mock import Mock, patch
from nose.tools import eq_
from pyquery import PyQuery as pq

import amo
import amo.tests
from amo.urlresolvers import reverse
from applications.models import AppVersion
from addons.tests.test_views import TestMobile
from search.tests import SphinxTestCase
from search import views
from search.client import SearchError
from addons.models import Addon, Category
from tags.models import AddonTag, Tag


def test_parse_bad_type():
    """
    Given a type that doesn't exist, we should not throw a KeyError.

    Note: This does not require sphinx to be running.
    """
    c = client.Client()
    try:
        c.get("/en-US/firefox/api/1.2/search/firebug%20type:dict")
    except KeyError:  # pragma: no cover
        assert False, ("We should not throw a KeyError just because we had a "
                       "nonexistent addon type.")


class PersonaSearchTest(SphinxTestCase):
    fixtures = ['base/apps', 'addons/persona']

    def get_response(self, **kwargs):
        return self.client.get(reverse('search.search') +
                               '?' + urllib.urlencode(kwargs))

    def test_default_personas_query(self):
        r = self.get_response(cat='personas')
        eq_(r.status_code, 200)
        doc = pq(r.content)
        eq_(doc('title').text(),
                'Personas Search Results :: Add-ons for Firefox')


class FrontendSearchTest(SphinxTestCase):
    fixtures = ('base/addon_3615', 'base/appversions',
                'base/addon_6704_grapple', 'addons/persona')

    def get_response(self, **kwargs):
        return self.client.get(reverse('search.search') +
                               '?' + urllib.urlencode(kwargs))

    def test_default_no_personas(self):
        """Reverting the personas experiment... for now.  bug 618622"""
        r = self.get_response(q='My Persona')
        doc = pq(r.content)
        eq_(len(doc('.item')), 0)

    def test_xss(self):
        """Inputs should be escaped so people don't XSS."""
        r = self.get_response(q='><strong>My Balls</strong>')
        doc = pq(r.content)
        eq_(len([1 for a in doc('strong') if a.text == 'My Balls']), 0)

    def test_tag_xss(self):
        """Test that the tag params are escaped as well."""

        r = self.get_response(tag="<script>alert('balls')</script>")
        self.assertNotContains(r, "<script>alert('balls')</script>")

    def test_default_query(self):
        """Verify some expected things on a query for nothing."""
        resp = self.get_response()
        doc = pq(resp.content)
        num_actual_results = len(Addon.objects.filter(
            versions__apps__application=amo.FIREFOX.id,
            versions__files__gt=0))
        # Verify that we have the expected number of results.
        eq_(doc('.item').length, num_actual_results)

        # We should count the number of expected results and match.
        eq_(doc('h3.results-count').text(), "Showing 1 - %d of %d results"
           % (num_actual_results, num_actual_results, ))

        # Verify that we have the Refine Results.
        eq_(doc('.secondary .highlight h3').length, 1)

    def test_default_collections_query(self):
        r = self.get_response(cat='collections')
        doc = pq(r.content)
        eq_(doc('title').text(),
            'Collection Search Results :: Add-ons for Firefox')

    def test_basic_query(self):
        "Test a simple query"
        resp = self.get_response(q='delicious')
        doc = pq(resp.content)
        el = doc('title')[0].text_content().strip()
        eq_(el, 'Add-on Search Results for delicious :: Add-ons for Firefox')

    def test_category(self):
        """
        Verify that we have nothing in category 72.
        """
        resp = self.get_response(cat='1,72')
        doc = pq(resp.content)
        eq_(doc('.item').length, 0)

    def test_addontype(self):
        resp = self.get_response(atype=amo.ADDON_LPAPP)
        doc = pq(resp.content)
        eq_(doc('.item').length, 0)

    def test_version_selected(self):
        "The selected version should match the lver param."
        resp = self.get_response(lver='3.6')
        doc = pq(resp.content)
        el = doc('#refine-compatibility li.selected')[0].text_content().strip()
        eq_(el, '3.6')

    def test_version_text(self):
        """Test that the version text is calculated correctly."""
        AppVersion.objects.create(application_id=1, version='4.46',
                                  version_int=4460000000000L)
        resp = self.get_response(lver='4.46', q='')
        doc = pq(resp.content)
        eq_(doc('#refine-compatibility li a')[1].text, '4.46')
        eq_(doc('#refine-compatibility li a')[2].text, '3.6')

    def test_version_text_asterix(self):
        """Test that the version text is calculated correctly for .*"""
        request = Mock()
        request.get_full_path = lambda: ''
        request.APP.min_display_version = 4.0
        eq_(views._get_versions(request, [5990000200100L], [])[1].text, '5.*')

    def test_empty_version_selected(self):
        """If a user filters by a version that has no results, that version
        should show up on the filter list anyway."""
        resp = self.get_response(lver='3.6', q='adjkhasdjkasjkdhash')
        doc = pq(resp.content)
        el = doc('#refine-compatibility li.selected').text().strip()
        eq_(el, '3.6')

    def test_sort_newest(self):
        "Test that we selected the right sort."
        resp = self.get_response(sort='newest')
        doc = pq(resp.content)
        el = doc('.listing-header li.selected')[0].text_content().strip()
        eq_(el, 'Created')

    def test_sort_default(self):
        "Test that by default we're sorting by Keyword Search"
        resp = self.get_response()
        doc = pq(resp.content)
        els = doc('.listing-header li.selected')
        eq_(len(els), 1, "No selected sort :(")
        eq_(els[0].text_content().strip(), 'Keyword Match')

    def test_sort_bad(self):
        "Test that a bad sort value won't bring the system down."
        self.get_response(sort='yermom')

    def test_non_existent_tag(self):
        """
        If you are searching for a tag that doesn't exist we shouldn't return
        any results.
        """
        resp = self.get_response(tag='stockholmsyndrome')
        doc = pq(resp.content)
        eq_(doc('.item').length, 0)

    def test_themes_in_results(self):
        """Many themes have platform ids that aren't 1, we should make sure we
        are returning them."""
        resp = self.get_response(q='grapple')
        doc = pq(resp.content)
        eq_(u'GrApple Yummy Aronnax', doc('.item h3 a').text())

    def test_tag_refinement(self):
        """Don't show the tag list if there's no tags to be shown."""
        r = self.get_response(q='vuvuzela')
        doc = pq(r.content)
        eq_(len(doc('.addon-tags')), 0)

    def test_pagination_refinement(self):
        """Refinement panel shouldn't have the page parameter in urls."""
        r = self.get_response(page=2)
        doc = pq(r.content)
        for link in doc('#refine-results a'):
            assert 'page=2' not in link.attrib['href'], (
                    "page parameter found in %s link" % link.text)

    def test_version_refinement(self):
        """For an addon, if we search for it, we get the
        full range of versions for refinement purposes."""
        # Delicious is 3.6-3.7 compatible
        r = self.get_response(q='delicious')
        doc = pq(r.content)
        eq_([a.text for a in doc(r.content)('#refine-compatibility a')],
            ['All Versions', '3.6'])

    def test_bad_cat(self):
        r = self.get_response(cat='1)f,ff')
        eq_(r.status_code, 200)


class MobileSearchTest(SphinxTestCase, TestMobile):

    def test_search(self):
        r = self.client.get(reverse('search.search'))
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, 'search/mobile/results.html')


class ViewTest(amo.tests.TestCase):
    """Tests some of the functions used in building the view."""

    fixtures = ('base/category',)

    def setUp(self):
        self.fake_request = Mock()
        self.fake_request.get_full_path = lambda: 'http://fatgir.ls/'

    def test_get_categories(self):
        cats = Category.objects.all()
        cat = cats[0].id

        # Select a category.
        items = views._get_categories(self.fake_request, cats, category=cat)
        eq_(len(cats), len(items[1].children))
        assert any((i.selected for i in items[1].children))

        # Select an addon type.
        atype = cats[0].type
        items = views._get_categories(self.fake_request, cats,
                                      addon_type=atype)
        assert any((i.selected for i in items))

    def test_get_tags(self):
        t = Tag(tag_text='yermom')
        assert views._get_tags(self.fake_request, tags=[t], selected='yermom')


class AjaxTest(SphinxTestCase):
    fixtures = ('base/addon_3615',)

    def test_json(self):
        r = self.client.get(reverse('search.ajax') + '?q=del')
        data = json.loads(r.content)

        check = lambda x, y: eq_(data[0][val], expected)

        addon = Addon.objects.get(pk=3615)
        check_me = (
                ('id', addon.id),
                ('icon', addon.icon_url),
                ('label', unicode(addon.name)),
                ('value', unicode(addon.name).lower()))

        for val, expected in check_me:
            check(val, expected)

    @patch('search.client.Client.query')
    def test_errors(self, searchclient):
        searchclient.side_effect = SearchError()
        r = self.client.get(reverse('search.ajax') + '?q=del')
        eq_('[]', r.content)


class TestAdminDisabledAddons(SphinxTestCase):
    fixtures = ('base/addon_3615',)

    def setUp(self):
        Addon.objects.get(pk=3615).update(status=amo.STATUS_DISABLED)
        super(TestAdminDisabledAddons, self).setUp()

    def test_search(self):
        r = self.client.get(reverse('search.ajax') + '?q=del')
        eq_('[]', r.content)


class TestUserDisabledAddons(SphinxTestCase):
    fixtures = ('base/addon_3615',)

    def setUp(self):
        Addon.objects.get(pk=3615).update(disabled_by_user=True)
        super(TestUserDisabledAddons, self).setUp()

    def test_search(self):
        r = self.client.get(reverse('search.ajax') + '?q=del')
        eq_('[]', r.content)


class TagTest(SphinxTestCase):
    fixtures = ('base/apps', 'addons/persona', 'base/addon_3615')

    def setUp(self):
        a = Addon.objects.get(pk=15663)

        tags = ('donkeybuttrhino', 'bar', 'foo')
        for tag in tags:
            t = Tag.objects.create(tag_text=tag)
            AddonTag.objects.create(tag=t, addon=a)

        t = Tag.objects.create(tag_text='bar2')
        a = Addon.objects.get(pk=3615)
        AddonTag.objects.create(tag=t, addon=a)

        super(TagTest, self).setUp()

    def test_persona_results(self):
        url = reverse('tags.detail', args=('donkeybuttrhino',))
        r = self.client.get(url, follow=True)
        eq_(len(r.context['pager'].object_list), 1)

    def test_related_tags_change(self):
        url = reverse('tags.detail', args=('bar',))
        r = self.client.get(url, follow=True)
        old_related_tags = pq(r.content)('#refine-tags li a').text()

        url = reverse('tags.detail', args=('bar2',))
        r = self.client.get(url, follow=True)
        new_related_tags = pq(r.content)('#refine-tags li a').text()
        assert old_related_tags != new_related_tags


class TestSearchboxTarget(amo.tests.TestCase):
    # Check that we search within addons/personas/collections as appropriate.

    def check(self, url, placeholder, cat):
        doc = pq(self.client.get(url).content)('.header-search form')
        eq_(doc('input[name=q]').attr('placeholder'), placeholder)
        eq_(doc('input[name=cat]').val(), cat)

    def test_addons_is_default(self):
        self.check(reverse('home'), 'search for add-ons', 'all')

    def test_themes(self):
        self.check(reverse('browse.themes'), 'search for add-ons',
                   '%s,0' % amo.ADDON_THEME)

    def test_collections(self):
        self.check(reverse('collections.list'), 'search for collections',
                   'collections')

    def test_personas(self):
        self.check(reverse('browse.personas'), 'search for personas',
                   'personas')


class TestESSearch(amo.tests.TestCase):

    def test_legacy_redirects(self):
        base = reverse('search.es_search')
        r = self.client.get(base + '?sort=averagerating')
        self.assertRedirects(r, base + '?sort=rating', status_code=301)


def test_search_redirects():
    changes = (
        ('q=yeah&sort=newest', 'q=yeah&sort=updated'),
        ('sort=weeklydownloads', 'sort=users'),
        ('sort=averagerating', 'sort=rating'),
        ('lver=5.*', 'appver=5.*'),
        ('q=woo&sort=averagerating&lver=6.0', 'q=woo&sort=rating&appver=6.0'),
        ('pid=2', 'platform=linux'),
        ('q=woo&lver=6.0&sort=users&pid=5',
         'q=woo&appver=6.0&sort=users&platform=windows'),
    )

    def check(before, after):
        eq_(views.fix_search_query(QueryDict(before)),
            dict(urlparse.parse_qsl(after)))
    for before, after in changes:
        yield check, before, after

    queries = (
        'q=yeah',
        'q=yeah&sort=users',
        'sort=users',
        'q=yeah&appver=6.0',
        'q=yeah&appver=6.0&platform=mac',
    )

    def same(qs):
        q = QueryDict(qs)
        assert views.fix_search_query(q) is q
    for qs in queries:
        yield same, qs
