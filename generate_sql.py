import os
from langchain_google_vertexai import VertexAI
from langchain.sql_database import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from google.cloud import bigquery
from sqlalchemy import create_engine

# Set your Google Cloud Project ID and Dataset ID
PROJECT_ID = "roi-genai-joey"  # Replace with your Google Cloud Project ID
BIGQUERY_PROJECT_ID = "joey-gagliardo"
DATASET_ID = "northwind"  # Replace with your BigQuery dataset ID

# Initialize the LLM (using Vertex AI Gemini Pro as an example)
# Ensure you have Vertex AI API enabled and appropriate permissions.
# You might need to set GOOGLE_APPLICATION_CREDENTIALS environment variable
# if running outside of a Google Cloud environment with default credentials.
llm = VertexAI(model_name="gemini-pro", project=PROJECT_ID, location="us-central1")

# Authenticate BigQuery client (ensure you have necessary permissions)
client = bigquery.Client(project=PROJECT_ID)
def query_and_results(input: str):
    prompt = f"""Given an input like the following Natural Language Query: Using the products table list show how many products are in each category. Show the category name and count.
Generated SQL Query (for 'customers' table): ## Question: How many products are in each category?

## SQLQuery: 
```sql
SELECT 
    c.category_name, 
    COUNT(*) AS total_products
FROM 
    categories c
JOIN 
    products p ON c.category_id = p.category_id
GROUP BY 
    c.category_name
ORDER BY 
    total_products DESC
LIMIT 5
```

## SQLResult:
| category_name          | total_products |
|--------------------------|------------------|
| Condiments              | 112             |
| Confections             | 107             |
| Beverages               | 87              |
| Produce                 | 77              |
| Dairy Products           | 43              |

## Answer: The category with the most products is Condiments with 112 products. The category with the least products is Dairy Products with 43 products.

Generate an output in JSON format with keys of Natural_Language, SQL, Result, Answer.

{input}
"""
    return llm.invoke(prompt)

def get_table_names(dataset_id: str, project_id: str = PROJECT_ID): 
    """Lists all table names in a given BigQuery dataset."""
    tables = client.list_tables(project_id + '.' + dataset_id)
    return [table.table_id for table in tables]

# Construct the Database URI for BigQuery
bq_uri = f"bigquery://{BIGQUERY_PROJECT_ID}/{DATASET_ID}"
db = SQLDatabase.from_uri(bq_uri)

# Create the SQL Database Chain
db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True)  # verbose=True for debugging

def generate_sql(natural_language_query: str, table_names: list = None):
    """
    Generates a SQL query for BigQuery based on a natural language request
    and the provided table names (optional).
    """
    if table_names:
        table_info = db.get_table_info(table_names=table_names)
    else:
        table_info = db.get_table_info()

    prompt = db_chain.llm_chain.prompt.format_prompt(
        input=natural_language_query,
        dialect="bigquery",
        table_info=table_info
        ,top_k=5  # Add the top_k parameter with a default value
    )
    sql_query = llm(prompt.to_string())
    ret = query_and_results(sql_query)
    print(ret)
    # return sql_query.split('\nSQLQuery:')[-1].strip()

if __name__ == "__main__":
    available_tables = get_table_names(DATASET_ID, BIGQUERY_PROJECT_ID)
    print("Available tables:", available_tables)

    # Example 1: Get all table names
    natural_language_query_1 = "What are the names of all the tables in the dataset?"
    print(f"\nNatural Language Query: {natural_language_query_1}")
    sql_query_1 = generate_sql(natural_language_query_1)
    print("Generated SQL Query:", sql_query_1)

    # Example 2: Query a specific table (assuming a table named 'products' exists)
    if "products" in available_tables:
        natural_language_query_2 = "Using the products table list show how many products are in each category. Show the category name and count."
        print(f"\nNatural Language Query: {natural_language_query_2}")
        sql_query_2 = generate_sql(natural_language_query_2, table_names=None)
        print("Generated SQL Query (for 'customers' table):", sql_query_2)
    else:
        print("\n'customers' table not found in the dataset, skipping example 2.")

    