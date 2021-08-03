# fds
 
The go-to **F**irewallD CLI app that **d**oesn't **s**uck.

## What is `fds`?
 
Firewall management is often a task that you do once at the time of setting up a server.
But if you're maintaining a server like a PRO, you are monitoring logs, and blocking malicious users as they come, on a *regular basis*.

FirewallD is a great firewall software. It has the concepts of zones, sources, and supports IP sets. 
However, its client app, `firewall-cmd` is far from user-friendly when it comes to blocking and managing blocked IP addresses.
Furthermore, if you also use Cloudflare firewall, you also want to propagate your blocked IP addresses to it for best protection.
 
`fds` is the CLI client for FirewallD/Cloudflare, that you'll love to use any day.
It is an alternative, client for FirewallD.

Use it for simple or complex banning tasks, instead of `firewall-cmd`.

Look how simple things are with `fds`:

```bash
fds block <country name>
fds block 1.2.3.4
```

It makes the task of managing your FirewallD easy and human-friendly.

## Installation on CentOS/RHEL 7, 8 and Fedora 33, 34

First, install RPM repository configuration:

```bash
sudo yum -y install https://extras.getpagespeed.com/release-latest.rpm
```

## Free installation

For free installation and usage, disable the binary packages sub-repository,
which contains non-essential dependencies for `fds`:

```bash
sudo yum -y install yum-utils
sudo yum-config-manager --disable getpagespeed-extras
```

Now you can install `fds`:

```bash
sudo yum -y install fds
```

## Installation with subscription

By [subscribing to the GetPageSpeed RPM repository](https://www.getpagespeed.com/repo-subscribe), you gain access to a [number of packages](https://extras.getpagespeed.com/redhat/8/x86_64/repoview/) other than `fds`, as well support its development.

Simply run this command:

```bash
sudo yum -y install fds
```

The subscription ships with packages for IP prefixes' aggregation.
`fds` can use those, and thus essentially overcome some [serious FirewallD bugs](https://fds.getpagespeed.com/firewalld/).

So it's highly recommended to also run the following if you are a subscriber:

### CentOS/RHEL 7

```bash
sudo yum -y install python2-aggregate6
```

### CentOS/RHEL 8

```bash
sudo yum -y install python3-aggregate6
```




## What `fds` can do 

The `fds` is utility program for users of FirewallD. It is a helper to easily perform day-to-day 
firewall tasks:

* block users of Tor
* block countries
* block arbitrary IP addresses
* block the same over at Cloudflare

### Integrations

By default, `fds` only operates with FirewallD. 

To enable [Cloudflare integration](docs/cloudflare.md), run:
 
    fds config 

## Block Tor

You can block all Tor exit nodes by running:

```bash
fds block tor
```

Note that since these addresses constantly change, you may want to run this command in a cron.

## Ban a single IP

```bash
fds block 1.2.3.4
```

This blocks IP address in a proper(©) fashion by ensuring that the IP is in a set named `networkblock4`,
that the set is a source to FirewallD's `drop` zone. Using IP sets is the corner stone of consistent
firewall management!

`fds` is also smart enough to break any existing connections originating from that IP address.
Useful if malicious requests are in process.

You can specify base name of created/used IP set for blocking, by specifying it in `--ipset`, e.g.
for `banned4` (IPv4) or `banned4` (IPv6), use:

```bash
fds block 1.2.3.4 --ipset banned
```

## Ban a country or a continent

```bash
fds block <Country Name>
fds block China
fds block Asia
```

To block a country which has spaces in its name, use quotes:

```bash
fds block "Country Name"
```

You can list all country names available for blocking by running:

```bash
fds list countries
``` 

You can list all continents available for blocking by running:

```bash
fds list continents
``` 



### `--no-reload` (`-nr`)

Use this optional flag to prevent FirewallD from being reloaded.
This is only useful when adding multiple blocks, as it ensure faster blocking:

```bash
fds block 1.2.3.4 --no-reload
fds block 2.3.4.5 --no-reload
fds block Country1 --no-reload
...
fds block Country2
```

In the above example, we block some IP addresses and a few countries.
The last block operation will reload FirewallD and actually apply our ban.

Alternatively, invoke all `fds block` with `--no-reload` option and invoke `firewall-cmd --reload`
in the end.

## List all blocked networks and countries

The following allows to easily see what is blocked: 

```bash
fds list blocked
``` 

## Unblock a country or IP/network

Use `fds unblock ...` like the following:

```fds
fds unblock China
fds unblock 1.2.3.4
```

## Reset all bans

You can quickly remove all blocks (and by that, all IP sets associated with `fds`):

```bash
fds reset
```

## Notes

The `fds` package automatically installs a cron job that syncs your blocked IP sets daily.
So there is no need to do anything to ensure a country (or Tor) stays blocked.

### Planned

* declare a CDN of servers and push blocking commands across those server from one place (ansible-like), useful for dynamic blocking
from the central server (honeypot)
* drop outbound connections (shortcut to https://cogitantium.blogspot.com/2017/06/how-to-drop-outbound-connections-with.html) 

See contributing guide for development setup (if not using packages).

## Files

* not in use: `/etc/fds.conf` (info on currently blocked countries or otherwise small data sets suitable for a single config file)
* not in use: `/var/lib/fds`: zone files, (state data) + (info on what is currently blocked) (???)
* `/var/cache/fds`: cachecontrol cache
* `/root/.cloudflare/cloudflare.cfg` Cloudflare authentication
