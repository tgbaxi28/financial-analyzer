"""
Gradio-based web interface for Financial Report Analyzer with Multi-Agent System.
Integrates LlamaIndex agents for intelligent financial analysis.
"""

import gradio as gr
import uuid
import time
from typing import Optional, List, Tuple
import os
from pathlib import Path

from config import (
    MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS,
    EMBEDDING_DIMENSION, SIMILARITY_THRESHOLD, MAX_CHUNKS_PER_QUERY
)
from models import get_session_maker, init_db, Report
from embedding_service import EmbeddingService
from audit_service import AuditService
from document_processor import DocumentProcessor, FinancialDataValidator
from llm_providers import LLMProviderFactory, ProviderCredentials
from llm_adapter import LLMAdapter
from agents import AgentOrchestrator
from agent_config import AgentConfigManager
from utils.logger import get_logger, LogContext

# Configure logging
logger = get_logger(__name__)

# Initialize database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://finuser:secure_password_123@localhost:5432/financial_reports"
)
init_db(DATABASE_URL)
SessionMaker = get_session_maker(DATABASE_URL)

# Initialize agent config manager
agent_config_manager = AgentConfigManager()

# Global state for session
current_session = {
    "session_id": str(uuid.uuid4()),
    "credentials": None,
    "provider": None,
    "model": None,
    "conversation_history": [],
    "uploaded_reports": {},
    "orchestrator": None,  # Multi-agent orchestrator
}

logger.info(f"Session initialized: {current_session['session_id']}")


# ===================== HELPER FUNCTIONS =====================

def get_session():
    """Get database session."""
    return SessionMaker()


def is_valid_file(filename: str) -> Tuple[bool, str]:
    """Validate uploaded file."""
    if not filename:
        return False, "No file selected"

    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type .{ext} not allowed. Allowed: {ALLOWED_EXTENSIONS}"

    return True, ""


def format_bytes(bytes_size: int) -> str:
    """Format bytes to human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} TB"


def initialize_orchestrator() -> Optional[AgentOrchestrator]:
    """Initialize multi-agent orchestrator with current credentials."""
    if not current_session["credentials"]:
        return None
    
    try:
        # Create LlamaIndex LLM
        llm = LLMAdapter.create_llm(current_session["credentials"])
        
        # Create orchestrator
        orchestrator = AgentOrchestrator(
            llm=llm,
            embedding_service=EmbeddingService,
            session_maker=SessionMaker,
        )
        
        logger.info("Multi-agent orchestrator initialized successfully")
        return orchestrator
        
    except Exception as e:
        logger.error(f"Error initializing orchestrator: {e}", exc_info=True)
        return None


# ===================== CREDENTIALS TAB =====================

def validate_credentials(provider: str, **kwargs) -> Tuple[str, bool]:
    """Validate credentials for selected provider."""
    with LogContext(logger, provider=provider):
        try:
            credentials_dict = {}

            if provider == "Azure AI":
                credentials_dict = {
                    "api_key": kwargs.get("azure_api_key", ""),
                    "endpoint": kwargs.get("azure_endpoint", ""),
                }
                model = kwargs.get("azure_model", "gpt-4")

            elif provider == "Google Gemini":
                credentials_dict = {
                    "api_key": kwargs.get("google_api_key", ""),
                }
                model = kwargs.get("gemini_model", "gemini-pro")

            elif provider == "AWS Bedrock":
                credentials_dict = {
                    "access_key": kwargs.get("aws_access_key", ""),
                    "secret_key": kwargs.get("aws_secret_key", ""),
                    "region": kwargs.get("aws_region", "us-east-1"),
                }
                model = kwargs.get("bedrock_model", "anthropic.claude-3-sonnet-20240229-v1:0")

            # Check all required fields are filled
            for key, value in credentials_dict.items():
                if not value:
                    return f"❌ Missing {key} for {provider}", False

            # Create credentials object
            provider_map = {"Azure AI": "azure", "Google Gemini": "google", "AWS Bedrock": "aws"}
            creds = ProviderCredentials(
                provider=provider_map[provider],
                credentials=credentials_dict,
                model=model,
            )

            # Validate with provider
            llm_provider = LLMProviderFactory.create_provider(creds)
            if llm_provider.validate_credentials():
                # Store in session
                current_session["credentials"] = creds
                current_session["provider"] = provider
                current_session["model"] = model
                
                # Initialize multi-agent orchestrator
                current_session["orchestrator"] = initialize_orchestrator()
                
                logger.info(f"Credentials validated for {provider}, model: {model}")

                return (
                    f"✅ {provider} credentials validated successfully!\n"
                    f"Model: {model}\n"
                    f"🤖 Multi-Agent System: Initialized",
                    True,
                )
            else:
                return f"❌ Failed to validate {provider} credentials", False

        except Exception as e:
            logger.error(f"Credential validation error: {e}", exc_info=True)
            return f"❌ Error validating credentials: {str(e)}", False


def get_credentials_status() -> str:
    """Get current credentials status."""
    if current_session["credentials"]:
        orchestrator_status = "✅ Active" if current_session["orchestrator"] else "❌ Not initialized"
        return (
            f"✅ Active Provider: {current_session['provider']}\n"
            f"   Model: {current_session['model']}\n"
            f"   Multi-Agent System: {orchestrator_status}"
        )
    else:
        return "❌ No credentials configured. Please enter credentials above."


# ===================== REPORTS TAB =====================

def upload_report(file, password: str = "") -> str:
    """Process uploaded financial report."""
    if not file:
        return "❌ No file selected"

    with LogContext(logger, file=file.name):
        try:
            start_time = time.time()

            # Validate file
            valid, msg = is_valid_file(file.name)
            if not valid:
                return f"❌ {msg}"

            file_path = file.name
            file_size = os.path.getsize(file_path)

            if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                return f"❌ File exceeds {MAX_FILE_SIZE_MB}MB limit"

            file_ext = Path(file_path).suffix.lower().lstrip(".")

            # Process document
            try:
                processor = DocumentProcessor(file_path, file_ext, password=password if password else None)
                full_text, chunks = processor.process()
            except ValueError as ve:
                error_msg = str(ve)
                if "password" in error_msg.lower():
                    return f"🔒 {error_msg}\n\nPlease enter the file password and try again."
                return f"❌ Error: {error_msg}"

            # Validate financial content
            is_valid, validation_issues = FinancialDataValidator.is_valid_financial_document(full_text)

            if validation_issues:
                logger.warning(f"Validation issues: {validation_issues}")

            # Check if credentials are set
            if not current_session["credentials"]:
                return "❌ Please configure credentials first"

            # Generate embeddings
            llm_provider = LLMProviderFactory.create_provider(current_session["credentials"])

            embeddings = []
            for chunk_data in chunks:
                emb = llm_provider.generate_embedding(chunk_data["text"])
                if emb:
                    embeddings.append(emb)
                else:
                    embeddings.append([0.0] * EMBEDDING_DIMENSION)

            # Store in database
            session = get_session()
            try:
                report = Report(
                    filename=Path(file_path).name,
                    file_path=str(file_path),
                    file_size_bytes=file_size,
                    file_type=file_ext,
                    processing_status="processing",
                )
                session.add(report)
                session.flush()

                embedding_service = EmbeddingService(session)
                stored = embedding_service.store_embeddings(
                    report.id,
                    chunks,
                    embeddings,
                    current_session["credentials"].provider,
                    current_session["model"],
                )

                report.processing_status = "ready"
                session.commit()

                current_session["uploaded_reports"][report.id] = {
                    "filename": report.filename,
                    "chunks": len(chunks),
                }

                elapsed = time.time() - start_time

                # Log to audit trail
                audit_service = AuditService(session)
                audit_service.log_query(
                    query_text=f"Upload: {Path(file_path).name}",
                    query_type="embedding",
                    provider_name=current_session["credentials"].provider,
                    provider_model=current_session["model"],
                    report_id=report.id,
                    chunks_used=len(chunks),
                    processing_time_ms=elapsed * 1000,
                    session_id=current_session["session_id"],
                )

                logger.info(f"Report uploaded successfully: {report.filename}, {stored} chunks")

                return (
                    f"✅ Report uploaded successfully!\n"
                    f"   Filename: {Path(file_path).name}\n"
                    f"   Chunks: {stored}\n"
                    f"   Time: {elapsed:.2f}s\n"
                    f"   Provider: {current_session['provider']}"
                )

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error uploading report: {e}", exc_info=True)
            return f"❌ Error uploading report: {str(e)}"


def get_reports_list() -> str:
    """Get list of uploaded reports."""
    try:
        session = get_session()
        try:
            reports = session.query(Report).filter(
                Report.processing_status.in_(["ready", "indexed"])
            ).all()

            if not reports:
                return "No reports uploaded yet."

            report_list = "📊 Uploaded Reports:\n"
            for report in reports:
                report_list += (
                    f"\n• {report.filename}\n"
                    f"  Size: {format_bytes(report.file_size_bytes)}\n"
                    f"  Chunks: {report.chunks_created}\n"
                    f"  Uploaded: {report.upload_date.strftime('%Y-%m-%d %H:%M')}\n"
                    f"  Provider: {report.embedding_provider or 'N/A'}"
                )

            return report_list

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error retrieving reports: {e}", exc_info=True)
        return f"❌ Error retrieving reports: {str(e)}"


# ===================== CHAT TAB (Multi-Agent) =====================

def chat_query(user_message: str, use_multi_agent: bool = True) -> Tuple[List[List[str]], str]:
    """Process user chat query using multi-agent system."""
    if not user_message.strip():
        return current_session["conversation_history"], "Please enter a query"

    if not current_session["credentials"]:
        return current_session["conversation_history"], "❌ Please configure credentials first"

    with LogContext(logger, query=user_message[:100], session_id=current_session["session_id"]):
        try:
            start_time = time.time()

            if use_multi_agent and current_session["orchestrator"]:
                # Use multi-agent system
                logger.info("Processing query with multi-agent system")
                
                result = current_session["orchestrator"].execute_query(
                    query=user_message,
                    context={},
                    use_routing=True,
                )
                
                response_content = result["answer"]
                agent_used = result.get("agent_used", "unknown")
                
                # Add agent info to response
                response_with_meta = (
                    f"{response_content}\n\n"
                    f"*🤖 Agent: {agent_used.replace('_', ' ').title()}*"
                )
                
            else:
                # Fallback to single LLM (old behavior)
                logger.info("Processing query with single LLM")
                session = get_session()
                try:
                    llm_provider = LLMProviderFactory.create_provider(
                        current_session["credentials"]
                    )

                    # Generate query embedding
                    query_embedding = llm_provider.generate_embedding(user_message)
                    if not query_embedding:
                        return current_session["conversation_history"], "❌ Failed to generate query embedding"

                    # Search for relevant chunks
                    embedding_service = EmbeddingService(session)
                    relevant_chunks = embedding_service.semantic_search(
                        query_embedding,
                        top_k=MAX_CHUNKS_PER_QUERY,
                        similarity_threshold=SIMILARITY_THRESHOLD,
                    )

                    if not relevant_chunks:
                        context = "No relevant information found in uploaded documents."
                    else:
                        context = "\n\n".join(
                            [f"From {chunk['report_filename']}:\n{chunk['text']}"
                             for chunk in relevant_chunks]
                        )

                    # Generate response
                    system_prompt = (
                        "You are a financial analysis expert. Answer based only on the provided context."
                    )

                    response = llm_provider.generate_chat_response(
                        query=user_message,
                        context=context,
                        system_prompt=system_prompt,
                        conversation_history=[
                            {"role": "user" if msg[0] == "User" else "assistant", "content": msg[1]}
                            for msg in current_session["conversation_history"]
                        ],
                    )

                    if response.error:
                        return current_session["conversation_history"], f"❌ Error: {response.error}"

                    response_with_meta = response.content
                    
                finally:
                    session.close()

            # Update conversation history
            current_session["conversation_history"].append(["User", user_message])
            current_session["conversation_history"].append(["Assistant", response_with_meta])

            elapsed = time.time() - start_time
            logger.info(f"Query processed in {elapsed:.2f}s")

            return current_session["conversation_history"], f"✅ Response time: {elapsed:.2f}s"

        except Exception as e:
            logger.error(f"Error in chat query: {e}", exc_info=True)
            return current_session["conversation_history"], f"❌ Error: {str(e)}"


def clear_chat():
    """Clear chat history."""
    current_session["conversation_history"] = []
    if current_session["orchestrator"]:
        current_session["orchestrator"].reset_conversation()
    logger.info("Chat history cleared")
    return [], "Chat cleared"


# ===================== GRADIO INTERFACE =====================

def create_interface():
    """Create Gradio interface with all tabs."""

    with gr.Blocks(title="Financial Report Analyzer - Multi-Agent", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 📊 Financial Report Analysis System")
        gr.Markdown(
            "🤖 **Multi-Agent AI System** - Powered by LlamaIndex\n"
            "Intelligent financial analysis with specialized agents for documents, metrics, and trends."
        )

        with gr.Tabs():
            # ==================== CREDENTIALS TAB ====================
            with gr.TabItem("🔐 Credentials", id="credentials"):
                gr.Markdown("### Enter AI Provider Credentials (Runtime Only)")

                provider_choice = gr.Radio(
                    choices=["Azure AI", "Google Gemini", "AWS Bedrock"],
                    label="Select Provider",
                    value="Azure AI",
                )

                # Azure AI credentials
                with gr.Group(visible=True) as azure_group:
                    gr.Markdown("#### Azure AI Credentials")
                    azure_api_key = gr.Textbox(
                        label="API Key",
                        type="password",
                        placeholder="Your Azure OpenAI API Key",
                    )
                    azure_endpoint = gr.Textbox(
                        label="Endpoint",
                        placeholder="https://your-resource.openai.azure.com/",
                    )
                    azure_model = gr.Dropdown(
                        choices=["gpt-4", "gpt-35-turbo", "gpt-4-turbo"],
                        label="Model",
                        value="gpt-4",
                    )

                # Google Gemini credentials
                with gr.Group(visible=False) as google_group:
                    gr.Markdown("#### Google Gemini Credentials")
                    google_api_key = gr.Textbox(
                        label="API Key",
                        type="password",
                        placeholder="Your Google Generative AI API Key",
                    )
                    gemini_model = gr.Dropdown(
                        choices=["gemini-pro", "gemini-pro-vision"],
                        label="Model",
                        value="gemini-pro",
                    )

                # AWS Bedrock credentials
                with gr.Group(visible=False) as aws_group:
                    gr.Markdown("#### AWS Bedrock Credentials")
                    aws_access_key = gr.Textbox(
                        label="Access Key ID",
                        type="password",
                        placeholder="Your AWS Access Key ID",
                    )
                    aws_secret_key = gr.Textbox(
                        label="Secret Access Key",
                        type="password",
                        placeholder="Your AWS Secret Access Key",
                    )
                    aws_region = gr.Textbox(
                        label="Region",
                        value="us-east-1",
                        placeholder="e.g., us-east-1",
                    )
                    bedrock_model = gr.Dropdown(
                        choices=[
                            "anthropic.claude-3-sonnet-20240229-v1:0",
                            "anthropic.claude-3-opus-20240229-v1:0",
                        ],
                        label="Model",
                        value="anthropic.claude-3-sonnet-20240229-v1:0",
                    )

                def toggle_credential_groups(provider):
                    return (
                        gr.update(visible=(provider == "Azure AI")),
                        gr.update(visible=(provider == "Google Gemini")),
                        gr.update(visible=(provider == "AWS Bedrock")),
                    )

                provider_choice.change(
                    toggle_credential_groups,
                    inputs=provider_choice,
                    outputs=[azure_group, google_group, aws_group],
                )

                validate_btn = gr.Button("✅ Validate & Initialize Multi-Agent System", variant="primary")
                validation_output = gr.Textbox(label="Validation Result", interactive=False)

                def handle_validation(
                    provider,
                    azure_api_key, azure_endpoint, azure_model,
                    google_api_key, gemini_model,
                    aws_access_key, aws_secret_key, aws_region, bedrock_model,
                ):
                    kwargs = {
                        "azure_api_key": azure_api_key,
                        "azure_endpoint": azure_endpoint,
                        "azure_model": azure_model,
                        "google_api_key": google_api_key,
                        "gemini_model": gemini_model,
                        "aws_access_key": aws_access_key,
                        "aws_secret_key": aws_secret_key,
                        "aws_region": aws_region,
                        "bedrock_model": bedrock_model,
                    }
                    result, success = validate_credentials(provider, **kwargs)
                    return result

                validate_btn.click(
                    handle_validation,
                    inputs=[
                        provider_choice,
                        azure_api_key, azure_endpoint, azure_model,
                        google_api_key, gemini_model,
                        aws_access_key, aws_secret_key, aws_region, bedrock_model,
                    ],
                    outputs=validation_output,
                )

                status_output = gr.Textbox(label="Current Status", interactive=False)
                gr.Button("🔄 Refresh Status").click(
                    get_credentials_status,
                    outputs=status_output,
                )

            # ==================== REPORTS TAB ====================
            with gr.TabItem("📄 Reports", id="reports"):
                gr.Markdown("### Upload & Manage Financial Reports")

                with gr.Row():
                    file_upload = gr.File(
                        label="Upload Financial Report",
                        file_count="single",
                        file_types=[".pdf", ".xlsx", ".csv", ".json", ".docx"],
                    )
                    password_input = gr.Textbox(
                        label="File Password (if protected)",
                        placeholder="Enter password for password-protected files",
                        type="password",
                        interactive=True,
                    )

                upload_output = gr.Textbox(label="Upload Status", interactive=False)
                upload_btn = gr.Button("📤 Upload Report", variant="primary")

                upload_btn.click(
                    upload_report,
                    inputs=[file_upload, password_input],
                    outputs=upload_output,
                )

                gr.Markdown("### Uploaded Reports")
                reports_list = gr.Textbox(
                    label="Reports",
                    interactive=False,
                    lines=10,
                )

                gr.Button("🔄 Refresh List").click(
                    get_reports_list,
                    outputs=reports_list,
                )

            # ==================== CHAT TAB (Multi-Agent) ====================
            with gr.TabItem("💬 Chat (Multi-Agent)", id="chat"):
                gr.Markdown("### 🤖 AI-Powered Financial Analysis with Specialized Agents")
                gr.Markdown(
                    "*Agents will automatically route your query to the most appropriate specialist:*\n"
                    "- 📄 **Document Agent**: Searches and extracts information\n"
                    "- 📊 **Metrics Agent**: Calculates financial ratios\n"
                    "- 📈 **Trend Agent**: Analyzes patterns over time"
                )

                chatbot = gr.Chatbot(label="Conversation", height=400)

                with gr.Row():
                    query_input = gr.Textbox(
                        label="Your Question",
                        placeholder="Ask about financial metrics, trends, or document content...",
                        scale=5,
                    )
                    submit_btn = gr.Button("Send", variant="primary", scale=1)

                with gr.Row():
                    use_agents_checkbox = gr.Checkbox(
                        label="Use Multi-Agent System (Recommended)",
                        value=True,
                    )
                
                status_text = gr.Textbox(label="Status", interactive=False)

                submit_btn.click(
                    chat_query,
                    inputs=[query_input, use_agents_checkbox],
                    outputs=[chatbot, status_text],
                ).then(lambda: "", outputs=query_input)

                clear_btn = gr.Button("🗑️ Clear Chat History")
                clear_btn.click(
                    clear_chat,
                    outputs=[chatbot, status_text],
                )

        gr.Markdown(
            "---\n"
            "**🤖 Multi-Agent System Powered by LlamaIndex** | "
            "**Security:** Credentials are runtime-only, never stored | "
            "**Logs:** All queries are audited"
        )

    return interface


if __name__ == "__main__":
    logger.info("Creating Gradio interface...")
    interface = create_interface()
    
    logger.info("Launching application at http://0.0.0.0:7860")
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
