# Router Agent — classifies user intent
# Uses Foundry agent with instructions to return: coverage, provider_search, cost_estimate, general
# Supports multi-intent: returns comma-separated values (e.g. "coverage,provider_search")

import os
from dotenv import load_dotenv
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import AgentThreadCreationOptions, ThreadMessageOptions, MessageTextContent, MessageRole
from azure.identity import DefaultAzureCredential

load_dotenv()

AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
ROUTER_AGENT_ID = os.getenv("ROUTER_AGENT_ID")


def classify_intent(user_query: str) -> str:
    """
    Classify user intent using the Router agent.
    Returns one or more of: coverage, provider_search, cost_estimate, general
    Multiple intents returned as comma-separated string.
    """
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


# ── Entry point for standalone testing ────────────────────────────────────────
if __name__ == "__main__":
    print("Router Agent Test")
    print("=" * 40)

    while True:
        query = input("\nEnter query (or 'quit'): ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        intent = classify_intent(query)
        print(f"Intent: {intent}")