"""Multi-LLM provider abstraction layer."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import openai
from anthropic import Anthropic
import google.generativeai as genai
import boto3
import json

from app.schemas import AIProviderCredentials
from app.utils.logger import logger


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Generate completion from messages."""
        pass

    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider."""

    def __init__(self, credentials: AIProviderCredentials):
        """Initialize OpenAI client."""
        self.api_key = credentials.api_key
        self.model_name = credentials.model_name or "gpt-4-turbo-preview"
        self.embedding_model = "text-embedding-3-small"

        openai.api_key = self.api_key
        logger.info("OpenAI provider initialized")

    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Generate completion using OpenAI."""
        try:
            response = openai.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return {
                "response": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "model": self.model_name
            }

        except Exception as e:
            logger.error(f"OpenAI completion error: {str(e)}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        try:
            response = openai.embeddings.create(
                model=self.embedding_model,
                input=text
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"OpenAI embedding error: {str(e)}")
            raise


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI provider."""

    def __init__(self, credentials: AIProviderCredentials):
        """Initialize Azure OpenAI client."""
        self.api_key = credentials.api_key
        self.endpoint = credentials.endpoint
        self.model_name = credentials.model_name or "gpt-4"
        self.embedding_model = "text-embedding-ada-002"

        openai.api_type = "azure"
        openai.api_key = self.api_key
        openai.api_base = self.endpoint
        openai.api_version = "2024-02-01"

        logger.info("Azure OpenAI provider initialized")

    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Generate completion using Azure OpenAI."""
        try:
            response = openai.chat.completions.create(
                deployment_id=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return {
                "response": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "model": self.model_name
            }

        except Exception as e:
            logger.error(f"Azure OpenAI completion error: {str(e)}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Azure OpenAI."""
        try:
            response = openai.embeddings.create(
                deployment_id=self.embedding_model,
                input=text
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Azure OpenAI embedding error: {str(e)}")
            raise


class AWSBedrockProvider(BaseLLMProvider):
    """AWS Bedrock provider."""

    def __init__(self, credentials: AIProviderCredentials):
        """Initialize AWS Bedrock client."""
        self.region = credentials.region or "us-east-1"
        self.model_name = credentials.model_name or "anthropic.claude-3-sonnet-20240229-v1:0"

        # Extract AWS credentials from API key (format: access_key:secret_key)
        if ":" in credentials.api_key:
            access_key, secret_key = credentials.api_key.split(":", 1)
        else:
            access_key = credentials.api_key
            secret_key = ""

        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )

        logger.info("AWS Bedrock provider initialized")

    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Generate completion using AWS Bedrock."""
        try:
            # Format for Claude 3
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": temperature
            })

            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_name,
                body=body
            )

            response_body = json.loads(response.get('body').read())

            return {
                "response": response_body.get("content")[0].get("text"),
                "tokens_used": response_body.get("usage", {}).get("total_tokens", 0),
                "model": self.model_name
            }

        except Exception as e:
            logger.error(f"AWS Bedrock completion error: {str(e)}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using AWS Bedrock Titan."""
        try:
            body = json.dumps({
                "inputText": text
            })

            response = self.bedrock_runtime.invoke_model(
                modelId="amazon.titan-embed-text-v1",
                body=body
            )

            response_body = json.loads(response.get('body').read())
            return response_body.get("embedding")

        except Exception as e:
            logger.error(f"AWS Bedrock embedding error: {str(e)}")
            raise


class GoogleGeminiProvider(BaseLLMProvider):
    """Google Gemini provider."""

    def __init__(self, credentials: AIProviderCredentials):
        """Initialize Google Gemini client."""
        self.api_key = credentials.api_key
        self.model_name = credentials.model_name or "gemini-pro"

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

        logger.info("Google Gemini provider initialized")

    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Generate completion using Google Gemini."""
        try:
            # Convert messages to Gemini format
            prompt = self._format_messages(messages)

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )

            return {
                "response": response.text,
                "tokens_used": 0,  # Gemini doesn't provide token count
                "model": self.model_name
            }

        except Exception as e:
            logger.error(f"Google Gemini completion error: {str(e)}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Google Gemini."""
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )

            return result['embedding']

        except Exception as e:
            logger.error(f"Google Gemini embedding error: {str(e)}")
            raise

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Gemini."""
        formatted = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                formatted.append(f"System: {content}")
            elif role == "user":
                formatted.append(f"User: {content}")
            elif role == "assistant":
                formatted.append(f"Assistant: {content}")

        return "\n\n".join(formatted)


class LLMProviderFactory:
    """Factory for creating LLM providers."""

    @staticmethod
    def create_provider(credentials: AIProviderCredentials) -> BaseLLMProvider:
        """
        Create LLM provider based on credentials.

        Args:
            credentials: Provider credentials

        Returns:
            LLM provider instance

        Raises:
            ValueError: If provider not supported
        """
        provider_map = {
            "openai": OpenAIProvider,
            "azure_openai": AzureOpenAIProvider,
            "aws_bedrock": AWSBedrockProvider,
            "google_gemini": GoogleGeminiProvider
        }

        provider_class = provider_map.get(credentials.provider)

        if not provider_class:
            raise ValueError(f"Unsupported provider: {credentials.provider}")

        return provider_class(credentials)
