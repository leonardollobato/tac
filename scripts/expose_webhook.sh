#!/bin/bash

# Run Cloudflare tunnel to expose adws/trigger_webhook.py to the public internet
# Requires CLOUDFLARED_TUNNEL_TOKEN to be set in .env

# Load CLOUDFLARED_TUNNEL_TOKEN from .env file
if [ -f .env ]; then
    export CLOUDFLARED_TUNNEL_TOKEN=$(grep CLOUDFLARED_TUNNEL_TOKEN .env | cut -d '=' -f2)
fi

cloudflared tunnel run --token $CLOUDFLARED_TUNNEL_TOKEN