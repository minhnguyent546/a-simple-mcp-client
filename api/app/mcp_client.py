import os
import traceback
from contextlib import AsyncExitStack
from typing import Any, AsyncGenerator

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_ollama.chat_models import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.utils.loguru import logger


class MCPClient:
    def __init__(self) -> None:
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        self.tools: list[BaseTool] = []

    async def connect_to_mcp_server(self, server_file_path: str) -> None:
        if not os.path.isfile(server_file_path):
            raise ValueError(f'Server file path not found: {server_file_path}')
        try:
            logger.info('Connecting to MCP server')
            server_params = StdioServerParameters(
                command='python', args=[server_file_path],
            )

            self.stdio, self.write = await self.exit_stack.enter_async_context(
                stdio_client(server_params),
            )
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write),
            )

            await self.session.initialize()
            logger.info('Connected to MCP server!')

            self.tools = await self.get_mcp_tools()
            logger.info(f'Available tool list: {[tool.name for tool in self.tools]}')

            self.agent = self._create_react_agent()
            self.agent_config = RunnableConfig(
                configurable={"thread_id": "abc123"},
            )

        except Exception as e:
            logger.error(f'Error connecting to MCP server: {e}')
            raise

    async def get_mcp_tools(self):
        self._ensure_initialized()

        try:
            tools = await load_mcp_tools(self.session)
            return tools
        except Exception as e:
            logger.error(f'Error getting MCP tool list: {e}')
            raise

    async def process_query(self, query: str, stream: bool = False) -> Any:
        """Process a query with optional streaming support."""
        self._ensure_initialized()

        try:
            logger.info(f'Processing query: {query}')
            user_message = HumanMessage(content=query)

            if stream:
                return self._stream_response(user_message)
            else:
                response = await self.agent.ainvoke(
                    input={
                        'messages': [user_message],
                    },
                    config=self.agent_config,
                )
                return response
        except Exception as e:
            logger.info(f'Error processing query: {e}')
            raise

    async def _stream_response(self, user_message: HumanMessage) -> AsyncGenerator[Any, None]:
        """Internal method to handle streaming queries."""
        async for chunk in self.agent.astream(
            input={
                'messages': [user_message],
            },
            config=self.agent_config,
            stream_mode='messages',
        ):
            yield chunk

    async def cleanup(self) -> None:
        try:
            logger.info('Cleaning up MCP client resources')
            await self.exit_stack.aclose()
            logger.info('Disconnected from MCP server')
        except Exception as e:
            logger.error(f'Error during cleanup: {e}')
            traceback.print_exc()
            raise

    def _ensure_initialized(self) -> None:
        if self.session is None:
            raise RuntimeError('Not connected to MCP server. Please call connect_to_mcp_server first.')

    def _create_react_agent(self):
        self._ensure_initialized()

        model_name = os.environ.get('MODEL_NAME', 'qwen3:0.6b')
        base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        logger.info(f'Using model {model_name} with base URL {base_url}')
        llm = ChatOllama(model=model_name, temperature=0.0, base_url=base_url)

        # Create agent with system prompt
        agent = create_react_agent(
            model=llm,
            tools=self.tools,
            checkpointer=InMemorySaver(),
        )

        return agent
