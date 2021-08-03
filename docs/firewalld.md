# FirewallD

## Bugs

Unfortunately, FirewallD has notorious bugs like [this one](https://bugzilla.redhat.com/show_bug.cgi?id=1836571).
This issue is very severe and occurs when you attempt to block overlapping networks.
It causes the server to appear down and its network connectivity will appear down.

To fix this, run the following to reset FirewallD completely:

```bash
sudo systemctl stop firewalld
sudo rm -rf /etc/firewalld/{zones,ipsets}
sudo systemctl restart firewalld
```

To ensure this does not happen: either wait FirewallD to fix it, or install package `python3-aggregate6` (CentOS/RHEL 8),
or `python2-aggregate6` (CentOS/RHEL 7). Then `fds` will automagically use the installed module and aggregate
blocked networks. At this time, the aggregate packages are available by [subscription](https://www.getpagespeed.com/repo-subscribe) only.