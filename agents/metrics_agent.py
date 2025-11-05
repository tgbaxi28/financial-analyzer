"""
Financial Metrics Agent - Calculates and analyzes financial metrics and ratios.
"""

from typing import Any, List
from llama_index.core.tools import FunctionTool

from .base_agent import BaseFinancialAgent
from utils.logger import get_logger

logger = get_logger("agent.financial_metrics")


class FinancialMetricsAgent(BaseFinancialAgent):
    """Agent specialized in calculating financial metrics and ratios."""

    def __init__(self, llm: Any):
        """
        Initialize financial metrics agent.
        
        Args:
            llm: LlamaIndex LLM instance
        """
        tools = self._create_tools()
        
        super().__init__(
            name="financial_metrics",
            description="Calculates financial ratios and metrics from financial data",
            llm=llm,
            tools=tools,
        )

    def _create_tools(self) -> List[FunctionTool]:
        """Create tools for financial calculations."""
        
        def calculate_ratio(
            numerator: float,
            denominator: float,
            ratio_name: str = "custom"
        ) -> str:
            """
            Calculate a financial ratio.
            
            Args:
                numerator: Numerator value
                denominator: Denominator value
                ratio_name: Name of the ratio
                
            Returns:
                Calculated ratio with interpretation
            """
            logger.info(f"Calculating {ratio_name}: {numerator}/{denominator}")
            
            if denominator == 0:
                return f"Cannot calculate {ratio_name}: denominator is zero"
            
            ratio = numerator / denominator
            return f"{ratio_name}: {ratio:.2f}"
        
        def calculate_liquidity_ratios(
            current_assets: float,
            current_liabilities: float,
            cash: float,
            inventory: float
        ) -> str:
            """
            Calculate liquidity ratios.
            
            Args:
                current_assets: Current assets value
                current_liabilities: Current liabilities value
                cash: Cash and equivalents
                inventory: Inventory value
                
            Returns:
                Liquidity ratio analysis
            """
            logger.info("Calculating liquidity ratios")
            
            results = []
            
            # Current Ratio
            if current_liabilities > 0:
                current_ratio = current_assets / current_liabilities
                results.append(f"Current Ratio: {current_ratio:.2f}")
                
                # Interpretation
                if current_ratio < 1.0:
                    results.append("  → Low liquidity risk")
                elif current_ratio < 1.5:
                    results.append("  → Moderate liquidity")
                else:
                    results.append("  → Strong liquidity")
            
            # Quick Ratio (Acid Test)
            if current_liabilities > 0:
                quick_assets = current_assets - inventory
                quick_ratio = quick_assets / current_liabilities
                results.append(f"Quick Ratio: {quick_ratio:.2f}")
            
            # Cash Ratio
            if current_liabilities > 0:
                cash_ratio = cash / current_liabilities
                results.append(f"Cash Ratio: {cash_ratio:.2f}")
            
            return "\n".join(results)
        
        def calculate_profitability_ratios(
            net_income: float,
            revenue: float,
            total_assets: float,
            shareholders_equity: float
        ) -> str:
            """
            Calculate profitability ratios.
            
            Args:
                net_income: Net income
                revenue: Total revenue
                total_assets: Total assets
                shareholders_equity: Total shareholders equity
                
            Returns:
                Profitability analysis
            """
            logger.info("Calculating profitability ratios")
            
            results = []
            
            # Net Profit Margin
            if revenue > 0:
                npm = (net_income / revenue) * 100
                results.append(f"Net Profit Margin: {npm:.2f}%")
            
            # Return on Assets (ROA)
            if total_assets > 0:
                roa = (net_income / total_assets) * 100
                results.append(f"Return on Assets (ROA): {roa:.2f}%")
            
            # Return on Equity (ROE)
            if shareholders_equity > 0:
                roe = (net_income / shareholders_equity) * 100
                results.append(f"Return on Equity (ROE): {roe:.2f}%")
            
            return "\n".join(results)
        
        def calculate_leverage_ratios(
            total_debt: float,
            total_assets: float,
            total_equity: float,
            ebit: float,
            interest_expense: float
        ) -> str:
            """
            Calculate leverage/solvency ratios.
            
            Args:
                total_debt: Total debt
                total_assets: Total assets
                total_equity: Total equity
                ebit: Earnings before interest and taxes
                interest_expense: Interest expense
                
            Returns:
                Leverage analysis
            """
            logger.info("Calculating leverage ratios")
            
            results = []
            
            # Debt-to-Assets
            if total_assets > 0:
                debt_to_assets = total_debt / total_assets
                results.append(f"Debt-to-Assets: {debt_to_assets:.2f}")
            
            # Debt-to-Equity
            if total_equity > 0:
                debt_to_equity = total_debt / total_equity
                results.append(f"Debt-to-Equity: {debt_to_equity:.2f}")
            
            # Interest Coverage
            if interest_expense > 0:
                interest_coverage = ebit / interest_expense
                results.append(f"Interest Coverage: {interest_coverage:.2f}x")
            
            return "\n".join(results)
        
        return [
            FunctionTool.from_defaults(fn=calculate_ratio),
            FunctionTool.from_defaults(fn=calculate_liquidity_ratios),
            FunctionTool.from_defaults(fn=calculate_profitability_ratios),
            FunctionTool.from_defaults(fn=calculate_leverage_ratios),
        ]

    def get_system_prompt(self) -> str:
        """Return system prompt for metrics agent."""
        return """You are a Financial Metrics Agent specialized in calculating and interpreting financial ratios.

Your role is to:
1. Calculate key financial ratios (liquidity, profitability, leverage, efficiency)
2. Interpret what the ratios mean for financial health
3. Compare ratios against industry benchmarks
4. Identify trends in ratio changes over time

You have access to tools to calculate:
- Liquidity ratios (current, quick, cash)
- Profitability ratios (ROA, ROE, profit margins)
- Leverage ratios (debt-to-equity, interest coverage)
- Custom ratios as needed

Always provide interpretation along with the numbers.
Use industry context when available."""
