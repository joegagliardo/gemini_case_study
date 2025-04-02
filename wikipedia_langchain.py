import os
from langchain_google_vertexai import VertexAI
from google.cloud import bigquery
from langchain.tools import WikipediaQueryRun
from langchain.utilities import WikipediaAPIWrapper
from langchain.tools import StructuredTool
from langchain.agents import AgentType, initialize_agent, load_tools
import wikipedia


PROJECT_ID = "roi-genai-joey"  # Replace with your Google Cloud Project ID

def get_current_date():
    """
    Gets the current date (today), in the format YYYY-MM-DD
    """

    from datetime import datetime

    todays_date = datetime.today().strftime("%Y-%m-%d")

    return todays_date

# Initialize the LLM (using Vertex AI Gemini Pro as an example)
# Ensure you have Vertex AI API enabled and appropriate permissions.
# You might need to set GOOGLE_APPLICATION_CREDENTIALS environment variable
# if running outside of a Google Cloud environment with default credentials.
llm = VertexAI(model_name="gemini-pro", project=PROJECT_ID, location="us-central1")

# t_get_current_date = StructuredTool.from_function(get_current_date)
t_get_current_date = StructuredTool.from_function(get_current_date, name="get_current_date", description="Use this tool to retrieve the current date. The output will be in YYYY-MM-DD format.")

tools = [
    t_get_current_date,
]

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

_ = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

tools = load_tools(["wikipedia"], llm=llm)

tools.append(t_get_current_date)

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

# agent.run("What former US President was first?")
agent.run(
    "Fetch today's date, and tell me which famous person was born or who died on the same day as today?"
)
