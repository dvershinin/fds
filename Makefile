# Makefile to build and run firewalld tests in Docker

IMAGE ?= my-firewalld-image
CONTAINER ?= firewalld-container
DOCKERFILE ?= firewalld.Dockerfile
UNAME_S := $(shell uname -s)
DOCKER ?= docker
DOCKER_CONTEXT := $(shell docker context show 2>/dev/null)

# On some hosts (e.g. macOS), you may need to override CGROUP_FLAGS to empty:
#   make test CGROUP_FLAGS=
CGROUP_FLAGS ?= --volume=/sys/fs/cgroup:/sys/fs/cgroup:rw --cgroupns=host
TMPFS_FLAGS ?= --tmpfs /run --tmpfs /run/lock
RUN_FLAGS ?= --detach --privileged $(CGROUP_FLAGS) --name $(CONTAINER)
TEST_SCRIPT := $(abspath firewalld-tests.sh)
PKG_DIR := $(abspath fds)

.PHONY: build rebuild ensure-image start start-mac stop rm logs shell exec test test-mac tests tests-colima ensure-env stop-colima-if-needed clean up down

build:
	@DOCKER_BUILDKIT=0 $(DOCKER) build -t $(IMAGE) -f $(DOCKERFILE) .

rebuild:
	@DOCKER_BUILDKIT=0 $(DOCKER) build --no-cache -t $(IMAGE) -f $(DOCKERFILE) .

ensure-image:
	@$(DOCKER) image inspect $(IMAGE) >/dev/null 2>&1 || (echo "Building $(IMAGE)..." && DOCKER_BUILDKIT=0 $(DOCKER) build -t $(IMAGE) -f $(DOCKERFILE) .)

start:
	@-$(DOCKER) rm -f $(CONTAINER) >/dev/null 2>&1 || true
	@$(DOCKER) run $(RUN_FLAGS) $(IMAGE)
	@sleep 10
	@running=$$($(DOCKER) inspect -f '{{.State.Running}}' $(CONTAINER) 2>/dev/null || true); \
	if [ "$$running" != "true" ]; then \
	  echo "Container failed to start. Logs:"; \
	  $(DOCKER) logs $(CONTAINER) || true; \
	  $(DOCKER) inspect $(CONTAINER) || true; \
	  exit 1; \
	fi

stop:
	@-$(DOCKER) stop $(CONTAINER) >/dev/null 2>&1 || true

rm: stop
	@-$(DOCKER) rm $(CONTAINER) >/dev/null 2>&1 || true

logs:
	@$(DOCKER) logs -f $(CONTAINER)

shell:
	@$(DOCKER) exec -it $(CONTAINER) /bin/bash

exec:
	@$(DOCKER) exec $(CONTAINER) /bin/bash -c "$(CMD)"

test: ensure-image start
	@$(DOCKER) cp $(TEST_SCRIPT) $(CONTAINER):/app/firewalld-tests.sh
	@$(DOCKER) cp -a $(PKG_DIR) $(CONTAINER):/usr/local/lib/python3.9/site-packages/
	@$(DOCKER) exec -e FDS_NOCACHE=1 $(CONTAINER) /bin/bash -c "./firewalld-tests.sh"

start-mac: CGROUP_FLAGS=
start-mac:
	@-$(DOCKER) rm -f $(CONTAINER) >/dev/null 2>&1 || true
	@$(DOCKER) run --detach --privileged $(TMPFS_FLAGS) --name $(CONTAINER) $(IMAGE) sleep infinity
	@sleep 10
	@running=$$($(DOCKER) inspect -f '{{.State.Running}}' $(CONTAINER) 2>/dev/null || true); \
	if [ "$$running" != "true" ]; then \
	  echo "Container failed to start. Logs:"; \
	  $(DOCKER) logs $(CONTAINER) || true; \
	  $(DOCKER) inspect $(CONTAINER) || true; \
	  exit 1; \
	fi

test-mac: CGROUP_FLAGS=
test-mac: ensure-image start-mac
	@$(DOCKER) cp $(TEST_SCRIPT) $(CONTAINER):/app/firewalld-tests.sh
	@$(DOCKER) cp -a $(PKG_DIR) $(CONTAINER):/usr/local/lib/python3.9/site-packages/
	@$(DOCKER) exec -e FDS_NOCACHE=1 $(CONTAINER) /bin/bash -c "./firewalld-tests.sh"

ensure-env:
	@# Ensure environment for tests (start Colima on macOS if available)
	@if [ "$(UNAME_S)" = "Darwin" ]; then \
	  if command -v colima >/dev/null 2>&1; then \
	    if ! colima status 2>/dev/null | grep -q Running; then \
	      echo "Starting Colima for systemd-compatible Docker..."; \
	      colima start --cpu 2 --memory 4 --disk 20 || true; \
	      touch .colima-started-by-make; \
	    fi; \
	  else \
	    if command -v brew >/dev/null 2>&1; then \
	      echo "Colima not found. Installing via Homebrew..."; \
	      brew install colima || true; \
	      if command -v colima >/dev/null 2>&1; then \
	        echo "Starting Colima..."; \
	        colima start --cpu 2 --memory 4 --disk 20 || true; \
	        touch .colima-started-by-make; \
	      fi; \
	    fi; \
	  fi; \
	fi

tests: ensure-env
	@status=0; \
	if [ "$(UNAME_S)" = "Darwin" ] && command -v colima >/dev/null 2>&1 && colima status 2>/dev/null | grep -q Running; then \
	  echo "Using Colima Docker context"; \
	  $(MAKE) DOCKER='docker --context colima' DOCKER_BUILDKIT=0 test; \
	  status=$$?; \
	else \
	  if [ "$(UNAME_S)" = "Darwin" ]; then \
	    echo "Colima not available; using Docker Desktop fallback"; \
	    $(MAKE) DOCKER='docker' test-mac; \
	    status=$$?; \
	  else \
	    $(MAKE) DOCKER='docker' test; \
	    status=$$?; \
	  fi; \
	fi; \
	$(MAKE) stop-colima-if-needed; \
	exit $$status

tests-colima:
	@status=0; \
	if ! command -v colima >/dev/null 2>&1 || ! colima status 2>/dev/null | grep -q Running; then \
	  echo "Starting Colima for systemd-compatible Docker..."; \
	  colima start --cpu 2 --memory 4 --disk 20 || true; \
	  touch .colima-started-by-make; \
	fi; \
	$(MAKE) DOCKER='docker --context colima' DOCKER_BUILDKIT=0 test; \
	status=$$?; \
	$(MAKE) stop-colima-if-needed; \
	exit $$status

stop-colima-if-needed:
	@if [ -f .colima-started-by-make ]; then \
	  echo "Stopping Colima started by tests..."; \
	  colima stop; \
	  rm -f .colima-started-by-make; \
	fi

clean: rm
	@-$(DOCKER) rmi $(IMAGE) >/dev/null 2>&1 || true

up: start

down: rm


