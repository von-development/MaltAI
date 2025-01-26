"""Tool for managing user profile information."""

from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import Tool

class Profile(BaseModel):
    """User profile information."""
    name: Optional[str] = Field(description="User's name", default=None)
    location: Optional[str] = Field(description="User's location", default=None)
    interests: List[str] = Field(description="User's interests", default_factory=list)
    preferences: dict = Field(description="User's preferences", default_factory=dict)

async def update_profile(
    field: str,
    value: str,
    *,
    store,
    config
) -> str:
    """Update a field in the user's profile.
    
    Args:
        field: The profile field to update
        value: The new value for the field
    """
    user_id = config["configurable"]["user_id"]
    namespace = ("profile", user_id)
    
    # Get existing profile or create new
    profile_data = await store.aget(namespace, "profile")
    profile = Profile(**(profile_data or {}))
    
    # Update the field
    if hasattr(profile, field):
        setattr(profile, field, value)
        await store.aput(namespace, "profile", profile.model_dump())
        return f"Updated profile {field} to: {value}"
    else:
        return f"Unknown profile field: {field}"

profile_tool = Tool.from_function(
    func=update_profile,
    name="UpdateProfile",
    description="Update user profile information"
) 