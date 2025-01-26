"""Graphs that extract memories on a schedule."""

import asyncio
import logging
from datetime import datetime

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore

from maltai_agent import configuration, utils
from maltai_agent.state import State, MessagesState
from maltai_agent.audio import AudioProcessor

from dotenv import load_dotenv
from maltai_agent.tools import memory_tool, todo_tool, profile_tool, instructions_tool

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize the language model to be used for memory extraction
llm = init_chat_model()

# Initialize audio processor
audio_processor = AudioProcessor()

# Initialize store
memory_store = InMemoryStore()

async def call_model(state: State, config: RunnableConfig, *, store: BaseStore = memory_store) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    configurable = configuration.Configuration.from_runnable_config(config)

    # Retrieve the most recent memories for context
    memories = await store.asearch(
        ("memories", configurable.user_id),
        query=str([m.content for m in state.messages[-3:]]),
        limit=10,
    )

    # Format memories for inclusion in the prompt
    formatted = "\n".join(f"[{mem.key}]: {mem.value} (similarity: {mem.score})" for mem in memories)
    if formatted:
        formatted = f"""
<memories>
{formatted}
</memories>"""

    # Retrieve profile information from the store
    profile_info = await store.asearch(
        ("profile", configurable.user_id),
        query="",
        limit=1,
    )
    profile_info = profile_info[0].value if profile_info else ""

    # Retrieve todo list from the store
    todo_list = await store.asearch(
        ("todos", configurable.user_id),
        query="",
        limit=10,
    )
    todo_list = "\n".join([f"- {todo.value}" for todo in todo_list])

    # Retrieve instructions from the store
    instructions = await store.asearch(
        ("instructions", configurable.user_id),
        query="",
        limit=1,
    )
    instructions = instructions[0].value if instructions else ""

    # Prepare the system prompt with user memories and current time
    # This helps the model understand the context and temporal relevance
    sys = configurable.system_prompt.format(
        user_info=formatted,
        time=datetime.now().isoformat(),
        profile_info=profile_info,
        todo_list=todo_list,
        instructions=instructions
    )

    # Invoke the language model with the prepared prompt and tools
    # "bind_tools" gives the LLM the JSON schema for all tools in the list so it knows how
    # to use them.
    msg = await llm.bind_tools([
        memory_tool.upsert_memory,
        todo_tool,
        profile_tool,
        instructions_tool
    ]).ainvoke(
        [{"role": "system", "content": sys}, *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )
    return {"messages": [msg]}


async def store_memory(state: State, config: RunnableConfig, *, store: BaseStore = memory_store):
    # Extract tool calls from the last message
    tool_calls = state.messages[-1].tool_calls

    # Concurrently execute all upsert_memory calls
    saved_memories = await asyncio.gather(
        *(
            memory_tool.upsert_memory(**tc["args"], config=config, store=store)
            for tc in tool_calls
        )
    )

    # Format the results of memory storage operations
    # This provides confirmation to the model that the actions it took were completed
    results = [
        {
            "role": "tool",
            "content": mem,
            "tool_call_id": tc["id"],
        }
        for tc, mem in zip(tool_calls, saved_memories)
    ]
    return {"messages": results}


def route_message(state: State):
    """Determine the next step based on the tool calls."""
    msg = state.messages[-1]
    if not msg.tool_calls:
        return END
        
    # Get the tool name from the first tool call
    tool_name = msg.tool_calls[0].name
    
    # Route based on tool
    if tool_name == "AddTodo":
        return "update_todos"
    elif tool_name == "UpdateProfile":
        return "update_profile"
    elif tool_name == "UpdateInstructions":
        return "update_instructions"
    elif tool_name == "upsert_memory":
        return "store_memory"
    
    return END


async def audio_input(state: MessagesState) -> dict:
    """Record and transcribe audio input."""
    message = audio_processor.record_audio()
    return {"messages": [message]}


async def audio_output(state: MessagesState):
    """Convert response to speech and play it."""
    response = state.messages[-1]
    audio_processor.speak_response(response.content)
    return state


async def update_todos(state: State, config: RunnableConfig, *, store: BaseStore = memory_store):
    """Handle todo updates."""
    tool_calls = state.messages[-1].tool_calls
    results = await asyncio.gather(
        *(
            todo_tool.add_todo(**tc.args, config=config, store=store)
            for tc in tool_calls
            if tc.name == "AddTodo"
        )
    )
    return {
        "messages": [{
            "role": "tool",
            "content": result,
            "tool_call_id": tc.id
        } for tc, result in zip(tool_calls, results)]
    }

async def update_profile(state: State, config: RunnableConfig, *, store: BaseStore = memory_store):
    """Handle profile updates."""
    tool_calls = state.messages[-1].tool_calls
    results = await asyncio.gather(
        *(
            profile_tool.update_profile(**tc.args, config=config, store=store)
            for tc in tool_calls
            if tc.name == "UpdateProfile"
        )
    )
    return {
        "messages": [{
            "role": "tool",
            "content": result,
            "tool_call_id": tc.id
        } for tc, result in zip(tool_calls, results)]
    }

async def update_instructions(state: State, config: RunnableConfig, *, store: BaseStore = memory_store):
    """Handle instruction updates."""
    tool_calls = state.messages[-1].tool_calls
    results = await asyncio.gather(
        *(
            instructions_tool.update_instructions(**tc.args, config=config, store=store)
            for tc in tool_calls
            if tc.name == "UpdateInstructions"
        )
    )
    return {
        "messages": [{
            "role": "tool",
            "content": result,
            "tool_call_id": tc.id
        } for tc, result in zip(tool_calls, results)]
    }

# Update the graph builder
builder = StateGraph(State, config_schema=configuration.Configuration)

# Add all nodes
builder.add_node("audio_input", audio_input)
builder.add_node("process_input", call_model)
builder.add_node("store_memory", store_memory)
builder.add_node("update_todos", update_todos)
builder.add_node("update_profile", update_profile)
builder.add_node("update_instructions", update_instructions)
builder.add_node("audio_output", audio_output)

# Define the flow
builder.add_edge("__start__", "audio_input")
builder.add_edge("audio_input", "process_input")
builder.add_conditional_edges(
    "process_input",
    route_message,
    {
        "store_memory": "store_memory",
        "update_todos": "update_todos",
        "update_profile": "update_profile",
        "update_instructions": "update_instructions",
        END: "audio_output"
    }
)

# Add edges from tool handlers back to audio output
builder.add_edge("store_memory", "audio_output")
builder.add_edge("update_todos", "audio_output")
builder.add_edge("update_profile", "audio_output")
builder.add_edge("update_instructions", "audio_output")
builder.add_edge("audio_output", END)

# Compile with store
graph = builder.compile(store=memory_store)
graph.name = "MaltaiAgent"

__all__ = ["graph"]
