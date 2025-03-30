import os
from langchain_google_vertexai import VertexAIEmbeddings, ChatVertexAI
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
# from langchain.document_loaders import BigQueryLoader
from langchain_google_community.document_loaders import BigQueryLoader

# Set your Google Cloud Project ID and location
PROJECT_ID = "roi-genai-joey"  # Replace with your actual project ID
LOCATION = "us-central1"  # Or your preferred Vertex AI location

# Set the BigQuery table details
TABLE_ID = "northwind.orders"

import os
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    del os.environ['GOOGLE_APPLICATION_CREDENTIALS']


# Initialize Vertex AI Embeddings and Chat model
embeddings = VertexAIEmbeddings("text-embedding-004")
llm = ChatVertexAI(model_name="gemini-pro", project=PROJECT_ID, location=LOCATION)

# Define the columns to load from BigQuery
QUERY = f"""
SELECT
    CAST(order_id as STRING) || ' - Customer: ' || customer_id || ' - Shipped to: ' || ship_name || ', ' || ship_city || ', ' || ship_country AS text,
    order_id AS id
FROM
    `joey-gagliardo.{TABLE_ID}`
"""

# Initialize the BigQueryLoader
loader = BigQueryLoader(
    query=QUERY,
    project=PROJECT_ID,
    page_content_columns=["text"],
    metadata_columns=["id"],
)

# Load data from BigQuery
documents = loader.load()

# Create a Chroma vector store
persist_directory = "chroma_db_orders_gemini"
vectordb = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory=persist_directory
)
vectordb.persist()

# Initialize the RetrievalQA chain with Gemini
qa = RetrievalQA.from_llm(
    llm=llm,
    retriever=vectordb.as_retriever(search_kwargs={"k": 3}),
    return_source_documents=True,
)

# Define your prompt
prompt = "Tell me about orders shipped to London."

# Run the query
result = qa({"query": prompt})

# Print the answer and source documents
print("Question:", prompt)
print("Answer:", result["result"])
print("\nSource Documents:")
for doc in result["source_documents"]:
    print(doc.page_content)
    print(doc.metadata)
    print("-" * 40)
