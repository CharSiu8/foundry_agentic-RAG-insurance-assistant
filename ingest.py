import os
from azure.storage.blob import BlobServiceClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchFieldDataType,
    SearchableField, VectorSearch, HnswAlgorithmConfiguration,
    VectorSearchProfile, SearchField
)
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from pypdf import PdfReader
from dotenv import load_dotenv
import io
import uuid

load_dotenv()
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CONTAINER_NAME = "dentalplanpdfs"
INDEX_NAME = "dental-plans"
CHUNK_SIZE = 500

# Connect to Azure OpenAI for embeddings
openai_client = AzureOpenAI(
    api_key=OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version="2024-11-20"
)
embedding_client = AzureOpenAI(
    api_key=os.getenv("AZURE_EMBEDDING_KEY"),
    azure_endpoint=os.getenv("AZURE_EMBEDDING_ENDPOINT"),
    api_version="2024-10-21"
)
# Connect to Blob Storage
def download_blobs():
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    container = blob_service_client.get_container_client(CONTAINER_NAME)
    files = {}
    for blob in container.list_blobs():
        data = container.download_blob(blob.name).readall()
        files[blob.name] = data
    return files

# Parse files 
def parse_file(filename, data):
    if filename.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    elif filename.endswith(".txt"):
        return data.decode("utf-8")
    else:
        return ""
    
# Chunk text
def chunk_text(text, chunk_size=500, overlap=50):
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", "?", "!", " ", ""]
    )
    return splitter.split_text(text)

# Embeddings 
def get_embedding(text):
    response = embedding_client.embeddings.create(
        input=text,
        model=os.getenv("AZURE_EMBEDDING_DEPLOYMENT")
    )
    return response.data[0].embedding

# create Azure Search index
def create_index():
    credential = AzureKeyCredential(AZURE_SEARCH_API_KEY)
    index_client = SearchIndexClient(endpoint=AZURE_SEARCH_ENDPOINT, credential=credential)

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="text", type=SearchFieldDataType.String),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="dental-vector-profile"
        )
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="dental-hnsw")],
        profiles=[VectorSearchProfile(name="dental-vector-profile", algorithm_configuration_name="dental-hnsw")]
    )

    index = SearchIndex(name=INDEX_NAME, fields=fields, vector_search=vector_search)
    try:
        index_client.delete_index(INDEX_NAME)
        print(f"Deleted existing index.")
    except:
        pass
    index_client.create_or_update_index(index)
    print(f"Index '{INDEX_NAME}' created/updated.")

# Upload chunks to AI Search
def upload_chunks(filename, chunks):
    credential = AzureKeyCredential(AZURE_SEARCH_API_KEY)
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=credential
    )

    documents = []
    for chunk in chunks:
        embedding = get_embedding(chunk)
        documents.append({
            "id": str(uuid.uuid4()),
            "text": chunk,
            "source": filename,
            "embedding": embedding
        })

    search_client.upload_documents(documents=documents)
    print(f"Uploaded {len(documents)} chunks from {filename}")

# ── Main ──────────────────────────────────────────
if __name__ == "__main__":
    print("Creating index...")
    create_index()

    print("Downloading files from Blob Storage...")
    files = download_blobs()

    for filename, data in files.items():
        print(f"Processing: {filename}")
        text = parse_file(filename, data)
        if not text:
            continue
        chunks = chunk_text(text)
        print(f"  {len(chunks)} chunks generated")
        upload_chunks(filename, chunks)

    print("\nIngestion complete!")