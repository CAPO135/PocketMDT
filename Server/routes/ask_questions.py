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
async def ask_question(
    question: str = Form(...), 
    user_id: str = Form(..., description="Unique identifier for the user asking the question"),
    patient_history: Optional[str] = Form(None)
):
    try:
        logger.info(f"user query from user {user_id}: {question}")
        logger.info(f"patient history provided for user {user_id}: {patient_history is not None}")
        if patient_history:
            logger.info(f"patient history type: {type(patient_history)}, value: {patient_history[:100] if isinstance(patient_history, str) else str(patient_history)[:100]}")

        # Embed model + Pinecone setup
        pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        index = pc.Index(os.environ["PINECONE_INDEX_NAME"])
        embed_model = OpenAIEmbeddings(model="text-embedding-3-large")
        embedded_query = embed_model.embed_query(question)
        
        # Use user-specific document query to ensure isolation
        from modules.load_vectorstore import query_user_documents
        matches = query_user_documents(embedded_query, user_id, top_k=10)

        logger.info(f"Vector store query returned {len(matches)} matches for user {user_id}")

        docs = []
        seen_filenames = set()  # Track which files we've seen to avoid duplicates
        
        for match in matches:
            metadata = match.get("metadata", {})
            # Try to get text content from metadata
            text_content = metadata.get("text", "")
            
            # If no text in metadata, try to get it from page_content if available
            if not text_content and "page_content" in metadata:
                text_content = metadata.get("page_content", "")
            
            # Get filename for tracking
            filename = metadata.get("filename", "unknown")
            
            # Verify this document belongs to the requesting user
            document_user_id = metadata.get("user_id", "")
            if document_user_id != user_id:
                logger.warning(f"Document {filename} belongs to user {document_user_id}, not requesting user {user_id}")
                continue
                
            # Skip if we've already seen this file (to avoid duplicate content)
            if filename in seen_filenames:
                logger.info(f"Skipping duplicate file for user {user_id}: {filename}")
                continue
                
            # Log the first few characters of each document for debugging
            if text_content:
                logger.info(f"Document preview from {filename} for user {user_id}: {text_content[:100]}...")
                seen_filenames.add(filename)
            else:
                logger.warning(f"No text content found in document metadata for user {user_id}: {metadata.keys()}")
                continue
            
            doc = Document(
                page_content=text_content,
                metadata=metadata
            )
            docs.append(doc)
            
            # Limit to top 5 unique documents to avoid overwhelming the context
            if len(docs) >= 5:
                break

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
                # Log which documents are being used
                filenames_used = [doc.metadata.get("filename", "unknown") for doc in valid_docs]
                logger.info(f"Using documents from files for user {user_id}: {filenames_used}")
                
                document_content = "\n\n".join([doc.page_content for doc in valid_docs])
                logger.info(f"Retrieved {len(valid_docs)} relevant documents with content for context for user {user_id}")
                logger.info(f"Total document context length for user {user_id}: {len(document_content)} characters")
            else:
                logger.warning(f"All retrieved documents have empty content for user {user_id}")
        else:
            logger.info(f"No relevant documents found in vector store for user {user_id}")

        # Parse patient history if provided
        patient_context = ""
        if patient_history:
            try:
                # Handle both JSON string and dict object formats
                if isinstance(patient_history, str):
                    if patient_history.strip():  # Check if string is not empty
                        patient_data = json.loads(patient_history)
                    else:
                        logger.info(f"Empty patient history string for user {user_id}")
                        patient_context = ""
                        patient_data = None
                else:
                    patient_data = patient_history
                
                if patient_data:
                    patient_context = format_patient_history(patient_data)
                    logger.info(f"Patient history context length for user {user_id}: {len(patient_context)} characters")
                else:
                    logger.info(f"No patient data available for user {user_id}")
                    
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Error parsing patient history for user {user_id}: {e}")
                logger.error(f"Patient history type: {type(patient_history)}, value: {patient_history}")
                patient_context = ""
        else:
            logger.info(f"No patient history provided for user {user_id}")

        # Combine document and patient context
        full_context = ""
        if patient_context:
            full_context += f"PATIENT HISTORY:\n{patient_context}\n\n"
        if document_content:
            full_context += f"DOCUMENT CONTEXT:\n{document_content}"

        # Use the CentralOrchestratorAgent to process the question with combined context
        agent = CentralOrchestratorAgent()
        result = agent.orchestrate(question, document_context=full_context)

        logger.info(f"query successful for user {user_id}")
        return result

    except Exception as e:
        logger.exception(f"Error processing question for user {user_id}")
        return JSONResponse(status_code=500, content={"error": str(e)})

def format_patient_history(patient_data):
    """Format patient history data into a readable string for agents"""
    if not patient_data or not isinstance(patient_data, dict):
        return ""
        
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
    if patient_data.get("conditions") and isinstance(patient_data["conditions"], list):
        formatted.append("\nMedical Conditions:")
        for condition in patient_data["conditions"]:
            if isinstance(condition, dict):
                name = condition.get('name', 'Unknown')
                date = condition.get('date', 'Unknown date')
                formatted.append(f"  - {name} (Diagnosed: {date})")
    
    if patient_data.get("medications") and isinstance(patient_data["medications"], list):
        formatted.append("\nCurrent Medications:")
        for med in patient_data["medications"]:
            if isinstance(med, dict):
                name = med.get('name', 'Unknown')
                dosage = med.get('dosage', 'Unknown dosage')
                reason = med.get('reason', 'Unknown reason')
                formatted.append(f"  - {name} ({dosage}) - {reason}")
    
    if patient_data.get("family_history") and isinstance(patient_data["family_history"], list):
        formatted.append(f"\nFamily History: {', '.join(patient_data['family_history'])}")
    
    # Goals
    if patient_data.get("health_goals"):
        formatted.append(f"\nHealth Goals: {patient_data['health_goals']}")
    
    # Symptoms
    if patient_data.get("symptoms") and isinstance(patient_data["symptoms"], list):
        formatted.append("\nCurrent Symptoms:")
        for symptom in patient_data["symptoms"]:
            if isinstance(symptom, dict):
                symptom_name = symptom.get('symptom', 'Unknown')
                frequency = symptom.get('frequency', 'Unknown')
                severity = symptom.get('severity', 'Unknown')
                duration = symptom.get('duration', 'Unknown')
                formatted.append(f"  - {symptom_name} (Frequency: {frequency}, Severity: {severity}, Duration: {duration})")
    
    return "\n".join(formatted)