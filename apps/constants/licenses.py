from lib.licenses import license_text
from tower import ugettext_lazy as _


# Built-in Licenses
class _LicenseBase(object):
    """Base class for built-in licenses."""
    shortname = None
    icons = None     # CSS classes. See zamboni.css for a list.
    linktext = None  # Link text distinct from full license name.
    on_form = True

    @classmethod
    def text(cls):
        return cls.shortname and license_text(cls.shortname) or None


class LICENSE_CUSTOM(_LicenseBase):
    """
    Not an actual license, but used as a placeholder for author-defined
    licenses
    """
    id = -1
    name = _(u'Custom License')
    url = None
    shortname = 'other'


class LICENSE_MPL(_LicenseBase):
    id = 0
    name = _(u'Mozilla Public License, version 1.1')
    url = 'http://www.mozilla.org/MPL/MPL-1.1.html'
    shortname = 'mpl'


class LICENSE_GPL2(_LicenseBase):
    id = 1
    name = _(u'GNU General Public License, version 2.0')
    url = 'http://www.gnu.org/licenses/gpl-2.0.html'
    shortname = 'gpl2'


class LICENSE_GPL3(_LicenseBase):
    id = 2
    name = _(u'GNU General Public License, version 3.0')
    url = 'http://www.gnu.org/licenses/gpl-3.0.html'
    shortname = 'gpl3'


class LICENSE_LGPL21(_LicenseBase):
    id = 3
    name = 'GNU Lesser General Public License, version 2.1'
    url = 'http://www.gnu.org/licenses/lgpl-2.1.html'
    shortname = 'lgpl21'


class LICENSE_LGPL3(_LicenseBase):
    id = 4
    name = _(u'GNU Lesser General Public License, version 3.0')
    url = 'http://www.gnu.org/licenses/lgpl-3.0.html'
    shortname = 'lgpl3'


class LICENSE_MIT(_LicenseBase):
    id = 5
    name = _(u'MIT/X11 License')
    url = 'http://www.opensource.org/licenses/mit-license.php'
    shortname = 'mit'


class LICENSE_BSD(_LicenseBase):
    id = 6
    name = _(u'BSD License')
    url = 'http://www.opensource.org/licenses/bsd-license.php'
    shortname = 'bsd'


class LICENSE_COPYRIGHT(_LicenseBase):
    id = 7
    name = _(u'All Rights Reserved')
    url = None
    shortname = None
    icons = ('copyr',)
    on_form = False


class LICENSE_CC_BY_NC_SA(_LicenseBase):
    id = 8
    name = _(u'Creative Commons Attribution-NonCommercial-Share Alike 3.0')
    linktext = _(u'Some rights reserved')
    url = 'http://creativecommons.org/licenses/by-nc-sa/3.0/'
    shortname = None
    icons = ('cc-attrib', 'cc-noncom', 'cc-share')
    on_form = False


# TODO(cvan): Need migrations for these licenses.
class LICENSE_CC_BY(_LicenseBase):
    id = 9
    name = _(u'Creative Commons Attribution 3.0')
    linktext = _(u'Some rights reserved')
    url = 'http://creativecommons.org/licenses/by/3.0/'
    shortname = None
    icons = ('cc-attrib',)
    on_form = False


class LICENSE_CC_BY_NC(_LicenseBase):
    id = 10
    name = _(u'Creative Commons Attribution-NonCommercial 3.0')
    linktext = _(u'Some rights reserved')
    url = 'http://creativecommons.org/licenses/by-nc/3.0/'
    shortname = None
    icons = ('cc-attrib', 'cc-noncom')
    on_form = False


class LICENSE_CC_BY_NC_ND(_LicenseBase):
    id = 11
    name = _(u'Creative Commons Attribution-NonCommercial-NoDerivs 3.0')
    linktext = _(u'Some rights reserved')
    url = 'http://creativecommons.org/licenses/by-nc-nd/3.0/'
    shortname = None
    icons = ('cc-attrib', 'cc-noncom', 'cc-noderiv')
    on_form = False


class LICENSE_CC_BY_ND(_LicenseBase):
    id = 12
    name = _(u'Creative Commons Attribution-NoDerivs 3.0')
    linktext = _(u'Some rights reserved')
    url = 'http://creativecommons.org/licenses/by-nd/3.0/'
    shortname = None
    icons = ('cc-attrib', 'cc-noderiv')
    on_form = False


class LICENSE_CC_BY_SA(_LicenseBase):
    id = 13
    name = _(u'Creative Commons Attribution-ShareAlike 3.0')
    linktext = _(u'Some rights reserved')
    url = 'http://creativecommons.org/licenses/by-sa/3.0/'
    shortname = None
    icons = ('cc-attrib', 'cc-share')
    on_form = False


PERSONA_LICENSES = (LICENSE_CC_BY, LICENSE_CC_BY_NC,
                    LICENSE_CC_BY_NC_ND, LICENSE_CC_BY_NC_SA, LICENSE_CC_BY_ND,
                    LICENSE_CC_BY_SA)
LICENSES = (LICENSE_CUSTOM, LICENSE_COPYRIGHT, LICENSE_MPL, LICENSE_GPL2,
            LICENSE_GPL3, LICENSE_LGPL21, LICENSE_LGPL3, LICENSE_MIT,
            LICENSE_BSD) + PERSONA_LICENSES
LICENSE_IDS = dict((license.id, license) for license in LICENSES)

PERSONA_LICENSES = (LICENSE_COPYRIGHT,) + PERSONA_LICENSES
PERSONA_LICENSES_IDS = [(l.id, l) for l in PERSONA_LICENSES]
