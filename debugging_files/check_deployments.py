# check_deployments.py
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
import os

load_dotenv()

client = AIProjectClient(
    endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
    credential=DefaultAzureCredential(),
)

for d in client.deployments.list():
    print(f"Name: {d.name}, Model: {d.model_name}, Connection: {d.connection_name}")