# OBSERVE.md — "See What I See"

Watch one fault travel all 5 layers of your pod after YOU inject it.
Mock devices, canned LLM — same A2A/MCP/ACP protocol as production.
Inject **only on your own pod**. Never touch the shared EVE-NG stack.

```
LAYER MAP
  L0  Trigger ........... POST /incident/trigger      -> Redis incident_queue
  L1  Team Leader ....... classify + delegate         (docker logs)
  L2  A2A bus ........... Redis a2a_*_inbox lists      (redis-cli)
  L3  Specialist ........ MCP reads + stub diagnosis   (docker logs)
       - stability_specialist  (ospf / bgp / evpn)
       - your_specialist       (qos -> this is the one YOU build in Lab 3)
  L4  MCP server ........ mock device facts            (docker logs)
  L5  Approval card ..... ACP /acp/approvals + UI      (curl + browser)
```

---

## 0. Pre-flight — bring the pod up (once)

```bash
cd ~/autocon5-ws-c2-from-alert-to-action          # your pod repo
docker compose up -d
docker compose ps                                  # 6 containers: redis, mcp, team-leader, stability, your-agent, ui
curl -s localhost:8001/health      ; echo          # MCP   -> {"status":"healthy",...}
curl -s localhost:8002/acp/health  ; echo          # Team Leader -> {"status":"ok",...}
```

UI in your browser: **http://localhost:8501**  (or via SSH tunnel: `ssh -L 8501:localhost:8501 <pod>`)

---

## 1. Open the "watch windows" — 3 terminals, leave them running

```bash
# TERMINAL A — every service log, prefixed (the whole story in one stream)
docker compose logs -f --tail=20

# TERMINAL B — Team Leader (L1) + Stability (L3) reasoning only
docker compose logs -f team-leader stability-agent

# TERMINAL C — live queue depths, refreshes every 1s (watch numbers move)
watch -n1 'curl -s localhost:8002/acp/queues'
```

---

## 2. Inject the fault (L0)

Pick ONE. Run it, then immediately watch terminals A/B/C.

```bash
# OSPF adjacency stuck in INIT (Cisco router-1)
curl -s -X POST localhost:8001/incident/trigger \
  -H "X-MCP-API-Key: dev-key-123" -H "Content-Type: application/json" \
  -d '{"scenario_id":"ospf_neighbor_down","device_id":"router-1"}' ; echo

# BGP session idle / ACL blocking TCP-179 (Cisco router-1)
curl -s -X POST localhost:8001/incident/trigger \
  -H "X-MCP-API-Key: dev-key-123" -H "Content-Type: application/json" \
  -d '{"scenario_id":"bgp_session_idle","device_id":"router-1"}' ; echo

# EVPN Type-2 route missing / RT mismatch (Arista leaf-1)
curl -s -X POST localhost:8001/incident/trigger \
  -H "X-MCP-API-Key: dev-key-123" -H "Content-Type: application/json" \
  -d '{"scenario_id":"evpn_route_missing","device_id":"leaf-1"}' ; echo

# QoS egress congestion / voice drops (router-1) -> routes to YOUR_SPECIALIST (Lab 3)
curl -s -X POST localhost:8001/incident/trigger \
  -H "X-MCP-API-Key: dev-key-123" -H "Content-Type: application/json" \
  -d '{"scenario_id":"qos_interface_congested","device_id":"router-1"}' ; echo
```

Expected return: `{"status":"queued","incident":{"id":"syslog-xxxxxxxx", ...}}`
(Or just click the matching button in the UI sidebar — same effect.)

---

## 3. L0 -> see it land on the incident_queue (Redis)

```bash
# Watch the syslog event arrive (run BEFORE step 2 to catch it; Team Leader drains it in <1s)
docker exec ws-c2-redis redis-cli LLEN incident_queue          # 1 right after trigger, 0 once consumed
docker exec ws-c2-redis redis-cli LRANGE incident_queue 0 -1   # the raw syslog JSON, if not yet drained
```

## 4. L1 -> Team Leader classifies + delegates (logs)

In TERMINAL B you will see:
```
[team-leader] received incident syslog-xxxxxxxx scenario=ospf_neighbor_down
[team-leader] -> delegating to stability_specialist as task-xxxxxxxx
[A2A] team_leader -> stability_specialist: task_delegation
```

## 5. L2 -> the A2A message on the Redis bus

```bash
# The delegation message sitting in the specialist's inbox (peek FAST — drained in <1s)
docker exec ws-c2-redis redis-cli LRANGE a2a_stability_specialist_inbox 0 -1

# See ALL the agent mailboxes Redis knows about
docker exec ws-c2-redis redis-cli KEYS 'a2a_*'

# The reply travelling back to the Team Leader
docker exec ws-c2-redis redis-cli LRANGE a2a_team_leader_inbox 0 -1
```

## 6. L3+L4 -> Stability agent reads MCP, runs stub diagnosis (logs)

In TERMINAL B (the `[A2A]` line confirms it received the task):
```
[stability-agent-ws-c2] ===== delegation task-xxxxxxxx =====
[stability-agent-ws-c2] step 1/3: gathering MCP evidence for router-1
[stability-agent-ws-c2] step 2/3: LLM diagnosis for scenario=ospf_neighbor_down
[stability-agent-ws-c2] step 3/3: sending response to team_leader (confidence=0.92, duration=0.0Xs)
[A2A] stability_specialist -> team_leader: task_response
```

Call the same MCP tools the agent just called, by hand (L4 mock devices):
```bash
curl -s -X POST localhost:8001/tools/ospf_parser \
  -H "X-MCP-API-Key: dev-key-123" -H "Content-Type: application/json" \
  -d '{"device_id":"router-1"}' ; echo          # OSPF neighbor stuck INIT
curl -s -X POST localhost:8001/tools/bgp_summary \
  -H "X-MCP-API-Key: dev-key-123" -H "Content-Type: application/json" \
  -d '{"device_id":"router-1"}' ; echo          # BGP neighbor Idle
curl -s -X POST localhost:8001/tools/interface_parser \
  -H "X-MCP-API-Key: dev-key-123" -H "Content-Type: application/json" \
  -d '{"device_id":"router-1"}' ; echo          # interface counters / timers
```

## 7. L5 -> the approval card (ACP API + UI)

```bash
# The recommendation waiting for YOUR sign-off (root cause, evidence, fix, rollback, confidence)
curl -s localhost:8002/acp/approvals | python3 -m json.tool

# grab the task_id of the newest card
TASK=$(curl -s localhost:8002/acp/approvals | python3 -c 'import sys,json;print(json.load(sys.stdin)[0]["task_id"])')
echo "$TASK"
```

In the UI (**http://localhost:8501**): the yellow card under **Pending approvals** shows
the same root cause / evidence / proposed fix / rollback. Click **Approve** or **Reject**.

Or decide from the CLI (human-in-the-loop, the L5 gate):
```bash
curl -s -X POST localhost:8002/acp/approval \
  -H "Content-Type: application/json" \
  -d "{\"action\":\"approve\",\"task_id\":\"$TASK\",\"decision_rationale\":\"looks right\"}" ; echo

curl -s localhost:8002/acp/history | python3 -m json.tool     # card moved to approved/rejected
```

---

## End-to-end in 10 seconds (the "money shot")

```bash
watch -n1 'curl -s localhost:8002/acp/queues' &      # leave running in another pane
curl -s -X POST localhost:8001/incident/trigger \
  -H "X-MCP-API-Key: dev-key-123" -H "Content-Type: application/json" \
  -d '{"scenario_id":"bgp_session_idle","device_id":"router-1"}' >/dev/null
sleep 1
curl -s localhost:8002/acp/approvals | python3 -m json.tool
```
You watched: `incident_queue 1->0`  ->  `specialist inbox 1->0`  ->  `pending approvals 0->1`.
That number moving across the queues IS the fault crossing all 5 layers.

---

## Cheat constants
- MCP key: `dev-key-123` (env `MCP_API_KEY`)   • Ports: UI 8501 · TL 8002 · MCP 8001 · Redis 6379
- Containers: `ws-c2-redis ws-c2-mcp ws-c2-team-leader ws-c2-stability ws-c2-your-agent ws-c2-ui`
- Scenario IDs: `ospf_neighbor_down` (router-1) · `bgp_session_idle` (router-1) · `evpn_route_missing` (leaf-1) · `qos_interface_congested` (router-1, -> your_specialist)
- QoS MCP tool (the one YOUR agent reads): `curl -s -XPOST localhost:8001/tools/qos_parser -H "X-MCP-API-Key: dev-key-123" -H "Content-Type: application/json" -d '{"device_id":"router-1"}'`
- Lab 3: see your own scenario in the catalogue — `curl -s localhost:8001/scenarios | python3 -m json.tool`

## If a panel is empty
```bash
docker compose ps                       # all 5 Up & healthy?
docker compose restart team-leader stability-agent
docker exec ws-c2-redis redis-cli PING  # -> PONG
```
Queues drain in <1s — if `redis-cli LRANGE` shows nothing, that's success, not failure: read the logs instead.
