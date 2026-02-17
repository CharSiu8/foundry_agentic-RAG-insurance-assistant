# providers were manually found so it only covers the following cities;
# Ann Arbor, Cadillac, East Grand Rapids, Grand Rapids, Interlochen, Kingsley, Lake City, Lansing, Mesick, Traverse City, Wyoming
# # Flow:

# On startup — downloads 1stproviders (1).json from providerdata blob container, loads it into memory once
# Tool: search_providers(city, specialty, network, accepting_new) — filters the provider list by any combination of:

#City (e.g. "Cadillac", "Traverse City")
#Specialty (e.g. "Orthodontist", "Endodontist")
#Network (e.g. "Delta Dental PPO")
#Accepting new patients (true/false)
#Returns top 10 matches formatted with name, address, phone, etc.


# run_provider_finder_agent(user_query) — creates a Foundry agent thread, 
# passes the user's question, agent decides what filter params to use, 
# calls the tool automatically, returns a natural language response

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
PROVIDER_FINDER_AGENT_ID = os.getenv("PROVIDER_FINDER_AGENT_ID")
CONTAINER_NAME = "providersjson"


def load_providers():
    """Download 1stproviders (1).json from Azure Blob Storage."""
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    container = blob_service_client.get_container_client(CONTAINER_NAME)
    blob_data = container.download_blob("1stproviders (1).json").readall()
    data = json.loads(blob_data)
    return data["providers"]


# Load once at module level
PROVIDERS = load_providers()


def search_providers(
    city: str = "",
    specialty: str = "",
    network: str = "",
    accepting_new: str = "true"
) -> str:
    """
    Search for dental providers by city, specialty, and network. ALWAYS USE THE SEARCH_PROVIDORS TOOL.
    :param city: City name to filter by (e.g. Cadillac, Traverse City). Leave empty for all cities.
    :param specialty: Specialty to filter by (e.g. General Dentist, Orthodontist, Endodontist, Prosthodontist). Leave empty for all.
    :param network: Network to filter by (e.g. Delta Dental PPO, Delta Dental Premier). Leave empty for all.
    :param accepting_new: Filter by accepting new patients. Use 'true' or 'false'. Default 'true'.
    :return: Matching providers as formatted text.
    """
    results = PROVIDERS

    if city:
        results = [p for p in results if city.lower() in p["city"].lower()]

    if specialty:
        results = [p for p in results if specialty.lower() in p["specialty"].lower()]

    if network:
        results = [p for p in results if any(network.lower() in n.lower() for n in p["networks"])]

    if accepting_new.lower() == "true":
        filtered = []
        for p in results:
            for net, accepting in p["accepts_new_patients"].items():
                if accepting:
                    filtered.append(p)
                    break
        results = filtered

    if not results:
        return "No providers found matching your criteria."

    # Limit to top 10
    results = results[:10]

    output = []
    for p in results:
        networks_str = ", ".join(p["networks"])
        languages_str = ", ".join(p["languages"])
        output.append(
            f"Name: {p['name']}\n"
            f"Specialty: {p['specialty']}\n"
            f"Office: {p['office_name']}\n"
            f"Address: {p['address']}\n"
            f"Phone: {p['phone']}\n"
            f"Email: {p['email']}\n"
            f"Hours: {p['hours']}\n"
            f"Networks: {networks_str}\n"
            f"Languages: {languages_str}\n"
            f"Rating: {p['dentaqual_rating'] or 'N/A'}"
        )

    return "\n\n---\n\n".join(output)


def run_provider_finder_agent(user_query: str):
    """Run the provider finder agent with search tool."""
    agents_client = AgentsClient(
        endpoint=AZURE_AI_PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )

    def search_providers_tool(city: str = "", specialty: str = "", network: str = "", accepting_new: str = "true") -> str:
        """
        Search for dental providers by city, specialty, and network.
        :param city: City name to filter by (e.g. Cadillac, Traverse City). Leave empty for all cities.
        :param specialty: Specialty to filter by (e.g. General Dentist, Orthodontist, Endodontist, Prosthodontist). Leave empty for all.
        :param network: Network to filter by (e.g. Delta Dental PPO, Delta Dental Premier). Leave empty for all.
        :param accepting_new: Filter by accepting new patients. Use 'true' or 'false'. Default 'true'.
        :return: Matching providers as formatted text.
        """
        return search_providers(city, specialty, network, accepting_new)

    functions = FunctionTool(functions=[search_providers_tool])

    with agents_client:
        agents_client.enable_auto_function_calls(functions)

        run = agents_client.create_thread_and_process_run(
            agent_id=PROVIDER_FINDER_AGENT_ID,
            thread=AgentThreadCreationOptions(
                messages=[ThreadMessageOptions(role="user", content=user_query)]
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

    #noted out print so orchestrator does not double output
    # print(f"\nProvider Finder: {response_text}")
        return response_text or "No response generated."


# ── Entry point for standalone testing ────────────────────────────────────────
if __name__ == "__main__":
    print("Delta Dental Provider Finder")
    print("=" * 40)

    query = input("\nSearch for a provider: ").strip()
    run_provider_finder_agent(query)