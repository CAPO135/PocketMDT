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
import json

router=APIRouter()

@router.post("/ask/")
async def ask_question(question: str = Form(...), patient_history: Optional[str] = Form(None)):
    try:
        logger.info(f"user query: {question}")
        logger.info(f"patient history provided: {patient_history is not None}")

        # Embed model + Pinecone setup
        pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        index = pc.Index(os.environ["PINECONE_INDEX_NAME"])
        embed_model = OpenAIEmbeddings(model="text-embedding-3-large")
        embedded_query = embed_model.embed_query(question)
        res = index.query(vector=embedded_query, top_k=5, include_metadata=True)  # Increased top_k for better coverage

        logger.info(f"Vector store query returned {len(res.get('matches', []))} matches")

        docs = []
        for match in res.get("matches", []):
            metadata = match.get("metadata", {})
            # Try to get text content from metadata
            text_content = metadata.get("text", "")
            
            # If no text in metadata, try to get it from page_content if available
            if not text_content and "page_content" in metadata:
                text_content = metadata.get("page_content", "")
            
            # Log the first few characters of each document for debugging
            if text_content:
                logger.info(f"Document preview: {text_content[:100]}...")
            else:
                logger.warning(f"No text content found in document metadata: {metadata.keys()}")
            
            doc = Document(
                page_content=text_content,
                metadata=metadata
            )
            docs.append(doc)

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
            # Filter out empty documents
            valid_docs = [doc for doc in docs if doc.page_content.strip()]
            if valid_docs:
                document_content = "\n\n".join([doc.page_content for doc in valid_docs])
                logger.info(f"Retrieved {len(valid_docs)} relevant documents with content for context")
                logger.info(f"Total document context length: {len(document_content)} characters")
            else:
                logger.warning("All retrieved documents have empty content")
        else:
            logger.info("No relevant documents found in vector store")

        # Parse patient history if provided
        patient_context = ""
        if patient_history:
            try:
                patient_data = json.loads(patient_history)
                patient_context = format_patient_history(patient_data)
                logger.info(f"Patient history context length: {len(patient_context)} characters")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing patient history JSON: {e}")
                patient_context = ""

        # Combine document and patient context
        full_context = ""
        if patient_context:
            full_context += f"PATIENT HISTORY:\n{patient_context}\n\n"
        if document_content:
            full_context += f"DOCUMENT CONTEXT:\n{document_content}"

        # Use the CentralOrchestratorAgent to process the question with combined context
        agent = CentralOrchestratorAgent()
        result = agent.orchestrate(question, document_context=full_context)

        logger.info("query successful")
        return result

    except Exception as e:
        logger.exception("Error processing question")
        return JSONResponse(status_code=500, content={"error": str(e)})

def format_patient_history(patient_data):
    """Format patient history data into a readable string for agents"""
    formatted = []
    
    # Demographics
    if patient_data.get("name"):
        formatted.append(f"Name: {patient_data['name']}")
    if patient_data.get("dob"):
        formatted.append(f"Date of Birth: {patient_data['dob']}")
    if patient_data.get("gender"):
        formatted.append(f"Gender: {patient_data['gender']}")
    if patient_data.get("height_ft") or patient_data.get("height_in"):
        height = f"{patient_data.get('height_ft', 0)}' {patient_data.get('height_in', 0)}\""
        formatted.append(f"Height: {height}")
    if patient_data.get("weight_lbs"):
        formatted.append(f"Weight: {patient_data['weight_lbs']} lbs")
    
    # Medical History
    if patient_data.get("conditions"):
        formatted.append("\nMedical Conditions:")
        for condition in patient_data["conditions"]:
            formatted.append(f"  - {condition['name']} (Diagnosed: {condition['date']})")
    
    if patient_data.get("medications"):
        formatted.append("\nCurrent Medications:")
        for med in patient_data["medications"]:
            formatted.append(f"  - {med['name']} ({med['dosage']}) - {med['reason']}")
    
    if patient_data.get("family_history"):
        formatted.append(f"\nFamily History: {', '.join(patient_data['family_history'])}")
    
    # Goals
    if patient_data.get("health_goals"):
        formatted.append(f"\nHealth Goals: {patient_data['health_goals']}")
    
    # Symptoms
    if patient_data.get("symptoms"):
        formatted.append("\nCurrent Symptoms:")
        for symptom in patient_data["symptoms"]:
            formatted.append(f"  - {symptom['symptom']} (Frequency: {symptom['frequency']}, Severity: {symptom['severity']}, Duration: {symptom['duration']})")
    
    return "\n".join(formatted)