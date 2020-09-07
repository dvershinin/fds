# fds
 
The go-to FirewallD CLI app.

### Why FirewallD doesn't suck?
 
 Firewall management is often a task that you do once at the time of setting up a server.
 FirewallD is so great with the concepts of zones, source, support for IP sets.
 
 But if you're maintaining a server like a PRO, you are monitoring logs, and blocking malicious users as they come, on a *regular basis*.
 
 Blocking and managing blocked IP addresses, is where, unfortunately, `firewall-cmd` is very awkward to use.
 And if you're using Cloudflare firewall, you also want to propagate your blocked IP addresses there for even better protection.
 
`fds` is the CLI wrapper for FirewallD/Cloudflare, that you'll love to use any day.

It makes the task of managing your FirewallD easy and human-friendly :-)

## BETA !!! HIGHLY NON-FUNCTIONAL

## Goals 

The `fds` is utility program for users of FirewallD. It is a helper to easily perform day-to-day 
firewall tasks:

* block countries
* block ranges in the Cloudflare firewall (kinda helper firewall for cloudflare) 
and works with both firewalld and cloudflare, e.g. http://jodies.de/ipcalc?host=114.119.128.0&mask1=18&mask2=24
* declare a CDN of servers and push blocking commands across those server from one place (ansible-like), useful for dynamic blocking
from the central server (honeypot)
* drop outbound connections (shortcut to https://cogitantium.blogspot.com/2017/06/how-to-drop-outbound-connections-with.html) 

# Synopsys

### Works

### Ban a single IP

```bash
fds block 1.2.3.4
```

This blocks IP address in a proper(©) fashion by ensuring that the IP is in a set named `networkblock4`,
that the set is a source to FirewallD's `drop` zone. Using IP sets is the corner stone of consistent
firewall management!

### Planned

```bash
fds block <Country Name>
```

## Installation on CentOS/RHEL 7, 8

```bash
sudo yum -y install https://extras.getpagespeed.com/release-latest.rpm
sudo yum -y install fds
```

See contributing guide for development setup (if not using packages).

## Files

* /etc/fds.conf
* /var/lib/fds: zone files, info on what is currently blocked (state data)
* /var/cache/fds: cachecontrol cache