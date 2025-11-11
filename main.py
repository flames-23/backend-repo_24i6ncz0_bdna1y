import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime

from database import create_document, get_documents
from schemas import Contactmessage

app = FastAPI(title="Setiawan Dwi Novantoro - Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Portfolio API running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the portfolio backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except ImportError:
        response["database"] = "❌ Database module not found"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Contact endpoints
class ContactRequest(Contactmessage):
    pass

class ContactResponse(BaseModel):
    id: str
    name: str
    email: str
    subject: str | None
    message: str
    created_at: datetime

@app.post("/api/contact", response_model=ContactResponse)
async def submit_contact(payload: ContactRequest):
    data = payload.dict()
    data["created_at"] = datetime.utcnow()
    doc = create_document("contactmessage", data)
    if not doc or "_id" not in doc:
        raise HTTPException(status_code=500, detail="Failed to save message")
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "email": doc["email"],
        "subject": doc.get("subject"),
        "message": doc["message"],
        "created_at": doc["created_at"],
    }

@app.get("/api/contact", response_model=List[ContactResponse])
async def list_contacts(limit: int = 25):
    docs = get_documents("contactmessage", {}, limit)
    results: List[ContactResponse] = []
    for d in docs:
        results.append(ContactResponse(
            id=str(d.get("_id")),
            name=d.get("name", ""),
            email=d.get("email", ""),
            subject=d.get("subject"),
            message=d.get("message", ""),
            created_at=d.get("created_at", datetime.utcnow()),
        ))
    return results

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
