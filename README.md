# 🦷 Delta Dental AI Assistant (Unofficial)

An AI-powered multi-agent dental insurance assistant built on **Azure AI Foundry**. Ask questions about coverage, find providers, and estimate out-of-pocket costs — all in one conversation.

> **Disclaimer:** This is an independent portfolio project. It is not affiliated with, endorsed by, or official software of Delta Dental. Intended for demonstration purposes only.

**Live Demo:** https://delta-dental-app.whitemushroom-7c468829.canadaeast.azurecontainerapps.io/

---

## Features

- **Coverage Q&A** — Ask about plan benefits, percentages, deductibles, and annual maximums
- **Provider Search** — Find Delta Dental PPO and Premier dentists by city and specialty
- **Cost Estimation** — Get out-of-pocket estimates for both PPO and Premier dentists with math shown
- **Multi-Intent Queries** — Combine coverage, provider, and cost questions in a single message (e.g., *"Find me a dentist in Grand Rapids for a cleaning and tell me what my plan covers"*)
- **Multi-Plan Support** — Base Plan, Premium Plan, State Plan, Plan Comparison, and FAQ
- **Parallel Agent Execution** — Coverage and Provider agents run simultaneously for faster responses

---

## Architecture

```
User → Streamlit UI → Orchestrator → Router Agent (intent classification)
                                   ├→ Coverage Agent (RAG + Azure AI Search)
                                   ├→ Provider Finder Agent (JSON provider database)
                                   └→ Cost Estimator Agent (procedure cost database)
```
## Orchestration

hybrid orchestration pattern: router-based orchestration with concurrent execution and sequential chaining.

### Foundry Agents

| Agent | Role | Tools |
|-------|------|-------|
| **Router** | Classifies user intent (coverage, provider_search, cost_estimate) | LLM classification |
| **Coverage** | Answers plan benefit questions using RAG | `search_dental_plan_tool` → Azure AI Search |
| **Provider Finder** | Searches provider database by city, specialty, network | `search_providers` → Azure Blob Storage |
| **Cost Estimator** | Calculates out-of-pocket costs with coverage percentages | `get_procedure_cost` → procedure cost data |
| **Orchestrator** | Routes queries, chains agents, runs parallel execution | Coordinates all agents |

### Cost Estimation Chain

For cost queries, the orchestrator chains agents sequentially:

1. **Coverage Agent** extracts PPO and Premier coverage percentages
2. **Cost Estimator** calculates out-of-pocket costs using: `procedure cost × (1 - coverage%)`
3. If PPO and Premier rates differ, both estimates are shown

---

## Tech Stack

- **Frontend:** Streamlit (dark theme)
- **Agents:** Azure AI Foundry (GPT-4o)
- **RAG:** Azure AI Search (hybrid search with vector embeddings)
- **Embeddings:** Azure OpenAI `text-embedding-ada-002`
- **Provider Data:** Azure Blob Storage (JSON)
- **Deployment:** Azure Container Apps
- **Container Registry:** Azure Container Registry
- **Auth:** Azure Service Principal

---

## Data Sources

### Plan Documents
Five Delta Dental of Michigan plan documents indexed via RAG into Azure AI Search (1500-char chunks, 200-char overlap):

- **Base Plan** — MSU Base Plan (Group #11496), 50% coverage across all services
- **Premium Plan** — MSU Premium Plan (Group #11496), 100% preventive / 70% basic / 50% major
- **State Plan** — State of Michigan Dental Plan (Group #8700), varies by service and network
- **Plan Comparison** — Delta Dental PPO vs DeltaCare USA comparison
- **FAQ** — Common Delta Dental member questions

### Provider Data
Provider data was sourced from Delta Dental's public provider directory (https://www.deltadentalmi.com/Member/Using-Your-Benefits/Find-a-Dentist). The available PDFs were downloaded, converted to JSON, and uploaded to Azure Blob Storage.

**160+ providers** across **11 Michigan cities:**

- Ann Arbor
- Lansing
- East Grand Rapids
- Grand Rapids
- Cadillac
- Interlochen
- Kingsley
- Lake City
- Mesick
- Traverse City
- Wyoming

**6 specialties covered:** General Dentist, Endodontist, Oral Surgeon, Orthodontist, Pediatric Dentist, Prosthodontist

### Procedure Cost Data
Cost data for **53 dental procedures** was manually gathered from Delta Dental's public cost estimator tool (https://www.deltadental.com/member/cost-estimator/) using the 45901 zip code, then converted to JSON.

---

## Project Structure

```
├── streamlit_app.py              # Streamlit UI
├── orchestrator.py               # Multi-agent orchestrator with parallel execution
├── router_agent.py               # Intent classification agent
├── coverage_agent.py             # Plan coverage RAG agent
├── provider_finder_agent.py      # Provider search agent
├── cost_estimator_agent.py       # Cost estimation agent
├── router_agent_config.json      # Router agent configuration
├── ingest.py                     # PDF ingestion → Azure AI Search
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container image definition
├── .dockerignore                 # Docker build exclusions
└── .streamlit/config.toml        # Streamlit dark theme config
```

---

## Local Setup

1. Clone the repo
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Create `.env` file with:

```
AZURE_AI_PROJECT_ENDPOINT=your-endpoint
AZURE_OPENAI_ENDPOINT=your-openai-endpoint
AZURE_OPENAI_DEPLOYMENT=your-deployment
AZURE_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
OPENAI_API_KEY=your-key
AZURE_SEARCH_ENDPOINT=your-search-endpoint
AZURE_SEARCH_API_KEY=your-search-key
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
COVERAGE_AGENT_ID=your-agent-id
PROVIDER_FINDER_AGENT_ID=your-agent-id
COST_ESTIMATOR_AGENT_ID=your-agent-id
ROUTER_AGENT_ID=your-agent-id
```

6. Ingest plan documents: `python ingest.py`
7. Run locally: `streamlit run streamlit_app.py`

---

## Deployment (Azure Container Apps)

1. Build Docker image: `docker build -t delta-dental-assistant .`
2. Test locally: `docker run -p 8501:8501 --env-file .env delta-dental-assistant`
3. Create Azure Container Registry: `az acr create --resource-group <RG> --name <NAME> --sku Basic`
4. Push image: `docker tag` → `docker push` to ACR
5. Create Container App: `az containerapp create` with environment variables
6. Set env vars: `az containerapp update --set-env-vars`

---

## Example Queries

- *"What is my coverage for a cleaning?"*
- *"Find me an orthodontist in Grand Rapids"*
- *"How much will a root canal cost me?"*
- *"Find me a dentist in Cadillac for a cleaning and tell me what my plan covers"*
- *"How much coverage do I have for wisdom tooth removal and how much will it cost?"*
- *"Find me a Spanish-speaking dentist in Grand Rapids"*

---

## License

All Rights Reserved. Recruiters and employers permitted to copy and test.
