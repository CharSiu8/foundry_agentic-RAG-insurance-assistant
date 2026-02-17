"""
One-time script: Attach search_providers_tool to existing Provider Finder agent.
Run once, then delete or ignore.
"""
import os
from dotenv import load_dotenv
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FunctionTool
from azure.identity import DefaultAzureCredential

load_dotenv()

AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
PROVIDER_FINDER_AGENT_ID = os.getenv("PROVIDER_FINDER_AGENT_ID")


def search_providers_tool(city: str = "", specialty: str = "", network: str = "", accepting_new: str = "true") -> str:
    """
    Search for dental providers by city, specialty, and network.
    :param city: City name to filter by (e.g. Cadillac, Traverse City). Leave empty for all cities.
    :param specialty: Specialty to filter by (e.g. General Dentist, Orthodontist, Endodontist, Prosthodontist). Leave empty for all.
    :param network: Network to filter by (e.g. Delta Dental PPO, Delta Dental Premier). Leave empty for all.
    :param accepting_new: Filter by accepting new patients. Use 'true' or 'false'. Default 'true'.
    :return: Matching providers as formatted text.
    """
    return ""  # Dummy — only need the schema


functions = FunctionTool(functions=[search_providers_tool])

agents_client = AgentsClient(
    endpoint=AZURE_AI_PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)

with agents_client:
    updated_agent = agents_client.update_agent(
        agent_id=PROVIDER_FINDER_AGENT_ID,
        tools=functions.definitions,
    )
    print(f"✅ Updated agent: {updated_agent.id}")
    print(f"   Tools: {[t['function']['name'] for t in updated_agent.tools]}")