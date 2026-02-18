# setup_agent.py
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FunctionTool
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
import os

load_dotenv()

def search_dental_plan_tool(query: str) -> str:
    """
    Search dental plan documents for coverage information.
    :param query: The user's dental coverage question.
    :return: Relevant plan text chunks.
    """
    return ""

functions = FunctionTool(functions=[search_dental_plan_tool])

agents_client = AgentsClient(
    endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
    credential=DefaultAzureCredential(),
)

with agents_client:
    agent = agents_client.create_agent(
        model="gpt-4o",
        name="coverage_agent",
        instructions="""You are a dental insurance coverage assistant.
            ALWAYS use the search_dental_plan_tool to retrieve plan information before answering.
            Answer ONLY based on retrieved context.
            Be specific about coverage percentages, deductibles, annual maximums.
            Map procedures to categories (wisdom tooth = Oral Surgery, braces = Orthodontics).
            NEVER make up information.""",
        tools=functions.definitions,
    )
    print(f"Agent ID: {agent.id}")
    print("Add this to .env as COVERAGE_AGENT_ID")