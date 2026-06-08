#!/bin/bash
# start-neo4j.sh — start Neo4j for Lab 4.
#
# You reach it from your laptop with an SSH tunnel (see README), so Neo4j only
# needs to advertise Bolt on localhost — nothing is exposed to the internet.
set -e

docker rm -f ospf-neo4j >/dev/null 2>&1 || true
docker run -d --name ospf-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/ospf12345 \
  -e NEO4J_server_bolt_advertised__address=localhost:7687 \
  -e NEO4J_server_memory_heap_max__size=512m \
  -e NEO4J_server_memory_pagecache_size=256m \
  neo4j:5-community >/dev/null

echo "Neo4j is starting (give it ~30 seconds)."
echo "From your LAPTOP, open a tunnel (new terminal):"
echo "    ssh -L 7474:localhost:7474 -L 7687:localhost:7687 ubuntu@<your-pod-ip>"
echo "Then in your browser:  http://localhost:7474   (login: neo4j / ospf12345)"
echo "Then back here:        python3 load.py   (and later: python3 load_rich.py)"
