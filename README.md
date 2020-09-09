# fds
 
The go-to **F**irewallD CLI app that **d**oesn't **s**uck.

### What is `fds`?
 
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

## What `fds` can do 

The `fds` is utility program for users of FirewallD. It is a helper to easily perform day-to-day 
firewall tasks:

* block countries
* block arbitrary IP addresses

# Synopsys

## Ban a single IP

```bash
fds block 1.2.3.4
```

This blocks IP address in a proper(©) fashion by ensuring that the IP is in a set named `networkblock4`,
that the set is a source to FirewallD's `drop` zone. Using IP sets is the corner stone of consistent
firewall management!

## Ban a country

```bash
fds block <Country Name>
fds block China
```

## Reset bans

```bash
fds reset
```

### Planned

* block ranges in the Cloudflare firewall (kinda helper firewall for cloudflare) 
and works with both firewalld and cloudflare, e.g. http://jodies.de/ipcalc?host=114.119.128.0&mask1=18&mask2=24
* declare a CDN of servers and push blocking commands across those server from one place (ansible-like), useful for dynamic blocking
from the central server (honeypot)
* drop outbound connections (shortcut to https://cogitantium.blogspot.com/2017/06/how-to-drop-outbound-connections-with.html) 

## Installation on CentOS/RHEL 7, 8

```bash
sudo yum -y install https://extras.getpagespeed.com/release-latest.rpm
sudo yum -y install fds
```

See contributing guide for development setup (if not using packages).

## Files

* `/etc/fds.conf` (info on currently blocked countries or otherwise small data sets suitable for a single config file)
* `/var/lib/fds`: zone files, (state data) + (info on what is currently blocked) (???)
* `/var/cache/fds`: cachecontrol cache