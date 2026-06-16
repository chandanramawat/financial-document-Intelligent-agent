# rag/vector_store.py
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

# ✅ Free HuggingFace model
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

FAISS_PATH = "./faiss_db"
vector_store = None

# ✅ Step 1 — Load PDF
def document_loader(pdf_path: str):
    print(f"[RAG] Loading PDF: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    print(f"[RAG] Loaded {len(documents)} pages")
    return documents

# ✅ Step 2 — Split into chunks
def split_chunks(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=20
    )
    chunks = splitter.split_documents(documents)
    print(f"[RAG] Created {len(chunks)} chunks")
    return chunks

# ✅ Step 3 — Create vector store
def create_vector_store(chunks):
    global vector_store
    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(FAISS_PATH)
    print(f"[RAG] Vector store saved!")
    return vector_store

# ✅ Step 4 — Load existing vector store
def load_vector_store():
    global vector_store
    if os.path.exists(FAISS_PATH):
        vector_store = FAISS.load_local(
            FAISS_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        print("[RAG] Loaded existing vector store")
    return vector_store

# ✅ Step 5 — Get retriever
def get_retriever():
    global vector_store
    if vector_store is None:
        load_vector_store()
    if vector_store is None:
        return None
    return vector_store.as_retriever(
        search_kwargs={"k": 3}
    )

# ✅ Step 6 — Complete pipeline
def process_pdf(pdf_path: str, doc_name: str) -> str:
    try:
        # Load → Chunk → Store
        documents = document_loader(pdf_path)
        chunks    = split_chunks(documents)

        # Add source metadata
        for chunk in chunks:
            chunk.metadata["source"] = doc_name

        create_vector_store(chunks)
        return f"✅ Processed {doc_name} — {len(chunks)} chunks stored"

    except Exception as e:
        return f"❌ Error: {e}"

# ✅ Step 7 — Search documents
def search_documents(query: str) -> str:
    retriever = get_retriever()

    if retriever is None:
        return "No documents uploaded yet. Please upload a PDF first."

    try:
        results = retriever.invoke(query)

        if not results:
            return "No relevant information found"

        context = ""
        for i, doc in enumerate(results, 1):
            context += f"\nChunk {i}:\n"
            context += f"Source : {doc.metadata.get('source', 'Unknown')}\n"
            context += f"Page   : {doc.metadata.get('page', 'N/A')}\n"
            context += f"Content: {doc.page_content}\n"
            context += "-" * 40 + "\n"

        return context

    except Exception as e:
        return f"Search error: {e}"

# ✅ Step 8 — List documents
def list_documents() -> list:
    global vector_store
    if vector_store is None:
        load_vector_store()
    if vector_store is None:
        return []
    try:
        docs = vector_store.docstore._dict.values()
        sources = list(set([
            d.metadata.get("source", "Unknown")
            for d in docs
        ]))
        return sources
    except:
        return []

# Load on startup
load_vector_store()
print("✅ RAG Vector Store ready!")