"""ChromaDB vector store management."""

import os
from typing import List, Optional
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from ..utils.config import config


class ChromaDBManager:
    """Manage ChromaDB vector store operations."""

    def __init__(self):
        """Initialize ChromaDB manager."""
        self.collection_name = config.CHROMA_COLLECTION
        self.persist_directory = config.CHROMA_PERSIST_DIR

        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            model=config.EMBEDDING_MODEL,
            openai_api_key=config.OPENAI_API_KEY
        )

        # Create persist directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)

        # Load or initialize vector store
        self._vectorstore = None

    @property
    def vectorstore(self) -> Chroma:
        """Get or initialize vector store."""
        if self._vectorstore is None:
            # Try to load existing vector store
            if os.path.exists(os.path.join(self.persist_directory, "chroma.sqlite3")):
                print(
                    f"📂 Loading existing ChromaDB from {self.persist_directory}...")
                self._vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=self.persist_directory
                )
                count = self._vectorstore._collection.count()
                print(f"✅ Loaded ChromaDB with {count} documents")
            else:
                # Create empty vector store
                print(
                    f"🆕 Creating new ChromaDB at {self.persist_directory}...")
                self._vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=self.persist_directory
                )
                print("✅ Created empty ChromaDB")

        return self._vectorstore

    def index_documents(self, documents: List[Document]) -> None:
        """
        Index documents into ChromaDB.

        Args:
            documents: List of Document chunks to index
        """
        if not documents:
            print("⚠️  No documents to index")
            return

        print(f"🔄 Indexing {len(documents)} documents into ChromaDB...")

        # Create embeddings and store (auto-tracked by MVK SDK with vectordb wrapper)
        self._vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=self.collection_name,
            persist_directory=self.persist_directory
        )

        # ChromaDB auto-persists in newer versions (>= 0.4.0)

        count = self._vectorstore._collection.count()
        print(f"✅ Indexed {count} documents in ChromaDB")

    def search(self, query: str, k: int = None) -> List[Document]:
        """
        Similarity search in ChromaDB.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of relevant Documents
        """
        k = k or config.TOP_K_RESULTS

        # Perform search (auto-tracked by MVK SDK with vectordb wrapper)
        results = self.vectorstore.similarity_search(query, k=k)

        return results

    def search_with_score(self, query: str, k: int = None) -> List[tuple[Document, float]]:
        """
        Similarity search with relevance scores.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of (Document, score) tuples
        """
        k = k or config.TOP_K_RESULTS

        # Perform search with score (auto-tracked by MVK SDK)
        results = self.vectorstore.similarity_search_with_score(query, k=k)

        return results

    def is_indexed(self) -> bool:
        """Check if documents are indexed."""
        try:
            count = self.vectorstore._collection.count()
            return count > 0
        except Exception:
            return False

    def get_document_count(self) -> int:
        """Get total number of indexed documents."""
        try:
            return self.vectorstore._collection.count()
        except Exception:
            return 0

    def get_stats(self) -> dict:
        """Get ChromaDB statistics."""
        return {
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "document_count": self.get_document_count(),
            "is_indexed": self.is_indexed(),
        }


# Export singleton instance
chromadb_manager = ChromaDBManager()
