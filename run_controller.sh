#!/bin/bash
set -e

echo "🤖 Starting AgentBeats Controller..."


cd /Users/liaokeyue/green-agent

export CLOUDRUN_HOST="laboratories-treat-strips-derek.trycloudflare.com"


export HTTPS_ENABLED=true


agentbeats run_ctrl
