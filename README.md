script for firewalld, helper to easily:

* block countries
* block ranges in cloudflare firewall (kinda helper firewall for cloudflare) 
and works with both firewalld and cloudflare, e.g. http://jodies.de/ipcalc?host=114.119.128.0&mask1=18&mask2=24
* declare a CDN of servers and push blocking commands across those server from one place (ansible-like), useful for dynamic blocking
from the central server (honeypot)
* drop outbound connections (shortcut to https://cogitantium.blogspot.com/2017/06/how-to-drop-outbound-connections-with.html) 


sudo yum -y install python3-firewall

For use with Python 3:

  python3-dbus
  python3-slip-dbus
  python3-decorator
  python3-gobject
  python3-nftables (nftables >= 0.9.3)
  