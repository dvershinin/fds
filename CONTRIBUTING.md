## Local development setup

You basically need a virtualenv created with and setup `fds` using it.
Since `fds` mostly is meant to be run as superuser, ensure that `sudo /path/to/venv/bin/python` runs without prompts.?

Complete walkthrough:

* Ensure FirewallD is installed:  
`sudo yum -y firewalld`
* Create installation tree:  
`sudo mkdir -p /opt/fds`
* Fetch `fds`:  
`sudo git clone https://github.com/dvershinin/fds.git /opt/fds`
* Create a virtualenv with system's Python version and access to system-wide packages:   
`sudo virtualenv  --system-site-packages /opt/fds/venv`

sudo mkdir -p /var/cache/fds /var/lib/fds


Running as regular user:

sudo visudo -f /etc/sudoers.d/python-fds

danila ALL=(ALL) NOPASSWD: /opt/fds/venv/bin/python

danila ALL=(ALL) NOPASSWD: /home/danila/Projects/fds/venv/bin/python

Pycharm: ensure "Emulate terminal" in run configurations, in order not to be prompted for authentication.