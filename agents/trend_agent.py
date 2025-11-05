"""
Trend Analysis Agent - Identifies trends and patterns in financial data.
"""

from typing import Any, List
from llama_index.core.tools import FunctionTool
import statistics

from .base_agent import BaseFinancialAgent
from utils.logger import get_logger

logger = get_logger("agent.trend_analysis")


class TrendAnalysisAgent(BaseFinancialAgent):
    """Agent specialized in identifying financial trends and patterns."""

    def __init__(self, llm: Any):
        """
        Initialize trend analysis agent.
        
        Args:
            llm: LlamaIndex LLM instance
        """
        tools = self._create_tools()
        
        super().__init__(
            name="trend_analysis",
            description="Analyzes trends and patterns in financial data over time",
            llm=llm,
            tools=tools,
        )

    def _create_tools(self) -> List[FunctionTool]:
        """Create tools for trend analysis."""
        
        def analyze_growth_trend(values: List[float], periods: List[str]) -> str:
            """
            Analyze growth trend from time series data.
            
            Args:
                values: List of values over time
                periods: List of period labels
                
            Returns:
                Trend analysis
            """
            logger.info(f"Analyzing growth trend for {len(values)} periods")
            
            if len(values) < 2:
                return "Insufficient data for trend analysis (need at least 2 periods)"
            
            results = []
            
            # Calculate period-over-period growth
            growth_rates = []
            for i in range(1, len(values)):
                if values[i-1] != 0:
                    growth = ((values[i] - values[i-1]) / values[i-1]) * 100
                    growth_rates.append(growth)
                    results.append(f"{periods[i-1]} → {periods[i]}: {growth:+.2f}%")
            
            # Calculate average growth
            if growth_rates:
                avg_growth = statistics.mean(growth_rates)
                results.append(f"\nAverage Growth Rate: {avg_growth:+.2f}%")
                
                # Trend direction
                if avg_growth > 5:
                    results.append("Trend: Strong Growth 📈")
                elif avg_growth > 0:
                    results.append("Trend: Moderate Growth ↗️")
                elif avg_growth > -5:
                    results.append("Trend: Slight Decline ↘️")
                else:
                    results.append("Trend: Significant Decline 📉")
            
            return "\n".join(results)
        
        def compare_periods(
            current_value: float,
            previous_value: float,
            metric_name: str
        ) -> str:
            """
            Compare two periods for a specific metric.
            
            Args:
                current_value: Current period value
                previous_value: Previous period value
                metric_name: Name of the metric
                
            Returns:
                Comparison analysis
            """
            logger.info(f"Comparing periods for {metric_name}")
            
            if previous_value == 0:
                return f"{metric_name}: Cannot calculate change (previous value is zero)"
            
            change = current_value - previous_value
            pct_change = (change / previous_value) * 100
            
            results = [
                f"{metric_name} Analysis:",
                f"  Current: {current_value:,.2f}",
                f"  Previous: {previous_value:,.2f}",
                f"  Change: {change:+,.2f}",
                f"  % Change: {pct_change:+.2f}%",
            ]
            
            return "\n".join(results)
        
        def identify_variance(
            actual: float,
            budget: float,
            metric_name: str,
            threshold_pct: float = 10.0
        ) -> str:
            """
            Identify variance between actual and budget/forecast.
            
            Args:
                actual: Actual value
                budget: Budgeted/forecasted value
                metric_name: Name of the metric
                threshold_pct: Variance threshold for flagging
                
            Returns:
                Variance analysis
            """
            logger.info(f"Analyzing variance for {metric_name}")
            
            if budget == 0:
                return f"{metric_name}: Cannot calculate variance (budget is zero)"
            
            variance = actual - budget
            variance_pct = (variance / budget) * 100
            
            results = [
                f"{metric_name} Variance Analysis:",
                f"  Actual: {actual:,.2f}",
                f"  Budget: {budget:,.2f}",
                f"  Variance: {variance:+,.2f}",
                f"  Variance %: {variance_pct:+.2f}%",
            ]
            
            # Flag significant variances
            if abs(variance_pct) > threshold_pct:
                if variance_pct > 0:
                    results.append(f"  ⚠️  Favorable variance exceeds {threshold_pct}%")
                else:
                    results.append(f"  🚨 Unfavorable variance exceeds {threshold_pct}%")
            else:
                results.append(f"  ✓ Within acceptable range (±{threshold_pct}%)")
            
            return "\n".join(results)
        
        def seasonal_analysis(
            q1: float, q2: float, q3: float, q4: float,
            metric_name: str
        ) -> str:
            """
            Analyze seasonal patterns in quarterly data.
            
            Args:
                q1: Q1 value
                q2: Q2 value
                q3: Q3 value
                q4: Q4 value
                metric_name: Name of the metric
                
            Returns:
                Seasonal analysis
            """
            logger.info(f"Analyzing seasonal patterns for {metric_name}")
            
            quarters = [q1, q2, q3, q4]
            avg = statistics.mean(quarters)
            
            results = [
                f"{metric_name} Seasonal Analysis:",
                f"  Q1: {q1:,.2f} ({((q1/avg - 1) * 100):+.1f}% vs avg)",
                f"  Q2: {q2:,.2f} ({((q2/avg - 1) * 100):+.1f}% vs avg)",
                f"  Q3: {q3:,.2f} ({((q3/avg - 1) * 100):+.1f}% vs avg)",
                f"  Q4: {q4:,.2f} ({((q4/avg - 1) * 100):+.1f}% vs avg)",
                f"  Average: {avg:,.2f}",
            ]
            
            # Identify peak quarter
            max_q = max(enumerate(quarters, 1), key=lambda x: x[1])
            min_q = min(enumerate(quarters, 1), key=lambda x: x[1])
            
            results.append(f"  Peak Quarter: Q{max_q[0]}")
            results.append(f"  Lowest Quarter: Q{min_q[0]}")
            
            return "\n".join(results)
        
        return [
            FunctionTool.from_defaults(fn=analyze_growth_trend),
            FunctionTool.from_defaults(fn=compare_periods),
            FunctionTool.from_defaults(fn=identify_variance),
            FunctionTool.from_defaults(fn=seasonal_analysis),
        ]

    def get_system_prompt(self) -> str:
        """Return system prompt for trend agent."""
        return """You are a Trend Analysis Agent specialized in identifying patterns in financial data.

Your role is to:
1. Identify growth trends over time
2. Compare periods (YoY, QoQ, MoM)
3. Analyze variances between actual and budget/forecast
4. Detect seasonal patterns
5. Flag significant changes and anomalies

You have access to tools for:
- Growth trend analysis
- Period comparison
- Variance analysis
- Seasonal pattern detection

Always provide context for the trends you identify.
Explain what the trends might indicate about business performance."""
