"""
Gradio-based web interface for Financial Report Analyzer.
Single Python application with tabbed interface:
- Chat Tab: Query financial reports
- BI Bot Tab: Pre-built financial analysis
- Credentials Tab: Enter AI provider credentials (runtime only, not stored)
- Reports Tab: Manage uploaded documents
"""

import logging
import gradio as gr
import uuid
import time
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import os
from pathlib import Path

from config import (
    UPLOAD_DIR, LOG_LEVEL, MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS,
    EMBEDDING_DIMENSION, SIMILARITY_THRESHOLD, MAX_CHUNKS_PER_QUERY
)
from models import get_session_maker, init_db, Report, Chunk
from embedding_service import EmbeddingService
from audit_service import AuditService
from document_processor import DocumentProcessor, FinancialDataValidator
from llm_providers import LLMProviderFactory, ProviderCredentials

# Configure logging
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://finuser:secure_password_123@localhost:5432/financial_reports"
)
init_db(DATABASE_URL)
SessionMaker = get_session_maker(DATABASE_URL)

# Global state for session credentials (runtime only, not persisted)
current_session = {
    "session_id": str(uuid.uuid4()),
    "credentials": None,
    "provider": None,
    "model": None,
    "conversation_history": [],
    "uploaded_reports": {},
}


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


# ===================== CREDENTIALS TAB =====================

def validate_credentials(provider: str, **kwargs) -> Tuple[str, bool]:
    """Validate credentials for selected provider."""
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
            # Store in session (not in database)
            current_session["credentials"] = creds
            current_session["provider"] = provider
            current_session["model"] = model

            return (
                f"✅ {provider} credentials validated successfully!\n"
                f"Model: {model}",
                True,
            )
        else:
            return f"❌ Failed to validate {provider} credentials", False

    except Exception as e:
        return f"❌ Error validating credentials: {str(e)}", False


def get_credentials_status() -> str:
    """Get current credentials status."""
    if current_session["credentials"]:
        return (
            f"✅ Active Provider: {current_session['provider']}\n"
            f"   Model: {current_session['model']}"
        )
    else:
        return "❌ No credentials configured. Please enter credentials above."


# ===================== REPORTS TAB =====================

def upload_report(file, password: str = "") -> str:
    """
    Process uploaded financial report with optional password for protected files.
    
    Args:
        file: Uploaded file object
        password: Optional password for password-protected files
        
    Returns:
        Status message with upload result
    """
    if not file:
        return "❌ No file selected"

    try:
        start_time = time.time()

        # Validate file
        valid, msg = is_valid_file(file.name)
        if not valid:
            return f"❌ {msg}"

        # Get file info
        file_path = file.name
        file_size = os.path.getsize(file_path)

        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            return f"❌ File exceeds {MAX_FILE_SIZE_MB}MB limit"

        file_ext = Path(file_path).suffix.lower().lstrip(".")

        # Process document with optional password
        try:
            processor = DocumentProcessor(file_path, file_ext, password=password if password else None)
            full_text, chunks = processor.process()
        except ValueError as ve:
            # Handle password-related errors
            error_msg = str(ve)
            if "password" in error_msg.lower():
                return f"🔒 {error_msg}\n\nPlease enter the file password in the password field and try again."
            return f"❌ Error: {error_msg}"
        except Exception as e:
            logger.error(f"Document processing error: {e}", exc_info=True)
            return f"❌ Error processing document: {str(e)}"

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
                embeddings.append([0.0] * EMBEDDING_DIMENSION)  # Fallback

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
            session.flush()  # Get report ID

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
        logger.error(f"Error uploading report: {e}")
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
        logger.error(f"Error retrieving reports: {e}")
        return f"❌ Error retrieving reports: {str(e)}"


# ===================== CHAT TAB =====================

def chat_query(user_message: str) -> Tuple[List[List[str]], str]:
    """Process user chat query."""
    if not user_message.strip():
        return current_session["conversation_history"], "Please enter a query"

    if not current_session["credentials"]:
        return current_session["conversation_history"], "❌ Please configure credentials first"

    try:
        start_time = time.time()

        # Get relevant documents
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
                "You are a financial analysis expert. Answer based only on the provided context. "
                "If the information is not in the provided documents, say so clearly."
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

            # Format response with sources
            response_with_sources = response.content
            if relevant_chunks:
                response_with_sources += "\n\n**Sources:**"
                for chunk in relevant_chunks[:3]:
                    response_with_sources += (
                        f"\n• {chunk['report_filename']} "
                        f"(Similarity: {chunk['similarity']:.2%})"
                    )

            # Update conversation history
            current_session["conversation_history"].append(["User", user_message])
            current_session["conversation_history"].append(["Assistant", response_with_sources])

            # Log to audit
            audit_service = AuditService(session)
            elapsed = time.time() - start_time
            audit_service.log_query(
                query_text=user_message,
                query_type="chat",
                provider_name=current_session["credentials"].provider,
                provider_model=current_session["model"],
                chunks_used=len(relevant_chunks),
                processing_time_ms=elapsed * 1000,
                response_length=len(response_with_sources),
                session_id=current_session["session_id"],
            )

            return current_session["conversation_history"], f"✅ Response time: {elapsed:.2f}s"

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in chat query: {e}")
        return current_session["conversation_history"], f"❌ Error: {str(e)}"


def clear_chat():
    """Clear chat history."""
    current_session["conversation_history"] = []
    return [], "Chat cleared"


# ===================== BI BOT TAB =====================

def run_bi_analysis(analysis_type: str) -> str:
    """Run pre-built BI analysis."""
    if not current_session["credentials"]:
        return "❌ Please configure credentials first"

    try:
        session = get_session()
        try:
            # Get all reports for context
            reports = session.query(Report).filter(
                Report.processing_status == "ready"
            ).all()

            if not reports:
                return "❌ No reports available for analysis"

            llm_provider = LLMProviderFactory.create_provider(
                current_session["credentials"]
            )

            # Build context from all reports
            context = "Financial Reports Summary:\n"
            for report in reports:
                chunks = session.query(Chunk).filter(
                    Chunk.report_id == report.id
                ).limit(5).all()

                context += f"\n{report.filename}:\n"
                for chunk in chunks:
                    context += f"- {chunk.chunk_text[:200]}...\n"

            # Generate analysis
            response = llm_provider.generate_bi_analysis(
                analysis_type=analysis_type,
                data_context=context,
                parameters={},
            )

            if response.error:
                return f"❌ Analysis failed: {response.error}"

            return response.content

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in BI analysis: {e}")
        return f"❌ Error: {str(e)}"


# ===================== GRADIO INTERFACE =====================

def create_interface():
    """Create Gradio interface with all tabs."""

    with gr.Blocks(title="Financial Report Analyzer", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 📊 Financial Report Analysis System")
        gr.Markdown(
            "Analyze financial reports using AI. "
            "All credentials are entered at runtime and not stored."
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
                    """Toggle visibility of credential groups."""
                    return (
                        gr.update(visible=(provider == "Azure AI")),  # azure_group
                        gr.update(visible=(provider == "Google Gemini")),  # google_group
                        gr.update(visible=(provider == "AWS Bedrock")),  # aws_group
                    )

                provider_choice.change(
                    toggle_credential_groups,
                    inputs=provider_choice,
                    outputs=[azure_group, google_group, aws_group],
                )

                # Validation button
                validate_btn = gr.Button("✅ Validate & Save Credentials", variant="primary")
                validation_output = gr.Textbox(label="Validation Result", interactive=False)

                def handle_validation(
                    provider,
                    azure_api_key, azure_endpoint, azure_model,
                    google_api_key, gemini_model,
                    aws_access_key, aws_secret_key, aws_region, bedrock_model,
                ):
                    """Handle credential validation."""
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

                # Status display
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

                # Reports list
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

            # ==================== CHAT TAB ====================
            with gr.TabItem("💬 Chat", id="chat"):
                gr.Markdown("### Query Financial Reports with AI")

                chatbot = gr.Chatbot(label="Conversation", height=400)

                with gr.Row():
                    query_input = gr.Textbox(
                        label="Your Question",
                        placeholder="Ask about financial metrics, ratios, trends...",
                        scale=5,
                    )
                    submit_btn = gr.Button("Send", variant="primary", scale=1)

                status_text = gr.Textbox(label="Status", interactive=False)

                submit_btn.click(
                    chat_query,
                    inputs=query_input,
                    outputs=[chatbot, status_text],
                ).then(lambda: "", outputs=query_input)

                clear_btn = gr.Button("🗑️ Clear Chat History")
                clear_btn.click(
                    clear_chat,
                    outputs=[chatbot, status_text],
                )

            # ==================== BI BOT TAB ====================
            with gr.TabItem("📈 BI Bot", id="bi_bot"):
                gr.Markdown("### Pre-built Financial Analysis")

                analysis_type = gr.Dropdown(
                    choices=[
                        "variance_analysis",
                        "trend_analysis",
                        "ratio_analysis",
                    ],
                    label="Select Analysis Type",
                    value="variance_analysis",
                )

                analyze_btn = gr.Button("🔍 Run Analysis", variant="primary")
                analysis_output = gr.Textbox(
                    label="Analysis Results",
                    interactive=False,
                    lines=15,
                )

                analyze_btn.click(
                    run_bi_analysis,
                    inputs=analysis_type,
                    outputs=analysis_output,
                )

        gr.Markdown(
            "---\n"
            "**Security Note:** Credentials are entered at runtime and not stored in any database. "
            "All queries are logged for audit purposes."
        )

    return interface


if __name__ == "__main__":
    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )