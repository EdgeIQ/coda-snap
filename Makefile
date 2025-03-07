.PHONY: build

SNAPCRAFT := $(shell if snapcraft --version > /dev/null 2>&1; then echo snapcraft; else echo sudo snapcraft; fi)
LXD := $(shell if lxd --version > /dev/null 2>&1; then echo lxd; else echo sudo lxd; fi)
SNAP := sudo snap

EDGEIQ_SNAP_NAME ?= coda
EDGEIQ_API_URL ?= https://api.edgeiq.io
EDGEIQ_CODA_VERSION ?= latest
EDGEIQ_CODA_SNAP_VERSION ?= $(shell echo $(EDGEIQ_CODA_VERSION) | sed 's/_/-/g')
SNAPCRAFT_CHANNEL ?= "edge,beta,candidate,stable"

setup:
	$(SNAP) install snapcraft --classic
	$(SNAP) install lxd
	$(LXD) init --auto

template:
	rm -rf snap/snapcraft.yaml
	cp snap/local/snapcraft.template.yaml snap/snapcraft.yaml
	sed -i 's#{{EDGEIQ_SNAP_NAME}}#'"$(EDGEIQ_SNAP_NAME)"'#' snap/snapcraft.yaml
	sed -i 's#{{EDGEIQ_API_URL}}#'"$(EDGEIQ_API_URL)"'#' snap/snapcraft.yaml
	sed -i 's#{{EDGEIQ_CODA_SNAP_VERSION}}#'"$(EDGEIQ_CODA_SNAP_VERSION)"'#' snap/snapcraft.yaml
	sed -i 's#{{EDGEIQ_CODA_VERSION}}#'"$(EDGEIQ_CODA_VERSION)"'#' snap/snapcraft.yaml

build:
	$(MAKE) template
	$(SNAPCRAFT) --use-lxd

build-interactive:
	$(MAKE) template
	$(SNAPCRAFT) build --shell --use-lxd

clean:
	$(LXD) shutdown
	$(SNAPCRAFT) clean --use-lxd
	rm -rf snap/*.snap
	rm -rf $(EDGEIQ_SNAP_NAME)*.snap
	rm -rf $(EDGEIQ_SNAP_NAME)*.txt

uninstall:
	$(SNAP) remove $(EDGEIQ_SNAP_NAME)

install:
	$(SNAP) install --dangerous $(EDGEIQ_SNAP_NAME)*.snap
	$(MAKE) connect

connect:
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):home :home
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):shutdown :shutdown
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):snapd-control :snapd-control
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):hardware-observe :hardware-observe
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):system-observe :system-observe
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):network :network
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):network-bind :network-bind
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):network-control :network-control
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):network-manager :network-manager
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):network-manager-observe :network-manager-observe
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):network-observe :network-observe
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):network-setup-control :network-setup-control
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):network-setup-observe :network-setup-observe
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):network-status :network-status
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):modem-manager :modem-manager
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):ppp :ppp
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):firewall-control :firewall-control
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):tpm :tpm
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):log-observe :log-observe
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):physical-memory-observe :physical-memory-observe
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):mount-observe :mount-observe
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):ssh-public-keys :ssh-public-keys
	$(SNAP) connect $(EDGEIQ_SNAP_NAME):raw-usb :raw-usb

login:
	$(SNAPCRAFT) export-login --snaps=$(EDGEIQ_SNAP_NAME) --acls package_access,package_push,package_update,package_release ./exported.txt

remote-build:
	$(SNAPCRAFT) remote-build --launchpad-accept-public-upload --launchpad-timeout 3600 --build-for=amd64,armhf,arm64

publish:
	$(SNAPCRAFT) upload --release=$(SNAPCRAFT_CHANNEL) $(EDGEIQ_SNAP_NAME)*.snap