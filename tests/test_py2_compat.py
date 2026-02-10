"""Verify all fds modules can be imported (syntax/compatibility check)."""
from __future__ import unicode_literals


def test_all_modules_import():
    import fds
    import fds.Country
    import fds.Countries
    import fds.Config
    import fds.fds
    import fds.FirewallWrapper
    import fds.utils
    import fds.WebClient


def test_country_flag_unicode():
    from fds.Country import Country
    country = Country('Germany', {'cca2': 'DE', 'demonym': 'German', 'tld': '.de'})
    flag = country.getFlag()
    assert flag is not False
    assert len(flag) == 2
