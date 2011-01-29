# -*- coding: utf8 -*-
from nose.tools import eq_
import test_utils

import amo
from addons.models import Addon
from versions.models import Version, ApplicationsVersions
from files.models import Platform, File
from applications.models import Application, AppVersion
from editors.models import (ViewPendingQueue, ViewFullReviewQueue,
                            ViewPreliminaryQueue)


def create_addon_file(name, version_str, addon_status, file_status,
                      platform=amo.PLATFORM_ALL, application=amo.FIREFOX):
    app, created = Application.objects.get_or_create(id=application.id,
                                                     guid=application.guid)
    app_vr, created = AppVersion.objects.get_or_create(application=app,
                                                       version='1.0')
    pl, created = Platform.objects.get_or_create(id=platform.id)
    try:
        ad = Addon.objects.get(name__localized_string=name)
    except Addon.DoesNotExist:
        ad = Addon.objects.create(type=amo.ADDON_EXTENSION, name=name)
    vr, created = Version.objects.get_or_create(addon=ad, version=version_str)
    va, created = ApplicationsVersions.objects.get_or_create(
                        version=vr, application=app, min=app_vr, max=app_vr)
    fi = File.objects.create(version=vr, filename=u"%s.xpi" % name,
                             platform=pl, status=file_status)
    # Update status *after* there are files:
    Addon.objects.get(pk=ad.id).update(status=addon_status)
    return {
        'addon': ad,
        'version': vr
    }


def create_search_ext(name, version_str, addon_status, file_status):
    try:
        ad = Addon.objects.get(name__localized_string=name)
    except Addon.DoesNotExist:
        ad = Addon.objects.create(type=amo.ADDON_SEARCH, name=name)
    vr, created = Version.objects.get_or_create(addon=ad, version=version_str)
    pl, created = Platform.objects.get_or_create(id=amo.PLATFORM_ALL.id)
    fi = File.objects.create(version=vr, filename=u"%s.xpi" % name,
                             platform=pl, status=file_status)
    # Update status *after* there are files:
    Addon.objects.get(pk=ad.id).update(status=addon_status)
    return ad


class TestQueue(test_utils.TestCase):
    """Tests common attributes and coercions that each view must support."""
    __test__ = False # this is an abstract test case

    def test_latest_version(self):
        self.new_file(version=u'0.1')
        self.new_file(version=u'0.2')
        latest = self.new_file(version=u'0.3')
        row = self.Queue.objects.get()
        eq_(row.latest_version, '0.3')
        eq_(row.latest_version_id, latest['version'].id)

    def test_file_platforms(self):
        self.new_file(version=u'0.1', platform=amo.PLATFORM_LINUX)
        self.new_file(version=u'0.1', platform=amo.PLATFORM_MAC)
        # Here's a dupe platform in another version:
        self.new_file(version=u'0.2', platform=amo.PLATFORM_MAC)
        row = self.Queue.objects.get()
        eq_(sorted(row.file_platform_ids),
            [amo.PLATFORM_LINUX.id, amo.PLATFORM_MAC.id])

    def test_file_applications(self):
        self.new_file(version=u'0.1', application=amo.FIREFOX)
        self.new_file(version=u'0.1', application=amo.THUNDERBIRD)
        # Duplicate:
        self.new_file(version=u'0.1', application=amo.FIREFOX)
        row = self.Queue.objects.get()
        eq_(sorted(row.application_ids),
            [amo.FIREFOX.id, amo.THUNDERBIRD.id])

    def test_reviewed_files_are_hidden(self):
        self.new_file(name='Unreviewed', version=u'0.1')
        create_addon_file('Already Reviewed', '0.1',
                          amo.STATUS_PUBLIC, amo.STATUS_LISTED)
        eq_(sorted(q.addon_name for q in self.Queue.objects.all()),
            ['Unreviewed'])

    def test_search_extensions(self):
        self.new_search_ext('Search Tool', '0.1')
        row = self.Queue.objects.get()
        eq_(row.addon_name, u'Search Tool')
        eq_(row.application_ids, [])
        eq_(row.file_platform_ids, [amo.PLATFORM_ALL.id])


class TestPendingQueue(TestQueue):
    __test__ = True
    Queue = ViewPendingQueue

    def new_file(self, name=u'Pending', version=u'1.0', **kw):
        return create_addon_file(name, version,
                                 amo.STATUS_PUBLIC, amo.STATUS_UNREVIEWED,
                                 **kw)

    def new_search_ext(self, name, version, **kw):
        return create_search_ext(name, version,
                                 amo.STATUS_PUBLIC, amo.STATUS_UNREVIEWED,
                                 **kw)


class TestFullReviewQueue(TestQueue):
    __test__ = True
    Queue = ViewFullReviewQueue

    def new_file(self, name=u'Nominated', version=u'1.0', **kw):
        return create_addon_file(name, version,
                                 amo.STATUS_NOMINATED, amo.STATUS_UNREVIEWED,
                                 **kw)

    def new_search_ext(self, name, version, **kw):
        return create_search_ext(name, version,
                                 amo.STATUS_NOMINATED, amo.STATUS_UNREVIEWED,
                                 **kw)

    def test_lite_review_addons_also_shows_up(self):
        create_addon_file('Full', '0.1',
                          amo.STATUS_NOMINATED, amo.STATUS_UNREVIEWED)
        create_addon_file('Lite', '0.1',
                          amo.STATUS_LITE_AND_NOMINATED,
                          amo.STATUS_UNREVIEWED)
        eq_(sorted(q.addon_name for q in self.Queue.objects.all()),
            ['Full', 'Lite'])

    def test_any_nominated_file_shows_up(self):
        create_addon_file('Disabled', '0.1',
                          amo.STATUS_NOMINATED, amo.STATUS_DISABLED)
        create_addon_file('Null', '0.1',
                          amo.STATUS_NOMINATED, amo.STATUS_NULL)
        eq_(sorted(q.addon_name for q in self.Queue.objects.all()),
            ['Disabled', 'Null'])


class TestPreliminaryQueue(TestQueue):
    __test__ = True
    Queue = ViewPreliminaryQueue

    def new_file(self, name=u'Preliminary', version=u'1.0', **kw):
        return create_addon_file(name, version,
                                 amo.STATUS_LITE, amo.STATUS_UNREVIEWED,
                                 **kw)

    def new_search_ext(self, name, version, **kw):
        return create_search_ext(name, version,
                                 amo.STATUS_LITE, amo.STATUS_UNREVIEWED,
                                 **kw)

    def test_unreviewed_addons_are_in_q(self):
        create_addon_file('Lite', '0.1',
                          amo.STATUS_LITE, amo.STATUS_UNREVIEWED)
        create_addon_file('Unreviewed', '0.1',
                          amo.STATUS_UNREVIEWED, amo.STATUS_UNREVIEWED)
        eq_(sorted(q.addon_name for q in self.Queue.objects.all()),
            ['Lite', 'Unreviewed'])