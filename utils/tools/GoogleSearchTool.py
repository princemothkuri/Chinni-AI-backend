from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('SERPAPI_API_KEY')

class GoogleSearchTool(BaseTool):
    """
    GoogleSearchTool is a tool that performs a search query using the Google Serper API.

    Purpose:
    - Useful for retrieving search results from Google based on a query.
    - Can be used to fetch information, news, or any data available through Google's search engine.

    Functionality:
    - Sends a search query to the Google Serper API and retrieves the results.
    - Handles API requests and responses, including error handling.

    Usage:
    - Accepts a `query` as input, which is the search term or phrase.
    - Returns the search results in JSON format.

    Example:
    - Input: `query="apple inc"`
    - Output: JSON response with search results.
    """
    name: str = "GoogleSearchTool"
    description: str = (
        "Performs a search query using the Google Serper API. "
        "Accepts `query` as input, which is the search term or phrase."
    )
    url: str = "https://google.serper.dev/search"

    class InputSchema(BaseModel):
        query: str = Field(..., description="The search term or phrase to query Google.")

    def _run(self, query: str):
        """Performs a search query using the Google Serper API."""
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(self.url, headers=headers, data=payload)
            response.raise_for_status()  # Raise an error for bad responses
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Error during search: {e}"} 