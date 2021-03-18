# Cloudflare integration

`fds` is capable of working with FirewallD and Cloudflare at the same time.

This means that blocking IP address or networks propagates to both FirewallD and Cloudflare, thus allowing you to
prevent more malicious connections.

The Cloudflare firewall allows only blocking single IP addresses and specific network ranges.
`fds` will automatically convert and chunk networks to appropriate subnets for Cloudflare.

So with `fds` you can easily block, e.g. 114.119.128.0/18 on Cloudflare.
It is smart enough to chunk that to [multiple /24 networks](http://jodies.de/ipcalc?host=114.119.128.0&mask1=18&mask2=24).
You cannot easily do that with Cloudflare's own interface!
