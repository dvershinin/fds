# fds

Keep runtime code compatible with Python 2.7: production EL7 uses python2-fds.
The default branch is master. RPM CI is myci, using `.myci/settings.yml` to
select `.circleci/config.yml`; real `v*` tags enable package publication.

## Testing

Fast suite (no live Cloudflare or firewall operations):

```sh
~/.virtualenvs/fds-tests/bin/python -m pytest tests/test_cloudflare_wrapper.py tests/test_unblock_atomicity.py tests/test_py2_compat.py -q
```

Bootstrap the dedicated environment if necessary:

```sh
uv venv --python 3.12 ~/.virtualenvs/fds-tests
uv pip install --python ~/.virtualenvs/fds-tests/bin/python pytest mock six netaddr 'cloudflare>=2.7.1,<2.20' appdirs cachecontrol tqdm requests psutil
```

The platform import check skips when dbus/firewalld bindings are unavailable.
The atomicity suite uses import-only substitutes on macOS, and real bindings
on Linux; backend calls are test doubles. Also run it with Python 2.7 and
real EL7 bindings before shipping (`python2 -m unittest discover -s tests
-p test_unblock_atomicity.py`). Use a temporary checkout so the installed
package cannot mask source imports. EL7's `mock` package is sufficient.

`tests/test_unblock_region.py` requires a separately provisioned Docker
firewalld container and network country lists; it is not part of the fast suite.
For release verification, exercise a documentation-only IP in both runtime
and permanent firewalld state and a controlled Cloudflare block, verifying
absence through both account and legacy user API views after unblocking.
Never use a real customer or administrator IP as the test target.
