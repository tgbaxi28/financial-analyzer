"""
LlamaIndex LLM adapter for multi-provider support.
Adapts the existing LLM providers to work with LlamaIndex.
"""

from typing import Any
from llama_index.llms.azure_openai import AzureOpenAI as LlamaIndexAzureOpenAI
from llama_index.llms.bedrock import Bedrock as LlamaIndexBedrock
from llama_index.llms.gemini import Gemini as LlamaIndexGemini

from llm_providers import ProviderCredentials
from utils.logger import get_logger

logger = get_logger("llm_adapter")


class LLMAdapter:
    """Adapter to convert provider credentials to LlamaIndex LLM instances."""

    @staticmethod
    def create_llm(credentials: ProviderCredentials) -> Any:
        """
        Create LlamaIndex LLM from provider credentials.
        
        Args:
            credentials: Provider credentials
            
        Returns:
            LlamaIndex LLM instance
        """
        provider = credentials.provider.lower()
        creds = credentials.credentials
        model = credentials.model
        
        logger.info(f"Creating LlamaIndex LLM for provider: {provider}, model: {model}")
        
        try:
            if provider == "azure":
                return LlamaIndexAzureOpenAI(
                    model=model,
                    api_key=creds.get("api_key"),
                    azure_endpoint=creds.get("endpoint"),
                    api_version="2024-02-15-preview",
                    temperature=0.7,
                )
            
            elif provider == "google":
                return LlamaIndexGemini(
                    model=model,
                    api_key=creds.get("api_key"),
                    temperature=0.7,
                )
            
            elif provider == "aws":
                return LlamaIndexBedrock(
                    model=model,
                    aws_access_key_id=creds.get("access_key"),
                    aws_secret_access_key=creds.get("secret_key"),
                    region_name=creds.get("region", "us-east-1"),
                    temperature=0.7,
                )
            
            else:
                logger.error(f"Unsupported provider: {provider}")
                raise ValueError(f"Unsupported provider: {provider}")
        
        except Exception as e:
            logger.error(f"Error creating LLM adapter: {e}", exc_info=True)
            raise

    @staticmethod
    def get_embedding_model(credentials: ProviderCredentials) -> Any:
        """
        Create embedding model from provider credentials.
        
        Args:
            credentials: Provider credentials
            
        Returns:
            Embedding model instance
        """
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
        
        provider = credentials.provider.lower()
        creds = credentials.credentials
        
        logger.info(f"Creating embedding model for provider: {provider}")
        
        try:
            if provider == "azure":
                return AzureOpenAIEmbedding(
                    model="text-embedding-3-small",
                    api_key=creds.get("api_key"),
                    azure_endpoint=creds.get("endpoint"),
                    api_version="2024-02-15-preview",
                )
            
            elif provider == "google":
                # Google uses their own embedding model
                return OpenAIEmbedding(
                    model="models/embedding-001",
                    api_key=creds.get("api_key"),
                )
            
            elif provider == "aws":
                # AWS Bedrock uses Titan embeddings
                return OpenAIEmbedding(
                    model="amazon.titan-embed-text-v1",
                )
            
            else:
                logger.error(f"Unsupported provider for embeddings: {provider}")
                raise ValueError(f"Unsupported provider: {provider}")
        
        except Exception as e:
            logger.error(f"Error creating embedding model: {e}", exc_info=True)
            raise
