from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from modules.central_orchestrator.agent import CentralOrchestratorAgent
from langchain_core.documents import Document
from langchain.schema import BaseRetriever
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
from pydantic import Field
from typing import List, Optional
from logger import logger
import os

router=APIRouter()

@router.post("/ask/")
async def ask_question(question: str = Form(...)):
    try:
        logger.info(f"user query: {question}")

        # Embed model + Pinecone setup
        pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        index = pc.Index(os.environ["PINECONE_INDEX_NAME"])
        embed_model = OpenAIEmbeddings(model="text-embedding-3-large")
        embedded_query = embed_model.embed_query(question)
        res = index.query(vector=embedded_query, top_k=3, include_metadata=True)

        logger.info(f"Vector store query returned {len(res.get('matches', []))} matches")

        docs = [
            Document(
                page_content=match.get("metadata", {}).get("text", ""),
                metadata=match.get("metadata", {})
            ) for match in res.get("matches", [])
        ]



        class SimpleRetriever(BaseRetriever):
            tags: Optional[List[str]] = Field(default_factory=list)
            metadata: Optional[dict] = Field(default_factory=dict)

            def __init__(self, documents: List[Document]):
                super().__init__()
                self._docs = documents

            def _get_relevant_documents(self, query: str) -> List[Document]:
                return self._docs

        # Extract document content for context
        document_content = ""
        if docs:
            document_content = "\n\n".join([doc.page_content for doc in docs])
            logger.info(f"Retrieved {len(docs)} relevant documents for context")
        else:
            logger.info("No relevant documents found in vector store")

        # Use the CentralOrchestratorAgent to process the question with document context
        agent = CentralOrchestratorAgent()
        result = agent.orchestrate(question, document_context=document_content)

        logger.info("query successful")
        return result

    except Exception as e:
        logger.exception("Error processing question")
        return JSONResponse(status_code=500, content={"error": str(e)})