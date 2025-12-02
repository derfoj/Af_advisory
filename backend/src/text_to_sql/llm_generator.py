from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage
from typing import List
from .config_loader import GLOBAL_CONFIG
from .llm_provider import LLMProvider

class LLMGenerator:
    def __init__(self):
        llm_provider = LLMProvider()
        self.llm = llm_provider.get_llm()

        prompt_template = (
            "You are a world-class SQL writer. Your job is to take a user's question and a database schema, "
            "and generate a valid, runnable SQL query that answers the question.\n\n"
            "- Only output the SQL query. Do not include any other text, explanations, or markdown.\n"
            "- Ensure the query is compatible with SQLite.\n"
            "- The user is in a read-only environment. Do not generate any write queries (INSERT, UPDATE, DELETE, DROP, etc.).\n\n"
            "Here is the database schema you must use:\n{schema}\n{correction_instruction}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_template),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        self.chain = prompt | self.llm | StrOutputParser()

    def generate_query(self, question: str, schema: str, chat_history: List[BaseMessage] = [], error: str = "") -> str:
        correction_instruction = ""
        if error:
            correction_instruction = f"\n\nPREVIOUS ERROR: {error}\nCORRECTION: Please fix the SQL query to resolve the error above."
            
        invocation_params = {
            "schema": schema,
            "question": question,
            "chat_history": chat_history,
            "correction_instruction": correction_instruction
        }
        print(f"LLM INVOCATION PARAMS: {invocation_params}")
        return self.chain.invoke(invocation_params)