"""Initialization script for indexing PDF documentation."""

import os
import sys

from utils.config import config
from tools.pdf_ingestion import pdf_ingestor
from tools.chromadb_manager import chromadb_manager


def check_prerequisites() -> bool:
    """
    Check if all prerequisites are met.

    Returns:
        True if all checks pass
    """
    print("🔍 Checking prerequisites...")

    errors = config.validate()

    if errors:
        print("\n❌ Configuration errors:")
        for error in errors:
            print(f"  • {error}")
        print()
        return False

    print("✅ All prerequisites met")
    return True


def index_pdf_if_needed() -> bool:
    """
    Index PDF documentation if not already indexed.

    Returns:
        True if indexing successful or already indexed
    """
    print("\n📚 Checking ChromaDB index status...")

    # Check if already indexed
    if chromadb_manager.is_indexed():
        doc_count = chromadb_manager.get_document_count()
        print(f"✅ ChromaDB already indexed with {doc_count} documents")
        return True

    print("📄 ChromaDB not indexed. Starting PDF ingestion...")

    try:
        # Ingest PDF
        chunks = pdf_ingestor.ingest()

        if not chunks:
            print("❌ No chunks created from PDF")
            return False

        # Index into ChromaDB
        chromadb_manager.index_documents(chunks)

        doc_count = chromadb_manager.get_document_count()
        print(f"✅ Successfully indexed {doc_count} documents")

        return True

    except FileNotFoundError as e:
        print(f"❌ {e}")
        return False

    except Exception as e:
        print(f"❌ Error during indexing: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_stats():
    """Print system statistics."""
    print("\n📊 System Statistics:")
    print(f"  • ChromaDB Collection: {config.CHROMA_COLLECTION}")
    print(f"  • Persist Directory: {config.CHROMA_PERSIST_DIR}")
    print(f"  • Document Count: {chromadb_manager.get_document_count()}")
    print(f"  • LLM Model: {config.LLM_MODEL}")
    print(f"  • Agent ID: {config.MVK_AGENT_ID}")
    print()


def main():
    """Main initialization function."""
    print("=" * 60)
    print("Mavvrik SDK Assistant - Initialization")
    print("=" * 60)
    print()

    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Initialization failed. Please fix the errors above and try again.")
        sys.exit(1)

    # Index PDF if needed
    if not index_pdf_if_needed():
        print("\n❌ PDF indexing failed. The application may not work correctly.")
        print("Please ensure mvk_sdk_documentation.pdf is in the docs/ directory.")
        sys.exit(1)

    # Print stats
    print_stats()

    print("=" * 60)
    print("✅ Initialization complete!")
    print("=" * 60)
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
