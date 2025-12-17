import os
from dotenv import load_dotenv
load_dotenv()
from typing import Any

from pydantic import BaseModel, Field
from langchain_google_community import GoogleSearchAPIWrapper

from llm.logger import logger

google = GoogleSearchAPIWrapper(
    google_api_key=os.environ.get("GOOGLE_API_KEY"),
    google_cse_id=os.environ.get("GOOGLE_CSE_ID"),
)


class GoogleSearchRequest(BaseModel):
    """
    Request model for performing a Google search.
    """

    query: str = Field(..., description="The search query string.")
    num_results: int = Field(5, description="Number of search results to return.")


def perform_google_search(request: GoogleSearchRequest) -> list[dict[Any, Any]]:
    """
    Perform a Google search using the provided query and number of results.
    Returns the search results as a string.

    Args:
        request (GoogleSearchRequest): The search request containing query and num_results.
    Returns:
        str: The search results.
    """

    try:
        results = google.results(query=request.query, num_results=request.num_results)
    except Exception as e:
        logger.error(e)
        raise e
    return results


if __name__ == "__main__":
    request = GoogleSearchRequest(query="LangChain documentation", num_results=3)
    search_results = perform_google_search(request)
    print(search_results)
