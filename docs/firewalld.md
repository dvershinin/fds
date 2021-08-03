# FirewallD

## Bugs

Unfortunately, FirewallD has notorious bugs like [this one](https://bugzilla.redhat.com/show_bug.cgi?id=1836571).
This issue is very severe and occurs when you attempt to block overlapping networks.
It causes the server to appear down and its network connectivity will appear down.

To fix this once it happened, run the following to reset FirewallD completely:

```bash
sudo systemctl stop firewalld
sudo rm -rf /etc/firewalld/{zones,ipsets}
sudo systemctl restart firewalld
```

To ensure this does not happen, either:
 
* wait FirewallD to fix it
* ensure that you do not attempt to block an IP/network that may be a subset of a network you have already blocked
* optimally, install aggregation packages (see below)

#### ! Important note !

At this time, the aggregate packages are available by [subscription](https://www.getpagespeed.com/repo-subscribe) only.
This helps continued development of `fds` and other tools, as well as grants you access to a multitude of premium RPM
packages for CentOS/RHEL.

## CentOS/RHEL 8

```bash
sudo dnf -y install python3-aggregate6
```

## CentOS/RHEL 7

```bash
sudo yum -y install python2-aggregate6
```

Now `fds` will automagically use the installed module and aggregate blocked networks, when blocking.
Thus essentially overcoming the FirewallD bug altogether.