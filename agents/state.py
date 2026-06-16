
from typing import TypedDict,Optional
class AgentState(TypedDict):
    # User ka question
    question: str

    # Chat history
    chat_history: list

    # Tool results
    stock_result: str
    news_result: str
    rag_result: str
    calculator_result: str

    # Which agent used
    agent_used: str

    # Final answer
    human_approval:bool
    requires_approval:bool
    approval_message:str
    final_answer: str
