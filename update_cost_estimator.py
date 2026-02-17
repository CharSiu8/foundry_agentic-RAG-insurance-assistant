"""
One-time script: Attach get_procedure_cost_tool to existing Cost Estimator agent.
Run once, then delete or ignore.
"""
import os
from dotenv import load_dotenv
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FunctionTool
from azure.identity import DefaultAzureCredential

load_dotenv()

AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
COST_ESTIMATOR_AGENT_ID = os.getenv("COST_ESTIMATOR_AGENT_ID")


def get_procedure_cost_tool(procedure: str, coverage_percent: str = "0") -> str:
    """
    Look up the cost of a dental procedure and calculate patient out-of-pocket cost.
    :param procedure: Name or keyword of the procedure (e.g. cleaning, root canal, crown, extraction, wisdom tooth, filling, braces, denture, x-ray, implant, sealant, veneer, fluoride, exam).
    :param coverage_percent: Insurance coverage percentage as a number 0-100 (e.g. '80' for 80% coverage). Default '0' for no insurance.
    :return: Cost estimate and out-of-pocket calculation.
    """
    return ""  # Dummy — only need the schema


functions = FunctionTool(functions=[get_procedure_cost_tool])

agents_client = AgentsClient(
    endpoint=AZURE_AI_PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)

with agents_client:
    updated_agent = agents_client.update_agent(
        agent_id=COST_ESTIMATOR_AGENT_ID,
        tools=functions.definitions,
    )
    print(f"✅ Updated agent: {updated_agent.id}")
    print(f"   Tools: {[t['function']['name'] for t in updated_agent.tools]}")