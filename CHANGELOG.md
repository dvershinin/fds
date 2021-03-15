# Changelog
All notable changes to this project will be documented in this file.

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
