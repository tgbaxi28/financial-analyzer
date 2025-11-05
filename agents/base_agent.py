"""
Base agent class for all financial agents using LlamaIndex.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool

from utils.logger import get_logger


class BaseFinancialAgent(ABC):
    """Base class for all financial analysis agents."""

    def __init__(
        self,
        name: str,
        description: str,
        llm: Any,
        tools: Optional[List[FunctionTool]] = None,
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            description: Agent description
            llm: LlamaIndex LLM instance
            tools: List of tools available to agent
        """
        self.name = name
        self.description = description
        self.llm = llm
        self.tools = tools or []
        self.logger = get_logger(f"agent.{name}")
        
        # Create ReAct agent
        self.agent = self._create_agent()
        
        self.logger.info(f"Initialized {name} agent with {len(self.tools)} tools")

    def _create_agent(self) -> ReActAgent:
        """Create LlamaIndex ReAct agent."""
        return ReActAgent.from_tools(
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            max_iterations=10,
        )

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return agent-specific system prompt."""
        pass

    def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute agent with query.
        
        Args:
            query: User query
            context: Additional context (documents, data, etc.)
            
        Returns:
            Agent response
        """
        self.logger.info(f"Executing query: {query[:100]}...")
        
        try:
            # Build prompt with system message and context
            system_prompt = self.get_system_prompt()
            
            # Add context if provided
            if context:
                context_str = self._format_context(context)
                full_query = f"{system_prompt}\n\nContext:\n{context_str}\n\nQuery: {query}"
            else:
                full_query = f"{system_prompt}\n\nQuery: {query}"
            
            # Execute agent
            response = self.agent.chat(full_query)
            
            self.logger.info(f"Agent response generated successfully")
            return str(response)
            
        except Exception as e:
            self.logger.error(f"Error executing agent: {e}", exc_info=True)
            return f"Error: {str(e)}"

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into string."""
        formatted = []
        for key, value in context.items():
            if isinstance(value, list):
                formatted.append(f"{key}:")
                for item in value[:5]:  # Limit context
                    formatted.append(f"  - {item}")
            else:
                formatted.append(f"{key}: {value}")
        return "\n".join(formatted)

    def reset(self):
        """Reset agent conversation history."""
        self.agent.reset()
        self.logger.debug(f"Agent {self.name} reset")
