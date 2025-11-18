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
        async with httpx.AsyncClient(timeout=30.0) as client:
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

    except httpx.ConnectError:
        return f"❌ Cannot connect to backend server at {BACKEND_URL}. Please ensure the backend is running."
    except httpx.TimeoutException:
        return f"❌ Request timed out. Please try again."
    except Exception as e:
        return f"❌ Error: {str(e)}"


async def login_user(email: str) -> str:
    """Request magic link for login."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/auth/login",
                json={"email": email}
            )

            if response.status_code == 200:
                return f"✅ Magic link sent to {email}. Please check your inbox!"
            else:
                return f"❌ Login failed: {response.json().get('detail', 'Unknown error')}"

    except httpx.ConnectError:
        return f"❌ Cannot connect to backend server at {BACKEND_URL}. Please ensure the backend is running."
    except httpx.TimeoutException:
        return f"❌ Request timed out. Please try again."
    except Exception as e:
        return f"❌ Error: {str(e)}"


async def verify_magic_link(token: str):
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
                    f"Logged in as: {data['user']['email']}",
                    gr.update(visible=True),   # Show user info
                    gr.update(visible=True),   # Show logout button
                    gr.update(visible=True),   # Show upload tab
                    gr.update(visible=True),   # Show chat tab
                    gr.update(visible=True)    # Show dashboard tab
                )
            else:
                return (
                    f"❌ Verification failed: {response.json().get('detail', 'Unknown error')}", 
                    "",
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False)
                )

    except Exception as e:
        return (
            f"❌ Error: {str(e)}", 
            "",
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False)
        )


def show_registration_form():
    """Show registration form."""
    return (
        gr.update(visible=False),  # Hide login form    
        gr.update(visible=True)    # Show registration form
    )


def show_login_form():
    """Show login form."""
    return (
        gr.update(visible=True),   # Show login form
        gr.update(visible=False)   # Hide registration form
    )


def logout():
    """Logout user and reset session."""
    session_state["access_token"] = None
    session_state["user"] = None
    session_state["current_owner_id"] = None
    session_state["current_owner_type"] = "user"
    
    return (
        "",  # Clear user info
        gr.update(visible=False),  # Hide user info display
        gr.update(visible=False),  # Hide logout button
        gr.update(visible=False),  # Hide upload tab
        gr.update(visible=False),  # Hide chat tab
        gr.update(visible=False),  # Hide dashboard tab
        gr.update(visible=True),   # Show login form
        gr.update(visible=False)   # Hide registration form
    )


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

    # User info and logout button (initially hidden)
    with gr.Row(visible=False) as user_info_row:
        with gr.Column(scale=5):
            user_info_display = gr.Textbox(label="", interactive=False, show_label=False, container=False)
        with gr.Column(scale=1):
            logout_btn = gr.Button("🚪 Logout", variant="secondary", size="sm")

    # Authentication Section (initially visible)
    with gr.Column(visible=True) as auth_section:
        with gr.Row():
            gr.HTML("<div style='height: 50px;'></div>")  # Spacer
        
        # Login Form (initially visible)
        with gr.Column(visible=True, scale=1) as login_form:
            with gr.Row():
                with gr.Column(scale=1):
                    pass  # Left spacer
                with gr.Column(scale=2):
                    gr.Markdown("## 🔐 Login to Your Account")
                    login_email = gr.Textbox(
                        label="Email Address", 
                        placeholder="your@email.com",
                        type="email"
                    )
                    login_btn = gr.Button("Send Magic Link", variant="primary", size="lg")
                    login_output = gr.Textbox(label="Status", interactive=False, visible=False)
                    
                    # Magic link verification (shown after sending magic link)
                    with gr.Column(visible=False) as magic_link_section:
                        gr.Markdown("### ✉️ Check Your Email")
                        magic_token = gr.Textbox(
                            label="Magic Link Token", 
                            placeholder="Paste the token from your email"
                        )
                        verify_btn = gr.Button("Verify & Login", variant="primary")
                        verify_output = gr.Textbox(label="Status", interactive=False)
                    
                    gr.Markdown("---")
                    with gr.Row():
                        gr.Markdown("Don't have an account?")
                        show_register_btn = gr.Button("Register here", variant="link", size="sm")
                with gr.Column(scale=1):
                    pass  # Right spacer
        
        # Registration Form (initially hidden)
        with gr.Column(visible=False, scale=1) as registration_form:
            with gr.Row():
                with gr.Column(scale=1):
                    pass  # Left spacer
                with gr.Column(scale=2):
                    gr.Markdown("## 📝 Create New Account")
                    reg_email = gr.Textbox(
                        label="Email Address", 
                        placeholder="your@email.com",
                        type="email"
                    )
                    reg_first_name = gr.Textbox(label="First Name", placeholder="John")
                    reg_last_name = gr.Textbox(label="Last Name", placeholder="Doe")
                    register_btn = gr.Button("Register", variant="primary", size="lg")
                    register_output = gr.Textbox(label="Status", interactive=False, visible=False)
                    
                    # Magic link verification (shown after registration)
                    with gr.Column(visible=False) as reg_magic_link_section:
                        gr.Markdown("### ✉️ Check Your Email")
                        reg_magic_token = gr.Textbox(
                            label="Magic Link Token", 
                            placeholder="Paste the token from your email or terminal logs"
                        )
                        reg_verify_btn = gr.Button("Verify & Login", variant="primary")
                        reg_verify_output = gr.Textbox(label="Status", interactive=False)
                    
                    gr.Markdown("---")
                    with gr.Row():
                        gr.Markdown("Already have an account?")
                        show_login_btn = gr.Button("Login here", variant="link", size="sm")
                with gr.Column(scale=1):
                    pass  # Right spacer

    # Main application tabs (initially hidden)
    with gr.Tabs(visible=False) as main_tabs:
        # Document Upload Tab
        with gr.Tab("📄 Upload Documents") as upload_tab:
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
        with gr.Tab("💬 AI Chat") as chat_tab:
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
        with gr.Tab("📊 Dashboard") as dashboard_tab:
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

    # Set up event handlers after all components are defined
    
    # Show registration form
    show_register_btn.click(
        fn=show_registration_form,
        inputs=[],
        outputs=[login_form, registration_form]
    )
    
    # Show login form
    show_login_btn.click(
        fn=show_login_form,
        inputs=[],
        outputs=[login_form, registration_form]
    )
    
    # Register button
    async def handle_registration(email, first_name, last_name):
        """Handle registration and show magic link section."""
        result = await register_user(email, first_name, last_name)
        show_magic = "✅" in result
        return (
            gr.update(value=result, visible=True),
            gr.update(visible=show_magic)
        )
    
    register_btn.click(
        fn=handle_registration,
        inputs=[reg_email, reg_first_name, reg_last_name],
        outputs=[register_output, reg_magic_link_section]
    )

    # Login button
    async def handle_login(email):
        """Handle login and show magic link section."""
        result = await login_user(email)
        show_magic = "✅" in result
        return (
            gr.update(value=result, visible=True),
            gr.update(visible=show_magic)
        )
    
    login_btn.click(
        fn=handle_login,
        inputs=[login_email],
        outputs=[login_output, magic_link_section]
    )
    
    # Verify button - controls visibility
    verify_btn.click(
        fn=verify_magic_link,
        inputs=[magic_token],
        outputs=[verify_output, user_info_display, user_info_row, user_info_row, main_tabs, main_tabs, main_tabs]
    ).then(
        fn=lambda: gr.update(visible=False),
        inputs=[],
        outputs=[auth_section]
    )
    
    # Registration verify button - same functionality
    reg_verify_btn.click(
        fn=verify_magic_link,
        inputs=[reg_magic_token],
        outputs=[reg_verify_output, user_info_display, user_info_row, user_info_row, main_tabs, main_tabs, main_tabs]
    ).then(
        fn=lambda: gr.update(visible=False),
        inputs=[],
        outputs=[auth_section]
    )
    
    # Logout button click handler
    logout_btn.click(
        fn=logout,
        inputs=[],
        outputs=[user_info_display, user_info_row, user_info_row, main_tabs, main_tabs, main_tabs, login_form, registration_form]
    ).then(
        fn=lambda: gr.update(visible=True),
        inputs=[],
        outputs=[auth_section]
    )

    gr.Markdown("---")
    gr.Markdown("Built with ❤️ | All data is encrypted and secure | PII/PHI protected")


if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
