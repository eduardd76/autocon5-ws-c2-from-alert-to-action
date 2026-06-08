#!/usr/bin/env python3
"""
twin_validate.py — use the Knowledge Graph as a DIGITAL TWIN.

The idea (the whole point of Lab 5):
  An incident happens. An agent proposes a fix. BEFORE a human approves it, we
  *dry-run* that fix against the graph and ask: "does the network stay healthy?"

How the dry-run stays safe:
  We apply the proposed change inside a Neo4j TRANSACTION, run our health checks,
  then ROLL THE TRANSACTION BACK. The twin tells us the outcome without ever being
  mutated — simulate, read the verdict, discard.

Prereq: run Lab 4 first (python3 load.py) so the 3-router graph exists.
Same modeling as the production fabric twin, at 3-router scale.
"""
import base64, json, urllib.request

BASE = "http://localhost:7474/db/neo4j"
HDRS = {"Content-Type": "application/json",
        "Authorization": "Basic " + base64.b64encode(b"neo4j:ospf12345").decode()}


# ---------------------------------------------------------------- HTTP helpers
def _req(url, payload=None, method="POST"):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(url, data=data, headers=HDRS, method=method)
    return urllib.request.urlopen(r)

def commit_run(statements):
    """Run statements and COMMIT them (a permanent change)."""
    body = json.load(_req(BASE + "/tx/commit", {"statements": statements}))
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return [[d["row"] for d in res["data"]] for res in body["results"]]

def dryrun(statements):
    """Run statements in a transaction, read results, then ROLL BACK.
    Nothing is persisted — this is the 'twin' simulation."""
    body = json.load(_req(BASE + "/tx", {"statements": statements}))
    tx_url = body["commit"].rsplit("/", 1)[0]          # .../tx/<id>/commit -> .../tx/<id>
    try:
        if body.get("errors"):
            raise RuntimeError(body["errors"])
        return [[d["row"] for d in res["data"]] for res in body["results"]]
    finally:
        _req(tx_url, method="DELETE")                  # <-- the rollback


# ----------------------------------------------------------------- the checks
# A pair is PARTITIONED if there is NO path between them using only FULL adjacencies.
PARTITION = (
    "MATCH (a:Router),(b:Router) WHERE a.name < b.name "
    "WITH a,b WHERE NOT EXISTS { "
    "  MATCH p=(a)-[:OSPF_NEIGHBOR*1..6]-(b) "
    "  WHERE all(r IN relationships(p) WHERE r.state='FULL') } "
    "RETURN a.name + ' <-> ' + b.name AS broken"
)
# How many of the 3 designed adjacencies are currently FULL (the mesh completeness).
MESH = (
    "MATCH (a:Router)-[r:OSPF_NEIGHBOR]->(b:Router) "
    "WHERE r.state='FULL' AND a.name < b.name "
    "RETURN count(*) AS full_pairs"
)
# Is the incident's link (R2<->R3) directly FULL again?
RESOLVED = (
    "RETURN exists( (:Router{name:'R2'})-[:OSPF_NEIGHBOR {state:'FULL'}]-(:Router{name:'R3'}) ) AS ok"
)

def stmt(c):  # wrap a cypher string as a statement object
    return {"statement": c}


def health(prefix, extra_fix=None):
    """Run the checks (optionally after applying a proposed fix, dry-run)."""
    fix = [stmt(s) for s in extra_fix] if extra_fix else []
    rows = dryrun(fix + [stmt(PARTITION), stmt(MESH), stmt(RESOLVED)])  # non-destructive
    off = len(fix)
    partitions = [r[0] for r in rows[off + 0]]
    full_pairs = rows[off + 1][0][0]
    resolved   = rows[off + 2][0][0]
    return partitions, full_pairs, resolved


# ----------------------------------------------------------------- the scenario
def main():
    print("=" * 60)
    print("  TWIN VALIDATION — 3-router OSPF knowledge graph")
    print("=" * 60)

    # 0) Reset to a healthy full mesh so this script is repeatable.
    commit_run([stmt("MATCH ()-[r:OSPF_NEIGHBOR]->() SET r.state='FULL'")])
    p, full, _ = health("baseline")
    print(f"\n[0] Baseline: full_pairs={full}/3, partitions={p or 'none'}  -> HEALTHY")

    # 1) INCIDENT: the R2<->R3 OSPF adjacency goes DOWN (persist it = the live fault).
    commit_run([stmt("MATCH (:Router{name:'R2'})-[r:OSPF_NEIGHBOR]-(:Router{name:'R3'}) "
                     "SET r.state='DOWN'")])
    p, full, _ = health("incident")
    print(f"\n[1] INCIDENT: R2<->R3 adjacency DOWN.")
    print(f"    full_pairs={full}/3  partitions={p or 'none (R2 still reaches R3 via R1 — but R1 is now a single point of failure)'}")

    # 2) Agent proposes FIX A (good): restore the R2<->R3 adjacency.
    fix_a = ["MATCH (:Router{name:'R2'})-[r:OSPF_NEIGHBOR]-(:Router{name:'R3'}) SET r.state='FULL'"]
    p, full, resolved = health("fixA", fix_a)
    verdict = "PASS  ✅  (safe to approve)" if (not p and resolved) else "REJECT ❌"
    print(f"\n[2] FIX A (agent): restore R2<->R3 adjacency.")
    print(f"    twin dry-run -> partitions={p or 'none'}  mesh={full}/3  incident_resolved={resolved}")
    print(f"    VERDICT: {verdict}")

    # 3) Agent proposes FIX B (bad): shut the R1-R3 link to 'force a reconverge'.
    fix_b = ["MATCH (:Router{name:'R1'})-[r:OSPF_NEIGHBOR]-(:Router{name:'R3'}) SET r.state='DOWN'"]
    p, full, resolved = health("fixB", fix_b)
    verdict = "PASS  ✅" if not p else f"REJECT ❌  (would isolate: {', '.join(p)})"
    print(f"\n[3] FIX B (agent): shut the R1-R3 link to force a reconverge.")
    print(f"    twin dry-run -> partitions={p or 'none'}  mesh={full}/3")
    print(f"    VERDICT: {verdict}")

    print("\n" + "-" * 60)
    print("Both fixes were dry-run in rolled-back transactions — the twin is")
    print("unchanged (still showing the incident). The twin APPROVED the safe")
    print("fix and REJECTED the one that would black-hole R3, before any human.")
    print("Re-run this script to reset & replay. (load.py also resets the graph.)")


if __name__ == "__main__":
    main()
