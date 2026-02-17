# run_provider_finder_agent(user_query) from provider_finder_agent.py
# run_cost_estimator_agent(user_query, plan_filter) from cost_estimator_agent.py
# Calls router agent → gets intent (coverage, provider_search, cost_estimate, general)
# Delegates to the matching agent
# Includes a while loop so you can ask multiple questions
# Cost queries chain: Coverage Agent (get %) → Cost Estimator (calculate out-of-pocket)

import os
import re
from dotenv import load_dotenv
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import AgentThreadCreationOptions, ThreadMessageOptions, MessageTextContent, MessageRole
from azure.identity import DefaultAzureCredential

# Import agent runners
from coverage_agent import run_coverage_agent
from provider_finder_agent import run_provider_finder_agent
from cost_estimator_agent import run_cost_estimator_agent

load_dotenv()

AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
ROUTER_AGENT_ID = os.getenv("ROUTER_AGENT_ID")


def classify_intent(user_query: str) -> str:
    """Use router agent to classify user intent."""
    agents_client = AgentsClient(
        endpoint=AZURE_AI_PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )

    with agents_client:
        run = agents_client.create_thread_and_process_run(
            agent_id=ROUTER_AGENT_ID,
            thread=AgentThreadCreationOptions(
                messages=[ThreadMessageOptions(role="user", content=user_query)]
            ),
        )

        messages = list(agents_client.messages.list(thread_id=run.thread_id))
        for msg in messages:
            if msg.role == MessageRole.AGENT:
                for item in msg.content:
                    if isinstance(item, MessageTextContent):
                        return item.text.value.strip().lower()

    return "general"


def extract_coverage_percent(coverage_response: str) -> str:
    """Extract coverage percentage from coverage agent response."""
    # Look for patterns like "80%", "50 percent", "covered at 80"
    matches = re.findall(r'(\d{1,3})\s*%', coverage_response)
    if matches:
        # Return the first percentage found
        return matches[0]
    return "0"


def run_orchestrator(user_query: str, plan_filter: str = None):
    """Route query to the appropriate agent based on intent."""
    print(f"\nUser: {user_query}")

    intent = classify_intent(user_query)
    print(f"Intent: {intent}")

    if "coverage" in intent:
        response = run_coverage_agent(user_query, plan_filter)

    elif "provider" in intent:
        response = run_provider_finder_agent(user_query)

    elif "cost" in intent:
        # Step 1: Ask Coverage Agent for coverage %
        coverage_query = f"What is the coverage percentage for {user_query}? Reply with the specific percentage."
        print("  → Checking coverage first...")
        coverage_response = run_coverage_agent(coverage_query, plan_filter)

        # Step 2: Extract % from coverage response
        coverage_percent = extract_coverage_percent(coverage_response or "")
        print(f"  → Coverage found: {coverage_percent}%")

        # Step 3: Pass to Cost Estimator with coverage %
        enhanced_query = f"{user_query}\nCoverage percentage from plan: {coverage_percent}%"
        response = run_cost_estimator_agent(enhanced_query, plan_filter)

    else:
        response = "I can help with dental coverage questions, finding providers, or estimating costs. What would you like to know?"

    print(f"\nResponse: {response}")
    return response


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Delta Dental AI Assistant")
    print("=" * 40)

    plan_options = {
        "1": ("Base Plan", "baseplan.pdf"),
        "2": ("Premium Plan", "premiumplan.pdf"),
        "3": ("State Plan", "stateplan.pdf"),
        "4": ("Compare Plans", "plancompare.pdf"),
        "5": ("FAQ", "BasicFAQ.txt"),
        "6": ("All Plans", None)
    }

    print("\nSelect a plan:")
    for key, (name, _) in plan_options.items():
        print(f"  {key}. {name}")

    choice = input("\nEnter number (1-6): ").strip()
    plan_name, plan_filter = plan_options.get(choice, ("All Plans", None))
    print(f"Selected: {plan_name}")

    while True:
        query = input("\nAsk a question (or 'quit'): ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        run_orchestrator(query, plan_filter)