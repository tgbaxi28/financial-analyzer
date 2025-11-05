"""
Multi-agent system for financial analysis using LlamaIndex.
"""

from .base_agent import BaseFinancialAgent
from .document_agent import DocumentAnalysisAgent
from .metrics_agent import FinancialMetricsAgent
from .trend_agent import TrendAnalysisAgent
from .query_router import QueryRouterAgent
from .orchestrator import AgentOrchestrator

__all__ = [
    "BaseFinancialAgent",
    "DocumentAnalysisAgent",
    "FinancialMetricsAgent",
    "TrendAnalysisAgent",
    "QueryRouterAgent",
    "AgentOrchestrator",
]
