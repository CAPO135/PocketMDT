from fastapi import APIRouter, UploadFile, File, Query, Form
from typing import List, Optional
from fastapi.responses import JSONResponse
from logger import logger
from modules.load_vectorstore import load_vectorstore, clear_user_documents

router = APIRouter()

@router.post("/upload_pdfs/")
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    user_id: str = Form(..., description="Unique identifier for the user uploading documents"),
    clear_existing: bool = Query(False, description="Clear existing documents for this user before uploading")
):
    try:
        logger.info(f"Received {len(files)} uploaded files for user: {user_id}")
        
        # Log the filenames being uploaded
        filenames = [f.filename for f in files]
        logger.info(f"Files to process for user {user_id}: {filenames}")
        
        if clear_existing:
            logger.info(f"Clearing existing documents for user {user_id} as requested")
            clear_user_documents(user_id)
        
        load_vectorstore(files, user_id)
        logger.info(f"Documents added to vectorstore successfully for user: {user_id}")
        return {
            "message": f"Files processed and vectorstore updated for user {user_id}. Processed {len(files)} files: {filenames}",
            "files_processed": filenames,
            "user_id": user_id
        }
    except Exception as e:
        logger.exception(f"Error during PDF upload for user {user_id}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/clear_user_documents/")
async def clear_user_documents_endpoint(user_id: str = Form(..., description="User ID whose documents should be cleared")):
    """Clear all documents for a specific user from the vector store"""
    try:
        logger.info(f"Clearing vector store for user: {user_id}")
        clear_user_documents(user_id)
        return {"message": f"Vector store cleared successfully for user: {user_id}", "user_id": user_id}
    except Exception as e:
        logger.exception(f"Error clearing vector store for user {user_id}")
        return JSONResponse(status_code=500, content={"error": str(e)})