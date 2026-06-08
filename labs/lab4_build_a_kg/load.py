#!/usr/bin/env python3
"""
load.py — read ospf-area0.yaml and draw it into Neo4j as a knowledge graph.

It turns:
  - each router   -> a (:Router) node
  - each neighbor -> an (a)-[:OSPF_NEIGHBOR]->(b) relationship

Everything uses MERGE (create-or-update), so running it twice is safe:
you get the same graph, never duplicates.
"""
import base64, json, urllib.request, yaml

URL  = "http://localhost:7474/db/neo4j/tx/commit"
AUTH = "Basic " + base64.b64encode(b"neo4j:ospf12345").decode()

data  = yaml.safe_load(open("ospf-area0.yaml"))
area  = data["area"]
stmts = []

# 1) One :Router node per router. MERGE finds-or-creates on the unique key `name`,
#    then SET fills in its properties.
for r in data["routers"]:
    stmts.append({
        "statement": "MERGE (r:Router {name:$name}) "
                     "SET r.router_id=$rid, r.area=$area",
        "parameters": {"name": r["id"], "rid": r["router_id"], "area": area},
    })

# 2) One :OSPF_NEIGHBOR relationship per interface (this router -> its neighbor).
#    The interface details live ON the relationship (that router's own view).
for r in data["routers"]:
    for itf in r["interfaces"]:
        stmts.append({
            "statement": "MATCH (a:Router {name:$a}), (b:Router {name:$b}) "
                         "MERGE (a)-[n:OSPF_NEIGHBOR]->(b) "
                         "SET n.local_interface=$itf, n.local_ip=$ip, "
                         "    n.state='FULL', n.area=$area",
            "parameters": {"a": r["id"], "b": itf["neighbor"],
                           "itf": itf["name"], "ip": itf["ip"], "area": area},
        })

# Send them all in one transaction.
body = json.dumps({"statements": stmts}).encode()
req  = urllib.request.Request(URL, data=body,
        headers={"Content-Type": "application/json", "Authorization": AUTH})
result = json.load(urllib.request.urlopen(req))

errors = result.get("errors", [])
print(f"Sent {len(stmts)} statements "
      f"({len(data['routers'])} routers + relationships).")
print("Errors:", errors if errors else "none")
