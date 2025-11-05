"""
Agent configuration and management.
"""

from typing import Dict, Optional
from dataclasses import dataclass
import json
from pathlib import Path

from utils.logger import get_logger

logger = get_logger("agent_config")


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    description: str
    enabled: bool = True
    max_iterations: int = 10
    temperature: float = 0.7
    tools: list = None
    system_prompt: str = ""
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []


class AgentConfigManager:
    """Manages agent configurations."""
    
    DEFAULT_CONFIGS = {
        "document_analysis": AgentConfig(
            name="document_analysis",
            description="Analyzes financial documents and extracts key information",
            enabled=True,
            max_iterations=10,
            temperature=0.7,
            system_prompt="""You are a Document Analysis Agent specialized in financial documents.
Your role is to search, extract, and analyze information from financial documents."""
        ),
        "financial_metrics": AgentConfig(
            name="financial_metrics",
            description="Calculates financial ratios and metrics from financial data",
            enabled=True,
            max_iterations=8,
            temperature=0.5,
            system_prompt="""You are a Financial Metrics Agent specialized in calculating and interpreting financial ratios.
Your role is to calculate key financial ratios and provide interpretations."""
        ),
        "trend_analysis": AgentConfig(
            name="trend_analysis",
            description="Analyzes trends and patterns in financial data over time",
            enabled=True,
            max_iterations=8,
            temperature=0.6,
            system_prompt="""You are a Trend Analysis Agent specialized in identifying patterns in financial data.
Your role is to identify trends, compare periods, and detect anomalies."""
        ),
        "query_router": AgentConfig(
            name="query_router",
            description="Routes user queries to the most appropriate specialized agent",
            enabled=True,
            max_iterations=5,
            temperature=0.3,
            system_prompt="""You are a Query Router Agent that analyzes user questions and routes them to specialized agents.
Your role is to understand query intent and select the best agent."""
        ),
    }
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize agent config manager.
        
        Args:
            config_file: Optional path to config file
        """
        self.config_file = config_file or Path("config/agents.json")
        self.configs = self._load_configs()
        
    def _load_configs(self) -> Dict[str, AgentConfig]:
        """Load configurations from file or use defaults."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                
                configs = {}
                for name, config_data in data.items():
                    configs[name] = AgentConfig(**config_data)
                
                logger.info(f"Loaded {len(configs)} agent configs from {self.config_file}")
                return configs
                
            except Exception as e:
                logger.error(f"Error loading config file: {e}, using defaults")
                return self.DEFAULT_CONFIGS.copy()
        else:
            logger.info("No config file found, using defaults")
            return self.DEFAULT_CONFIGS.copy()
    
    def save_configs(self):
        """Save configurations to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {}
            for name, config in self.configs.items():
                data[name] = {
                    "name": config.name,
                    "description": config.description,
                    "enabled": config.enabled,
                    "max_iterations": config.max_iterations,
                    "temperature": config.temperature,
                    "tools": config.tools,
                    "system_prompt": config.system_prompt,
                }
            
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved agent configs to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error saving configs: {e}")
    
    def get_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get configuration for an agent."""
        return self.configs.get(agent_name)
    
    def update_config(self, agent_name: str, **kwargs):
        """Update configuration for an agent."""
        if agent_name in self.configs:
            config = self.configs[agent_name]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            logger.info(f"Updated config for {agent_name}")
        else:
            logger.warning(f"Agent {agent_name} not found in configs")
    
    def enable_agent(self, agent_name: str):
        """Enable an agent."""
        self.update_config(agent_name, enabled=True)
    
    def disable_agent(self, agent_name: str):
        """Disable an agent."""
        self.update_config(agent_name, enabled=False)
    
    def get_enabled_agents(self) -> Dict[str, AgentConfig]:
        """Get all enabled agents."""
        return {
            name: config
            for name, config in self.configs.items()
            if config.enabled
        }
