#!/bin/bash
set -e

echo "🚀 Registering Green Agent for AgentBeats..."


rm -rf .ab/agents
rm -f .ab/agents.json
mkdir -p .ab/agents


agentbeats register \
  --name "AppWorld Green Agent" \
  --scenario "appworld" \
  --card "scenarios/appworld/green_agent/green_agent_card.toml"

echo "🤖 Starting Controller..."
./run_controller.sh
