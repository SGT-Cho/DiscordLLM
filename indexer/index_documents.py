import os
import argparse
from typing import List, Optional
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader,
    DirectoryLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
import qdrant_client

# Load environment variables
load_dotenv()
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:5600')

def load_documents(docs_dir: str) -> List:
    """Load documents from the specified directory"""
    print(f"Loading documents from {docs_dir}...")
    
    # Load PDFs
    pdf_loader = DirectoryLoader(
        docs_dir,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader
    )
    
    # Load text files
    text_loader = DirectoryLoader(
        docs_dir,
        glob="**/*.txt",
        loader_cls=TextLoader
    )
    
    # Load the documents
    pdf_documents = pdf_loader.load()
    text_documents = text_loader.load()
    
    all_documents = pdf_documents + text_documents
    print(f"Loaded {len(all_documents)} documents")
    
    return all_documents

def split_documents(documents: List, chunk_size: int = 1000, chunk_overlap: int = 200):
    """Split documents into chunks"""
    print("Splitting documents into chunks...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} document chunks")
    
    return chunks

def create_vector_store(documents: List, collection_name: str):
    """Create a vector store from the documents"""
    print(f"Creating vector store in collection '{collection_name}'...")
    
    # Initialize the embedding model
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Connect to Qdrant
    client = qdrant_client.QdrantClient(url=QDRANT_URL)
    
    # Create and populate the vector store
    vector_store = Qdrant.from_documents(
        documents,
        embeddings,
        url=QDRANT_URL,
        collection_name=collection_name,
        force_recreate=True  # Set to False if you want to add to existing collection
    )
    
    print(f"Successfully indexed {len(documents)} document chunks in Qdrant collection '{collection_name}'")
    return vector_store

def search_documents(query: str, collection_name: str, limit: int = 3):
    """Search for documents relevant to the query"""
    print(f"Searching for documents related to: '{query}'")
    
    # Initialize the embedding model
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Connect to Qdrant
    vector_store = Qdrant(
        client=qdrant_client.QdrantClient(url=QDRANT_URL),
        collection_name=collection_name,
        embeddings=embeddings
    )
    
    # Perform the search
    results = vector_store.similarity_search_with_score(query, k=limit)
    
    # Display results
    print(f"Found {len(results)} relevant documents:")
    for i, (doc, score) in enumerate(results):
        print(f"Result {i+1} (Score: {score:.4f}):")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"Content: {doc.page_content[:200]}...\n")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Index documents in a Qdrant vector database")
    parser.add_argument("--docs-dir", type=str, default="./docs", help="Directory containing documents to index")
    parser.add_argument("--collection", type=str, default="documents", help="Qdrant collection name")
    parser.add_argument("--search", type=str, help="Search query (optional)")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Document chunk size")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Document chunk overlap")
    
    args = parser.parse_args()
    
    # If search query is provided, only perform search
    if args.search:
        search_documents(args.search, args.collection)
        return
    
    # Otherwise, load, split, and index documents
    documents = load_documents(args.docs_dir)
    document_chunks = split_documents(documents, args.chunk_size, args.chunk_overlap)
    vector_store = create_vector_store(document_chunks, args.collection)
    
    print("\nIndexing complete! You can now search your documents.")
    print(f"Example usage: python {__file__} --search \"your search query here\"")

if __name__ == "__main__":
    main()