#!/bin/bash
set -e

echo "🤖 Starting AgentBeats Controller..."

# IMPORTANT: Run inside repo root expected by AgentBeats platform
cd "$(dirname "$0")"

# Your Cloudflare Tunnel (must start with https)
export CLOUDRUN_HOST="https://ballet-bottle-layer-defend.trycloudflare.com"

# Enable HTTPS
export HTTPS_ENABLED=true

# Start controller
agentbeats run_ctrl
