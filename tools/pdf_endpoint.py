from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from io import BytesIO
import pypandoc
import tempfile
import os

router = APIRouter()

class PdfRequest(BaseModel):
    content: str
    filename: str = "document.pdf"

def generate_pdf(data: PdfRequest) -> BytesIO:
    buffer = BytesIO()
    # Create temporary input/output files
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp_in:
        tmp_in.write(data.content.encode("utf-8"))
        tmp_in.flush()
        input_path = tmp_in.name
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_out:
        output_path = tmp_out.name

    try:
        # Run Pandoc conversion via pypandoc
        pypandoc.convert_file(
            input_path,
            "pdf",
            outputfile=output_path,
            # Optionally, you can add extra_args for PDF-specific options
            # extra_args=["--pdf-engine=xelatex"]
        )
        # Read the generated PDF into memory
        with open(output_path, "rb") as f:
            buffer.write(f.read())
        buffer.seek(0)
        return buffer
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during conversion: {str(e)}")
    finally:
        # Cleanup temp files
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

@router.post("/generate-pdf")
async def create_pdf(request: PdfRequest):
    """
    FastAPI endpoint that receives Markdown and returns a PDF document.
    """
    try:
        buffer = generate_pdf(request)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={request.filename}"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
