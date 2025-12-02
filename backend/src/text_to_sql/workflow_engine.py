from typing import TypedDict, Annotated, Dict, Any, List
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from .llm_generator import LLMGenerator
from .sql_safety import validate_sql_safety, SQLSecurityError
from .sql_executor import execute_query_and_format
from .schema_inspector import get_db_schema
from .config_loader import GLOBAL_CONFIG

class AgentState(TypedDict):
    question: str
    schema: str
    sql: str
    result: Dict[str, Any]
    error: str
    retry_count: int
    chat_history: List[BaseMessage]
    db_path: str

class WorkflowEngine:
    def __init__(self):
        self.llm_generator = LLMGenerator()
        self.max_retries = GLOBAL_CONFIG.get('settings', {}).get('max_retries', 3)
        self.workflow = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # Define Nodes
        workflow.add_node("generate", self.generate_step)
        workflow.add_node("execute", self.execute_step)

        # Define Edges
        workflow.set_entry_point("generate")
        workflow.add_edge("generate", "execute")
        workflow.add_conditional_edges(
            "execute",
            self.check_execution_status,
            {
                "success": END,
                "retry": "generate",
                "error": END
            }
        )

        return workflow.compile()

    def generate_step(self, state: AgentState) -> AgentState:
        print(f"--- GENERATING SQL (Attempt {state['retry_count'] + 1}) ---")
        try:
            sql = self.llm_generator.generate_query(
                question=state['question'],
                schema=state['schema'],
                chat_history=state['chat_history'],
                error=state.get('error')
            )
            return {"sql": sql, "retry_count": state['retry_count'] + 1}
        except Exception as e:
             return {"error": f"Generation Error: {str(e)}"}

    def execute_step(self, state: AgentState) -> AgentState:
        print("--- EXECUTING SQL ---")
        sql = state['sql']
        
        # 1. Safety Check
        try:
            safe_sql = validate_sql_safety(sql)
        except SQLSecurityError as e:
            return {"error": str(e), "result": None}
        except Exception as e:
            return {"error": f"Safety Check Error: {str(e)}", "result": None}

        # 2. Execution
        result = execute_query_and_format(safe_sql, state['db_path'])
        
        if "error" in result:
            return {"error": result["error"], "result": None}
        
        return {"result": result, "error": None, "sql": safe_sql}

    def check_execution_status(self, state: AgentState):
        if state.get('error'):
            if "Security Violation" in state['error']:
                return "error" # Stop immediately on security issues
            
            if state['retry_count'] < self.max_retries:
                return "retry"
            else:
                return "error"
        return "success"

    def run(self, question: str, db_path: str, chat_history: List[BaseMessage]):
        schema = get_db_schema(db_path)
        if schema.startswith("Error"):
            return {"error": schema}

        initial_state = {
            "question": question,
            "schema": schema,
            "sql": "",
            "result": {},
            "error": None,
            "retry_count": 0,
            "chat_history": chat_history,
            "db_path": db_path
        }
        
        return self.workflow.invoke(initial_state)