import os
from typing import Any

import uvicorn
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.load import dumps
from langchain_core.tools import BaseTool
from pydantic import BaseModel, computed_field
from pydantic_settings import BaseSettings

from app.mcp_client import MCPClient
from app.utils.loguru import init_logger, logger


load_dotenv()
init_logger()

class HealthCheck(BaseModel):
    status: str

class Settings(BaseSettings):
    server_file_path: str = os.environ.get('MCP_SERVER_FILE_PATH', '')

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        origins = os.environ.get('CORS_ORIGINS', '*')
        if origins == '*':
            return ["*"]
        return [
            origin.rstrip('/')
            for origin in origins.split(',')
        ]

class QueryRequest(BaseModel):
    query: str
    stream: bool = False

class Message(BaseModel):
    role: str
    content: str

class ToolCall(BaseModel):
    name: str
    args: dict[str, Any]


settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = MCPClient()
    try:
        await client.connect_to_mcp_server(settings.server_file_path)
        app.state.client = client
        yield
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to MCP server: {e}")
    finally:
        await client.cleanup()

app = FastAPI(title='MCP client API', lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f'CORS origins: {settings.cors_origins}')

@app.get(
    '/health',
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def get_health() -> HealthCheck:
    return HealthCheck(status='OK')

@app.post('/generate')
async def process_query(request: QueryRequest):
    try:
        if request.stream:
            # For streaming, return a StreamingResponse
            async def generate_stream():
                stream_generator = await app.state.client.process_query(request.query, stream=True)
                async for chunk in stream_generator:
                    # Format each chunk as JSON and add newline for streaming
                    yield dumps(chunk)

            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            # Non-streaming: return the complete response
            messages = await app.state.client.process_query(request.query, stream=False)
            return {
                'messages': messages,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {e}")

@app.get('/list_tools')
async def list_tools():
    try:
        tools: list[BaseTool] = app.state.client.tools
        return {
            'tools': [
                {
                    'name': tool.name,
                    'description': tool.description,
                    'args_schema': tool.args_schema,
                }
                for tool in tools
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tools: {e}")
