from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import json
import csv
import os
from typing import Optional
from pydantic import BaseModel

app = FastAPI()

class ConversionRequest(BaseModel):
    folder_path: str

def file_converter_service(folder_path: str):
    # ... (keep the existing implementation exactly as is)
    # The function should return the output_dir path at the end
    return output_dir

@app.post("/convert-files/")
async def convert_files(request: ConversionRequest):
    """
    Convert transcription and translation files to various formats.
    
    Returns a list of downloadable file URLs that can be accessed via the /download endpoint.
    """
    try:
        output_dir = file_converter_service(request.folder_path)
        
        # Get list of generated files
        generated_files = os.listdir(output_dir)
        
        # Create download links
        file_links = [
            {"name": filename, "download_link": f"/download/{filename}"}
            for filename in generated_files
        ]
        
        return {
            "status": "success",
            "message": "Files converted successfully",
            "files": file_links
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str, folder_path: Optional[str] = None):
    """
    Download a converted file.
    
    If folder_path is not provided, it will look in the default output directory.
    """
    try:
        # In a real implementation, you'd want to secure this to prevent directory traversal
        if folder_path:
            file_path = os.path.join(folder_path, "converted_files", filename)
        else:
            # You might want to implement a better way to track file locations
            file_path = os.path.join("some_default_path", "converted_files", filename)
            
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
            
        return FileResponse(
            file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# For testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)