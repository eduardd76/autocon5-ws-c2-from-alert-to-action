# AutoCon5 WS:C2 — From Alert to Action

**4-hour hands-on workshop. AutoCon5 Munich, 2026-06-09, Tuesday morning, track 2.**

A 5-agent AI system that turns network alerts into safe, validated remediation in seconds. This repo is the laptop-local lab — strip-down of the production "Dream Team" stack that runs on your MacBook with `docker compose up`. No EVE-NG, no cloud, no GPU, no API keys, no real LLM. Mock devices + canned LLM responses so the agent reasoning chain is reproducible offline.

---

## ⚠️ What this is vs what this isn't

**This IS:** a teaching scaffold for the AutoCon5 workshop. ~1,600 LOC across 5 Docker services. Demonstrates the architectural pattern — *catalogue decides what to investigate, LLM writes the diagnosis, human approves the change* — with mock devices and a stub LLM that returns canned responses. Designed to be cloneable + runnable in under 5 minutes on a stranger's laptop.

**This is NOT:** the production Dream Team system. The following components are **proprietary vExpertAI software** and are **NOT included** in this repository:

| Production component | NOT here |
|---|---|
| 72-scenario diagnostic catalogue + 42 diagnostic trees | only 2-3 sample scenarios in this scaffold |
| **va-v2 fine-tuned LoRA** (gate-cleared, ~17× over baseline on hidden exam) | `stub_llm_client.py` returns canned responses |
| Multi-vendor adapter layer (Cisco NX-OS / Arista EOS) | mock devices only |
| 7-pass validation pipeline (CRO / BRF / DT sandbox / audit chain) | not included |
| DORA / NIS2 compliance mapping + audit-trail export | not included |
| Fabric Architect (multi-vendor EVPN audit agent) | conceptual demo only |
| TimescaleDB HMAC-chained reasoning audit | not included |
| Neo4j Knowledge Graph schema + live-sync | not included |

If you'd like access to the production system, see the **pilot path** in [`NOTICE`](./NOTICE).

---

## TL;DR — get running in 5 minutes

```bash
git clone https://github.com/eduardd76/autocon5-ws-c2-from-alert-to-action.git
cd autocon5-ws-c2-from-alert-to-action
cp .env.sample .env
./scripts/preflight_check.sh         # validates Docker, ports, RAM
docker compose up -d
open http://localhost:8501           # Streamlit UI
```

Then open `labs/lab1_trigger_an_incident/README.md` and follow.

---

## Workshop agenda (240 minutes)

| Time | Block | Pages |
|---|---|---|
| 09:00–09:20 | Intro: the on-call problem + 5-agent architecture | slides |
| 09:20–09:50 | **Lab 1** — trigger a BGP incident, watch 5 agents react | `labs/lab1_*` |
| 09:50–10:00 | Discuss: what the agents got right / wrong | plenary |
| 10:00–10:15 | **break** | — |
| 10:15–10:45 | **Lab 2** — multi-vendor EVPN audit (Cisco + Arista EOS) | `labs/lab2_*` |
| 10:45–11:00 | Discuss: vendor abstraction layer + neutral schema | plenary |
| 11:00–11:15 | **break** | — |
| 11:15–12:30 | **Lab 3** — wire your own specialist agent (TDD: red → green) | `labs/lab3_*` |
| 12:30–12:55 | Show & tell: 5 attendee specialists demoed | plenary |
| 12:55–13:00 | Wrap, Q&A, repo + slides handout | — |

---

## The 5 agents you'll see in action

| Agent | Specialty | Container |
|---|---|---|
| **Team Leader** | Triage incoming alerts, delegate to the right specialist, gate approvals | `team-leader` |
| **Stability Specialist** | OSPF / BGP / EIGRP routing protocol faults | `stability-agent` |
| **Troubleshooting Specialist** | Interface / connectivity / L1-L2 faults *(out of scope for laptop demo)* | — |
| **Security Specialist** | ACL / AAA / login policy faults *(out of scope for laptop demo)* | — |
| **Virtual Architect** | Multi-vendor fabric design + audit *(simulated in Lab 2)* | mocked |

For the laptop workshop we ship **only the Team Leader + Stability Specialist** as real containers. Labs 2 + 3 demonstrate the rest using canned responses + the scaffolding pattern.

---

## Architecture (what's actually running on your laptop)

```
┌─────────────────────┐
│ Streamlit UI (8501) │
└──────────┬──────────┘
           │ ACP/HTTP
┌──────────▼──────────┐
│ Team Leader (8002)  │
└──────────┬──────────┘
           │ A2A/Redis queues
┌──────────▼──────────┐    ┌────────────────────┐
│ Stability Agent     │───▶│ MCP Server (8001)  │
└─────────────────────┘    └────────┬───────────┘
                                    │ (no SSH — mock devices in-process)
                           ┌────────▼───────────┐
                           │ Mock Cisco/Arista  │
                           │ router state       │
                           └────────────────────┘
```

5 containers total: `redis`, `mcp-server`, `team-leader`, `stability-agent`, `ui`. RAM footprint ~1.5 GB.

The production system adds Neo4j, TimescaleDB, vLLM-on-GPU, real SSH-over-jump-host to EVE-NG, fine-tuned 7B models, syslog ingestion, and 3 more specialist containers. **None of that is needed to learn the pattern.** This repo proves the agent flow with the smallest possible footprint.

---

## What you need on your laptop

- macOS 14+ or Ubuntu 22.04+ (Windows: use WSL2)
- Docker Desktop ≥ 24 (or Docker Engine + Compose v2)
- 8 GB RAM available to Docker
- 6 GB free disk space
- Ports `8501`, `8002`, `8001`, `6379` free
- A browser

That's it. No Python install on the host, no Neo4j, no GPU.

---

## Files in this repo

| File / Dir | What it is |
|---|---|
| `PRE_WORKSHOP_SETUP.md` | 5-step "do this before Munich" guide. Read this 24h before. |
| `TROUBLESHOOTING.md` | Top 10 errors with verbatim fix commands. |
| `docker-compose.yml` | The 5-service minimal stack. |
| `.env.sample` | Copy to `.env`. Has 3 vars, all optional. |
| `labs/lab1_trigger_an_incident/` | Lab 1 — your first incident. |
| `labs/lab2_observe_multi_vendor_audit/` | Lab 2 — Fabric Architect multi-vendor audit. |
| `labs/lab3_wire_your_own_specialist/` | Lab 3 — TDD scaffolding for a new specialist. |
| `scripts/preflight_check.sh` | Validate your laptop is ready. **Run this first.** |
| `scripts/pull_all_images.sh` | Pre-pull every Docker image (wifi-failure insurance). |
| `services/` | The 5 service implementations (Python). Read if curious. |
| `slides_handout.pdf` | Workshop slides one-pager. |

---

## License

**Apache License 2.0** — see [`LICENSE`](./LICENSE) for the full text and [`NOTICE`](./NOTICE) for what's covered (the teaching scaffold) vs what's NOT covered (the proprietary production system).

Use it, fork it, learn from it. If you build a derivative work, please retain the `NOTICE` file — it makes the proprietary boundary clear to your downstream users too.

Contributions back to this scaffold are welcome under a light CLA — see [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Credits

Eduard Dulharu (vExpertAI) — workshop presenter + author of the production Dream Team system that this scaffold demonstrates. *"Dream Team"* and *"vExpertAI"* are trademarks of Eduard Dulharu / vExpertAI; the Apache 2.0 license on this software does not grant a license to these trademarks (see `NOTICE` for details).

## Help

- Workshop Slack channel: `#autocon5-ws-c2` on NAF Slack ([join][slack])
- Issues during the workshop: hand-raise + flag your laptop with the **red sticky note** on the table
- Pre-workshop questions: open an issue on this repo

[slack]: https://join.slack.com/t/networkautomationfrm/shared_invite/zt-3jzfd6hte-v_TQmi2sqdPilYJ6wwgZAg
