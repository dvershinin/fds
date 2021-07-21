# Changelog
All notable changes to this project will be documented in this file.

## [0.0.22] - 2021-07-21
### Fixed
* Auto-start FirewallD if not running
* Validate Cloudflare token upon saving

## [0.0.21] - 2021-06-08
### Fixed
* RPM requires python-psutil

## [0.0.20] - 2021-04-22
### Fixed
* RPM requires python-psutil

## [0.0.19] - 2021-04-21
### Fixed
* Incorrect capitalization of country names

## [0.0.18] - 2021-04-07
### Added
* Cloudflare: Fallback to Captcha challenge when account is not eligible for complete country block #11

## [0.0.17] - 2021-04-04
### Fixed
* `fds cron` is now functional
### Added
* Support for lowercase country names in `fds block`
* Fix `conntrack` invocation on Python 2 / CentOS 7

## [0.0.16] - 2021-03-17
### Added
* `fds block` now accepts `--ipset` argument for specifying base of IP set name
* Unicode fixes for Python 2
* Cloudflare integration
* Break existing connection when blocking an IP

## [0.0.11] - 2021-03-17
### Added
* `fds cron`. When using packaged install, this is automatically there for you.

## [0.0.10] - 2021-03-15
### Added
* `fds block` now has new option `--no-reload` to skip reloading FirewallD.
 Useful when adding many blocks at once. 
 
## [0.0.9] - 2021-02-20
### Added
* `fds block tor` allows to easily ban Tor users

## [0.0.8] - 2021-01-16
### Fixed
* `reset` action no longer destroys all IP sets, only `fds` specific ones 
### Added
* `fds list blocked` allows to easily see what is blocked 
* `fds list countries` lists all country names available for blocking
* `fds unblock <ip>` allows unblocking an individual IP address or network
