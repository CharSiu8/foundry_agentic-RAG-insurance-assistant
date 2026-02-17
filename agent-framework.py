from agent_framework import AgentThread, ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential
from pydantic import Field
from typing import Annotated


# 1. Imports
# - agent_framework (AgentThread, ChatAgent)
# - AzureAIAgentClient
# - AzureCliCredential
# - azure-ai-projects (for AI Search tool)
# - dotenv, os

# 2. Load .env
# - AZURE_AI_PROJECT_ENDPOINT
# - AZURE_OPENAI_DEPLOYMENT
# - AZURE_SEARCH_ENDPOINT
# - AZURE_SEARCH_INDEX_NAME

# 3. Define search tool function
# - Takes query + plan_name as parameters
# - Calls Azure AI Search index
# - Returns relevant chunks from plan PDFs

# 4. Create ChatAgent
# - AzureCliCredential
# - AzureAIAgentClient
# - Agent name: "coverage_agent"
# - Instructions: answer dental coverage questions using search results only
# - Tools: search tool function

# 5. Run agent
# - Take user query input
# - Pass to agent
# - Print response