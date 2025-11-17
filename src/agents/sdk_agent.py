"""SDK Agent - RAG-based MVK SDK documentation query."""

from typing import Dict, List, Optional
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.schema import Document

from ..utils.config import config
from ..utils.mvk_tracker import tracker
from ..tools.chromadb_manager import chromadb_manager
from ..prompts import SDK_AGENT_PROMPT


class SDKAgent:
    """Agent for querying MVK SDK documentation."""

    def __init__(self):
        """Initialize SDK Agent."""
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE_SDK,
            openai_api_key=config.OPENAI_API_KEY
        )

        self.vectorstore = chromadb_manager.vectorstore

    def query(self, question: str) -> Dict[str, any]:
        """
        Query MVK SDK documentation.

        Args:
            question: User's SDK-related question

        Returns:
            Dictionary with answer and sources
        """
        with tracker.track_agent("sdk_agent", "rag_query"):
            try:
                # Check if ChromaDB is indexed
                if not chromadb_manager.is_indexed():
                    return {
                        "answer": "⚠️ Documentation not yet indexed. Please wait for indexing to complete.",
                        "sources": [],
                        "success": False
                    }

                # Retrieve relevant documents
                with tracker.track_tool("chromadb_search", "similarity_search"):
                    docs = chromadb_manager.search(question, k=config.TOP_K_RESULTS)

                if not docs:
                    return {
                        "answer": "I couldn't find relevant information in the MVK SDK documentation for this question.",
                        "sources": [],
                        "success": False
                    }

                # Build context from retrieved documents
                context = self._build_context(docs)

                # Generate answer using LLM
                with tracker.track_tool("llm_generation", "generate_answer"):
                    prompt = SDK_AGENT_PROMPT.format(
                        context=context,
                        question=question
                    )

                    response = self.llm.invoke([
                        {"role": "system", "content": "You are an MVK SDK expert assistant."},
                        {"role": "user", "content": prompt}
                    ])

                    answer = response.content

                # Extract sources
                sources = self._extract_sources(docs)

                # Track metrics
                tracker.track_metric("sdk_agent.queries", 1, "query")

                return {
                    "answer": answer,
                    "sources": sources,
                    "success": True
                }

            except Exception as e:
                print(f"❌ SDK Agent error: {e}")
                tracker.track_metric("sdk_agent.errors", 1, "error")

                return {
                    "answer": f"❌ Error querying SDK documentation: {str(e)}",
                    "sources": [],
                    "success": False
                }

    def _build_context(self, docs: List[Document]) -> str:
        """Build context string from retrieved documents."""
        context = ""
        for i, doc in enumerate(docs, 1):
            page = doc.metadata.get("page", "?")
            content = doc.page_content.strip()
            context += f"[Source {i} - Page {page}]\n{content}\n\n"

        return context

    def _extract_sources(self, docs: List[Document]) -> List[Dict[str, any]]:
        """Extract source metadata from documents."""
        sources = []
        for doc in docs:
            sources.append({
                "page": doc.metadata.get("page", "?"),
                "source": doc.metadata.get("source", "mvk_sdk_documentation.pdf"),
                "content_preview": doc.page_content[:150] + "..."
            })

        return sources

    def get_stats(self) -> Dict[str, any]:
        """Get SDK Agent statistics."""
        return {
            "chromadb_indexed": chromadb_manager.is_indexed(),
            "document_count": chromadb_manager.get_document_count(),
            "model": config.LLM_MODEL,
            "temperature": config.LLM_TEMPERATURE_SDK
        }


# Export singleton instance
sdk_agent = SDKAgent()
