# Lab 4 — Build a Knowledge Graph for a 3-router network

**The brain behind the agents.** In Labs 1–3 the specialists *read* a knowledge graph
to ground their answers. Here you **build one** — from a YAML description of a tiny
OSPF network (3 routers in a triangle) to a live, clickable Neo4j graph you can query.

> Same modeling as the production fabric KG (Device + Interface + Network), at 3-router
> scale. If you can sketch it, you can query it.

You're SSH'd into your pod (`ssh ubuntu@<your-pod-ip>`, password `Cisco123`).

```
cd ~/autocon5-ws-c2-from-alert-to-action/labs/lab4_build_a_kg
```

---

## Step 1 — Look at the source of truth (YAML)
```
cat ospf-area0.yaml
```
3 routers (R1/R2/R3), all in OSPF area 0, each interface names the neighbor it connects
to. This file is the single source of truth; the loader turns it into the graph.

## Step 2 — Start Neo4j (one command)
```
bash start-neo4j.sh
```
This starts the `neo4j:5-community` container on your pod (auth `neo4j/ospf12345`).
Wait ~30 seconds for it to come up.

## Step 3 — Open a tunnel to the Neo4j Browser
Neo4j isn't exposed to the internet — you reach it through your SSH session.
In a **new terminal on your laptop**, open a tunnel (use your pod IP):
```
ssh -L 7474:localhost:7474 -L 7687:localhost:7687 ubuntu@<your-pod-ip>
```
(password `Cisco123`; leave this terminal open). Now your pod's Neo4j appears at
your own `localhost`.

## Step 4 — Load the YAML into the graph
Back in your **first** terminal (the lab folder):
```
python3 load.py
```
Creates one `(:Router)` node per router and one `(:Router)-[:OSPF_NEIGHBOR]->(:Router)`
relationship per interface. `MERGE` makes it idempotent — safe to re-run.
Expect: `Sent 9 statements (3 routers + relationships). Errors: none`.

## Step 5 — See it in the browser
Open **http://localhost:7474**, log in with **neo4j / ospf12345**,
paste this and press ▶:
```cypher
MATCH (r:Router)-[n:OSPF_NEIGHBOR]->(m:Router) RETURN r, n, m;
```
You'll see your triangle — 3 circles joined by arrows. Click a circle for node
properties; click a line for the interface/IP on that adjacency.
*(Tip: set the node caption to `name` so the circles read R1/R2/R3.)*

## Step 6 — Ask the graph questions (Cypher)
```cypher
// all routers
MATCH (r:Router) RETURN r.name, r.router_id, r.area;
// R1's neighbors
MATCH (:Router {name:'R1'})-[:OSPF_NEIGHBOR]->(n) RETURN n.name;
// mesh check
MATCH (r)-[:OSPF_NEIGHBOR]->(n) RETURN r.name, count(n);
// shortest path R2 -> R3
MATCH p=shortestPath((a:Router {name:'R2'})-[:OSPF_NEIGHBOR*]-(b:Router {name:'R3'})) RETURN p;
```

## Step 7 — Enrich it: Interface + Network layer
```
python3 load_rich.py
```
Promotes each port to an `(:Interface)` node and adds a shared `(:Network)` (subnet)
node = the "cable". Two interfaces in the same Network are the two ends of one link.
The payoff query — discover physical links via shared subnet:
```cypher
MATCH (r1:Router)-[:HAS_INTERFACE]->(:Interface)-[:IN_SUBNET]->(s:Network)
      <-[:IN_SUBNET]-(:Interface)<-[:HAS_INTERFACE]-(r2:Router)
WHERE r1.name < r2.name
RETURN s.cidr, r1.name, r2.name;
```
Final graph: 12 nodes (3 Router · 6 Interface · 3 Network), 18 relationships.

---

## Restart any time
```
docker start ospf-neo4j   # if stopped
python3 load.py && python3 load_rich.py
```

**What you learned:** a knowledge graph is just **dots (nodes) and lines (relationships)
you can walk**, and Cypher is that walk written down. You turned a YAML description of a
network into a queryable graph — exactly what grounds the agents in Labs 1–3.

Full line-by-line walkthrough: the *Neo4j-KG-Tutorial-OSPF* deck.
