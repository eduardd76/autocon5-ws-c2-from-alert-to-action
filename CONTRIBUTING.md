# Contributing to the AutoCon5 WS:C2 Workshop Scaffold

Thanks for considering a contribution!

This repository is the **teaching scaffold** for the AutoCon5 Munich workshop *"From Alert to Action."* It exists to teach the architectural pattern — *catalogue decides, LLM writes, human approves* — on a stack you can run on your laptop. It is **not** the production Dream Team system (see [`NOTICE`](./NOTICE) for the boundary).

Contributions that improve the *teaching* are warmly welcomed. Contributions that try to lift the scaffold toward production-grade behavior are out of scope — those decisions belong to the proprietary production codebase.

---

## What this repo accepts

- 🐛 **Bug fixes** — Docker issues, port conflicts, README clarifications, broken Make targets
- 📚 **Documentation improvements** — clearer READMEs, better troubleshooting entries, translations
- 🎓 **Lab quality-of-life** — better preflight checks, more helpful error messages, cleaner output
- 🧪 **New community example specialists** under `labs/lab3_wire_your_own_specialist/solution/community/` — your own "wire your own specialist" submission, kept alongside the QoS reference solution
- 🧹 **Style + tidy** — typos, dead code, minor refactors that don't change behavior

## What this repo does NOT accept

- ❌ **Production-grade scenarios or diagnostic trees** — the production catalogue (72 scenarios, 42 trees) lives in a proprietary codebase
- ❌ **Real LLM client implementations** — the `stub_llm_client.py` is intentional for the workshop; canned responses keep the demo reproducible offline
- ❌ **Multi-vendor adapter improvements** — production has its own adapter layer (NeutralEvpnState, EVPNParserResponse, etc.)
- ❌ **Compliance mapping tables (DORA/NIS2)** — production has the authoritative mapping; this scaffold has a placeholder reference only
- ❌ **Anything that would require a GPU, AWS account, EVE-NG license, or paid API key** to run — the scaffold's whole point is "runs on a stranger's laptop"

If you're not sure whether your idea fits, **open an issue first** before writing code — we'd rather discuss the shape than burn your time.

---

## Contributor License Agreement (light CLA)

By submitting a pull request to this repository, you agree that:

1. **You retain the copyright** to your own contribution and may use it elsewhere however you like.

2. **You grant Eduard Dulharu / vExpertAI a perpetual, worldwide, non-exclusive, royalty-free, irrevocable, sublicensable license** to use, copy, modify, distribute, prepare derivative works of, publicly display, publicly perform, and incorporate your contribution into:
   - this public teaching scaffold,
   - the proprietary vExpertAI production codebase, and
   - any future vExpertAI products, services, or training materials.

3. **Your contribution is your own work**, you have the right to grant this license, and (if your employer has rights to work-product you create) your employer has waived such rights or you have permission to contribute on their behalf.

4. **Your contribution is provided "as-is"**, without warranty of any kind. The Apache 2.0 disclaimers in [`LICENSE`](./LICENSE) §7-8 apply to your contribution.

This is a **"light CLA"**: you keep the rights to your own work; we just need a clear license so we can incorporate improvements both into the open scaffold AND into our proprietary product without needing a separate negotiation for each PR. By opening a PR you signal agreement; no separate signed document is required.

---

## Contribution process

1. **Open an issue first.** Describe what you'd like to change and why. Wait for a maintainer ack before doing significant work — we don't want you to write code that won't merge.

2. **Fork + branch.** Branch name like `fix/preflight-port-message` or `docs/translate-readme-de`.

3. **Submit a PR.** Reference the issue. Keep it focused — one concept per PR.

4. **Be patient.** This repo is maintained alongside production work. PR turnaround may be days to weeks, especially during the workshop preparation window.

5. **Workshop attendees:** during the workshop, please use the Discord channel for help rather than opening issues — issues are better suited to durable improvements.

---

## Code style

- **Python**: black formatter, 100-char line length, type hints where they help readability
- **Markdown**: ~100-char line wrapping, fenced code blocks with language tags
- **Docker**: keep it minimal — every layer should pay for itself
- **Shell**: bash with `set -euo pipefail`, explicit error messages with FIX suggestions

---

## What you'll NOT see in the upstream

If you submit something that's a great idea but belongs in production (not in the teaching scaffold), the maintainer will say so — and may invite a separate conversation about pilot collaboration. Don't take "no" on a PR as a judgment on the idea; it's a judgment on the venue.

---

## Questions

- Open an issue
- Or reach the maintainer: dulharu.eduard@gmail.com
- Workshop attendees: use the Discord `#help-*` channels first

— Eduard Dulharu / vExpertAI
