# A simple MCP client

> A simple MCP client running with Ollama.

## Getting started

1. **Clone this repository:**
  ```bash
  git clone https://github.com/minhnguyent546/a-simple-mcp-client.git 
  cd a-simple-mcp-client
  ```

2. **Update the .env file:**
  ```bash
  cp .env.example .env
  ```
  Add your SERPER API key to .env file. You can get one from https://serper.dev/

3. **Start the application:**
  You can start the application with Docker compose:
  ```bash
  docker-compose up --build
  ```
  Point your browser to http://localhost:8501 to see the application.
