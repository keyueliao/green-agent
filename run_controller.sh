#!/bin/bash
set -e

echo "🤖 Starting AgentBeats Controller..."


cd /Users/liaokeyue/agentbeats-new


export CLOUDRUN_HOST="promoted-dual-annual-gave.trycloudflare.com"


export HTTPS_ENABLED=true

agentbeats run_ctrl
