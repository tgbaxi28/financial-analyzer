"""
Document Analysis Agent - Extracts and analyzes information from financial documents.
"""

from typing import Any, List
from llama_index.core.tools import FunctionTool

from .base_agent import BaseFinancialAgent
from utils.logger import get_logger

logger = get_logger("agent.document_analysis")


class DocumentAnalysisAgent(BaseFinancialAgent):
    """Agent specialized in document understanding and extraction."""

    def __init__(self, llm: Any, embedding_service: Any, session_maker: Any):
        """
        Initialize document analysis agent.
        
        Args:
            llm: LlamaIndex LLM instance
            embedding_service: Embedding service for vector search
            session_maker: Database session maker
        """
        self.embedding_service = embedding_service
        self.session_maker = session_maker
        
        # Create tools
        tools = self._create_tools()
        
        super().__init__(
            name="document_analysis",
            description="Analyzes financial documents and extracts key information",
            llm=llm,
            tools=tools,
        )

    def _create_tools(self) -> List[FunctionTool]:
        """Create tools for document analysis."""
        
        def search_documents(query: str, top_k: int = 5) -> str:
            """
            Search through uploaded financial documents.
            
            Args:
                query: Search query
                top_k: Number of results to return
                
            Returns:
                Relevant document chunks
            """
            logger.info(f"Searching documents with query: {query}")
            try:
                # This would use the embedding service
                # For now, return placeholder
                return f"Search results for: {query}"
            except Exception as e:
                logger.error(f"Document search error: {e}")
                return f"Error searching documents: {str(e)}"
        
        def extract_section(document_id: str, section_name: str) -> str:
            """
            Extract specific section from document.
            
            Args:
                document_id: Document identifier
                section_name: Section to extract (e.g., 'balance_sheet', 'income_statement')
                
            Returns:
                Extracted section content
            """
            logger.info(f"Extracting section '{section_name}' from document {document_id}")
            return f"Section {section_name} from document {document_id}"
        
        def list_available_reports() -> str:
            """
            List all uploaded financial reports.
            
            Returns:
                List of available reports
            """
            logger.info("Listing available reports")
            try:
                session = self.session_maker()
                from models import Report
                reports = session.query(Report).filter(
                    Report.processing_status == "ready"
                ).all()
                session.close()
                
                if not reports:
                    return "No reports available"
                
                report_list = []
                for r in reports:
                    report_list.append(f"- {r.filename} (ID: {r.id}, Chunks: {r.chunks_created})")
                
                return "\n".join(report_list)
            except Exception as e:
                logger.error(f"Error listing reports: {e}")
                return f"Error: {str(e)}"
        
        return [
            FunctionTool.from_defaults(fn=search_documents),
            FunctionTool.from_defaults(fn=extract_section),
            FunctionTool.from_defaults(fn=list_available_reports),
        ]

    def get_system_prompt(self) -> str:
        """Return system prompt for document agent."""
        return """You are a Document Analysis Agent specialized in financial documents.

Your role is to:
1. Search through uploaded financial documents
2. Extract specific sections and data points
3. Understand document structure (balance sheets, income statements, cash flow)
4. Identify key financial information

You have access to tools to search documents and extract sections.
Always cite the source document when providing information.
If information is not in the documents, clearly state that."""
