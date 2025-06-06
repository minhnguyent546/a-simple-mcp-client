import asyncio
import os

import streamlit as st
from dotenv import load_dotenv

from app.chatbot import Chatbot


load_dotenv()

async def main():
    if 'server_connected' not in st.session_state:
        st.session_state.server_connected = False
    if 'tools' not in st.session_state:
        st.session_state.tools = []
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    st.set_page_config(
        page_title='A simple MCP client',
        page_icon=':robot_face:',
        layout='wide',
    )

    API_URL = os.environ.get('API_URL', '')
    chatbot = Chatbot(API_URL)

    await chatbot.render()


if __name__ == '__main__':
    asyncio.run(main())
