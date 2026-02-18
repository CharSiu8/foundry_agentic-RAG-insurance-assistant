from asyncio import run
import os
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from typing import Annotated
from pydantic import Field

# Load environment variables
load_dotenv()

AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_EMBEDDING_DEPLOYMENT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
INDEX_NAME = "dental-plans"

# Azure OpenAI client 
openai_client = AzureOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-10-21"
)

# Tool: Search dental plan documents
def search_dental_plan(
    query: Annotated[str, Field(description="The user's dental coverage question")],
    plan_filter: Annotated[str, Field(description="The plan PDF to filter by e.g. baseplan.pdf, premiumplan.pdf, stateplan.pdf, plancompare.pdf, BasicFAQ.txt. Use None to search all plans.")]
) -> str:
    """Search the dental plan documents for relevant coverage information."""
    try:
        # Generate embedding for query
        response = openai_client.embeddings.create(
            input=query,
            model=AZURE_EMBEDDING_DEPLOYMENT
        )
        query_vector = response.data[0].embedding

        # Build vector query
        vector_query = VectorizedQuery(
            vector=query_vector,
            fields="embedding"
        )

        # Connect to AI Search
        search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            index_name=INDEX_NAME,
            credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
        )

        # Apply source filter if plan specified
        filter_expr = f"source eq '{plan_filter}'" if plan_filter and plan_filter != "None" else None

        results = search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=filter_expr,
            top=3,
            select=["text", "source"]
        )

        chunks = [doc["text"] for doc in results]
        if not chunks:
            return "No relevant information found in the selected plan."

        return "\n\n---\n\n".join(chunks)

    except Exception as e:
        return f"Search error: {e}"

# Main agent function 
def run_coverage_agent(user_query: str, plan_filter: str = None):
    from azure.ai.agents import AgentsClient
    from azure.ai.agents.models import FunctionTool, MessageTextContent
    from azure.identity import DefaultAzureCredential

    agent_id = os.getenv("COVERAGE_AGENT_ID")

    def search_dental_plan_tool(query: str) -> str:
        """
        Search dental plan documents for coverage information.
        :param query: The user's dental coverage question.
        :return: Relevant plan text chunks.
        """
        return search_dental_plan(query, plan_filter or "None")

    functions = FunctionTool(functions=[search_dental_plan_tool])

    agents_client = AgentsClient(
        endpoint=AZURE_AI_PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )

    with agents_client:
        agents_client.enable_auto_function_calls(functions)

        from azure.ai.agents.models import AgentThreadCreationOptions, ThreadMessageOptions
        from azure.ai.agents.models import FunctionTool, MessageTextContent, MessageRole
        run = agents_client.create_thread_and_process_run(
            agent_id=agent_id,
            thread=AgentThreadCreationOptions(
                messages=[ThreadMessageOptions(role="user", content=user_query)]
            )
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

        print(f"\nCoverage Agent: {response_text}")
        return response_text or "No response generated."

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Delta Dental Coverage Agent")
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
    print(f"\nSelected: {plan_name}")

    query = input("\nAsk a question: ").strip()
    run_coverage_agent(query, plan_filter)