from pydantic import BaseModel
from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class Message(BaseModel):
    role: str
    content: str

    def to_langchain(self) -> BaseMessage:
        if self.role == "user":
            return HumanMessage(content=self.content)
        elif self.role == "assistant":
            return AIMessage(content=self.content)
        else:
            return HumanMessage(content=self.content)

class QueryRequest(BaseModel):
    question: str
    db_path: str
    chat_history: Optional[List[Message]] = []
    provider: Optional[str] = None
    model_name: Optional[str] = None
