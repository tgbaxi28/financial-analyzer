"""
Agent Orchestrator - Coordinates multiple agents to answer complex queries.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .document_agent import DocumentAnalysisAgent
from .metrics_agent import FinancialMetricsAgent
from .trend_agent import TrendAnalysisAgent
from .query_router import QueryRouterAgent
from utils.logger import get_logger

logger = get_logger("agent.orchestrator")


class AgentOrchestrator:
    """Orchestrates multiple agents to handle complex queries."""

    def __init__(
        self,
        llm: Any,
        embedding_service: Any = None,
        session_maker: Any = None,
    ):
        """
        Initialize orchestrator with all specialized agents.
        
        Args:
            llm: LlamaIndex LLM instance
            embedding_service: Embedding service for vector search
            session_maker: Database session maker
        """
        self.llm = llm
        self.logger = get_logger("orchestrator")
        
        # Initialize all agents
        self.logger.info("Initializing multi-agent system...")
        
        self.document_agent = DocumentAnalysisAgent(
            llm=llm,
            embedding_service=embedding_service,
            session_maker=session_maker,
        )
        
        self.metrics_agent = FinancialMetricsAgent(llm=llm)
        
        self.trend_agent = TrendAnalysisAgent(llm=llm)
        
        self.router_agent = QueryRouterAgent(llm=llm)
        
        self.agents = {
            "document_analysis": self.document_agent,
            "financial_metrics": self.metrics_agent,
            "trend_analysis": self.trend_agent,
        }
        
        self.logger.info(f"Initialized {len(self.agents)} specialized agents")
        
        # Track conversation context
        self.conversation_context = []

    def execute_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        use_routing: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute query using appropriate agent(s).
        
        Args:
            query: User query
            context: Additional context
            use_routing: Whether to use automatic routing
            
        Returns:
            Response dictionary with answer and metadata
        """
        start_time = datetime.now()
        self.logger.info(f"Processing query: {query[:100]}...")
        
        try:
            if use_routing:
                # Route to appropriate agent
                target_agent_name = self.router_agent.route_query(query)
                target_agent = self.agents.get(target_agent_name)
                
                if not target_agent:
                    return {
                        "answer": f"Error: Agent '{target_agent_name}' not found",
                        "agent_used": "error",
                        "success": False,
                    }
                
                self.logger.info(f"Query routed to: {target_agent_name}")
                
                # Execute with selected agent
                answer = target_agent.execute(query, context)
                
                result = {
                    "answer": answer,
                    "agent_used": target_agent_name,
                    "success": True,
                    "routing_used": True,
                }
                
            else:
                # Use document agent by default
                answer = self.document_agent.execute(query, context)
                result = {
                    "answer": answer,
                    "agent_used": "document_analysis",
                    "success": True,
                    "routing_used": False,
                }
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            result["processing_time_seconds"] = processing_time
            
            # Add to conversation context
            self.conversation_context.append({
                "query": query,
                "answer": answer,
                "agent": result["agent_used"],
                "timestamp": datetime.now().isoformat(),
            })
            
            self.logger.info(f"Query processed successfully in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                "answer": f"Error processing query: {str(e)}",
                "agent_used": "error",
                "success": False,
                "error": str(e),
            }

    def execute_multi_agent_query(
        self,
        query: str,
        agent_names: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute query with multiple agents and combine results.
        
        Args:
            query: User query
            agent_names: List of agent names to use
            context: Additional context
            
        Returns:
            Combined response from multiple agents
        """
        self.logger.info(f"Multi-agent query with: {agent_names}")
        
        responses = {}
        for agent_name in agent_names:
            agent = self.agents.get(agent_name)
            if agent:
                try:
                    response = agent.execute(query, context)
                    responses[agent_name] = response
                except Exception as e:
                    self.logger.error(f"Error in {agent_name}: {e}")
                    responses[agent_name] = f"Error: {str(e)}"
        
        # Combine responses
        combined_answer = "\n\n".join([
            f"**{name.replace('_', ' ').title()}:**\n{resp}"
            for name, resp in responses.items()
        ])
        
        return {
            "answer": combined_answer,
            "agents_used": list(responses.keys()),
            "success": True,
            "multi_agent": True,
        }

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return self.conversation_context

    def reset_conversation(self):
        """Reset conversation context."""
        self.conversation_context = []
        for agent in self.agents.values():
            agent.reset()
        self.logger.info("Conversation reset")

    def get_agent_info(self) -> Dict[str, str]:
        """Get information about available agents."""
        return {
            name: agent.description
            for name, agent in self.agents.items()
        }
