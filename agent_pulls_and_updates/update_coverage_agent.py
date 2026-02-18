"""
One-time script: Attach search_dental_plan_tool to existing Coverage Agent.
Run once, then delete or ignore.
"""
import os
from dotenv import load_dotenv
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FunctionTool
from azure.identity import DefaultAzureCredential

load_dotenv()

AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
COVERAGE_AGENT_ID = os.getenv("COVERAGE_AGENT_ID")


def search_dental_plan_tool(query: str) -> str:
    """
    Search dental plan documents for coverage information.
    :param query: The user's dental coverage question.
    :return: Relevant plan text chunks.
    """
    return ""  # Dummy — only need the schema


functions = FunctionTool(functions=[search_dental_plan_tool])

agents_client = AgentsClient(
    endpoint=AZURE_AI_PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)

with agents_client:
    updated_agent = agents_client.update_agent(
        agent_id=COVERAGE_AGENT_ID,
        tools=functions.definitions,
    )
    print(f"✅ Updated agent: {updated_agent.id}")
    print(f"   Tools: {[t['function']['name'] for t in updated_agent.tools]}")