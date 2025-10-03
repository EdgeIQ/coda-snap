FROM jrei/systemd-ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
# Disable snapd re-execution to avoid issues with core snap in containers
ENV SNAP_REEXEC=0

# Install snapd and dependencies
RUN apt-get update && \
    apt-get install -y \
    iproute2 \
    ubuntu-standard \
    snapd \
    squashfuse \
    fuse \
    python3 \
    python3-pip

# Remove unused packages
RUN apt-get autoremove -y && \
    apt-get clean

# Create necessary directories
RUN mkdir -p /run/snapd

# Set SNAP_REEXEC=0 globally for all systemd services
RUN mkdir -p /etc/systemd/system.conf.d && \
    echo '[Manager]' > /etc/systemd/system.conf.d/snap-reexec.conf && \
    echo 'DefaultEnvironment="SNAP_REEXEC=0"' >> /etc/systemd/system.conf.d/snap-reexec.conf

# Override snapd service to set SNAP_REEXEC=0
RUN mkdir -p /etc/systemd/system/snapd.service.d && \
    echo '[Service]' > /etc/systemd/system/snapd.service.d/no-reexec.conf && \
    echo 'Environment="SNAP_REEXEC=0"' >> /etc/systemd/system/snapd.service.d/no-reexec.conf

# Enable snapd services
RUN systemctl enable snapd.socket snapd.service

CMD ["/sbin/init"]
