import httpx
import re
from typing import Any

import streamlit as st
from loguru import logger


class Chatbot:
    def __init__(self, api_url: str) -> None:
        self.api_url = api_url
        self.messages = st.session_state.messages

    async def get_tools(self) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{self.api_url}/list_tools')
            if response.status_code == 200:
                return response.json()
            else:
                st.error('Failed to fetch tools')
                return {}

    def _parse_think_content(self, content: str) -> tuple[str, str]:
        """
        Parse content to separate <think></think> tags from main response.

        Returns:
            tuple: (think_content, main_content)
        """
        # Pattern to match <think>...</think> tags (case insensitive, multiline)
        think_pattern = r'<think>(.*?)</think>'

        # Find all think content
        think_matches = re.findall(think_pattern, content, re.DOTALL | re.IGNORECASE)
        think_content = '\n'.join(think_matches).strip() if think_matches else ""

        # Remove think tags from main content
        main_content = re.sub(think_pattern, '', content, flags=re.DOTALL | re.IGNORECASE).strip()

        return think_content, main_content

    def display_message(self, message: dict[str, Any]) -> None:
        if 'type' in message:
            role = message['type']
        else:
            role = message['role']
        content = message['content']

        if role == 'human':
            st.chat_message('user').write(content)
        elif role == 'ai':
            # Parse think content from main content
            think_content, main_content = self._parse_think_content(content)

            with st.chat_message('assistant', avatar='./assets/assistant.jpg'):
                # Display thinking process if present
                if think_content:
                    with st.expander("🤔 Thinking process", expanded=False):
                        st.markdown(f"```\n{think_content}\n```")

                # Display main response (will be original content if no think tags)
                st.write(main_content)

        elif role == 'tool':
            pass

    async def render(self):
        st.title('A simple MCP Client')
        with st.sidebar:
            st.subheader('Settings')
            st.write(f'API URL {self.api_url}')
            tools = await self.get_tools()
            st.subheader('Tools')
            st.write([tool['name'] for tool in tools['tools']])

            # TODO: add streaming feature
            # stream_enabled = st.checkbox('Enable Streaming', value=False)

        # Display all existing messages
        for message in self.messages:
            self.display_message(message)

        query = st.chat_input(placeholder='How do I use ChromaDB in langchain?')
        if query is None:
            return

        st.chat_message('user').write(query)

        messages_before = len(self.messages) + 1  # including the user query above

        # as we might have a long response when using large model with ollama, we set a longer timeout
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f'{self.api_url}/generate',
                json={'query': query},
            )
            if response.status_code == 200:
                data = response.json()
                messages = data['messages']['messages']
                st.session_state.messages = messages

                # Only display new messages (from the point where we left off)
                new_messages = messages[messages_before:]
                for message in new_messages:
                    self.display_message(message)

            else:
                st.error('Failed to process query')
                logger.error(f"Error: {response.text}")
