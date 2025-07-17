from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
import httpx

app = FastAPI()

@app.post("/synthesize")
async def synthesize(
    request: Request,
    token: str = Header(...),
    voice_id: str = Header(default="FEMALE3v2"),
    speed: float = Header(default=1.0),
    pitch: float = Header(default=1.0),
    sample_rate: int = Header(default=22050)
):
    # Read the request body as text
    text = (await request.body()).decode("utf-8")
    
    # Prepare headers for Chimege API
    chimege_headers = {
        "Content-Type": "text/plain",
        "token": token,
        "voice-id": voice_id,
        "speed": str(speed),
        "pitch": str(pitch),
        "sample-rate": str(sample_rate),
    }
    
    # Make request to Chimege API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.chimege.com/v1.2/synthesize",
            headers=chimege_headers,
            content=text.encode("utf-8"),
        )
        
        # Handle response
        if response.status_code == 200:
            return StreamingResponse(response.aiter_bytes(), media_type="audio/x-wav")
        else:
            error_code = response.headers.get("Error-Code")
            error_message = response.text
            raise HTTPException(
                status_code=response.status_code,
                detail={"error_code": error_code, "message": error_message}
            )