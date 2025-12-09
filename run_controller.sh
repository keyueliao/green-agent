#!/bin/bash
set -e

echo "🤖 Starting AgentBeats Controller..."

# IMPORTANT: Do NOT cd into a local Mac path!
# Platform expects to run inside the repo root.
cd "$(dirname "$0")"

# Your Cloudflare tunnel (MUST start with https)
export CLOUDRUN_HOST="https://promoted-dual-annual-gave.trycloudflare.com"

# Enable HTTPS
export HTTPS_ENABLED=true

# Run controller
agentbeats run_ctrl
