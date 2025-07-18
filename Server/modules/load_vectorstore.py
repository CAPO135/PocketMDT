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

# Suppress pypdf page label warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pypdf._page_labels")

load_dotenv()

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY=os.getenv("PINECONE_API_KEY")
PINECONE_ENV="us-east-1"
PINECONE_INDEX_NAME = "labworkindex"

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

# load,split,embed and upsert pdf docs content

def load_vectorstore(uploaded_files):
    embed_model = OpenAIEmbeddings(model="text-embedding-3-large")
    file_paths = []

    for file in uploaded_files:
        save_path = Path(UPLOAD_DIR) / file.filename
        with open(save_path, "wb") as f:
            f.write(file.file.read())
        file_paths.append(str(save_path))

    for file_path in file_paths:
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
            metadatas.append(metadata)
        
        ids = [f"{Path(file_path).stem}-{i}" for i in range(len(chunks))]

        print(f"🔍 Embedding {len(texts)} chunks...")
        embeddings = embed_model.embed_documents(texts)

        print("📤 Uploading to Pinecone...")
        with tqdm(total=len(embeddings), desc="Upserting to Pinecone") as progress:
            index.upsert(vectors=list(zip(ids, embeddings, metadatas)))
            progress.update(len(embeddings))

        print(f"✅ Upload complete for {file_path}")