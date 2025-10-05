.PHONY: help build setup template build-no-lxd build-interactive clean uninstall install connect login remote-build publish \
        install-multipass vm-create vm-delete vm-shell shell vm-info vm-list vm-wait-for-snapd \
        vm-services-setup vm-services-start vm-services-stop vm-services-logs e2e-tests-status e2e-tests-setup test e2e-tests-test-full e2e-tests-test \
        e2e-tests-clean e2e-tests-logs

SNAPCRAFT := $(shell if snapcraft --version > /dev/null 2>&1; then echo snapcraft; else echo sudo snapcraft; fi)
LXD := $(shell if lxd --version > /dev/null 2>&1; then echo lxd; else echo sudo lxd; fi)
SNAP := sudo snap

EDGEIQ_SNAP_NAME ?= coda
EDGEIQ_API_URL ?= https://api.edgeiq.io
EDGEIQ_CODA_VERSION ?= latest
EDGEIQ_CODA_SNAP_VERSION ?= $(shell echo $(EDGEIQ_CODA_VERSION) | sed 's/_/-/g')
SNAPCRAFT_CHANNEL ?= "edge,beta,candidate,stable"

# E2E Test Configuration
MULTIPASS_VM_NAME ?= coda-test-vm
MULTIPASS_VM_CPUS ?= 2
MULTIPASS_VM_MEMORY ?= 2G
MULTIPASS_VM_DISK ?= 10G
CLOUD_INIT_FILE ?= e2e-tests/cloud-init.yaml
MOCK_SERVER_PORT ?= 8080
MQTT_PORT ?= 1883

# Color output
COLOR_RESET := \033[0m
COLOR_BOLD := \033[1m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_BLUE := \033[36m
COLOR_RED := \033[31m

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

build-no-lxd:
	$(MAKE) template
	$(SNAPCRAFT) --destructive-mode

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

# ==============================================================================
# E2E Testing Targets - Multipass-based Testing
# ==============================================================================

install-multipass: ## Install Multipass (if not installed)
	@echo "$(COLOR_GREEN)Checking for Multipass installation...$(COLOR_RESET)"
	@which multipass > /dev/null 2>&1 || \
		(echo "$(COLOR_YELLOW)Installing Multipass via Homebrew...$(COLOR_RESET)" && brew install multipass)
	@echo "$(COLOR_GREEN)✓ Multipass is installed$(COLOR_RESET)"
	@multipass version

vm-create: ## Create Multipass VM for testing
	@echo "$(COLOR_GREEN)Creating Multipass VM: $(MULTIPASS_VM_NAME)$(COLOR_RESET)"
	@multipass launch 24.04 \
		--name $(MULTIPASS_VM_NAME) \
		--cpus $(MULTIPASS_VM_CPUS) \
		--memory $(MULTIPASS_VM_MEMORY) \
		--disk $(MULTIPASS_VM_DISK) \
		--cloud-init $(CLOUD_INIT_FILE) || \
		(echo "$(COLOR_RED)✗ Failed to create VM$(COLOR_RESET)" && exit 1)
	@echo "$(COLOR_YELLOW)Waiting for VM to be ready...$(COLOR_RESET)"
	@sleep 10
	@$(MAKE) vm-wait-for-snapd
	@$(MAKE) vm-services-setup
	@$(MAKE) vm-services-start
	@echo "$(COLOR_GREEN)✓ VM $(MULTIPASS_VM_NAME) is ready$(COLOR_RESET)"

vm-delete: ## Delete Multipass VM
	@echo "$(COLOR_YELLOW)Deleting VM: $(MULTIPASS_VM_NAME)$(COLOR_RESET)"
	@-multipass delete $(MULTIPASS_VM_NAME) 2>/dev/null
	@-multipass purge 2>/dev/null
	@echo "$(COLOR_GREEN)✓ VM deleted$(COLOR_RESET)"

vm-shell: ## Open shell in Multipass VM
	@echo "$(COLOR_BLUE)Opening shell in $(MULTIPASS_VM_NAME)...$(COLOR_RESET)"
	@multipass shell $(MULTIPASS_VM_NAME)

vm-info: ## Show VM information
	@echo "$(COLOR_BLUE)VM Information:$(COLOR_RESET)"
	@multipass info $(MULTIPASS_VM_NAME)

vm-list: ## List all Multipass VMs
	@echo "$(COLOR_BLUE)All Multipass VMs:$(COLOR_RESET)"
	@multipass list

vm-wait-for-snapd: ## Wait for snapd to be ready in VM
	@echo "$(COLOR_YELLOW)Waiting for snapd to be ready...$(COLOR_RESET)"
	@multipass exec $(MULTIPASS_VM_NAME) -- bash -c ' \
		i=0; \
		while [ $$i -lt 60 ]; do \
			if snap version > /dev/null 2>&1; then \
				echo "✓ snapd is ready"; \
				exit 0; \
			fi; \
			i=$$((i + 1)); \
			sleep 2; \
		done; \
		echo "✗ snapd did not become ready after 120 seconds"; \
		exit 1; \
	' && echo "$(COLOR_GREEN)✓ snapd is ready$(COLOR_RESET)" || \
	(echo "$(COLOR_RED)✗ snapd did not become ready$(COLOR_RESET)" && exit 1)

vm-services-setup: ## Transfer files and setup systemd service in VM
	@echo "$(COLOR_YELLOW)Setting up services in VM...$(COLOR_RESET)"
	@multipass transfer -r e2e-tests/mock-server $(MULTIPASS_VM_NAME):/home/ubuntu/
	@multipass transfer -r e2e-tests/fixtures $(MULTIPASS_VM_NAME):/home/ubuntu/
	@echo "$(COLOR_YELLOW)Installing Python dependencies in VM...$(COLOR_RESET)"
	@multipass exec $(MULTIPASS_VM_NAME) -- bash -c "cd /home/ubuntu/mock-server && pip3 install -r requirements.txt --break-system-packages"
	@echo "$(COLOR_YELLOW)Installing systemd service...$(COLOR_RESET)"
	@multipass exec $(MULTIPASS_VM_NAME) -- sudo cp /home/ubuntu/mock-server/edgeiq-mock-server.service /etc/systemd/system/
	@multipass exec $(MULTIPASS_VM_NAME) -- sudo systemctl daemon-reload
	@multipass exec $(MULTIPASS_VM_NAME) -- sudo systemctl enable edgeiq-mock-server.service
	@echo "$(COLOR_GREEN)✓ Services configured$(COLOR_RESET)"

vm-services-start: ## Start systemd services in VM
	@echo "$(COLOR_YELLOW)Starting mock server service...$(COLOR_RESET)"
	@multipass exec $(MULTIPASS_VM_NAME) -- sudo systemctl start edgeiq-mock-server.service
	@sleep 2
	@echo "$(COLOR_YELLOW)Verifying service status...$(COLOR_RESET)"
	@multipass exec $(MULTIPASS_VM_NAME) -- sudo systemctl is-active edgeiq-mock-server.service || \
		(echo "$(COLOR_RED)✗ Mock server service failed to start$(COLOR_RESET)" && \
		 echo "$(COLOR_YELLOW)Service status:$(COLOR_RESET)" && \
		 multipass exec $(MULTIPASS_VM_NAME) -- sudo systemctl status edgeiq-mock-server.service --no-pager && \
		 echo "$(COLOR_YELLOW)Service logs:$(COLOR_RESET)" && \
		 multipass exec $(MULTIPASS_VM_NAME) -- sudo journalctl -u edgeiq-mock-server.service -n 20 --no-pager && \
		 exit 1)
	@echo "$(COLOR_GREEN)✓ Mock server service is active$(COLOR_RESET)"
	@multipass exec $(MULTIPASS_VM_NAME) -- bash -c 'curl -s http://localhost:8080/health > /dev/null && echo "$(COLOR_GREEN)✓ HTTP server responding on port 8080$(COLOR_RESET)" || echo "$(COLOR_YELLOW)⚠ HTTP server not responding yet$(COLOR_RESET)"'

vm-services-stop: ## Stop systemd services in VM
	@echo "$(COLOR_YELLOW)Stopping services in VM...$(COLOR_RESET)"
	@multipass exec $(MULTIPASS_VM_NAME) -- sudo systemctl stop edgeiq-mock-server.service 2>/dev/null || true
	@echo "$(COLOR_GREEN)✓ Services stopped$(COLOR_RESET)"

e2e-tests-status: ## Show status of services and VM
	@echo "$(COLOR_BLUE)Multipass VMs:$(COLOR_RESET)"
	@multipass list 2>/dev/null || echo "  No VMs found"
	@echo ""
	@echo "$(COLOR_BLUE)Services in VM (if VM exists):$(COLOR_RESET)"
	@if multipass list 2>/dev/null | grep -q $(MULTIPASS_VM_NAME); then \
		echo "  Mock Server:  $$(multipass exec $(MULTIPASS_VM_NAME) -- sudo systemctl is-active edgeiq-mock-server.service 2>/dev/null || echo 'not running')"; \
		echo "  Mosquitto:    $$(multipass exec $(MULTIPASS_VM_NAME) -- sudo systemctl is-active mosquitto.service 2>/dev/null || echo 'not running')"; \
		echo ""; \
		echo "$(COLOR_BLUE)Service Details:$(COLOR_RESET)"; \
		multipass exec $(MULTIPASS_VM_NAME) -- sudo systemctl status edgeiq-mock-server.service --no-pager -l 2>/dev/null || echo "  Service not installed"; \
	else \
		echo "  VM not running"; \
	fi

e2e-tests-setup: ## Create VM and install services (run this first)
	@echo "$(COLOR_BOLD)$(COLOR_GREEN)Setting up E2E test environment...$(COLOR_RESET)"
	@$(MAKE) vm-create
	@echo "$(COLOR_GREEN)✓ E2E test environment ready$(COLOR_RESET)"
	@echo "$(COLOR_BLUE)Run 'make e2e-tests-test' to execute tests$(COLOR_RESET)"

e2e-tests-test-full: ## Run full E2E test suite (create VM, test, cleanup)
	@echo "$(COLOR_BOLD)$(COLOR_GREEN)Starting full E2E test suite...$(COLOR_RESET)"
	@$(MAKE) e2e-tests-setup
	@$(MAKE) e2e-tests-test || (echo "$(COLOR_RED)✗ Tests failed$(COLOR_RESET)" && $(MAKE) teardown && exit 1)
	@$(MAKE) e2e-tests-clean
	@echo "$(COLOR_GREEN)✓ Full E2E test suite completed successfully$(COLOR_RESET)"

e2e-tests-test: ## Run tests with verbose output (VM must be running)
	@echo "$(COLOR_BOLD)$(COLOR_GREEN)Running E2E test suite (verbose mode)...$(COLOR_RESET)"
	@if ! multipass list 2>/dev/null | grep -q $(MULTIPASS_VM_NAME); then \
		echo "$(COLOR_RED)✗ VM not found. Run 'make e2e-tests-setup' first$(COLOR_RESET)"; \
		exit 1; \
	fi
	@cd e2e-tests/test-runner && \
		MULTIPASS_VM_NAME=$(MULTIPASS_VM_NAME) \
		pytest tests/ -vv -s --log-cli-level=DEBUG
	@echo "$(COLOR_GREEN)✓ Tests completed$(COLOR_RESET)"
	
vm-services-logs: ## View service logs from VM
	@echo "$(COLOR_BLUE)Mock Server Service Logs (last 50 lines):$(COLOR_RESET)"
	@multipass exec $(MULTIPASS_VM_NAME) -- sudo journalctl -u edgeiq-mock-server.service -n 50 --no-pager || echo "  Service not running"
	@echo ""
	@echo "$(COLOR_BLUE)Mock Server Application Log:$(COLOR_RESET)"
	@multipass exec $(MULTIPASS_VM_NAME) -- tail -n 50 /home/ubuntu/mock-server/server.log 2>/dev/null || echo "  Log file not found"

e2e-tests-logs: ## Follow service logs in real-time
	@echo "$(COLOR_BLUE)Following mock server logs (Ctrl+C to stop)...$(COLOR_RESET)"
	@multipass exec $(MULTIPASS_VM_NAME) -- sudo journalctl -u edgeiq-mock-server.service -f

e2e-tests-clean:
	@echo "$(COLOR_YELLOW)Tearing down E2E test environment...$(COLOR_RESET)"
	@$(MAKE) vm-services-stop 2>/dev/null || true
	@$(MAKE) vm-delete 2>/dev/null || true
	@rm -rf e2e-tests/test-runner/tests/__pycache__ 2>/dev/null || true
	@rm -rf e2e-tests/test-runner/tests/.pytest_cache 2>/dev/null || true
	@echo "$(COLOR_GREEN)✓ Teardown complete$(COLOR_RESET)"


help:
	@echo "$(COLOR_BOLD)EdgeIQ Coda Snap - Build & Test$(COLOR_RESET)"
	@echo "=========================================="
	@echo ""
	@echo "$(COLOR_BLUE)Snap Build:$(COLOR_RESET)"
	@echo "  make build         Build snap package"
	@echo "  make install       Install snap locally"
	@echo "  make clean         Clean build artifacts"
	@echo ""
	@echo "$(COLOR_BLUE)E2E Testing - VM Configuration:$(COLOR_RESET)"
	@echo "  make e2e-tests-setup     # 1. Create VM and install services"
	@echo "  make e2e-tests-test      # 2. Run tests"
	@echo "  make e2e-tests-clean     # 3. Clean up VM and results"
	@echo ""
	@echo "$(COLOR_BLUE)E2E Testing - Advanced:$(COLOR_RESET)"
	@echo "  make e2e-tests-test-full     # Run full suite (setup + test + teardown)"
	@echo "  make vm-shell                # Access VM for debugging"
	@echo "  make e2e-tests-status        # Check VM and services status"
	@echo "  make vm-services-logs        # View service logs (last 50 lines)"
	@echo "  make e2e-tests-logs          # Follow service logs in real-time"
	@echo ""
	@echo "$(COLOR_BLUE)Common Commands:$(COLOR_RESET)"
	@echo "  make help            # Show this help message"