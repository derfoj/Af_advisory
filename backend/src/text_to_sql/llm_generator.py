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
        # Default LLM and chain setup
        llm_provider = LLMProvider()
        self.default_llm = llm_provider.get_llm()

        # Load prompts from config or use default
        self.system_prompt_template = GLOBAL_CONFIG.get('prompts', {}).get('system_prompt')
        if not self.system_prompt_template:
            self.system_prompt_template = (
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

        self.answer_prompt_template = GLOBAL_CONFIG.get('prompts', {}).get('answer_prompt')
        if not self.answer_prompt_template:
            self.answer_prompt_template = (
                "You are a helpful data assistant.\n"
                "User Question: {question}\n"
                "Data Result: {data_preview}\n\n"
                "Provide a concise natural language answer based on the data."
            )

        self.default_chain = self._build_chain(self.default_llm, self.system_prompt_template, ["chat_history", "question", "schema", "correction_instruction"])
    
    def _build_chain(self, llm, template, input_variables):
        messages = [("system", template)]
        if "chat_history" in input_variables:
             messages.append(MessagesPlaceholder(variable_name="chat_history"))
        
        # Add human message placeholder
        # The prompt template might not verify all vars, but we construct the chat prompt here
        if "question" in input_variables:
             messages.append(("human", "{question}"))
             
        prompt = ChatPromptTemplate.from_messages(messages)
        return prompt | llm | StrOutputParser()

    def _get_chain(self, provider: str = None, model_name: str = None, prompt_type: str = "query"):
        if not provider and not model_name:
             if prompt_type == "query":
                 return self.default_chain
             else:
                 # Build default explanation chain lazily or on fly
                 return self._build_chain(self.default_llm, self.answer_prompt_template, ["question", "data_preview", "sql"])
        
        # Dynamic creation
        llm = LLMProvider.get_llm(provider=provider, model_name=model_name)
        if prompt_type == "query":
            return self._build_chain(llm, self.system_prompt_template, ["chat_history", "question", "schema", "correction_instruction"])
        else:
            return self._build_chain(llm, self.answer_prompt_template, ["question", "data_preview", "sql"])

    def clean_sql(self, sql: str) -> str:
        """Remove markdown code fences and clean up the SQL."""
        sql = sql.strip()
        
        # Pattern to find markdown code blocks (sql, sqlite, or generic)
        match = re.search(r'```\w*\s*(.*?)\s*```', sql, re.DOTALL | re.IGNORECASE)
        if match:
            sql = match.group(1)
        
        sql = sql.strip()
        
        # If it still doesn't start with SELECT, try to find the first SELECT
        # This handles cases like "Here is the query: SELECT * FROM ..."
        if not sql.upper().startswith("SELECT"):
            match = re.search(r'(SELECT\s+.*)', sql, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1)
        
        return sql

    def generate_query(self, question: str, schema: str, chat_history: List[BaseMessage] = None, error: str = "", provider: str = None, model_name: str = None) -> str:
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
        print(f"--- LLM INVOCATION (Provider: {provider or 'Default'}, Model: {model_name or 'Default'}) ---")
        print(f"Question: {question}")
        print(f"Schema length: {len(schema)} chars")
        
        chain = self._get_chain(provider, model_name, "query")
        raw_sql = chain.invoke(invocation_params)
        print(f"Raw LLM output: {raw_sql}")
        
        clean_sql = self.clean_sql(raw_sql)
        print(f"Cleaned SQL: {clean_sql}")
        
        return clean_sql

    def generate_explanation(self, question: str, sql: str, data: List[Dict[str, Any]], provider: str = None, model_name: str = None) -> str:
        """
        Generates a natural language explanation of the data results.
        """
        # Format data preview (limit to first 5 rows to save tokens)
        data_preview = json.dumps(data[:5], indent=2, default=str)

        print(f"--- GENERATING EXPLANATION (Provider: {provider or 'Default'}, Model: {model_name or 'Default'}) ---")
        
        chain = self._get_chain(provider, model_name, "explanation")
        explanation = chain.invoke({
            "question": question,
            "sql": sql,
            "data_preview": data_preview
        })
        print(f"Explanation: {explanation}")
        return explanation