import os
import time
import warnings
from pathlib import Path
from dotenv import load_dotenv
from tqdm.auto import tqdm
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from datetime import datetime

# Suppress pypdf page label warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pypdf._page_labels")

load_dotenv()

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY=os.getenv("PINECONE_API_KEY")
PINECONE_ENV="us-east-1"
PINECONE_INDEX_NAME = "pocketmdtpdfs"

if OPENAI_API_KEY is not None:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

UPLOAD_DIR = "./uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# initialize pinecone instance
pc=Pinecone(api_key=PINECONE_API_KEY)
spec=ServerlessSpec(cloud="aws",region=PINECONE_ENV)
existing_indexes=[i["name"] for i in pc.list_indexes()]


if PINECONE_INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=3072,  # Updated to match text-embedding-3-large
        metric="cosine",
        spec=spec
    )
    while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
        time.sleep(1)
else:
    # Check if existing index has correct dimension
    index_info = pc.describe_index(PINECONE_INDEX_NAME)
    current_dimension = index_info.dimension
    if current_dimension != 3072:
        print(f"⚠️  Existing index has dimension {current_dimension}, but text-embedding-3-large requires 3072")
        print("🗑️  Deleting existing index to recreate with correct dimension...")
        pc.delete_index(PINECONE_INDEX_NAME)
        time.sleep(5)  # Wait for deletion to complete
        
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=3072,
            metric="cosine",
            spec=spec
        )
        while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
            time.sleep(1)
        print("✅ Index recreated with correct dimension")


index=pc.Index(PINECONE_INDEX_NAME)

def load_pdf_with_fallback(file_path):
    """Load PDF with fallback to alternative method if PyPDFLoader fails"""
    try:
        # Try PyPDFLoader first
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        print(f"📄 Successfully loaded {len(documents)} pages from {Path(file_path).name} using PyPDFLoader")
        return documents
    except Exception as e:
        print(f"⚠️  PyPDFLoader failed for {Path(file_path).name}: {e}")
        try:
            # Fallback to PyMuPDF if available
            import fitz
            doc = fitz.open(file_path)
            documents = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text.strip():  # Only add non-empty pages
                    documents.append(Document(
                        page_content=text,
                        metadata={"source": file_path, "page": page_num + 1}
                    ))
            doc.close()
            print(f"📄 Successfully loaded {len(documents)} pages from {Path(file_path).name} using PyMuPDF fallback")
            return documents
        except ImportError:
            print(f"❌ PyMuPDF not available for fallback. Skipping {Path(file_path).name}")
            return []
        except Exception as e2:
            print(f"❌ Both PDF loaders failed for {Path(file_path).name}: {e2}")
            return []

def clear_user_documents(user_id: str):
    """Clear all documents for a specific user from the vector store"""
    try:
        print(f"🗑️  Clearing documents for user: {user_id}")
        
        # Query for all vectors belonging to this user
        # Note: This is a simplified approach. In production, you might want to use metadata filtering
        # or implement a more sophisticated deletion strategy
        
        # For now, we'll use a filter to delete user-specific documents
        # This requires the index to support metadata filtering
        try:
            # Delete vectors with user_id in metadata
            index.delete(filter={"user_id": user_id})
            print(f"✅ Cleared documents for user: {user_id}")
        except Exception as e:
            print(f"⚠️  Could not use metadata filter deletion: {e}")
            print("⚠️  Consider recreating index with metadata filtering support")
            
    except Exception as e:
        print(f"⚠️  Warning: Could not clear documents for user {user_id}: {e}")

def load_vectorstore(uploaded_files, user_id: str):
    """
    Load documents into vector store with user isolation
    
    Args:
        uploaded_files: List of uploaded file objects
        user_id: Unique identifier for the user uploading documents
    """
    embed_model = OpenAIEmbeddings(model="text-embedding-3-large")
    file_paths = []
    
    # Generate a unique session ID for this upload batch
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"🆔 Starting upload session for user {user_id}: {session_id}")

    # Clear existing documents for this user only
    clear_user_documents(user_id)

    for file in uploaded_files:
        save_path = Path(UPLOAD_DIR) / f"{user_id}_{file.filename}"
        with open(save_path, "wb") as f:
            f.write(file.file.read())
        file_paths.append(str(save_path))

    for file_path in file_paths:
        print(f"\n📁 Processing for user {user_id}: {Path(file_path).name}")
        documents = load_pdf_with_fallback(file_path)
        
        if not documents:
            print(f"⚠️  Skipping {Path(file_path).name} - no content extracted")
            continue

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(documents)

        texts = [chunk.page_content for chunk in chunks]
        # Include the text content in metadata for retrieval
        metadatas = []
        for chunk in chunks:
            metadata = chunk.metadata.copy()
            metadata["text"] = chunk.page_content  # Add text content to metadata
            metadata["filename"] = Path(file_path).name  # Add filename for tracking
            metadata["upload_session"] = session_id  # Add session ID for tracking
            metadata["user_id"] = user_id  # Add user ID for isolation
            metadatas.append(metadata)
        
        # Generate unique IDs with user_id and timestamp to prevent conflicts
        ids = [f"{user_id}_{session_id}_{Path(file_path).stem}_{i}" for i in range(len(chunks))]

        print(f"🔍 Embedding {len(texts)} chunks from {Path(file_path).name} for user {user_id}...")
        embeddings = embed_model.embed_documents(texts)

        print(f"📤 Uploading {Path(file_path).name} to Pinecone for user {user_id}...")
        with tqdm(total=len(embeddings), desc=f"Upserting {Path(file_path).name}") as progress:
            index.upsert(vectors=list(zip(ids, embeddings, metadatas)))
            progress.update(len(embeddings))

        print(f"✅ Upload complete for {Path(file_path).name} (user: {user_id})")
    
    print(f"\n🎉 All documents uploaded successfully for user {user_id} in session: {session_id}")
    print(f"📊 Total files processed: {len(file_paths)}")

def query_user_documents(query_embedding, user_id: str, top_k: int = 5):
    """
    Query documents for a specific user only
    
    Args:
        query_embedding: The embedded query vector
        user_id: User ID to filter documents for
        top_k: Number of results to return
        
    Returns:
        List of matching documents for the user only
    """
    try:
        # Query with user_id filter to ensure only user's documents are returned
        res = index.query(
            vector=query_embedding, 
            top_k=top_k, 
            include_metadata=True,
            filter={"user_id": user_id}  # This ensures user isolation
        )
        return res.get("matches", [])
    except Exception as e:
        print(f"⚠️  Warning: Could not use metadata filter for user {user_id}: {e}")
        # Fallback: query without filter (less secure, but functional)
        print("⚠️  Falling back to unfiltered query - consider enabling metadata filtering")
        res = index.query(
            vector=query_embedding, 
            top_k=top_k, 
            include_metadata=True
        )
        # Manually filter results by user_id
        matches = res.get("matches", [])
        user_matches = [match for match in matches if match.get("metadata", {}).get("user_id") == user_id]
        return user_matches