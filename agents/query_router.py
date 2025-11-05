"""
Query Router Agent - Routes user queries to appropriate specialized agents.
"""

from typing import Any, List
from llama_index.core.tools import FunctionTool

from .base_agent import BaseFinancialAgent
from utils.logger import get_logger

logger = get_logger("agent.query_router")


class QueryRouterAgent(BaseFinancialAgent):
    """Agent that routes queries to appropriate specialized agents."""

    def __init__(self, llm: Any):
        """
        Initialize query router agent.
        
        Args:
            llm: LlamaIndex LLM instance
        """
        tools = self._create_tools()
        
        super().__init__(
            name="query_router",
            description="Routes user queries to the most appropriate specialized agent",
            llm=llm,
            tools=tools,
        )
        
        # Define agent capabilities
        self.agent_capabilities = {
            "document_analysis": [
                "find", "search", "locate", "extract", "show", "display",
                "document", "report", "statement", "balance sheet", "income"
            ],
            "financial_metrics": [
                "calculate", "ratio", "metric", "ROA", "ROE", "liquidity",
                "profitability", "leverage", "debt", "equity", "margin"
            ],
            "trend_analysis": [
                "trend", "growth", "change", "compare", "variance", "increase",
                "decrease", "over time", "YoY", "QoQ", "seasonal"
            ],
        }

    def _create_tools(self) -> List[FunctionTool]:
        """Create tools for query routing."""
        
        def classify_query(query: str) -> str:
            """
            Classify user query to determine appropriate agent.
            
            Args:
                query: User query
                
            Returns:
                Recommended agent name
            """
            logger.info(f"Classifying query: {query[:100]}...")
            
            query_lower = query.lower()
            scores = {agent: 0 for agent in self.agent_capabilities}
            
            # Score each agent based on keyword matches
            for agent, keywords in self.agent_capabilities.items():
                for keyword in keywords:
                    if keyword in query_lower:
                        scores[agent] += 1
            
            # Get agent with highest score
            best_agent = max(scores, key=scores.get)
            
            # If no clear match, default to document analysis
            if scores[best_agent] == 0:
                best_agent = "document_analysis"
            
            logger.info(f"Query routed to: {best_agent} (scores: {scores})")
            return best_agent
        
        def get_agent_description(agent_name: str) -> str:
            """
            Get description of what an agent can do.
            
            Args:
                agent_name: Name of the agent
                
            Returns:
                Agent description
            """
            descriptions = {
                "document_analysis": "Searches and extracts information from financial documents",
                "financial_metrics": "Calculates financial ratios and metrics",
                "trend_analysis": "Analyzes trends and patterns in financial data",
            }
            return descriptions.get(agent_name, "Unknown agent")
        
        return [
            FunctionTool.from_defaults(fn=classify_query),
            FunctionTool.from_defaults(fn=get_agent_description),
        ]

    def route_query(self, query: str) -> str:
        """
        Route query to appropriate agent.
        
        Args:
            query: User query
            
        Returns:
            Name of the agent to handle the query
        """
        query_lower = query.lower()
        scores = {agent: 0 for agent in self.agent_capabilities}
        
        # Score each agent based on keyword matches
        for agent, keywords in self.agent_capabilities.items():
            for keyword in keywords:
                if keyword in query_lower:
                    scores[agent] += 1
        
        # Get agent with highest score
        best_agent = max(scores, key=scores.get)
        
        # If no clear match, default to document analysis
        if scores[best_agent] == 0:
            best_agent = "document_analysis"
        
        logger.info(f"Query '{query[:50]}...' routed to: {best_agent}")
        return best_agent

    def get_system_prompt(self) -> str:
        """Return system prompt for router agent."""
        return """You are a Query Router Agent that analyzes user questions and routes them to specialized agents.

Available agents:
1. Document Analysis Agent - Searches and extracts information from documents
2. Financial Metrics Agent - Calculates ratios and financial metrics
3. Trend Analysis Agent - Analyzes trends and patterns over time

Your role is to:
1. Understand the user's query intent
2. Determine which agent(s) can best answer the question
3. Route the query appropriately

Consider the query carefully and choose the most appropriate agent."""
