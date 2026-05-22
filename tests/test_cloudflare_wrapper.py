"""Unit tests for CloudflareWrapper account_ids handling and unblock_ip."""
from __future__ import unicode_literals

import pytest

# unittest.mock is the stdlib in py3 and a backport (mock package) on py2
try:
    from unittest.mock import MagicMock, patch, call
except ImportError:
    from mock import MagicMock, patch, call

from CloudFlare.exceptions import CloudFlareAPIError


@pytest.fixture
def cf_cfg(tmp_path, monkeypatch):
    """Point CloudflareWrapper's cf_config_filename at a temp file.

    Returns a writer callable: cf_cfg("body of cloudflare.cfg") -> path.
    Patches the module global so both _read_account_ids and __init__ see it.
    """
    cfg_path = tmp_path / "cloudflare.cfg"

    def write(body):
        cfg_path.write_text(body)
        return str(cfg_path)

    from cds import CloudflareWrapper as cw_mod
    monkeypatch.setattr(cw_mod, "cf_config_filename", str(cfg_path))
    return write


@pytest.fixture
def patched_cf_init():
    """No-op out CloudFlare.__init__ so we don't hit the real lib's config loading.

    We still set `_base` on the instance because the real CloudFlare class has a
    `__del__` that touches it; without this, GC'd test doubles emit noisy
    PytestUnraisableExceptionWarning.
    """
    def fake_init(self, *args, **kwargs):
        self._base = None

    with patch("cds.CloudflareWrapper.CloudFlare.__init__", new=fake_init):
        yield


def _make_wrapper_with_fake_accounts(fake_accounts_mock=None):
    """Build a CloudflareWrapper and attach a MagicMock-backed `accounts` namespace.

    Returns (wrapper, fake_accounts) so tests can assert on call patterns.
    """
    from cds.CloudflareWrapper import CloudflareWrapper

    cw = CloudflareWrapper()
    if fake_accounts_mock is None:
        fake_accounts_mock = MagicMock()
    cw.accounts = fake_accounts_mock
    return cw, fake_accounts_mock


def test_account_ids_from_config_skips_listing(cf_cfg, patched_cf_init):
    cf_cfg(
        "[CloudFlare]\n"
        "token = dummy\n"
        "account_ids = aaa111, bbb222\n"
    )

    # Patch `accounts` BEFORE construction so we can prove .get() was never called.
    # CloudflareWrapper subclasses CloudFlare; .accounts is normally a dynamic attr.
    # We patch on the instance after init AND verify via the listing-shape (synthesized).
    from cds.CloudflareWrapper import CloudflareWrapper
    with patch.object(CloudflareWrapper, "accounts", new=MagicMock(), create=True) as fake_accounts:
        cw = CloudflareWrapper()

        assert cw.use is True
        assert cw.all_accounts == [
            {"id": "aaa111", "name": "aaa111"},
            {"id": "bbb222", "name": "bbb222"},
        ]
        fake_accounts.get.assert_not_called()


def test_no_account_ids_falls_back_to_listing(cf_cfg, patched_cf_init):
    cf_cfg("[CloudFlare]\ntoken = dummy\n")

    fake_listing = [
        {"id": "real-account-1", "name": "Real Account 1"},
        {"id": "real-account-2", "name": "Real Account 2"},
    ]
    from cds.CloudflareWrapper import CloudflareWrapper
    fake_accounts = MagicMock()
    fake_accounts.get.return_value = fake_listing
    with patch.object(CloudflareWrapper, "accounts", new=fake_accounts, create=True):
        cw = CloudflareWrapper()

        assert cw.use is True
        assert cw.all_accounts == fake_listing
        fake_accounts.get.assert_called_once_with()


def test_listing_apierror_degrades_gracefully(cf_cfg, patched_cf_init, caplog):
    cf_cfg("[CloudFlare]\ntoken = dummy\n")

    from cds.CloudflareWrapper import CloudflareWrapper
    fake_accounts = MagicMock()
    fake_accounts.get.side_effect = CloudFlareAPIError(503, "Service Unavailable")
    with patch.object(CloudflareWrapper, "accounts", new=fake_accounts, create=True):
        cw = CloudflareWrapper()  # must not raise

        assert cw.use is False
        assert cw.all_accounts == []


def test_missing_cf_config_use_false(cf_cfg, patched_cf_init, tmp_path, monkeypatch):
    # Point at a path that does NOT exist
    from cds import CloudflareWrapper as cw_mod
    missing = tmp_path / "does-not-exist.cfg"
    monkeypatch.setattr(cw_mod, "cf_config_filename", str(missing))

    from cds.CloudflareWrapper import CloudflareWrapper
    fake_accounts = MagicMock()
    with patch.object(CloudflareWrapper, "accounts", new=fake_accounts, create=True):
        cw = CloudflareWrapper()

        assert cw.use is False
        assert cw.all_accounts == []
        fake_accounts.get.assert_not_called()


def test_block_ip_iterates_configured_accounts_only(cf_cfg, patched_cf_init):
    cf_cfg(
        "[CloudFlare]\n"
        "token = dummy\n"
        "account_ids = aaa, bbb\n"
    )

    from cds.CloudflareWrapper import CloudflareWrapper
    fake_accounts = MagicMock()
    with patch.object(CloudflareWrapper, "accounts", new=fake_accounts, create=True):
        cw = CloudflareWrapper()
        cw.block_ip("192.0.2.1")

        post = fake_accounts.firewall.access_rules.rules.post
        assert post.call_count == 2
        called_account_ids = [c.args[0] for c in post.call_args_list]
        assert called_account_ids == ["aaa", "bbb"]
        # rule body sanity check
        first_data = post.call_args_list[0].kwargs["data"]
        assert first_data["mode"] == "block"
        assert first_data["configuration"]["target"] == "ip"
        assert first_data["configuration"]["value"] == "192.0.2.1"


def test_unblock_ip_searches_and_deletes_per_account(cf_cfg, patched_cf_init):
    cf_cfg(
        "[CloudFlare]\n"
        "token = dummy\n"
        "account_ids = aaa, bbb\n"
    )

    from cds.CloudflareWrapper import CloudflareWrapper
    fake_accounts = MagicMock()
    # Two rules in account aaa, one rule in account bbb
    rules_by_account = {
        "aaa": [{"id": "rule-aaa-1"}, {"id": "rule-aaa-2"}],
        "bbb": [{"id": "rule-bbb-1"}],
    }
    fake_accounts.firewall.access_rules.rules.get.side_effect = (
        lambda account_id, params=None: rules_by_account[account_id]
    )

    with patch.object(CloudflareWrapper, "accounts", new=fake_accounts, create=True):
        cw = CloudflareWrapper()
        cw.unblock_ip("192.0.2.5")

        get = fake_accounts.firewall.access_rules.rules.get
        delete = fake_accounts.firewall.access_rules.rules.delete

        # one GET per (account, network)
        assert get.call_count == 2
        for args, kwargs in get.call_args_list:
            assert kwargs["params"]["mode"] == "block"
            assert kwargs["params"]["configuration.target"] == "ip"
            assert kwargs["params"]["configuration.value"] == "192.0.2.5"

        # three DELETEs total: aaa x2 + bbb x1
        assert delete.call_count == 3
        delete.assert_any_call("aaa", "rule-aaa-1")
        delete.assert_any_call("aaa", "rule-aaa-2")
        delete.assert_any_call("bbb", "rule-bbb-1")


def test_unblock_ip_continues_on_per_account_error(cf_cfg, patched_cf_init):
    cf_cfg(
        "[CloudFlare]\n"
        "token = dummy\n"
        "account_ids = aaa, bbb\n"
    )

    from cds.CloudflareWrapper import CloudflareWrapper
    fake_accounts = MagicMock()

    def get_side_effect(account_id, params=None):
        if account_id == "aaa":
            raise CloudFlareAPIError(500, "transient")
        return [{"id": "rule-bbb-1"}]

    fake_accounts.firewall.access_rules.rules.get.side_effect = get_side_effect

    with patch.object(CloudflareWrapper, "accounts", new=fake_accounts, create=True):
        cw = CloudflareWrapper()
        cw.unblock_ip("192.0.2.5")  # must not raise

        # bbb still got its delete despite aaa's get failing
        delete = fake_accounts.firewall.access_rules.rules.delete
        delete.assert_called_once_with("bbb", "rule-bbb-1")


def test_unblock_ip_noop_when_use_false(cf_cfg, patched_cf_init, tmp_path, monkeypatch):
    # Force use=False by pointing at a missing cfg
    from cds import CloudflareWrapper as cw_mod
    monkeypatch.setattr(cw_mod, "cf_config_filename", str(tmp_path / "missing"))

    from cds.CloudflareWrapper import CloudflareWrapper
    fake_accounts = MagicMock()
    with patch.object(CloudflareWrapper, "accounts", new=fake_accounts, create=True):
        cw = CloudflareWrapper()
        assert cw.use is False
        cw.unblock_ip("192.0.2.5")

        fake_accounts.firewall.access_rules.rules.get.assert_not_called()
        fake_accounts.firewall.access_rules.rules.delete.assert_not_called()
