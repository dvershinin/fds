FROM rockylinux:9

# Install systemd and firewalld
RUN yum install -y systemd firewalld dbus python3-pip git \
    && yum clean all \
    && systemctl enable firewalld

# Set up the working directory
WORKDIR /app

# Copy your Python project files into the Docker image
COPY . /app

RUN echo "ref-names: HEAD -> master, tag: v0" > ".git_archival.txt"

# Install your Python project
RUN pip3 install .

# Copy the test script into the Docker image
COPY firewalld-tests.sh tests/firewalld-tests.sh
RUN chmod +x tests/firewalld-tests.sh

# Remove unnecessary systemd targets and set the default target to multi-user
RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done); \
    rm -f /lib/systemd/system/multi-user.target.wants/*;\
    rm -f /etc/systemd/system/*.wants/*;\
    rm -f /lib/systemd/system/local-fs.target.wants/*; \
    rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
    rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
    rm -f /lib/systemd/system/basic.target.wants/*; \
    rm -f /lib/systemd/system/anaconda.target.wants/*; \
    systemctl set-default multi-user.target

# Override systemd defaults
RUN mkdir -p /etc/systemd/system/service.d
RUN echo '[Service]' > /etc/systemd/system/service.d/override.conf
RUN echo 'ExecStart=' >> /etc/systemd/system/service.d/override.conf
RUN echo 'ExecStart=/usr/lib/systemd/systemd' >> /etc/systemd/system/service.d/override.conf

VOLUME [ "/sys/fs/cgroup" ]

CMD ["/sbin/init"]
