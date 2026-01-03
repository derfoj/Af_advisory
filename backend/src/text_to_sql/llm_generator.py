from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage
from typing import List, Dict, Any
import re
import json
from .config_loader import GLOBAL_CONFIG
from .llm_provider import LLMProvider

class LLMGenerator:
    def __init__(self):
        llm_provider = LLMProvider()
        self.llm = llm_provider.get_llm()

        # Load prompt from config or use default
        prompt_template = GLOBAL_CONFIG.get('prompts', {}).get('system_prompt')
        
        if not prompt_template:
            prompt_template = (
                "You are an expert SQL data analyst.\n"
                "Your goal is to generate a valid SQLite query to answer the user's question.\n\n"
                "Rules:\n"
                "1. Use only the provided schema.\n"
                "2. Do NOT use DELETE, DROP, ALTER, INSERT, UPDATE, GRANT, or TRUNCATE operations.\n"
                "3. Always limit your results to 100 rows if no limit is specified.\n"
                "4. Return ONLY the SQL query, no markdown, no explanations.\n"
                "5. Use standard SQLite syntax.\n\n"
                "Schema:\n{schema}\n{correction_instruction}"
            )

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_template),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        self.chain = prompt | self.llm | StrOutputParser()

    def clean_sql(self, sql: str) -> str:
        """Remove markdown code fences and clean up the SQL."""
        sql = sql.strip()
        
        # Remove ```sql ... ``` or ``` ... ```
        sql = re.sub(r'^```(?:sql)?\s*', '', sql)
        sql = re.sub(r'\s*```$', '', sql)
        
        # Remove any leading/trailing whitespace
        sql = sql.strip()
        
        return sql

    def generate_query(self, question: str, schema: str, chat_history: List[BaseMessage] = None, error: str = "") -> str:
        if chat_history is None:
            chat_history = []
            
        correction_instruction = ""
        if error:
            correction_instruction = f"\n\nPREVIOUS ERROR: {error}\nCORRECTION: Please fix the SQL query to resolve the error above."
            
        invocation_params = {
            "schema": schema,
            "question": question,
            "chat_history": chat_history,
            "correction_instruction": correction_instruction
        }
        print(f"--- LLM INVOCATION ---")
        print(f"Question: {question}")
        print(f"Schema length: {len(schema)} chars")
        
        raw_sql = self.chain.invoke(invocation_params)
        print(f"Raw LLM output: {raw_sql}")
        
        clean_sql = self.clean_sql(raw_sql)
        print(f"Cleaned SQL: {clean_sql}")
        
        return clean_sql

    def generate_explanation(self, question: str, sql: str, data: List[Dict[str, Any]]) -> str:
        """
        Generates a natural language explanation of the data results.
        """
        # Load prompt from config or use default
        prompt_template = GLOBAL_CONFIG.get('prompts', {}).get('answer_prompt')
        
        if not prompt_template:
            prompt_template = (
                "You are a helpful data assistant.\n"
                "User Question: {question}\n"
                "Data Result: {data_preview}\n\n"
                "Provide a concise natural language answer based on the data."
            )

        # Format data preview (limit to first 5 rows to save tokens)
        data_preview = json.dumps(data[:5], indent=2, default=str)

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_template),
            ("human", "Here is the data result. Please explain it.")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        print(f"--- GENERATING EXPLANATION ---")
        explanation = chain.invoke({
            "question": question,
            "sql": sql,
            "data_preview": data_preview
        })
        print(f"Explanation: {explanation}")
        return explanation