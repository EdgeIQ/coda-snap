# Cross-platform Makefile for E2E Tests
# Works on Windows (with Make for Windows), Linux, and macOS

# Detect operating system
ifeq ($(OS),Windows_NT)
	DETECTED_OS := Windows
	RM := del /Q
	RMDIR := rmdir /S /Q
	MKDIR := mkdir
	SHELL := cmd
else
	DETECTED_OS := $(shell uname -s)
	RM := rm -f
	RMDIR := rm -rf
	MKDIR := mkdir -p
endif

# Docker Compose command (works on all platforms)
COMPOSE := docker compose

# Color output (works on Unix-like systems, ignored on Windows)
ifneq ($(DETECTED_OS),Windows)
	COLOR_RESET := \033[0m
	COLOR_BOLD := \033[1m
	COLOR_GREEN := \033[32m
	COLOR_YELLOW := \033[33m
	COLOR_BLUE := \033[36m
else
	COLOR_RESET :=
	COLOR_BOLD :=
	COLOR_GREEN :=
	COLOR_YELLOW :=
	COLOR_BLUE :=
endif

.PHONY: help test test-verbose build up down clean logs logs-ubuntu logs-mock logs-mqtt shell-ubuntu shell-mock ps health rebuild stop restart

help: ## Show this help message
	@echo "E2E Test Suite - Cross-platform Makefile"
	@echo "========================================"
	@echo ""
	@echo "Operating System: $(DETECTED_OS)"
	@echo ""
	@echo "Available targets:"
	@echo ""
ifeq ($(DETECTED_OS),Windows)
	@findstr /R "^[a-zA-Z_-]*:.*##" $(MAKEFILE_LIST) | findstr /V "findstr"
else
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(COLOR_BLUE)%-20s$(COLOR_RESET) %s\n", $$1, $$2}'
endif
	@echo ""
	@echo "Examples:"
	@echo "  make test          # Run all tests"
	@echo "  make test-verbose  # Run tests with verbose output"
	@echo "  make logs          # View all container logs"
	@echo "  make clean         # Clean up everything"

test: ## Run e2e tests (default)
	@echo "$(COLOR_GREEN)Starting E2E test suite...$(COLOR_RESET)"
	$(COMPOSE) up -d --wait
	@echo "$(COLOR_YELLOW)Running tests...$(COLOR_RESET)"
	$(COMPOSE) run --rm test-runner
	@echo "$(COLOR_GREEN)Cleaning up...$(COLOR_RESET)"
	$(COMPOSE) down -v

test-verbose: ## Run tests with verbose pytest output
	@echo "$(COLOR_GREEN)Starting E2E test suite (verbose mode)...$(COLOR_RESET)"
	$(COMPOSE) up -d --wait
	@echo "$(COLOR_YELLOW)Running tests with verbose output...$(COLOR_RESET)"
	$(COMPOSE) run --rm test-runner pytest -vv -s
	@echo "$(COLOR_GREEN)Cleaning up...$(COLOR_RESET)"
	$(COMPOSE) down -v

test-keep: ## Run tests but keep containers running for debugging
	@echo "$(COLOR_GREEN)Starting E2E test suite (keep containers)...$(COLOR_RESET)"
	$(COMPOSE) up -d --wait
	@echo "$(COLOR_YELLOW)Running tests...$(COLOR_RESET)"
	$(COMPOSE) run --rm test-runner
	@echo ""
	@echo "$(COLOR_YELLOW)Containers are still running!$(COLOR_RESET)"
	@echo "Use 'make logs' to view logs or 'make down' to stop."

test-specific: ## Run specific test (usage: make test-specific TEST=test_name)
	@echo "$(COLOR_GREEN)Running specific test: $(TEST)$(COLOR_RESET)"
	$(COMPOSE) up -d --wait
	$(COMPOSE) run --rm test-runner pytest -vv -s -k "$(TEST)"
	$(COMPOSE) down -v

build: ## Build all Docker images
	@echo "$(COLOR_GREEN)Building Docker images...$(COLOR_RESET)"
	$(COMPOSE) build

rebuild: ## Rebuild all Docker images from scratch (no cache)
	@echo "$(COLOR_GREEN)Rebuilding Docker images (no cache)...$(COLOR_RESET)"
	$(COMPOSE) build --no-cache

up: ## Start all services (detached mode)
	@echo "$(COLOR_GREEN)Starting all services...$(COLOR_RESET)"
	$(COMPOSE) up -d --wait
	@echo "$(COLOR_YELLOW)All services are running!$(COLOR_RESET)"
	@echo "Run 'make test-runner' to execute tests."

down: ## Stop and remove all containers
	@echo "$(COLOR_YELLOW)Stopping all containers...$(COLOR_RESET)"
	$(COMPOSE) down

stop: down ## Alias for 'down'

clean: ## Clean up all containers, networks, volumes, and images
	@echo "$(COLOR_YELLOW)Cleaning up everything...$(COLOR_RESET)"
	$(COMPOSE) down -v --rmi local
	@echo "$(COLOR_GREEN)Cleanup complete!$(COLOR_RESET)"

logs: ## Show logs from all containers
	$(COMPOSE) logs -f

logs-ubuntu: ## Show logs from Ubuntu Core container
	$(COMPOSE) logs -f ubuntu-core

logs-mock: ## Show logs from mock server
	$(COMPOSE) logs -f mock-server

logs-mqtt: ## Show logs from MQTT broker
	$(COMPOSE) logs -f mqtt-broker

logs-test: ## Show logs from last test run
	$(COMPOSE) logs test-runner

shell-ubuntu: ## Open shell in Ubuntu Core container
	docker exec -it ubuntu-core bash

shell-mock: ## Open shell in mock server container
	docker exec -it mock-server sh

shell-test: ## Run test runner container with interactive shell
	$(COMPOSE) run --rm test-runner bash

ps: ## Show running containers
	$(COMPOSE) ps

health: ## Check health status of all services
	@echo "$(COLOR_BLUE)Service Health Status:$(COLOR_RESET)"
	@$(COMPOSE) ps

restart: ## Restart all services
	@echo "$(COLOR_YELLOW)Restarting all services...$(COLOR_RESET)"
	$(COMPOSE) restart
	@echo "$(COLOR_GREEN)Services restarted!$(COLOR_RESET)"

restart-ubuntu: ## Restart Ubuntu Core container
	$(COMPOSE) restart ubuntu-core

restart-mock: ## Restart mock server
	$(COMPOSE) restart mock-server

restart-mqtt: ## Restart MQTT broker
	$(COMPOSE) restart mqtt-broker

test-runner: ## Run test-runner container (services must be up)
	@echo "$(COLOR_YELLOW)Executing tests...$(COLOR_RESET)"
	$(COMPOSE) run --rm test-runner
