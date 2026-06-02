#!/usr/bin/env bash
# AutoCon5 WS:C2 — preflight. Run this BEFORE Munich. Exits 0 on READY,
# 1 on FIX-NEEDED with a clear human instruction.
set -u

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

fail=0
warn=0

ok()    { printf "%b ✓%b  %s\n"   "$GREEN" "$NC" "$1"; }
bad()   { printf "%b ✗%b  %s\n"   "$RED"   "$NC" "$1"; fail=$((fail+1)); }
warn()  { printf "%b !%b  %s\n"   "$YELLOW" "$NC" "$1"; warn=$((warn+1)); }
fix()   { printf "      %bFIX:%b %s\n" "$YELLOW" "$NC" "$1"; }

echo
echo "AutoCon5 WS:C2 preflight check"
echo "=============================="

# ---- Docker ------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
    bad "docker not installed"
    fix "Install Docker Desktop: https://docs.docker.com/desktop/install/"
else
    DOCKER_VER=$(docker version --format '{{.Server.Version}}' 2>/dev/null | cut -d. -f1)
    if [ -z "$DOCKER_VER" ]; then
        bad "docker installed but daemon not running"
        fix "Open Docker Desktop (mac/win) OR 'sudo systemctl start docker' (linux)"
    elif [ "$DOCKER_VER" -lt 24 ]; then
        warn "docker version $DOCKER_VER < 24 (will probably work but untested)"
        fix "Upgrade Docker Desktop to the latest stable"
    else
        ok "docker $(docker version --format '{{.Server.Version}}' 2>/dev/null) running"
    fi
fi

# ---- Docker Compose ----------------------------------------------------
if ! docker compose version >/dev/null 2>&1; then
    bad "'docker compose' (v2) not available"
    fix "Update Docker Desktop. The legacy 'docker-compose' v1 is unsupported."
else
    ok "docker compose $(docker compose version --short 2>/dev/null)"
fi

# ---- RAM allocated to Docker -------------------------------------------
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    MEM_BYTES=$(docker info --format '{{.MemTotal}}' 2>/dev/null)
    if [ -n "$MEM_BYTES" ] && [ "$MEM_BYTES" -gt 0 ]; then
        MEM_GB=$((MEM_BYTES / 1024 / 1024 / 1024))
        if [ "$MEM_GB" -lt 6 ]; then
            bad "Docker has only ${MEM_GB}GB RAM allocated (need >= 8GB)"
            fix "Docker Desktop -> Settings -> Resources -> Memory -> 8GB -> Apply"
        elif [ "$MEM_GB" -lt 8 ]; then
            warn "Docker has ${MEM_GB}GB RAM (recommended 8GB, will be tight)"
        else
            ok "Docker RAM: ${MEM_GB}GB available"
        fi
    fi
fi

# ---- Ports free --------------------------------------------------------
for PORT in 6379 8001 8002 8501; do
    if command -v lsof >/dev/null 2>&1; then
        BUSY=$(lsof -nP -iTCP:$PORT -sTCP:LISTEN 2>/dev/null | tail -n +2 | head -1)
    elif command -v ss >/dev/null 2>&1; then
        BUSY=$(ss -tlnp 2>/dev/null | grep ":$PORT " | head -1)
    else
        BUSY=""
    fi
    if [ -n "$BUSY" ]; then
        bad "port $PORT is already in use"
        fix "Stop whatever is using it OR edit docker-compose.yml to remap. Detail: $BUSY"
    else
        ok "port $PORT free"
    fi
done

# ---- Internet reachable for docker pull -------------------------------
if command -v curl >/dev/null 2>&1; then
    if curl -fsS -m 5 -o /dev/null https://registry-1.docker.io/v2/ 2>/dev/null; then
        ok "docker.io reachable"
    else
        warn "docker.io unreachable (will fail first-time pull — run pull_all_images.sh on better wifi)"
    fi
fi

# ---- Repo files exist --------------------------------------------------
HERE="$(cd "$(dirname "$0")/.." && pwd)"
for F in "docker-compose.yml" ".env.sample" \
         "services/mcp-server/main.py" "services/team-leader/main.py" \
         "services/stability-agent/main.py" "services/ui/app.py"; do
    if [ -f "$HERE/$F" ]; then
        ok "found $F"
    else
        bad "missing $F"
        fix "Re-clone the repo or pull latest: git pull"
    fi
done

# ---- .env file ---------------------------------------------------------
if [ -f "$HERE/.env" ]; then
    ok ".env present"
else
    warn ".env not found"
    fix "cp .env.sample .env"
fi

# ---- Summary -----------------------------------------------------------
echo
echo "----------------------------------------------"
if [ "$fail" -gt 0 ]; then
    printf "%b❌ %d FAILURE(S) — fix the items above and re-run %s/scripts/preflight_check.sh%b\n" \
        "$RED" "$fail" "$HERE" "$NC"
    exit 1
elif [ "$warn" -gt 0 ]; then
    printf "%b⚠️  %d warning(s) — should still work but be aware%b\n" "$YELLOW" "$warn" "$NC"
    printf "%b✅ READY — your laptop is set up for AutoCon5 WS:C2%b\n" "$GREEN" "$NC"
    exit 0
else
    printf "%b✅ READY — your laptop is set up for AutoCon5 WS:C2%b\n" "$GREEN" "$NC"
    exit 0
fi
