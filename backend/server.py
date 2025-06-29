from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import base64
import mimetypes

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class Artist(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    bio: Optional[str] = ""
    location: Optional[str] = ""
    website: Optional[str] = ""
    social_links: Optional[dict] = {}
    profile_image: Optional[str] = ""  # base64 encoded
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ArtistCreate(BaseModel):
    name: str
    email: str
    bio: Optional[str] = ""
    location: Optional[str] = ""
    website: Optional[str] = ""
    social_links: Optional[dict] = {}

class ArtistUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[dict] = None

class Content(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    artist_id: str
    title: str
    description: Optional[str] = ""
    file_data: str  # base64 encoded file
    file_type: str  # mime type
    file_name: str
    file_size: int
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ContentCreate(BaseModel):
    artist_id: str
    title: str
    description: Optional[str] = ""
    tags: List[str] = []

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Artist endpoints
@api_router.post("/artists", response_model=Artist)
async def create_artist(artist: ArtistCreate):
    """Create a new artist profile"""
    # Check if email already exists
    existing_artist = await db.artists.find_one({"email": artist.email})
    if existing_artist:
        raise HTTPException(status_code=400, detail="Artist with this email already exists")
    
    artist_dict = artist.dict()
    artist_obj = Artist(**artist_dict)
    await db.artists.insert_one(artist_obj.dict())
    return artist_obj

@api_router.get("/artists", response_model=List[Artist])
async def get_all_artists(skip: int = 0, limit: int = 20, search: Optional[str] = None):
    """Get all artists with optional search"""
    query = {}
    if search:
        query = {
            "$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"bio": {"$regex": search, "$options": "i"}},
                {"location": {"$regex": search, "$options": "i"}}
            ]
        }
    
    artists = await db.artists.find(query).skip(skip).limit(limit).to_list(limit)
    return [Artist(**artist) for artist in artists]

@api_router.get("/artists/{artist_id}", response_model=Artist)
async def get_artist(artist_id: str):
    """Get specific artist by ID"""
    artist = await db.artists.find_one({"id": artist_id})
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    return Artist(**artist)

@api_router.put("/artists/{artist_id}", response_model=Artist)
async def update_artist(artist_id: str, artist_update: ArtistUpdate):
    """Update artist profile"""
    artist = await db.artists.find_one({"id": artist_id})
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    update_data = {k: v for k, v in artist_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.artists.update_one({"id": artist_id}, {"$set": update_data})
    updated_artist = await db.artists.find_one({"id": artist_id})
    return Artist(**updated_artist)

@api_router.post("/artists/{artist_id}/profile-image")
async def upload_profile_image(artist_id: str, file: UploadFile = File(...)):
    """Upload profile image for artist"""
    artist = await db.artists.find_one({"id": artist_id})
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    # Read file and convert to base64
    file_content = await file.read()
    file_base64 = base64.b64encode(file_content).decode('utf-8')
    
    # Update artist with profile image
    await db.artists.update_one(
        {"id": artist_id}, 
        {"$set": {"profile_image": file_base64, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Profile image uploaded successfully"}

# Content endpoints
@api_router.post("/content")
async def upload_content(
    artist_id: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    file: UploadFile = File(...)
):
    """Upload content for an artist"""
    # Verify artist exists
    artist = await db.artists.find_one({"id": artist_id})
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    # Read file and convert to base64
    file_content = await file.read()
    file_base64 = base64.b64encode(file_content).decode('utf-8')
    
    # Get file info
    file_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    file_size = len(file_content)
    
    # Parse tags
    tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
    
    # Create content object
    content_obj = Content(
        artist_id=artist_id,
        title=title,
        description=description,
        file_data=file_base64,
        file_type=file_type,
        file_name=file.filename,
        file_size=file_size,
        tags=tags_list
    )
    
    await db.content.insert_one(content_obj.dict())
    return {"message": "Content uploaded successfully", "content_id": content_obj.id}

@api_router.get("/content", response_model=List[Content])
async def get_all_content(skip: int = 0, limit: int = 20, artist_id: Optional[str] = None, search: Optional[str] = None):
    """Get all content with optional filtering"""
    query = {}
    if artist_id:
        query["artist_id"] = artist_id
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}}
        ]
    
    content = await db.content.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return [Content(**c) for c in content]

@api_router.get("/content/{content_id}", response_model=Content)
async def get_content(content_id: str):
    """Get specific content by ID"""
    content = await db.content.find_one({"id": content_id})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return Content(**content)

@api_router.delete("/content/{content_id}")
async def delete_content(content_id: str):
    """Delete content"""
    result = await db.content.delete_one({"id": content_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    return {"message": "Content deleted successfully"}

@api_router.get("/artists/{artist_id}/content", response_model=List[Content])
async def get_artist_content(artist_id: str, skip: int = 0, limit: int = 20):
    """Get all content for a specific artist"""
    content = await db.content.find({"artist_id": artist_id}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return [Content(**c) for c in content]

# Original endpoints
@api_router.get("/")
async def root():
    return {"message": "Artist Platform API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()