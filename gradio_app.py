"""Gradio UI for Financial Analyzer."""
import gradio as gr
import httpx
import os
from typing import Optional, List, Tuple

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
WRENAI_URL = os.getenv("WRENAI_URL", "http://localhost:3000")

# Global state
session_state = {
    "access_token": None,
    "user": None,
    "current_owner_id": None,
    "current_owner_type": "user",
    "provider_credentials": None
}


async def register_user(email: str, first_name: str, last_name: str) -> str:
    """Register a new user."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/auth/register",
                json={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name
                }
            )

            if response.status_code == 200:
                return f"✅ Magic link sent to {email}. Please check your inbox!"
            else:
                return f"❌ Registration failed: {response.json().get('detail', 'Unknown error')}"

    except Exception as e:
        return f"❌ Error: {str(e)}"


async def login_user(email: str) -> str:
    """Request magic link for login."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/auth/login",
                json={"email": email}
            )

            if response.status_code == 200:
                return f"✅ Magic link sent to {email}. Please check your inbox!"
            else:
                return f"❌ Login failed: {response.json().get('detail', 'Unknown error')}"

    except Exception as e:
        return f"❌ Error: {str(e)}"


async def verify_magic_link(token: str) -> Tuple[str, str]:
    """Verify magic link token."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/auth/verify",
                json={"token": token}
            )

            if response.status_code == 200:
                data = response.json()
                session_state["access_token"] = data["access_token"]
                session_state["user"] = data["user"]
                session_state["current_owner_id"] = data["user"]["id"]
                session_state["current_owner_type"] = "user"

                return (
                    f"✅ Welcome, {data['user']['first_name']}!",
                    f"Logged in as: {data['user']['email']}"
                )
            else:
                return f"❌ Verification failed: {response.json().get('detail', 'Unknown error')}", ""

    except Exception as e:
        return f"❌ Error: {str(e)}", ""


async def upload_document(file, owner_type: str, password: Optional[str]) -> str:
    """Upload a document."""
    if not session_state.get("access_token"):
        return "❌ Please login first"

    try:
        files = {"file": (file.name, file, file.type)}
        data = {
            "owner_type": owner_type,
            "owner_id": session_state["current_owner_id"] if owner_type == "family_member" else None,
        }

        if password:
            data["password"] = password

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/documents",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {session_state['access_token']}"}
            )

            if response.status_code == 201:
                doc = response.json()
                return f"✅ Document uploaded successfully!\n\nFilename: {doc['filename']}\nStatus: {doc['processing_status']}\nChunks: {doc['chunk_count']}"
            else:
                return f"❌ Upload failed: {response.json().get('detail', 'Unknown error')}"

    except Exception as e:
        return f"❌ Error: {str(e)}"


async def chat_with_docs(
    query: str,
    provider: str,
    api_key: str,
    endpoint: Optional[str],
    model_name: Optional[str],
    history: List
) -> Tuple[str, List]:
    """Chat with documents using RAG."""
    if not session_state.get("access_token"):
        return "❌ Please login first", history

    if not api_key:
        return "❌ Please enter API key for AI provider", history

    try:
        # Build provider credentials
        credentials = {
            "provider": provider,
            "api_key": api_key,
        }

        if endpoint:
            credentials["endpoint"] = endpoint

        if model_name:
            credentials["model_name"] = model_name

        # Build request
        request_data = {
            "query": query,
            "owner_id": session_state["current_owner_id"],
            "owner_type": session_state["current_owner_type"],
            "provider_credentials": credentials,
            "conversation_history": [
                {"role": msg["role"], "content": msg["content"]}
                for msg in history
            ]
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/documents/chat",
                json=request_data,
                headers={"Authorization": f"Bearer {session_state['access_token']}"}
            )

            if response.status_code == 200:
                data = response.json()

                # Format response with sources
                response_text = data["response"]

                if data.get("sources"):
                    response_text += "\n\n**Sources:**\n"
                    for src in data["sources"]:
                        response_text += f"- {src['filename']} (Page {src.get('page_number', 'N/A')}, Relevance: {src['relevance_score']:.2f})\n"

                # Add to history
                history.append({"role": "user", "content": query})
                history.append({"role": "assistant", "content": response_text})

                return response_text, history
            else:
                error_msg = f"❌ Chat failed: {response.json().get('detail', 'Unknown error')}"
                return error_msg, history

    except Exception as e:
        return f"❌ Error: {str(e)}", history


# Create Gradio interface
with gr.Blocks(title="Financial Analyzer", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 💰 Financial Analyzer")
    gr.Markdown("AI-powered financial document analysis and portfolio tracking")

    with gr.Tabs():
        # Authentication Tab
        with gr.Tab("🔐 Authentication"):
            gr.Markdown("## Register or Login")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Register New Account")
                    reg_email = gr.Textbox(label="Email", placeholder="your@email.com")
                    reg_first_name = gr.Textbox(label="First Name")
                    reg_last_name = gr.Textbox(label="Last Name")
                    register_btn = gr.Button("Register", variant="primary")
                    register_output = gr.Textbox(label="Status", interactive=False)

                with gr.Column():
                    gr.Markdown("### Login (Existing User)")
                    login_email = gr.Textbox(label="Email", placeholder="your@email.com")
                    login_btn = gr.Button("Send Magic Link", variant="primary")
                    login_output = gr.Textbox(label="Status", interactive=False)

            gr.Markdown("### Verify Magic Link")
            magic_token = gr.Textbox(label="Magic Link Token", placeholder="Paste token from email")
            verify_btn = gr.Button("Verify & Login", variant="primary")
            verify_output = gr.Textbox(label="Status", interactive=False)
            user_info = gr.Textbox(label="User Info", interactive=False)

            # Register button
            register_btn.click(
                fn=register_user,
                inputs=[reg_email, reg_first_name, reg_last_name],
                outputs=register_output
            )

            # Login button
            login_btn.click(
                fn=login_user,
                inputs=[login_email],
                outputs=login_output
            )

            # Verify button
            verify_btn.click(
                fn=verify_magic_link,
                inputs=[magic_token],
                outputs=[verify_output, user_info]
            )

        # Document Upload Tab
        with gr.Tab("📄 Upload Documents"):
            gr.Markdown("## Upload Financial Documents")
            gr.Markdown("Supported formats: PDF, Excel (XLSX/XLS), CSV, Word (DOCX)")

            upload_file = gr.File(label="Select Document", file_types=[".pdf", ".xlsx", ".xls", ".csv", ".docx"])
            upload_owner_type = gr.Radio(
                choices=["user", "family_member"],
                value="user",
                label="Upload for"
            )
            upload_password = gr.Textbox(
                label="Password (if document is protected)",
                type="password",
                placeholder="Optional"
            )
            upload_btn = gr.Button("Upload & Process", variant="primary")
            upload_output = gr.Textbox(label="Upload Status", lines=5, interactive=False)

            upload_btn.click(
                fn=upload_document,
                inputs=[upload_file, upload_owner_type, upload_password],
                outputs=upload_output
            )

        # AI Chat Tab
        with gr.Tab("💬 AI Chat"):
            gr.Markdown("## Chat with Your Financial Documents")

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### AI Provider Configuration")
                    gr.Markdown("**Note:** API keys are NOT stored. Enter them each session.")

                    provider_choice = gr.Dropdown(
                        choices=["openai", "azure_openai", "aws_bedrock", "google_gemini"],
                        value="openai",
                        label="AI Provider"
                    )
                    provider_api_key = gr.Textbox(
                        label="API Key",
                        type="password",
                        placeholder="Enter your API key"
                    )
                    provider_endpoint = gr.Textbox(
                        label="Endpoint (Azure OpenAI only)",
                        placeholder="https://your-resource.openai.azure.com/"
                    )
                    provider_model = gr.Textbox(
                        label="Model Name (optional)",
                        placeholder="e.g., gpt-4-turbo-preview"
                    )

                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(label="Conversation", height=400)
                    chat_input = gr.Textbox(
                        label="Ask a question about your documents",
                        placeholder="What is my total investment in mutual funds?",
                        lines=2
                    )
                    chat_btn = gr.Button("Send", variant="primary")

                    chat_history = gr.State([])

            chat_btn.click(
                fn=chat_with_docs,
                inputs=[
                    chat_input,
                    provider_choice,
                    provider_api_key,
                    provider_endpoint,
                    provider_model,
                    chat_history
                ],
                outputs=[chatbot, chat_history]
            )

        # Dashboard Tab
        with gr.Tab("📊 Dashboard"):
            gr.Markdown("## WrenAI Analytics Dashboard")
            gr.Markdown(f"**Dashboard URL:** [{WRENAI_URL}]({WRENAI_URL})")
            gr.Markdown("""
            ### Features:
            - 📈 Spend Analysis
            - 💼 Portfolio Tracking
            - 📊 Performance Review
            - 🔍 Detailed Search
            - 📰 Latest News

            Click the link above to access your personalized financial dashboard.
            """)

            gr.HTML(f'<iframe src="{WRENAI_URL}" width="100%" height="800px" frameborder="0"></iframe>')

    gr.Markdown("---")
    gr.Markdown("Built with ❤️ | All data is encrypted and secure | PII/PHI protected")


if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
