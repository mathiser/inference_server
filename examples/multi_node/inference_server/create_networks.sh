#!/bin/bash
source .env
docker network create -d overlay --attachable $NETWORK_NAME
docker network create -d overlay --attachable traefik-public