"""Tool for managing user instructions and preferences."""

from langchain_core.tools import Tool

async def update_instructions(
    instruction: str,
    category: str,
    *,
    store,
    config
) -> str:
    """Update user instructions for a specific category.
    
    Args:
        instruction: The new instruction
        category: The category of instruction (e.g., 'todo', 'reminders')
    """
    user_id = config["configurable"]["user_id"]
    namespace = ("instructions", user_id)
    
    await store.aput(
        namespace,
        key=category,
        value={"instruction": instruction}
    )
    
    return f"Updated {category} instructions: {instruction}"

instructions_tool = Tool.from_function(
    func=update_instructions,
    name="UpdateInstructions",
    description="Update user instructions for different features"
) 