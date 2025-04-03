from langchain_google_vertexai import VertexAI
from langchain.tools import StructuredTool
from langchain.llms import VertexAI as LangchainVertexAI  # Explicitly import as LangchainVertexAI
# from langchain_google_bigquery import BigQueryLoader
from langchain_google_community import BigQueryLoader
from pydantic import BaseModel, Field
from typing import Optional, List
from langchain.agents import AgentType, initialize_agent, load_tools
from langchain.tools import StructuredTool

# --- Configuration ---
PROJECT_ID = "roi-genai-joey"  # Replace with your GCP Project ID
BIGQUERY_DATASET = "northwind"  # Replace with your Northwind dataset name
BIGQUERY_PROJECT_ID = "joey-gagliardo"  # Replace with your GCP Project ID

# --- Define Pydantic Schema for Tool Input ---
class OrderStatusInput(BaseModel):
    customer_id: str = Field(..., description="The ID of the customer to look up.")

# --- Define Pydantic Schema for Tool Output ---
class OrderStatusOutput(BaseModel):
    customer_id: str = Field(..., description="The ID of the customer.")
    order_id: Optional[int] = Field(None, description="The ID of the last order.")
    order_date: Optional[str] = Field(None, description="The date of the last order (YYYY-MM-DD).")
    ship_status: Optional[str] = Field(None, description="The shipping status of the last order.")

def parse_bq_return(input):
    """
    Parses a string containing order information into a dictionary.

    Args:
        input: A string with key-value pairs separated by colons and newlines.
                      Example: "order_id: 11011\ncustomer_id: ALFKI\norder_date: 1998-04-09 00:00:00\nshipped_date: 1998-04-13 00:00:00"

    Returns:
        A dictionary where keys are the order information fields and values are their corresponding data.
    """
    output = {}
    lines = input.strip().split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            output[key.strip()] = value.strip()
    return output

# --- Define the Tool Function ---
def lookup_last_order_status(customer_id: str) -> OrderStatusOutput:
    """
    Looks up the status of the last order for a given customer ID using the Northwind database.
    """
    query = f"""
                SELECT order_id, customer_id, order_date, shipped_date
                FROM `{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET}.orders`
                WHERE customer_id = '{customer_id}'
                ORDER BY order_date DESC
                LIMIT 1
            """
    print(query)
    try:
        loader = BigQueryLoader(
            query=query,
            project=BIGQUERY_PROJECT_ID,
        )        
        data = loader.load()

        if data:
            last_order = data[0].page_content
            last_order = parse_bq_return(last_order)
            order_date = last_order.get("order_date")
            shipped_date = last_order.get("shipped_date")
            ship_status = "Shipped" if shipped_date else "Processing"

            ret = OrderStatusOutput(
                customer_id=customer_id,
                order_id=last_order.get("order_id"),
                order_date=order_date,
                ship_status=ship_status,
            )
            return ret
        else:
            ret = OrderStatusOutput(
                customer_id=customer_id,
                order_id=None,
                order_date=None,
                ship_status="No orders found for this customer."
            )
            return ret

    except Exception as e:
        return OrderStatusOutput(
            customer_id=customer_id,
            order_id=None,
            order_date=None,
            ship_status=f"Error looking up order status: {e}"
        )

# --- Create the Langchain Tool ---
lookup_order_status_tool = StructuredTool.from_function(
    func=lookup_last_order_status,
    name="lookup_last_order_status",
    description="""
    Use this tool to find the status of the most recent order for a given customer ID.
    Provide the customer ID as input.
    Returns the last order ID, order date, and shipping status.
    """,
    args_schema=OrderStatusInput,
    return_direct=False,
)

if __name__ == '__main__':
    # --- Initialize Gemini LLM ---
    llm = VertexAI(model_name="gemini-pro", project=PROJECT_ID, location="us-central1")

    # --- Define the tools ---
    tools = [lookup_order_status_tool]

    # --- Initialize the Agent ---
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )

    # --- Example Usage ---
    customer_id_to_lookup = "ALFKI"
    query = f"What is the status of the last order for customer {customer_id_to_lookup}?"
    response = agent.run(query)
    print(f"\nResponse for customer {customer_id_to_lookup}: {response}")

    # customer_id_no_orders = "NONEXIST"
    # query_no_orders = f"What is the status of the last order for customer {customer_id_no_orders}?"
    # response_no_orders = agent.run(query_no_orders)
    # print(f"\nResponse for customer {customer_id_no_orders}: {response_no_orders}")

