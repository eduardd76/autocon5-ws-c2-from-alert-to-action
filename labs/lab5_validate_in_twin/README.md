# Lab 5 — Validate a fix against the twin (capstone)

**The missing step between "propose" and "approve."** In Labs 1–3 an agent proposes a
fix; a human approves it. Here we insert a safety gate in between: **dry-run the proposed
fix against the knowledge graph you built in Lab 4** — and only surface it if the network
stays healthy.

> Same idea as the production Digital Twin, at 3-router scale:
> **model proposes · evidence grounds · twin validates · human disposes.**

You're SSH'd into your pod, Neo4j is running (Lab 4), and the graph is loaded.

```
cd ~/autocon5-ws-c2-from-alert-to-action/labs/lab5_validate_in_twin
python3 twin_validate.py
```

## What it does
1. **Resets** the graph to a healthy full mesh (so it's repeatable).
2. **Injects an incident:** the `R2 ↔ R3` OSPF adjacency goes `DOWN` (persisted — this is
   the live fault you'd see in Neo4j Browser).
3. **Dry-runs FIX A** (good — *restore the R2↔R3 adjacency*) inside a transaction, checks
   health, then **rolls back**. → no partitions, mesh 3/3, incident resolved → **PASS ✅**
4. **Dry-runs FIX B** (bad — *shut the R1–R3 link to "force a reconverge"*), checks health,
   **rolls back**. → with R2↔R3 already down, this isolates R3 → **REJECT ❌**

Expected output (abridged):
```
[1] INCIDENT: R2<->R3 adjacency DOWN.
[2] FIX A: restore R2<->R3 ...  VERDICT: PASS  ✅
[3] FIX B: shut the R1-R3 link ...  VERDICT: REJECT ❌  (would isolate: R1 <-> R3 ... R3)
```

## The one idea
A knowledge graph isn't just a picture — it's a **non-destructive testbed**. The safety
check is pure graph reachability:

```cypher
// is any pair PARTITIONED? (no path using only FULL adjacencies)
MATCH (a:Router),(b:Router) WHERE a.name < b.name
WITH a,b WHERE NOT EXISTS {
  MATCH p=(a)-[:OSPF_NEIGHBOR*1..6]-(b)
  WHERE all(r IN relationships(p) WHERE r.state='FULL') }
RETURN a.name, b.name;   // empty = healthy
```

And the magic that keeps the twin clean: **apply the fix in a Neo4j transaction, run the
check, then `DELETE` (roll back) the transaction.** Simulate → read the verdict → discard.

## See the incident in the browser
After running the script the graph is left in the *faulted* state. With your Lab 4 tunnel
open, browse **http://localhost:7474** and run:
```cypher
MATCH (r:Router)-[n:OSPF_NEIGHBOR]->(m:Router) RETURN r, n, m;
```
The `R2–R3` adjacency now shows `state:'DOWN'`. Re-run `twin_validate.py` to reset & replay.

**What you learned:** you turned the graph into a digital twin and used it to **test a fix
before it touches the network** — catching a dangerous one (isolating R3) automatically.
That's the safety layer that makes autonomous remediation trustworthy.
