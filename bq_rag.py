import os
from langchain_google_vertexai import VertexAIEmbeddings, ChatVertexAI, VertexAI
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
# from langchain.document_loaders import BigQueryLoader
# from langchain_google_community.document_loaders import BigQueryLoader
#from langchain_community.document_loaders import BigQueryLoader
from langchain_community.document_loaders import BigQueryLoader
from google.cloud import bigquery

# Set your Google Cloud Project ID and location
PROJECT_ID = "roi-genai-joey"  # Replace with your actual project ID
BIGQUERY_PROJECT_ID = "joey-gagliardo"  # Replace with your actual project ID
DATASET_ID = "northwind"
LOCATION = "us-central1"  # Or your preferred Vertex AI location

# # Set the BigQuery table details
# TABLE_ID = "northwind.orders"

import os
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    del os.environ['GOOGLE_APPLICATION_CREDENTIALS']


# Initialize Vertex AI Embeddings and Chat model
embeddings = VertexAIEmbeddings("text-embedding-004")
# llm = ChatVertexAI(model_name="gemini-pro", project=PROJECT_ID, location=LOCATION)
llm = VertexAI(model_name="gemini-pro", project=PROJECT_ID, location=LOCATION)
bq = bigquery.Client(project=BIGQUERY_PROJECT_ID)


# def get_comment_by_id(id: str) -> str:
#     QUERY = "SELECT text FROM bigquery-public-data.hacker_news.full WHERE ID = {id} LIMIT 1".format(
#         id=id
#     )
#     df = bq.query(QUERY).to_dataframe()

#     return df

# # Define the columns to load from BigQuery
# QUERY = f"""
# SELECT
#     CAST(order_id as STRING) || ' - Customer: ' || customer_id || ' - Shipped to: ' || ship_name || ', ' || ship_city || ', ' || ship_country AS text,
#     order_id AS id
# FROM
#     `joey-gagliardo.{TABLE_ID}`
# """

# # Initialize the BigQueryLoader
# loader = BigQueryLoader(
#     query=QUERY,
#     project=PROJECT_ID,
#     page_content_columns=["text"],
#     metadata_columns=["id"],
# )

# # Load data from BigQuery
# documents = loader.load()

tables_config = [
    {
        "table_id": f"{DATASET_ID}.products",
        "query": f"""
            SELECT
                product_name AS text,
                CAST(product_id AS STRING) AS id,
                category_id,
                quantity_per_unit,
                supplier_id
            FROM
                `{BIGQUERY_PROJECT_ID}.{DATASET_ID}.products`
        """,
        "page_content_columns": ["text", "quantity_per_unit"],
        "metadata_columns": ["id", "category_id", "supplier_id"],
    },
    # {
    #     "table_id": f"{DATASET_ID}.categories",
    #     "query": f"""
    #         SELECT
    #             category_name AS text,
    #             CAST(category_id AS STRING) AS id,
    #             description
    #         FROM
    #             `{BIGQUERY_PROJECT_ID}.{DATASET_ID}.categories`
    #     """,
    #     "page_content_columns": ["text", "description"],
    #     "metadata_columns": ["id"],
    # },
    # {
    #     "table_id": f"{DATASET_ID}.orders",
    #     "query": f"""
    #         SELECT
    #             CAST(order_id AS STRING) || ' - Customer: ' || customer_id || ' - Shipped to: ' || ship_name || ', ' || ship_city || ', ' || ship_country AS text,
    #             CAST(order_id AS STRING) AS id,
    #             customer_id,
    #             CAST(order_date AS STRING) AS order_date
    #         FROM
    #             `{BIGQUERY_PROJECT_ID}.{DATASET_ID}.orders`
    #     """,
    #     "page_content_columns": ["text"],
    #     "metadata_columns": ["id", "customer_id", "order_date"],
    # },
    # {
    #     "table_id": f"{DATASET_ID}.customers",
    #     "query": f"""
    #         SELECT
    #             company_name AS text,
    #             customer_id AS id,
    #             contact_name,
    #             city,
    #             country
    #         FROM
    #             `{BIGQUERY_PROJECT_ID}.{DATASET_ID}.customers`
    #     """,
    #     "page_content_columns": ["text", "contact_name", "city", "country"],
    #     "metadata_columns": ["id"],
    # },
    # Add more tables here with their respective queries and configurations
]

all_documents = []

# Load data from each table
for config in tables_config:
    print(f"Loading data from {config['table_id']}...")
    loader = BigQueryLoader(
        query=config["query"],
        project=BIGQUERY_PROJECT_ID,
        page_content_columns=config["page_content_columns"],
        metadata_columns=config["metadata_columns"],
    )
    documents = loader.load()
    all_documents.extend(documents)
    print(f"Loaded {len(documents)} documents from {config['table_id']}.")

print(f"Total documents loaded: {len(all_documents)}")

# Create a Chroma vector store
# persist_directory = "chroma_db_orders_gemini"
vectordb = Chroma.from_documents(
    documents=all_documents,
    embedding=embeddings,
    # persist_directory=persist_directory
)
# vectordb.persist()

# Initialize the RetrievalQA chain with Gemini
qa = RetrievalQA.from_llm(
    llm=llm,
    retriever=vectordb.as_retriever(search_kwargs={"k": 10}),
    return_source_documents=True,
)

# # Define your prompt
# prompt = "Tell me about orders shipped to London."

# # Run the query
# result = qa.invoke({"query": prompt})

# # Print the answer and source documents
# print("Question:", prompt)
# print("Answer:", result["result"])
# print("\nSource Documents:")
# for doc in result["source_documents"]:
#     print(doc.page_content)
#     print(doc.metadata)
#     print("-" * 40)
####
prompt = "Tell me about products that are packaged in metric units or grams, kilograms, liters or milliliters, but not pounds or ounces oz or gallons based on the products table quantity_per_unit field."

# Run the query
result = qa.invoke({"query": prompt})

# Print the answer and source documents
print("Question:", prompt)
print("Answer:", result["result"])
print("\nSource Documents:")
for doc in result["source_documents"]:
    print(doc.page_content)
    print(doc.metadata)
    print("-" * 40)
