from langchain.tools import StructuredTool
import requests
import json
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
import pytz

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

class ExchangeRate(BaseModel):
    """Schema for the exchange rate between two currencies."""
    from_currency: str = Field(..., description="The source currency code (e.g., USD)")
    to_currency: str = Field(..., description="The target currency code (e.g., EUR)")
    rate: float = Field(..., description="The exchange rate (how many units of target currency equal one unit of source currency)")
    date: Optional[str] = Field(None, description="The date of the exchange rate (YYYY-MM-DD)")

def get_current_date():
    """
    Gets the current date (today), in the format YYYY-MM-DD
    """
    todays_date = datetime.today().strftime("%Y-%m-%d")
    return todays_date

t_get_current_date = StructuredTool.from_function(
    get_current_date,
    name="get_current_date",
    description="Use this tool to retrieve the current date. The output will be in YYYY-MM-DD format.",
)

def get_exchange_rate(from_currency: str, to_currency: str, date: Optional[str] = None) -> ExchangeRate:
    """
    Fetches the exchange rate between two currencies using an online API.

    Args:
        from_currency (str): The source currency code (e.g., USD).
        to_currency (str): The target currency code (e.g., EUR).
        date (Optional[str]): The specific date for the exchange rate (YYYY-MM-DD).
                                If None, returns the latest available rate.

    Returns:
        ExchangeRate: An object containing the exchange rate information.
    """
    # base_url = "https://api.exchangerate-api.com/v4/latest"
    base_url = "https://api.frankfurter.dev/v1"

    # https://api.frankfurter.dev/v1/latest?symbols=USD,%20EUR
    # https://api.frankfurter.dev/v1/1999-01-04?base=USD&symbols=EUR

    if date:
        api_url = f"{base_url}/{date}?base={from_currency}&symbols={to_currency}"
    else:
        api_url = f"{base_url}/latest?symbols={from_currency},{to_currency}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        if "rates" in data and to_currency in data["rates"]:
            rate = data["rates"][to_currency]
            return ExchangeRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=rate,
                date=data.get("date")  # Available for historical rates
            )
        else:
            return ExchangeRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=-1.0,  # Indicate failure
                date=date
            )

    except requests.exceptions.RequestException as e:
        return ExchangeRate(
            from_currency=from_currency,
            to_currency=to_currency,
            rate=-1.0,
            date=date
        )
    except json.JSONDecodeError:
        return ExchangeRate(
            from_currency=from_currency,
            to_currency=to_currency,
            rate=-1.0,
            date=date
        )

t_lookup_exchange_rate_tool = StructuredTool.from_function(
    func=get_exchange_rate,
    name="get_exchange_rate",
    description="""
    Use this tool to find the exchange rate between two currencies.
    Specify the source currency (from_currency) and the target currency (to_currency).
    You can also optionally specify a date (YYYY-MM-DD) for historical rates.
    Returns the exchange rate (how many units of target currency equal one unit of source currency) and the date of the rate.
    """,
    # args_schema=ExchangeRate.schema(),
)

if __name__ == '__main__':
    # Example usage:
    usd_to_eur_latest = get_exchange_rate(from_currency="EUR", to_currency="USD")
    print("Latest EUR to USD exchange rate:", usd_to_eur_latest)

    # Get yesterday's date for a likely valid historical rate
    yesterday = datetime.now(pytz.timezone('America/New_York')).date() - timedelta(days=1)
    historical_date_str = yesterday.strftime("%Y-%m-%d")
    usd_to_eur_historical = get_exchange_rate(from_currency="EUR", to_currency="USD", date=historical_date_str)
    print(f"EUR to USD exchange rate on {historical_date_str}:", usd_to_eur_historical)

    # Example of using the Langchain tool (you'd integrate this with an agent)
    # from langchain.agents import initialize_agent, AgentType
    # from langchain_google_vertexai import VertexAI

    llm = VertexAI(model_name="gemini-pro", project=PROJECT_ID, location="us-central1")
    tools = [
        # t_get_current_date,
             t_lookup_exchange_rate_tool]
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )
    # result = agent.run("What is the exchange rate of EUR to USD for April 2, 2025?")
    result = agent.run("What is the current exchange rate of EUR to USD?")
    print(result)
    