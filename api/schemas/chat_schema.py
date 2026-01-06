from pydantic import BaseModel, Field
from typing import Optional

class ChatSchema(BaseModel):
    user_id: str = Field(description="The user id of the user")
    thread_id: Optional[str] = Field(None, description="Thread id to maintain the conversation")
    msg: str = Field(description="The message which the user wants to send to LLM")