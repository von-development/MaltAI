"""Tool for managing user's todo items."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.tools import Tool

class ToDo(BaseModel):
    """Schema for a todo item."""
    task: str = Field(description="Task to be completed")
    time_to_complete: Optional[int] = Field(
        description="Estimated time in minutes",
        default=None
    )
    deadline: Optional[datetime] = Field(
        description="Deadline if any",
        default=None
    )
    status: Literal["not started", "in progress", "done"] = Field(
        description="Current status of the task",
        default="not started"
    )

async def add_todo(
    task: str,
    time_to_complete: Optional[int] = None,
    deadline: Optional[datetime] = None,
    *,
    store,
    config
) -> str:
    """Add a new todo item.
    
    Args:
        task: The task description
        time_to_complete: Estimated completion time in minutes
        deadline: When the task needs to be done by
    """
    todo = ToDo(
        task=task,
        time_to_complete=time_to_complete,
        deadline=deadline
    )
    
    user_id = config["configurable"]["user_id"]
    todo_id = f"todo_{datetime.now().timestamp()}"
    
    await store.aput(
        ("todos", user_id),
        key=todo_id,
        value=todo.model_dump()
    )
    
    return f"Added todo: {task}"

todo_tool = Tool.from_function(
    func=add_todo,
    name="AddTodo",
    description="Add a new todo item to the user's list"
) 