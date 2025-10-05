# Multipass-based E2E Test Suite Makefile
# For testing EdgeIQ Coda snap on macOS ARM64 with Ubuntu VMs

.PHONY: help setup test test-verbose test-keep-vm clean vm-create vm-delete vm-shell shell \
        services-start services-stop logs vm-info wait-for-snapd status

# Configuration
MULTIPASS_VM_NAME ?= coda-test-vm
MULTIPASS_VM_CPUS ?= 2
MULTIPASS_VM_MEMORY ?= 2G
MULTIPASS_VM_DISK ?= 10G
CLOUD_INIT_FILE ?= cloud-init.yaml
MOCK_SERVER_PORT ?= 8080
MQTT_PORT ?= 1883

# Color output
COLOR_RESET := \033[0m
COLOR_BOLD := \033[1m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_BLUE := \033[36m
COLOR_RED := \033[31m

help: ## Show this help message
	@echo "$(COLOR_BOLD)E2E Test Suite - Multipass-based Testing$(COLOR_RESET)"
	@echo "=========================================="
	@echo ""
	@echo "$(COLOR_BLUE)VM Configuration:$(COLOR_RESET)"
	@echo "  VM Name:   $(MULTIPASS_VM_NAME)"
	@echo "  CPUs:      $(MULTIPASS_VM_CPUS)"
	@echo "  Memory:    $(MULTIPASS_VM_MEMORY)"
	@echo "  Disk:      $(MULTIPASS_VM_DISK)"
	@echo ""
	@echo "$(COLOR_BLUE)Available targets:$(COLOR_RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(COLOR_BLUE)%-20s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(COLOR_BLUE)Quick Start:$(COLOR_RESET)"
	@echo "  make setup         # 1. Create VM and install services"
	@echo "  make test          # 2. Run tests"
	@echo "  make teardown      # 3. Clean up VM and results"
	@echo ""
	@echo "$(COLOR_BLUE)Advanced:$(COLOR_RESET)"
	@echo "  make test-full     # Run full suite (setup + test + teardown)"
	@echo "  make vm-shell      # Access VM for debugging"
	@echo "  make status        # Check VM and services status"

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
	@$(MAKE) wait-for-snapd
	@$(MAKE) setup-vm-services
	@echo "$(COLOR_GREEN)✓ VM $(MULTIPASS_VM_NAME) is ready$(COLOR_RESET)"

vm-delete: ## Delete Multipass VM
	@echo "$(COLOR_YELLOW)Deleting VM: $(MULTIPASS_VM_NAME)$(COLOR_RESET)"
	@-multipass delete $(MULTIPASS_VM_NAME) 2>/dev/null
	@-multipass purge 2>/dev/null
	@echo "$(COLOR_GREEN)✓ VM deleted$(COLOR_RESET)"

vm-shell: ## Open shell in Multipass VM
	@echo "$(COLOR_BLUE)Opening shell in $(MULTIPASS_VM_NAME)...$(COLOR_RESET)"
	@multipass shell $(MULTIPASS_VM_NAME)

shell: ## Open shell in VM (alias for vm-shell)
	@multipass shell $(MULTIPASS_VM_NAME)

vm-info: ## Show VM information
	@echo "$(COLOR_BLUE)VM Information:$(COLOR_RESET)"
	@multipass info $(MULTIPASS_VM_NAME)

vm-list: ## List all Multipass VMs
	@echo "$(COLOR_BLUE)All Multipass VMs:$(COLOR_RESET)"
	@multipass list

wait-for-snapd: ## Wait for snapd to be ready in VM
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

setup-vm-services: ## Transfer files and start services in VM
	@echo "$(COLOR_YELLOW)Setting up services in VM...$(COLOR_RESET)"
	@multipass transfer -r mock-server $(MULTIPASS_VM_NAME):/home/ubuntu/
	@multipass transfer -r fixtures $(MULTIPASS_VM_NAME):/home/ubuntu/
	@echo "$(COLOR_YELLOW)Installing Python dependencies in VM...$(COLOR_RESET)"
	@multipass exec $(MULTIPASS_VM_NAME) -- bash -c "cd /home/ubuntu/mock-server && pip3 install -r requirements.txt --break-system-packages"
	@echo "$(COLOR_YELLOW)Starting mock server in VM...$(COLOR_RESET)"
	@multipass exec $(MULTIPASS_VM_NAME) -- bash -c "setsid python3 /home/ubuntu/mock-server/server.py > /home/ubuntu/mock-server.log 2>&1 < /dev/null &"
	@sleep 3
	@echo "$(COLOR_YELLOW)Verifying mock server is running...$(COLOR_RESET)"
	@multipass exec $(MULTIPASS_VM_NAME) -- bash -c 'if pgrep -f "python3.*server.py" > /dev/null; then echo "  Mock server PID: $$(pgrep -f \"python3.*server.py\")"; else echo "  ERROR: Mock server failed to start"; exit 1; fi'
	@echo "$(COLOR_GREEN)✓ Services started in VM$(COLOR_RESET)"

services-start: ## Start services in VM (alias for setup-vm-services)
	@$(MAKE) setup-vm-services

services-stop: ## Stop services in VM
	@echo "$(COLOR_YELLOW)Stopping services in VM...$(COLOR_RESET)"
	@multipass exec $(MULTIPASS_VM_NAME) -- pkill -f "python3.*server.py" || true
	@multipass exec $(MULTIPASS_VM_NAME) -- pkill -f mosquitto || true
	@echo "$(COLOR_GREEN)✓ Services stopped$(COLOR_RESET)"

status: ## Show status of services and VM
	@echo "$(COLOR_BLUE)Multipass VMs:$(COLOR_RESET)"
	@multipass list 2>/dev/null || echo "  No VMs found"
	@echo ""
	@echo "$(COLOR_BLUE)Services in VM (if VM exists):$(COLOR_RESET)"
	@if multipass list 2>/dev/null | grep -q $(MULTIPASS_VM_NAME); then \
		multipass exec $(MULTIPASS_VM_NAME) -- bash -c "pgrep -f 'python3.*server.py' > /dev/null && echo '  Mock Server:  Running' || echo '  Mock Server:  Not running'"; \
		multipass exec $(MULTIPASS_VM_NAME) -- bash -c "pgrep -f mosquitto > /dev/null && echo '  Mosquitto:    Running' || echo '  Mosquitto:    Not running'"; \
	else \
		echo "  VM not running"; \
	fi

setup: ## Create VM and install services (run this first)
	@echo "$(COLOR_BOLD)$(COLOR_GREEN)Setting up E2E test environment...$(COLOR_RESET)"
	@$(MAKE) vm-create
	@echo "$(COLOR_GREEN)✓ E2E test environment ready$(COLOR_RESET)"
	@echo "$(COLOR_BLUE)Run 'make test' to execute tests$(COLOR_RESET)"

test: ## Run E2E test suite (VM must be running)
	@echo "$(COLOR_BOLD)$(COLOR_GREEN)Running E2E test suite...$(COLOR_RESET)"
	@if ! multipass list 2>/dev/null | grep -q $(MULTIPASS_VM_NAME); then \
		echo "$(COLOR_RED)✗ VM not found. Run 'make setup' first$(COLOR_RESET)"; \
		exit 1; \
	fi
	@cd test-runner && \
		MULTIPASS_VM_NAME=$(MULTIPASS_VM_NAME) \
		pytest tests/ -v -s
	@echo "$(COLOR_GREEN)✓ Tests completed$(COLOR_RESET)"

test-full: ## Run full E2E test suite (create VM, test, cleanup)
	@echo "$(COLOR_BOLD)$(COLOR_GREEN)Starting full E2E test suite...$(COLOR_RESET)"
	@$(MAKE) setup
	@$(MAKE) test || (echo "$(COLOR_RED)✗ Tests failed$(COLOR_RESET)" && $(MAKE) teardown && exit 1)
	@$(MAKE) teardown
	@echo "$(COLOR_GREEN)✓ Full E2E test suite completed successfully$(COLOR_RESET)"

test-verbose: ## Run tests with verbose output (VM must be running)
	@echo "$(COLOR_BOLD)$(COLOR_GREEN)Running E2E test suite (verbose mode)...$(COLOR_RESET)"
	@if ! multipass list 2>/dev/null | grep -q $(MULTIPASS_VM_NAME); then \
		echo "$(COLOR_RED)✗ VM not found. Run 'make setup' first$(COLOR_RESET)"; \
		exit 1; \
	fi
	@cd test-runner && \
		MULTIPASS_VM_NAME=$(MULTIPASS_VM_NAME) \
		pytest tests/ -vv -s --log-cli-level=DEBUG
	@echo "$(COLOR_GREEN)✓ Tests completed$(COLOR_RESET)"

teardown: ## Stop VM and clean up test results
	@echo "$(COLOR_YELLOW)Tearing down E2E test environment...$(COLOR_RESET)"
	@$(MAKE) services-stop 2>/dev/null || true
	@$(MAKE) vm-delete 2>/dev/null || true
	@rm -rf logs/*.log 2>/dev/null || true
	@rm -rf test-runner/tests/__pycache__ 2>/dev/null || true
	@rm -rf test-runner/tests/.pytest_cache 2>/dev/null || true
	@echo "$(COLOR_GREEN)✓ Teardown complete$(COLOR_RESET)"

logs: ## Show service logs
	@echo "$(COLOR_BLUE)=== Mock Server Logs ===$(COLOR_RESET)"
	@tail -n 50 logs/mock-server.log 2>/dev/null || echo "No logs available"
	@echo ""
	@echo "$(COLOR_BLUE)=== Mosquitto Logs ===$(COLOR_RESET)"
	@tail -n 50 logs/mosquitto.log 2>/dev/null || echo "No logs available"

logs-follow: ## Follow service logs in real-time
	@echo "$(COLOR_BLUE)Following service logs (Ctrl+C to stop)...$(COLOR_RESET)"
	@tail -f logs/*.log 2>/dev/null || echo "No logs available"

clean: teardown ## Alias for teardown (clean up all resources)
