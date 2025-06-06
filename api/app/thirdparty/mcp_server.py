import json
import os

import bs4
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


load_dotenv()

DOCS_URLS = {
    'langchain': 'python.langchain.com/docs/',
    'llama_index': 'docs.llamaindex.ai/en/stable/',
    'openai': 'platform.openai.com/docs',
    'anthropic': 'docs.anthropic.com/en/docs',
}

SERPER_API_URL = 'https://google.serper.dev/search'

mcp = FastMCP(name='simple-mcp-server')


async def search_web(query: str) -> dict | None:
    """
    Search the web for the given query.

    Args:
        query (str): The query to search for.

    Returns:
        dict: The search results.
    """
    payload = json.dumps({
        'q': query,
        'num': 2,
    })
    headers = {
      'X-API-KEY': os.environ.get('SERPER_API_KEY', ''),
      'Content-Type': 'application/json'
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url=SERPER_API_URL,
                headers=headers,
                data=payload,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as e:
            print(f'Timed out while making request: {e}')
            return {'organic': []}
        except Exception as e:
            print(f'An error occurred while making request: {e}')
            return {'organic': []}

@mcp.tool()
async def fetch_url(url: str) -> str:
    """
    Fetch content of the page at the given URL.

    Args:
        url (str): The URL to fetch.

    Returns:
        str: The content of the page.
    """

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url=url, timeout=15)
            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            return soup.get_text()
        except httpx.TimeoutException as e:
            print(f'Timed out while fetching URL: {e}')
            return ''
        except Exception as e:
            print(f'An error occurred while fetching URL: {e}')
            return ''

@mcp.tool()
async def get_docs(library: str, query: str):
    """
    Search the latest documentations for a given query in the specified library.
    Supported platforms: langchain, llama_index, openai, anthropic.

    Args:
        library (str): The library to search for (e.g., "langchain").
        query (str): The query to search for (.e.g, "Semantic search").

    Returns:
        str: Text from the documentations
    """
    if library not in DOCS_URLS:
        raise ValueError(f'Unsupported library {library}. Supported libraries are langchain, llama_index, openai, anthropic')

    query = f'site:{DOCS_URLS[library]} {query}'  # query format for SERPER
    results = await search_web(query)
    if not results['organic']:
        return 'No results found.'

    text_list: list[str] = []
    for result in results['organic']:
        text = await fetch_url(result['link'])
        text_list.append(text)

    return '\n\n'.join(text_list)


if __name__ == '__main__':
    mcp.run(transport='stdio')
