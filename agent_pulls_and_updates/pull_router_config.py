"""
Pull Router agent config from Foundry and save to router_agent_config.json.
Run once to version control your Router agent.
"""
import os
import json
from dotenv import load_dotenv
from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential

load_dotenv()

AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
ROUTER_AGENT_ID = os.getenv("ROUTER_AGENT_ID")

agents_client = AgentsClient(
    endpoint=AZURE_AI_PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)

with agents_client:
    agent = agents_client.get_agent(agent_id=ROUTER_AGENT_ID)

    config = {
        "id": agent.id,
        "name": agent.name,
        "model": agent.model,
        "instructions": agent.instructions,
        "tools": agent.tools,
    }

    with open("router_agent_config.json", "w") as f:
        json.dump(config, f, indent=2, default=str)

    print(f"✅ Saved Router agent config to router_agent_config.json")
    print(f"   Name: {agent.name}")
    print(f"   Model: {agent.model}")
    print(f"   Instructions: {agent.instructions[:100]}...")