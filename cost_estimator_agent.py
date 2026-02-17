# How it works:

# Downloads procedure_costs.json from blob
# get_procedure_cost(procedure, coverage_percent) → finds matching procedures, calculates out-of-pocket
# Agent passes plan context so it knows coverage %

import os
import json
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FunctionTool, MessageTextContent, MessageRole, AgentThreadCreationOptions, ThreadMessageOptions
from azure.identity import DefaultAzureCredential

load_dotenv()

AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
COST_ESTIMATOR_AGENT_ID = os.getenv("COST_ESTIMATOR_AGENT_ID")
CONTAINER_NAME = "procedurecosts"


def load_procedure_costs():
    """Download procedure_costs.json from Azure Blob Storage."""
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    container = blob_service_client.get_container_client(CONTAINER_NAME)
    blob_data = container.download_blob("procedure_costs.json").readall()
    data = json.loads(blob_data)
    return data["procedures"]


# Load once at module level
PROCEDURES = load_procedure_costs()


def get_procedure_cost(procedure: str, coverage_percent: str = "0") -> str:
    """
    Look up the cost of a dental procedure and calculate patient out-of-pocket cost.
    :param procedure: Name or keyword of the procedure (e.g. cleaning, root canal, crown, extraction, wisdom tooth, filling, braces, denture, x-ray, implant, sealant, veneer, fluoride, exam).
    :param coverage_percent: Insurance coverage percentage as a number 0-100 (e.g. '80' for 80% coverage). Default '0' for no insurance.
    :return: Cost estimate and out-of-pocket calculation.
    """
    keyword = procedure.lower()
    matches = [p for p in PROCEDURES if keyword in p["name"].lower()]

    if not matches:
        # Try matching by category
        matches = [p for p in PROCEDURES if keyword in p["category"].lower()]

    if not matches:
        return f"No cost data found for '{procedure}'. Try: cleaning, filling, crown, root canal, extraction, wisdom tooth, braces, denture, x-ray, implant, sealant, veneer, fluoride, exam."

    try:
        coverage = float(coverage_percent) / 100.0
    except ValueError:
        coverage = 0.0

    coverage = max(0.0, min(1.0, coverage))

    output = []
    for p in matches:
        avg_cost = (p["cost_low"] + p["cost_high"]) / 2
        patient_low = p["cost_low"] * (1 - coverage)
        patient_high = p["cost_high"] * (1 - coverage)

        entry = (
            f"Procedure: {p['name']}\n"
            f"Category: {p['category']}\n"
            f"Full Cost: ${p['cost_low']:,.0f} - ${p['cost_high']:,.0f}\n"
            f"Average Cost: ${avg_cost:,.0f}"
        )

        if coverage > 0:
            entry += (
                f"\nInsurance Coverage: {coverage_percent}%\n"
                f"Estimated Out-of-Pocket: ${patient_low:,.0f} - ${patient_high:,.0f}"
            )

        output.append(entry)

    return "\n\n---\n\n".join(output)


def run_cost_estimator_agent(user_query: str, plan_filter: str = None):
    """Run the cost estimator agent with cost lookup tool."""
    agents_client = AgentsClient(
        endpoint=AZURE_AI_PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )

    def get_procedure_cost_tool(procedure: str, coverage_percent: str = "0") -> str:
        """
        Look up the cost of a dental procedure and calculate patient out-of-pocket cost.
        :param procedure: Name or keyword of the procedure (e.g. cleaning, root canal, crown, extraction, wisdom tooth, filling, braces, denture, x-ray, implant, sealant, veneer, fluoride, exam).
        :param coverage_percent: Insurance coverage percentage as a number 0-100 (e.g. '80' for 80% coverage). Default '0' for no insurance.
        :return: Cost estimate and out-of-pocket calculation.
        """
        return get_procedure_cost(procedure, coverage_percent)

    functions = FunctionTool(functions=[get_procedure_cost_tool])

    with agents_client:
        agents_client.enable_auto_function_calls(functions)

        # Add plan context to help agent know coverage percentages
        enhanced_query = user_query
        if plan_filter:
            enhanced_query += f"\n(User's plan: {plan_filter})"

        run = agents_client.create_thread_and_process_run(
            agent_id=COST_ESTIMATOR_AGENT_ID,
            thread=AgentThreadCreationOptions(
                messages=[ThreadMessageOptions(role="user", content=enhanced_query)]
            ),
        )

        messages = list(agents_client.messages.list(thread_id=run.thread_id))

        response_text = None
        for msg in messages:
            if msg.role == MessageRole.AGENT:
                for item in msg.content:
                    if isinstance(item, MessageTextContent):
                        response_text = item.text.value
                        break
                break
# NOTED OUT PRINT STATEMENT SO ORCHESTRATOR DOES NOT DOUBLE OUTPUT
        #print(f"\nCost Estimator: {response_text}")
        return response_text or "No response generated."


# ── Entry point for standalone testing ────────────────────────────────────────
if __name__ == "__main__":
    print("Delta Dental Cost Estimator")
    print("=" * 40)

    query = input("\nAsk about a procedure cost: ").strip()
    run_cost_estimator_agent(query)