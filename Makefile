.PHONY: build

EDGEIQ_SNAP_NAME ?= coda
EDGEIQ_API_URL ?= https://api.edgeiq.io
EDGEIQ_CODA_VERSION ?= latest
EDGEIQ_CODA_SNAP_VERSION ?= $(shell echo $(EDGEIQ_CODA_VERSION) | sed 's/_/-/g')
SNAPCRAFT_CHANNEL ?= stable

setup:
	sudo snap install snapcraft --classic
	sudo snap install lxd
	sudo lxd init --auto

template:
	rm -rf snap/snapcraft.yaml
	cp snap/local/snapcraft.template.yaml snap/snapcraft.yaml
	sed -i 's#{{EDGEIQ_SNAP_NAME}}#'"$(EDGEIQ_SNAP_NAME)"'#' snap/snapcraft.yaml
	sed -i 's#{{EDGEIQ_API_URL}}#'"$(EDGEIQ_API_URL)"'#' snap/snapcraft.yaml
	sed -i 's#{{EDGEIQ_CODA_SNAP_VERSION}}#'"$(EDGEIQ_CODA_SNAP_VERSION)"'#' snap/snapcraft.yaml
	sed -i 's#{{EDGEIQ_CODA_VERSION}}#'"$(EDGEIQ_CODA_VERSION)"'#' snap/snapcraft.yaml

build:
	$(MAKE) template
	sudo snapcraft --use-lxd

build-interactive:
	$(MAKE) template
	sudo snapcraft build --shell --use-lxd

clean:
	sudo lxd shutdown
	snapcraft clean --use-lxd
	rm -rf snap/*.snap
	rm -rf *.snap

uninstall:
	sudo snap remove $(EDGEIQ_SNAP_NAME)

install:
	sudo snap install --dangerous $(EDGEIQ_SNAP_NAME)*.snap
	sudo snap connect $(EDGEIQ_SNAP_NAME):home :home
	sudo snap connect $(EDGEIQ_SNAP_NAME):shutdown :shutdown
	sudo snap connect $(EDGEIQ_SNAP_NAME):snapd-control :snapd-control
	sudo snap connect $(EDGEIQ_SNAP_NAME):hardware-observe :hardware-observe
	sudo snap connect $(EDGEIQ_SNAP_NAME):network :network
	sudo snap connect $(EDGEIQ_SNAP_NAME):network-bind :network-bind
	sudo snap connect $(EDGEIQ_SNAP_NAME):network-control :network-control
	sudo snap connect $(EDGEIQ_SNAP_NAME):network-manager :network-manager
	sudo snap connect $(EDGEIQ_SNAP_NAME):network-manager-observe :network-manager-observe
	sudo snap connect $(EDGEIQ_SNAP_NAME):network-observe :network-observe
	sudo snap connect $(EDGEIQ_SNAP_NAME):network-setup-control :network-setup-control
	sudo snap connect $(EDGEIQ_SNAP_NAME):network-setup-observe :network-setup-observe
	sudo snap connect $(EDGEIQ_SNAP_NAME):network-status :network-status
	sudo snap connect $(EDGEIQ_SNAP_NAME):modem-manager :modem-manager
	sudo snap connect $(EDGEIQ_SNAP_NAME):ppp :ppp
	sudo snap connect $(EDGEIQ_SNAP_NAME):firewall-control :firewall-control
	sudo snap connect $(EDGEIQ_SNAP_NAME):tpm :tpm

login:
	snapcraft export-login --snaps=$(EDGEIQ_SNAP_NAME) --acls package_access,package_push,package_update,package_release ./exported.txt

publish:
	export SNAPCRAFT_STORE_CREDENTIALS=$(shell cat ./exported.txt)
	snapcraft upload --release=$(SNAPCRAFT_CHANNEL) $(EDGEIQ_SNAP_NAME)*.snap