"""Simple script to test the agent with voice interaction."""

import asyncio
from maltai_agent import graph
from langchain_core.messages import HumanMessage

async def main():
    # Configuration for the agent
    config = {
        "configurable": {
            "user_id": "test-user",
            "model": "openai/gpt-4o-mini"  # or any other supported model
        }
    }

    print("Starting MaltAI Agent...")
    print("The agent will listen for your voice input.")
    print("Press Enter to stop recording when you're done speaking.")

    # Run the agent
    async for response in graph.astream(
        {"messages": [HumanMessage(content="Hello, I'm ready to help!")]}, 
        config=config
    ):
        if "messages" in response:
            # Print the actual response content
            messages = response["messages"]
            if messages:
                print("\nAgent Response:", messages[-1].content)

if __name__ == "__main__":
    asyncio.run(main()) 