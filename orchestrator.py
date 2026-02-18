# Calls router agent → gets intent (coverage, provider_search, cost_estimate, general)
# Delegates to the matching agent(s)
# Supports multi-intent queries (e.g. "coverage,provider_search")
# Cost queries chain: Coverage Agent (get PPO + Premier %) → Cost Estimator (calculate out-of-pocket)

import os
import re
from dotenv import load_dotenv
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import AgentThreadCreationOptions, ThreadMessageOptions, MessageTextContent, MessageRole
from azure.identity import DefaultAzureCredential
from concurrent.futures import ThreadPoolExecutor

# Import agent runners
from router_agent import classify_intent
from coverage_agent import run_coverage_agent
from provider_finder_agent import run_provider_finder_agent
from cost_estimator_agent import run_cost_estimator_agent

load_dotenv()

AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")


def extract_coverage_percent(coverage_response: str) -> dict:
    """Extract PPO and Premier coverage percentages from coverage agent response."""
    result = {"ppo": "0", "premier": "0"}

    text = coverage_response.lower()

    # Try to find PPO-specific percentage
    ppo_match = re.search(r'ppo[^0-9]*(\d{1,3})\s*%', text)
    if ppo_match:
        result["ppo"] = ppo_match.group(1)

    # Try to find Premier-specific percentage
    premier_match = re.search(r'premier[^0-9]*(\d{1,3})\s*%', text)
    if premier_match:
        result["premier"] = premier_match.group(1)

    # If neither found, grab first percentage as fallback for both
    if result["ppo"] == "0" and result["premier"] == "0":
        fallback = re.findall(r'(\d{1,3})\s*%', coverage_response)
        if fallback:
            result["ppo"] = fallback[0]
            result["premier"] = fallback[0]

    # If only one found, use it for both
    if result["ppo"] == "0" and result["premier"] != "0":
        result["ppo"] = result["premier"]
    elif result["premier"] == "0" and result["ppo"] != "0":
        result["premier"] = result["ppo"]

    return result

# query cleaner
def make_coverage_query(user_query: str) -> str:
    """Extract procedure keyword and build clean coverage query."""
    procedures = ["cleaning", "crown", "root canal", "filling", "extraction", "wisdom tooth",
                   "braces", "denture", "x-ray", "implant", "sealant", "veneer", "fluoride",
                   "exam", "bridge", "orthodontic", "periodontic", "checkup"]
    found = [p for p in procedures if p in user_query.lower()]
    if found:
        return f"What is my coverage percentage for {found[0]}? Include deductible and annual maximum."
    return user_query

def run_orchestrator(user_query: str, plan_filter: str = None):
    """Route query to the appropriate agent(s) based on intent."""
    print(f"\nUser: {user_query}")

    intent_raw = classify_intent(user_query)
    intents = [i.strip() for i in intent_raw.split(",")]
    print(f"Intent(s): {intents}")

    responses = []
    has_coverage = any("coverage" in i for i in intents)
    has_provider = any("provider" in i for i in intents)
    has_cost = any("cost" in i for i in intents)

    # Run coverage and provider — parallel if both, otherwise individual
    if has_coverage and has_provider:
        with ThreadPoolExecutor(max_workers=2) as executor:
            coverage_future = executor.submit(run_coverage_agent, make_coverage_query(user_query), plan_filter)
            provider_future = executor.submit(run_provider_finder_agent, user_query)
            responses.append(coverage_future.result())
            responses.append(provider_future.result())
    else:
        if has_coverage:
            responses.append(run_coverage_agent(make_coverage_query(user_query), plan_filter))
        if has_provider:
            responses.append(run_provider_finder_agent(user_query))

    #cost chain needs to be sequential to extract coverage % first, then pass to cost estimator
    if has_cost:
        coverage_query = f"What is the coverage percentage for {user_query}? Provide the percentage for both Delta Dental PPO dentists and Delta Dental Premier dentists separately."
        print("  → Checking coverage first...")
        coverage_response = run_coverage_agent(coverage_query, plan_filter)

        coverage = extract_coverage_percent(coverage_response or "")
        print(f" → Extracted coverage: PPO {coverage['ppo']}%, Premier {coverage['premier']}%")

        ppo_query = f"Calculate the out-of-pocket cost for a procedure with {coverage['ppo']}% coverage. {user_query}"
        ppo_response = run_cost_estimator_agent(ppo_query, plan_filter)

        if coverage["ppo"] != coverage["premier"]:
            premier_query = f"{user_query}\nCoverage percentage for Delta Dental Premier dentists is: {coverage['premier']}%. Calculate the out-of-pocket cost for a procedure with this coverage."
            premier_response = run_cost_estimator_agent(premier_query, plan_filter)
            combined_cost = f"**With a Delta Dental PPO dentist:** {ppo_response}\n\n**With a Delta Dental Premier dentist:** {premier_response}"
        else:
            combined_cost = f"**Coverage is the same for PPO and Premier dentists at {coverage['ppo']}%**, so the out-of-pocket cost is: {ppo_response}"
        
        responses.append(combined_cost)

    if not responses:
        responses.append("I can help with dental coverage questions, finding providers, or estimating costs. What would you like to know?")

    combined = "\n\n---\n\n".join(responses)
    print(f"\nResponse:\n{combined}")
    return combined

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
# Updated to be able to let users change plans without restarting the program
    while True:
        query = input("\nAsk a question (or 'quit' or 'change plan'): ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if query.lower() in ("change plan", "change", "plan", "switch plan"):
            print("\nSelect a plan:")
            for key, (name, _) in plan_options.items():
                print(f"  {key}. {name}")
            choice = input("\nEnter number (1-6): ").strip()
            plan_name, plan_filter = plan_options.get(choice, ("All Plans", None))
            print(f"Selected: {plan_name}")
            continue

        run_orchestrator(query, plan_filter)
