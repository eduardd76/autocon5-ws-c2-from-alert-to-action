#!/usr/bin/env python3
"""
load_rich.py — add an Interface + Network layer to the existing OSPF graph.

For every interface in the YAML it creates:
  (Router)-[:HAS_INTERFACE]->(Interface)       # the port belongs to the router
  (Interface)-[:IN_SUBNET]->(Network)          # the port sits in a subnet (the "cable")

Two interfaces that share a Network = the two ends of one physical link.
Idempotent (MERGE), so it's safe to re-run. Run load.py first.
"""
import base64, ipaddress, json, urllib.request, yaml

URL  = "http://localhost:7474/db/neo4j/tx/commit"
AUTH = "Basic " + base64.b64encode(b"neo4j:ospf12345").decode()

data  = yaml.safe_load(open("ospf-area0.yaml"))
stmts = []

for r in data["routers"]:
    for itf in r["interfaces"]:
        ifid = f"{r['id']}:{itf['name']}"                       # unique key, e.g. "R1:Gi0/0"
        cidr = str(ipaddress.ip_interface(itf["ip"]).network)   # "10.0.12.1/30" -> "10.0.12.0/30"
        stmts.append({
            "statement":
                "MATCH (r:Router {name:$dev}) "
                "MERGE (i:Interface {iface_id:$ifid}) "
                "  SET i.name=$name, i.ip=$ip, i.status='up' "
                "MERGE (r)-[:HAS_INTERFACE]->(i) "
                "MERGE (s:Network {cidr:$cidr}) "
                "MERGE (i)-[:IN_SUBNET]->(s)",
            "parameters": {"dev": r["id"], "ifid": ifid, "name": itf["name"],
                           "ip": itf["ip"], "cidr": cidr},
        })

body = json.dumps({"statements": stmts}).encode()
req  = urllib.request.Request(URL, data=body,
        headers={"Content-Type": "application/json", "Authorization": AUTH})
result = json.load(urllib.request.urlopen(req))
print(f"Sent {len(stmts)} statements.")
print("Errors:", result.get("errors") or "none")
