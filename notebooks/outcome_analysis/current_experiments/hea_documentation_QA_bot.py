import os
import lancedb
from lancedb.schema import vector
from sentence_transformers import SentenceTransformer
import ssl
import certifi
import httpx
import openai
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

LANCEDB_PATH = "data/hea_lancedb"
TABLE_NAME = "hea"

def initialize_azure_client(division="ts", region="eastus2", api_version="2024-10-21"):
    openai_endpoints = {
            'ts': {
                'eastus':'https://air-ts-eastus.openai.azure.com/',
                'eastus2':'https://air-ts-eastus2.openai.azure.com/',
                'northcentralus':'https://air-poc-northcentralus.openai.azure.com/',
            },
            'ps': {
                'eastus':'https://air-ps-eastus.openai.azure.com/',
                'eastus2':'https://air-ps-eastus2.openai.azure.com/',
                'northcentralus':'https://air-poc-northcentralus.openai.azure.com/'
            },
        }
    openai_endpoint = openai_endpoints[division][region]
    token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    ctx = ssl.create_default_context(cafile=os.environ.get('REQUESTS_CA_BUNDLE', certifi.where()))
    httpx_client = httpx.Client(verify=ctx)
    openai_client = openai.AzureOpenAI(
        api_version=api_version,
        azure_endpoint=openai_endpoint,
        azure_ad_token_provider=token_provider,
        http_client=httpx_client
    )
    return openai_client

# --- RAG Components ---

class QnAPipeline:
    def __init__(self):
        # Initialize the embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Connect to LanceDB and the document chunks table
        try:
            db = lancedb.connect(LANCEDB_PATH)
            self.table = db.open_table(TABLE_NAME)
        except Exception as e:
            raise FileNotFoundError(f"LanceDB table not found at {LANCEDB_PATH}/{TABLE_NAME}. Please run the ingestion script first. Error: {e}")

        self.client = initialize_azure_client()

    def search_knowledge_base(self, query: str, top_k: int = 5):
        """
        Embeds a query and searches the LanceDB table for the most relevant chunks.
        """
        # Embed the user's query
        query_vector = self.embedding_model.encode(query).tolist()
        
        # Search the LanceDB table using the vector
        # .to_list() retrieves the search results as a Python list of dictionaries
        search_results = (
            self.table
            .search(query_vector)
            .limit(top_k)
            .to_list()
        )
        
        return search_results

    def generate_response(self, user_question: str, context: list):
        """
        Constructs a prompt with retrieved context and generates a response using Azure OpenAI.
        """
        # Format the context for the LLM
        context_str = "\n".join([f"Source: {c['source_uri']}\nContent: {c['text']}" for c in context])

        # Define the system message to guide the LLM's behavior
        system_message = (
            "You are a helpful assistant that answers questions based on the provided context. "
            "Only use the information from the documents provided. "
            "If the answer is not in the context, say 'I cannot answer this question based on the provided documents.' "
            "Please cite the source document(s) for your answer."
        )

        # Send the prompt to the Azure OpenAI client
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Context: {context_str}\n\nQuestion: {user_question}"}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content

    def run_qa_loop(self):
        """
        Runs the interactive Q&A loop.
        """
        print("Welcome to the LIAS Q&A System! Type 'quit' to exit.")
        while True:
            user_question = input("\nAsk a question: ")
            if user_question.lower() == 'quit':
                break
            
            try:
                # 1. Retrieve relevant chunks
                relevant_chunks = self.search_knowledge_base(user_question)
                
                if not relevant_chunks:
                    print("I couldn't find any relevant information for that question.")
                    continue
                
                # 2. Generate a response with the retrieved context
                answer = self.generate_response(user_question, relevant_chunks)
                
                # 3. Print the final answer
                print(f"\nAI Answer: {answer}")
                
            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    try:
        qa_system = QnAPipeline()
        qa_system.run_qa_loop()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run your document ingestion script first to create the LanceDB table.")
    except Exception as e:
        print(f"An unexpected error occurred during setup: {e}")