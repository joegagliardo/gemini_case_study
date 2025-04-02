from langchain_google_vertexai import VertexAI
from langchain.agents import AgentType, initialize_agent, load_tools
from langchain.tools import StructuredTool
import os
from datetime import datetime
import requests
import json
from typing import Dict
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# --- Configuration ---
PROJECT_ID = "roi-genai-joey"  # Replace with your GCP Project ID
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/your/credentials.json"  # Replace with your credentials path

# --- Define Tools ---
def get_current_date():
    """
    Gets the current date (today), in the format YYYY-MM-DD
    """
    todays_date = datetime.today().strftime("%Y-%m-%d")
    return todays_date

def get_euro_to_dollar_exchange_rate():
    """
    Fetches the current Euro to US Dollar exchange rate using an online API.
    """
    try:
        api_url = "https://api.exchangerate-api.com/v4/latest/EUR"
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        if "rates" in data and "USD" in data["rates"]:
            exchange_rate = data["rates"]["USD"]
            # return f"The current EUR to USD exchange rate is: {exchange_rate}"
            return f"""{"EUR":1, "USD":{exchange_rate}}"""
        else:
            return "Could not retrieve the EUR to USD exchange rate from the API."
    except requests.exceptions.RequestException as e:
        return f"Error fetching exchange rate: {e}"
    except json.JSONDecodeError:
        return "Error decoding JSON response from the exchange rate API."

def how_many_dollars_equals_one_euro():
    """
    Fetches the current Euro to US Dollar exchange rate using an online API.
    """
    try:
        api_url = "https://api.exchangerate-api.com/v4/latest/EUR"
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        if "rates" in data and "USD" in data["rates"]:
            exchange_rate = data["rates"]["USD"]
            # return f"The current EUR to USD exchange rate is: {exchange_rate}"
            return exchange_rate
        else:
            return "Could not retrieve the EUR to USD exchange rate from the API."
    except requests.exceptions.RequestException as e:
        return f"Error fetching exchange rate: {e}"

t_get_current_date = StructuredTool.from_function(
    get_current_date,
    name="get_current_date",
    description="Use this tool to retrieve the current date. The output will be in YYYY-MM-DD format.",
)

t_get_euro_to_dollar_rate = StructuredTool.from_function(
    get_euro_to_dollar_exchange_rate,
    name="get_euro_to_dollar_exchange_rate",
    description="Use this tool to get the current exchange rate between the Euro (EUR) and the US Dollar (USD).",
)

class Eur_Usd(BaseModel):
    eur: float = Field(description="How many Euros")
    usd: float = Field(description="How many dollars")
    date: str = Field(description="Current date")

# Initialize the LLM
llm = VertexAI(model_name="gemini-pro", project=PROJECT_ID, location="us-central1")
output_parser = PydanticOutputParser(pydantic_object=Eur_Usd)

# Define the tools
tools = [
    t_get_current_date,
    t_get_euro_to_dollar_rate,
]

# Initialize the agent with the tools
# agent = initialize_agent(
#     tools,
#     llm,
#     agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
#     verbose=True,
# )

# agent_kwargs = {
#     "output_parser": output_parser,
#     "return_intermediate_steps": True,
# }

# Initialize the agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    # agent_kwargs=agent_kwargs,
)

# --- Run the Agent ---
query = "What is the current exchange rate of Euro to US Dollar? Also, what is today's date?"
query = "What is the current exchange rate of Euro to US Dollar? Also, what is today's date? Return only the rate and date as JSON with keys of EUR, USD and DATE"
response = agent.run(query)
print(response)
print(type(response))

# query_rate_only = "What is the current Euro to Dollar exchange rate?"
# response_rate_only = agent.run(query_rate_only)
# print(response_rate_only)
