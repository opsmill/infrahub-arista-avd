.DEFAULT_GOAL = start

# =============================================================================
# containerlab
# =============================================================================

# =============================================================================
# CV onboarding bind — single source of truth for the cEOS-side CVaaS bind.
# Consumed by topology.clab.yml as `${CV_TOKEN_BIND}` (containerlab env-var
# substitution). The value below is exported to the environment by the `start`
# target, so editing the topology is unnecessary when switching patterns.
#
#   USE_ZTP=1                 → bind global/ztp/ to /mnt/usb1/ztp; EOS ZTP reads
#                               ztpConfig.yaml at boot and pulls the token. The
#                               lab MUST omit `startup-config:` from its
#                               topology.clab.yml (else ZTP is bypassed).
#   LAB_ONBOARDING_TOKEN=<file>.tok  → bind that file to /mnt/flash/cv-onboarding-token;
#                               TerminAttr reads it directly (cv_settings.cvaas
#                               .clusters[].token_file or raw_terminattr).
#   neither                   → CV_TOKEN_BIND unset → topology must NOT reference
#                               ${CV_TOKEN_BIND} (no-CVaaS lab).
# =============================================================================
ifeq ($(USE_ZTP),1)
  CV_TOKEN_BIND ?= ../ztp:/mnt/usb1/ztp:ro
else ifneq ($(LAB_ONBOARDING_TOKEN),)
  CV_TOKEN_BIND ?= ../ztp/$(LAB_ONBOARDING_TOKEN):/mnt/flash/cv-onboarding-token:ro
endif

.PHONY: start stop destroy
start:
	$(if $(CV_TOKEN_BIND),CV_TOKEN_BIND='$(CV_TOKEN_BIND)') containerlab deploy --reconfigure

stop:
	containerlab save
	containerlab destroy --graceful --keep-mgmt-net

destroy:
	containerlab destroy --cleanup --keep-mgmt-net

# Ansible
ANSIBLE_CONFIG ?= ansible.cfg
ANSIBLE_INVENTORY ?=  avd/inventory.yml
ANSIBLE_PLAYBOOK = ANSIBLE_CONFIG=${ANSIBLE_CONFIG} ${EXTRA_ANSIBLE_ARGS} ${UV} ansible-playbook -i ${ANSIBLE_INVENTORY}

# Topology graph (clab-io-draw via `containerlab graph --drawio`).
# Reads topology.clab.yml + sibling topology.clab.yml.annotations.json (groups,
# free shapes, traffic annotations — edited via the VSCode Containerlab plugin)
# to produce a clean docs/topology.drawio.
.PHONY: graph
graph:
	@mkdir -p docs
	containerlab graph --drawio --drawio-args "--theme nokia_modern_soft --output docs/topology.drawio"

# =============================================================================
# Ansible - Arista AVD
# =============================================================================
.PHONY: build deploy workspace eapi-deploy eapi-check test

build:
	${ANSIBLE_PLAYBOOK} playbooks/build.yml

# Submit workspace only, do not execute change control
workspace:
	${ANSIBLE_PLAYBOOK} playbooks/deploy.yml

# Execute change control after submit workspace
deploy:
	${ANSIBLE_PLAYBOOK} playbooks/deploy.yml -e cv_run_change_control=true

eapi-check:
	${ANSIBLE_PLAYBOOK} playbooks/deploy-eapi.yml --diff --check

eapi-deploy:
	${ANSIBLE_PLAYBOOK} playbooks/deploy-eapi.yml --diff

test:
	${ANSIBLE_PLAYBOOK} playbooks/test.yml

.PHONY: clean
clean:
	rm -rf avd/documentation avd/intended/structured_configs
	rm -rf avd/anta/reports avd/anta/avd_catalogs

# =============================================================================
# Ping tests
# =============================================================================
.PHONY: ping ping_vrf10_dc1_to_dc2 ping_vrf10_dc2_to_dc1 ping_vlan19_bridged
ping: ping_vrf10_dc1_to_dc2 ping_vrf10_dc2_to_dc1 ping_vlan19_bridged

ping_vrf10_dc1_to_dc2:
	docker exec clab-infrahub-avd-dc1-server1 ping -I vlan11 -c 5 10.10.12.10

ping_vrf10_dc2_to_dc1:
	docker exec clab-infrahub-avd-dc2-server1 ping -I vlan12 -c 5 10.10.11.10

ping_vlan19_bridged:
	docker exec clab-infrahub-avd-dc1-server1 ping -I vlan19 -c 5 10.10.19.102

# =============================================================================
# Installation
# =============================================================================
# Single Python venv driven by uv (pyproject.toml + uv.lock). uv manages the
# Python 3.12 interpreter itself — no system Python 3.12 needed (Debian 13
# ships only 3.13). All Make targets invoke CLIs via `uv run` so they work
# from any shell without venv activation.
ceos:
	@if [ ! -z $(version) ]; then\
		uv run ardl get eos --format cEOS --import-docker --docker-name arista/ceos --version $(version);\
	elif [ -z "$(shell docker images -f reference=arista/ceos:$$(uv run ardl info latest --format json | jq -r '.version') -q)" ]; then\
		echo "latest cEOSlab image not found, downloading...";\
		uv run ardl get eos --format cEOS --latest --import-docker --docker-name arista/ceos;\
	else\
		echo "latest cEOSlab image found, skipping download...";\
	fi
	@rm -f cEOS-lab-*.tar.xz*

# Required for ansible-pylibssh native build on macOS
CFLAGS := $(if $(filter Darwin,$(shell uname -s)),-I $(shell brew --prefix 2>/dev/null)/include -I ext -L $(shell brew --prefix 2>/dev/null)/lib -lssh)

upgrade:
	CFLAGS="$(CFLAGS)" uv sync --upgrade
	uv run ansible-galaxy collection install -U arista.avd

install:
	CFLAGS="$(CFLAGS)" uv sync
	uv run ansible-galaxy collection install arista.avd