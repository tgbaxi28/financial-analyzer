"""
Multi-provider LLM abstraction layer.
Unified interface for Azure AI, Google Gemini, and AWS Bedrock.
Credentials are passed at runtime (NOT stored).
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ProviderCredentials:
    """Container for provider-specific credentials (runtime only, not stored)."""
    provider: str  # "azure", "google", "aws"
    credentials: Dict[str, str]
    model: str


@dataclass
class LLMResponse:
    """Standardized LLM response format."""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    error: Optional[str] = None


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, credentials: ProviderCredentials):
        self.credentials = credentials
        self.provider = credentials.provider
        self.model = credentials.model

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Test connection and validate credentials."""
        pass

    @abstractmethod
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text."""
        pass

    @abstractmethod
    def generate_chat_response(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> LLMResponse:
        """Generate chat response with context."""
        pass

    @abstractmethod
    def generate_bi_analysis(
        self,
        analysis_type: str,
        data_context: str,
        parameters: Dict[str, Any],
    ) -> LLMResponse:
        """Generate BI analysis based on type and context."""
        pass


class AzureAIProvider(BaseLLMProvider):
    """Azure OpenAI provider implementation."""

    def __init__(self, credentials: ProviderCredentials):
        super().__init__(credentials)
        try:
            from azure.identity import DefaultAzureCredential
            from openai import AzureOpenAI
            self.AzureOpenAI = AzureOpenAI
            self.client = None
        except ImportError:
            raise ImportError("azure-openai package required for Azure provider")

    def validate_credentials(self) -> bool:
        """Validate Azure credentials."""
        try:
            creds = self.credentials.credentials
            required_fields = ["api_key", "endpoint"]
            if not all(field in creds for field in required_fields):
                logger.error(f"Missing required Azure fields: {required_fields}")
                return False

            # Initialize client
            self.client = self.AzureOpenAI(
                api_key=creds["api_key"],
                api_version="2024-02-15-preview",
                azure_endpoint=creds["endpoint"],
            )

            # Test with a simple completion
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10,
            )
            logger.info(f"Azure credentials validated successfully")
            return True
        except Exception as e:
            logger.error(f"Azure credential validation failed: {str(e)}")
            return False

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using Azure OpenAI."""
        try:
            if not self.client:
                if not self.validate_credentials():
                    return None

            response = self.client.embeddings.create(
                input=text,
                model="text-embedding-3-small",
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Azure embedding generation failed: {str(e)}")
            return None

    def generate_chat_response(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> LLMResponse:
        """Generate chat response using Azure OpenAI."""
        try:
            if not self.client:
                if not self.validate_credentials():
                    return LLMResponse(
                        content="",
                        model=self.model,
                        provider=self.provider,
                        error="Failed to validate Azure credentials",
                    )

            messages = []

            # Add system prompt
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)

            # Add context and current query
            messages.append(
                {
                    "role": "system",
                    "content": f"Context from uploaded reports:\n\n{context}",
                }
            )
            messages.append({"role": "user", "content": query})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model,
                provider=self.provider,
                tokens_used=response.usage.total_tokens,
            )
        except Exception as e:
            logger.error(f"Azure chat response generation failed: {str(e)}")
            return LLMResponse(
                content="",
                model=self.model,
                provider=self.provider,
                error=str(e),
            )

    def generate_bi_analysis(
        self,
        analysis_type: str,
        data_context: str,
        parameters: Dict[str, Any],
    ) -> LLMResponse:
        """Generate BI analysis."""
        analysis_prompts = {
            "variance_analysis": "Analyze the variances in the financial data provided",
            "trend_analysis": "Identify trends in the financial metrics",
            "ratio_analysis": "Calculate and interpret key financial ratios",
        }

        prompt = analysis_prompts.get(
            analysis_type, f"Perform {analysis_type} analysis"
        )
        return self.generate_chat_response(prompt, data_context)


class GoogleGeminiProvider(BaseLLMProvider):
    """Google Gemini provider implementation."""

    def __init__(self, credentials: ProviderCredentials):
        super().__init__(credentials)
        try:
            import google.generativeai as genai
            self.genai = genai
            self.client = None
        except ImportError:
            raise ImportError("google-generativeai package required for Google provider")

    def validate_credentials(self) -> bool:
        """Validate Google Gemini credentials."""
        try:
            creds = self.credentials.credentials
            if "api_key" not in creds:
                logger.error("Missing Google API key")
                return False

            self.genai.configure(api_key=creds["api_key"])

            # Test with a simple generation
            model = self.genai.GenerativeModel(self.model)
            response = model.generate_content("test", safety_settings=[])
            logger.info("Google Gemini credentials validated successfully")
            return True
        except Exception as e:
            logger.error(f"Google Gemini credential validation failed: {str(e)}")
            return False

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using Google Generative AI."""
        try:
            creds = self.credentials.credentials
            self.genai.configure(api_key=creds["api_key"])

            result = self.genai.embed_content(
                model="models/embedding-001",
                content=text,
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Google embedding generation failed: {str(e)}")
            return None

    def generate_chat_response(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> LLMResponse:
        """Generate chat response using Google Gemini."""
        try:
            creds = self.credentials.credentials
            self.genai.configure(api_key=creds["api_key"])

            model = self.genai.GenerativeModel(
                self.model,
                system_instruction=system_prompt or "You are a financial analysis expert.",
            )

            # Build conversation history
            chat_history = []
            if conversation_history:
                for msg in conversation_history:
                    chat_history.append(
                        {"role": msg["role"], "parts": [msg["content"]]}
                    )

            chat = model.start_chat(history=chat_history)

            # Send query with context
            full_message = (
                f"Context from uploaded reports:\n\n{context}\n\nQuery: {query}"
            )
            response = chat.send_message(full_message)

            return LLMResponse(
                content=response.text,
                model=self.model,
                provider=self.provider,
            )
        except Exception as e:
            logger.error(f"Google Gemini chat response generation failed: {str(e)}")
            return LLMResponse(
                content="",
                model=self.model,
                provider=self.provider,
                error=str(e),
            )

    def generate_bi_analysis(
        self,
        analysis_type: str,
        data_context: str,
        parameters: Dict[str, Any],
    ) -> LLMResponse:
        """Generate BI analysis."""
        analysis_prompts = {
            "variance_analysis": "Analyze the variances in the financial data provided",
            "trend_analysis": "Identify trends in the financial metrics",
            "ratio_analysis": "Calculate and interpret key financial ratios",
        }

        prompt = analysis_prompts.get(
            analysis_type, f"Perform {analysis_type} analysis"
        )
        return self.generate_chat_response(prompt, data_context)


class AWSBedrockProvider(BaseLLMProvider):
    """AWS Bedrock provider implementation."""

    def __init__(self, credentials: ProviderCredentials):
        super().__init__(credentials)
        try:
            import boto3
            self.boto3 = boto3
            self.bedrock_client = None
            self.bedrock_runtime = None
        except ImportError:
            raise ImportError("boto3 package required for AWS Bedrock provider")

    def validate_credentials(self) -> bool:
        """Validate AWS Bedrock credentials."""
        try:
            creds = self.credentials.credentials
            required_fields = ["access_key", "secret_key", "region"]
            if not all(field in creds for field in required_fields):
                logger.error(f"Missing required AWS fields: {required_fields}")
                return False

            # Initialize Bedrock clients
            self.bedrock_client = self.boto3.client(
                "bedrock",
                region_name=creds["region"],
                aws_access_key_id=creds["access_key"],
                aws_secret_access_key=creds["secret_key"],
            )

            self.bedrock_runtime = self.boto3.client(
                "bedrock-runtime",
                region_name=creds["region"],
                aws_access_key_id=creds["access_key"],
                aws_secret_access_key=creds["secret_key"],
            )

            logger.info("AWS Bedrock credentials validated successfully")
            return True
        except Exception as e:
            logger.error(f"AWS Bedrock credential validation failed: {str(e)}")
            return False

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using Amazon Titan."""
        try:
            if not self.bedrock_runtime:
                if not self.validate_credentials():
                    return None

            response = self.bedrock_runtime.invoke_model(
                modelId="amazon.titan-embed-text-v1",
                body={"inputText": text},
            )

            import json

            result = json.loads(response["body"].read())
            return result["embedding"]
        except Exception as e:
            logger.error(f"AWS embedding generation failed: {str(e)}")
            return None

    def generate_chat_response(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> LLMResponse:
        """Generate chat response using AWS Bedrock."""
        try:
            if not self.bedrock_runtime:
                if not self.validate_credentials():
                    return LLMResponse(
                        content="",
                        model=self.model,
                        provider=self.provider,
                        error="Failed to validate AWS credentials",
                    )

            import json

            # Build messages
            messages = []
            if conversation_history:
                messages.extend(conversation_history)

            messages.append(
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuery: {query}",
                }
            )

            # Model-specific request format (Claude)
            body = {
                "anthropic_version": "bedrock-2023-06-01",
                "max_tokens": 2000,
                "system": system_prompt
                or "You are a financial analysis expert. Answer based on provided context only.",
                "messages": messages,
            }

            response = self.bedrock_runtime.invoke_model(
                modelId=self.model, body=json.dumps(body)
            )

            result = json.loads(response["body"].read())
            content = result["content"][0]["text"]

            return LLMResponse(
                content=content,
                model=self.model,
                provider=self.provider,
            )
        except Exception as e:
            logger.error(f"AWS Bedrock chat response generation failed: {str(e)}")
            return LLMResponse(
                content="",
                model=self.model,
                provider=self.provider,
                error=str(e),
            )

    def generate_bi_analysis(
        self,
        analysis_type: str,
        data_context: str,
        parameters: Dict[str, Any],
    ) -> LLMResponse:
        """Generate BI analysis."""
        analysis_prompts = {
            "variance_analysis": "Analyze the variances in the financial data provided",
            "trend_analysis": "Identify trends in the financial metrics",
            "ratio_analysis": "Calculate and interpret key financial ratios",
        }

        prompt = analysis_prompts.get(
            analysis_type, f"Perform {analysis_type} analysis"
        )
        return self.generate_chat_response(prompt, data_context)


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    PROVIDERS = {
        "azure": AzureAIProvider,
        "google": GoogleGeminiProvider,
        "aws": AWSBedrockProvider,
    }

    @classmethod
    def create_provider(cls, credentials: ProviderCredentials) -> BaseLLMProvider:
        """Create provider instance from credentials."""
        provider_class = cls.PROVIDERS.get(credentials.provider.lower())
        if not provider_class:
            raise ValueError(
                f"Unknown provider: {credentials.provider}. "
                f"Supported: {', '.join(cls.PROVIDERS.keys())}"
            )

        return provider_class(credentials)

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported providers."""
        return list(cls.PROVIDERS.keys())