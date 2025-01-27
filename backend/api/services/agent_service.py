import asyncio
from typing import AsyncGenerator
import logging
import sys
from pathlib import Path

# Add the project root to Python path
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.append(str(root_dir))

from src.maltai_agent import graph
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        self.config = {
            "configurable": {
                "user_id": "test-user",
                "model": "openai/gpt-4o-mini"
            }
        }

    async def process_message(self, message: str) -> AsyncGenerator[str, None]:
        """Process a message through the agent and yield responses."""
        try:
            async for response in graph.astream(
                {"messages": [HumanMessage(content=message)]},
                config=self.config
            ):
                if "messages" in response and response["messages"]:
                    yield response["messages"][-1].content
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            yield f"Error: {str(e)}"

agent_service = AgentService() 