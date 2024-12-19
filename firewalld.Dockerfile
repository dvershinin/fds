FROM eniocarboni/docker-rockylinux-systemd:latest

## Install systemd and firewalld
#RUN yum install -y systemd firewalld dbus python3-pip git \
#    && yum clean all \
#    && systemctl enable firewalld

# Set up the working directory
WORKDIR /app

# Copy your Python project files into the Docker image
COPY . /app

RUN echo "ref-names: HEAD -> master, tag: v0" > ".git_archival.txt"

# Install your Python project
RUN pip3 install .

# Copy the test script into the Docker image
COPY firewalld-tests.sh firewalld-tests.sh
RUN chmod +x firewalld-tests.sh

## Override systemd defaults
#RUN mkdir -p /etc/systemd/system/service.d
#RUN echo '[Service]' > /etc/systemd/system/service.d/override.conf
#RUN echo 'ExecStart=' >> /etc/systemd/system/service.d/override.conf
#RUN echo 'ExecStart=/usr/lib/systemd/systemd' >> /etc/systemd/system/service.d/override.conf
#
#VOLUME [ "/sys/fs/cgroup" ]

CMD ["/sbin/init"]
