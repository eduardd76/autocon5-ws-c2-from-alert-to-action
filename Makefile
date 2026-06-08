# Optional convenience targets. The labs use `docker compose` + `curl` directly.

.PHONY: up down logs preflight pull trigger-ospf trigger-bgp trigger-evpn test-lab3 lab3-test lab3-solve list-scenarios validate-mine fire-mine

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=50

preflight:
	./scripts/preflight_check.sh

pull:
	./scripts/pull_all_images.sh

trigger-ospf:
	curl -s -X POST http://localhost:8001/incident/trigger \
	  -H "X-MCP-API-Key: dev-key-123" \
	  -H "Content-Type: application/json" \
	  -d '{"scenario_id":"ospf_neighbor_down","device_id":"router-1"}' | python3 -m json.tool

trigger-bgp:
	curl -s -X POST http://localhost:8001/incident/trigger \
	  -H "X-MCP-API-Key: dev-key-123" \
	  -H "Content-Type: application/json" \
	  -d '{"scenario_id":"bgp_session_idle","device_id":"router-1"}' | python3 -m json.tool

trigger-evpn:
	curl -s -X POST http://localhost:8001/incident/trigger \
	  -H "X-MCP-API-Key: dev-key-123" \
	  -H "Content-Type: application/json" \
	  -d '{"scenario_id":"evpn_route_missing","device_id":"leaf-1"}' | python3 -m json.tool

# --- Lab 3 (build a specialist) ---
# See the failing tests (compact — no scary traceback):
lab3-test:
	@cd labs/lab3_wire_your_own_specialist && python3 -m pytest test_my_specialist.py --tb=no -q

# Foolproof: copy the reference QoS specialist into the EXACT filename + re-test.
lab3-solve:
	@cp labs/lab3_wire_your_own_specialist/solution/agent_qos.py labs/lab3_wire_your_own_specialist/starter/agent_yourname.py
	@echo "✓ copied reference QoS specialist -> starter/agent_yourname.py"
	@cd labs/lab3_wire_your_own_specialist && python3 -m pytest test_my_specialist.py --tb=no -q

test-lab3: lab3-test

# --- Lab 3 (YAML authoring) ---
list-scenarios:
	curl -s http://localhost:8001/scenarios -H "X-MCP-API-Key: dev-key-123" | python3 -m json.tool

validate-mine:
	@test -n "$(F)" || (echo "usage: make validate-mine F=lab_scenarios/mine/<you>.yaml" && exit 1)
	python3 lab_scenarios/validate.py $(F)

fire-mine:
	@test -n "$(SCN)" || (echo "usage: make fire-mine SCN=<scenario_id> [DEV=router-1]" && exit 1)
	curl -s -X POST http://localhost:8001/incident/trigger \
	  -H "X-MCP-API-Key: dev-key-123" -H "Content-Type: application/json" \
	  -d '{"scenario_id":"$(SCN)","device_id":"$(if $(DEV),$(DEV),router-1)"}' | python3 -m json.tool
