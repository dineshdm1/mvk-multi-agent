"""MVK SDK tracking utilities."""

import uuid
from contextlib import contextmanager
from typing import Optional, Dict, Any
import mvk_sdk as mvk
from mvk_sdk import Metric

from .config import config


class MVKTracker:
    """Wrapper for MVK SDK tracking."""

    def __init__(self):
        """Initialize MVK SDK."""
        # Initialize MVK SDK with configuration
        mvk.instrument(
            wrappers={"include": ["genai"]},
            agent_id=config.MVK_AGENT_ID,
            api_key=config.MVK_API_KEY,
        )

    @staticmethod
    def create_session_id() -> str:
        """
        Create a new session_id for entire user journey.

        Returns:
            UUID string for session_id
        """
        return f"session_{uuid.uuid4().hex[:16]}"

    @staticmethod
    def create_conversation_id() -> str:
        """
        Create a new conversation_id for individual query.

        Returns:
            UUID string for conversation_id
        """
        return f"conv_{uuid.uuid4().hex[:12]}"

    @staticmethod
    @contextmanager
    def track_query(
        user_id: str,
        session_id: str,
        conversation_id: str,
        **additional_context
    ):
        """
        Track an entire user query with MVK context.

        Args:
            user_id: Username
            session_id: Entire user journey ID
            conversation_id: Individual query ID
            **additional_context: Additional context attributes
        """
        with mvk.context(
            user_id=user_id,
            session_id=session_id,
            tenant_id=config.MVK_TENANT_ID,
            **additional_context
        ):
            # Add conversation_id as metadata
            with mvk.context(conversation_id=conversation_id):
                yield

    @staticmethod
    @contextmanager
    def track_agent(agent_name: str, operation: str = "execute"):
        """
        Track an agent execution.

        Args:
            agent_name: Name of the agent (e.g., "orchestrator", "sdk_agent")
            operation: Operation being performed
        """
        with mvk.create_signal(
            name=f"agent.{agent_name}",
            step_type="AGENT",
            operation=operation
        ):
            yield

    @staticmethod
    @contextmanager
    def track_tool(tool_name: str, operation: str = "execute"):
        """
        Track a tool execution.

        Args:
            tool_name: Name of the tool (e.g., "chromadb_search", "tavily_search")
            operation: Operation being performed
        """
        with mvk.create_signal(
            name=f"tool.{tool_name}",
            step_type="TOOL",
            operation=operation
        ):
            yield

    @staticmethod
    def track_metric(metric_name: str, value: float, unit: str = "count", metadata: Optional[Dict[str, Any]] = None):
        """
        Track a custom metric.

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            metadata: Optional metadata
        """
        metric_dict = Metric(metric_name, quantity=value, uom=unit).to_dict()

        if metadata:
            metric_dict["metadata"] = metadata

        mvk.add_metered_usage([metric_dict])

    @staticmethod
    def track_feedback(feedback_type: str, value: int = 1):
        """
        Track user feedback.

        Args:
            feedback_type: Type of feedback ("helpful" or "not_helpful")
            value: Feedback value (default 1)
        """
        MVKTracker.track_metric(
            f"feedback.{feedback_type}",
            value=value,
            unit="feedback"
        )

    @staticmethod
    def track_cost(operation: str, estimated_cost: float, currency: str = "USD", provider: str = "openai"):
        """
        Track operation cost.

        Args:
            operation: Operation name
            estimated_cost: Estimated cost in currency
            currency: Currency code
            provider: Service provider
        """
        MVKTracker.track_metric(
            f"cost.{operation}",
            value=1,
            unit="operation",
            metadata={
                "estimated_cost": estimated_cost,
                "currency": currency,
                "provider": provider
            }
        )

    @staticmethod
    def track_latency(operation: str, latency_ms: float):
        """
        Track operation latency.

        Args:
            operation: Operation name
            latency_ms: Latency in milliseconds
        """
        MVKTracker.track_metric(
            f"latency.{operation}",
            value=latency_ms,
            unit="millisecond"
        )


# Export singleton instance
tracker = MVKTracker()
