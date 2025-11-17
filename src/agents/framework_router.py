"""Framework Router - Routes to framework-specific specialists."""

from typing import Dict, Optional
from langchain_openai import ChatOpenAI

from ..utils.config import config
from ..utils.mvk_tracker import tracker
from ..tools.tavily_search import tavily_search
from ..prompts import FRAMEWORK_SPECIALIST_PROMPT


class FrameworkSpecialist:
    """Specialist for a specific framework."""

    def __init__(self, framework_name: str):
        """
        Initialize framework specialist.

        Args:
            framework_name: Name of the framework (langchain, llamaindex, etc.)
        """
        self.framework_name = framework_name
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE_FRAMEWORK,
            openai_api_key=config.OPENAI_API_KEY
        )

    def query(self, question: str) -> Dict[str, any]:
        """
        Query framework-specific information.

        Args:
            question: User's question

        Returns:
            Dictionary with answer and sources
        """
        agent_name = f"framework_specialist.{self.framework_name}"

        with tracker.track_agent(agent_name, "web_search_query"):
            try:
                # Perform Tavily search
                with tracker.track_tool("tavily_search", f"search_{self.framework_name}"):
                    search_results = tavily_search.search_framework(
                        framework_name=self.framework_name,
                        query=question,
                        max_results=3
                    )

                if not search_results:
                    return {
                        "answer": f"⚠️ Couldn't find information about {self.framework_name}. Web search quota may be exceeded.",
                        "sources": [],
                        "success": False
                    }

                # Build context from search results
                context = tavily_search.get_combined_context(search_results)

                # Generate answer using LLM
                with tracker.track_tool("llm_synthesis", f"synthesize_{self.framework_name}"):
                    prompt = FRAMEWORK_SPECIALIST_PROMPT.format(
                        framework_name=self.framework_name.capitalize(),
                        search_results=context,
                        question=question
                    )

                    response = self.llm.invoke([
                        {"role": "system", "content": f"You are a {self.framework_name} expert."},
                        {"role": "user", "content": prompt}
                    ])

                    answer = response.content

                # Extract sources
                sources = [
                    {
                        "title": result["title"],
                        "url": result["url"],
                        "score": result.get("score", 0.0)
                    }
                    for result in search_results
                ]

                # Track metrics
                tracker.track_metric(f"framework_specialist.{self.framework_name}.queries", 1, "query")

                return {
                    "answer": answer,
                    "sources": sources,
                    "framework": self.framework_name,
                    "success": True
                }

            except Exception as e:
                print(f"❌ Framework Specialist ({self.framework_name}) error: {e}")
                tracker.track_metric(f"framework_specialist.{self.framework_name}.errors", 1, "error")

                return {
                    "answer": f"❌ Error querying {self.framework_name} information: {str(e)}",
                    "sources": [],
                    "framework": self.framework_name,
                    "success": False
                }


class FrameworkRouter:
    """Routes queries to appropriate framework specialists."""

    def __init__(self):
        """Initialize framework router with specialists."""
        self.specialists = {
            "langchain": FrameworkSpecialist("langchain"),
            "llamaindex": FrameworkSpecialist("llamaindex"),
            "crewai": FrameworkSpecialist("crewai"),
            "autogen": FrameworkSpecialist("autogen"),
            "haystack": FrameworkSpecialist("haystack"),
            "generic": FrameworkSpecialist("generic")
        }

    def query(self, question: str, framework: Optional[str] = None) -> Dict[str, any]:
        """
        Route query to appropriate framework specialist.

        Args:
            question: User's question
            framework: Framework name (if None, uses generic)

        Returns:
            Dictionary with answer and sources
        """
        with tracker.track_agent("framework_router", "route_query"):
            # Normalize framework name
            framework = (framework or "generic").lower()

            # Get specialist (fallback to generic)
            specialist = self.specialists.get(framework, self.specialists["generic"])

            # Query specialist
            result = specialist.query(question)

            # Track routing
            tracker.track_metric(f"framework_router.routed_to_{framework}", 1, "route")

            return result

    def get_supported_frameworks(self) -> list[str]:
        """Get list of supported frameworks."""
        return list(self.specialists.keys())


# Export singleton instance
framework_router = FrameworkRouter()
