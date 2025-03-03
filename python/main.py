import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException, Depends, File, UploadFile, Path
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
from contextlib import asynccontextmanager
import json
import hashlib

# Define the path to the images & sqlite3 database
images = pathlib.Path(__file__).parent.resolve() / "images"
db = pathlib.Path(__file__).parent.resolve() / "db" / "mercari.sqlite3"
items_json_path = pathlib.Path(__file__).parent.resolve() / "items.json"

images.mkdir(parents=True, exist_ok=True)

def get_db():
    if not db.exists():
        yield

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()

# STEP 5-1: set up the database connection
def setup_database():
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    yield

app = FastAPI(lifespan=lifespan)

logger = logging.getLogger("uvicorn")
logger.level = logging.DEBUG #4-6's DEBUG
#images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

class HelloResponse(BaseModel):
    message: str

@app.get("/", response_model=HelloResponse)
def hello():
    return HelloResponse(**{"message": "Hello, world!"})

class AddItemResponse(BaseModel):
    message: str

# add_item is a handler to add a new item for POST /items .
@app.post("/items", response_model=AddItemResponse)
async def add_item(
    name: str = Form(...),
    category: str = Form(...),
    image: UploadFile = File(...),
):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    if not category:
        raise HTTPException(status_code=400, detail="category is required")
    
    # Read the file content and generate SHA-256 hash
    image_bytes = await image.read()
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    image_name = f"{image_hash}.jpg"
    image_path = images / image_name

    # Save the image
    with open(image_path, "wb") as img_file:
        img_file.write(image_bytes)

    # Save item details to items.json
    item_data = Item(name=name, category=category, image_name=image_name)
    insert_item(item_data)

    #insert_item(Item(name=name, category=category))
    return AddItemResponse(**{"message": f"item received: {name}, category: {category}, image: {image_name}"})

# get_items is a handler to get a new item for POST /items .
@app.get("/items")
async def get_items():
    if not items_json_path.exists():
        return {"items": []}  # 空のリストを返す

    # JSONファイルを読み込む
    with open(items_json_path, "r") as f:
        data = json.load(f)

    return data

# get_image is a handler to return an image for GET /images/{filename} .
@app.get("/image/{image_name}")
async def get_image(image_name):
    # Create image path
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)

# get_item is a handler to return information about the item_id-th item for GET /items/<item_id>
@app.get("/items/{item_id}")
async def get_item(item_id: int = Path(..., title="Item ID", description="The index of the item (1-based)")):
    if not items_json_path.exists():
        raise HTTPException(status_code=404, detail="No items found")

    # JSONファイルを読み込む
    with open(items_json_path, "r") as f:
        data = json.load(f)

    items = data.get("items", [])
    
    # item_id は1-basedなので、リストのインデックスに変換
    index = item_id - 1

    if index < 0 or index >= len(items):
        raise HTTPException(status_code=404, detail="Item not found")

    return items[index]

class Item(BaseModel):
    name: str
    category: str
    image_name: str

def insert_item(item: Item):
    # Check if items.json exists
    if not items_json_path.exists():
        with open(items_json_path, "w") as f:
            json.dump({"items": []}, f, indent=2)

     # Load the existing JSON data
    with open(items_json_path, "r") as f:
        data = json.load(f)

    # Append new item
    data["items"].append({
        "name": item.name,
        "category": item.category,
        "image_name": item.image_name
    })

    # Write back to items.json
    with open(items_json_path, "w") as f:
        json.dump(data, f, indent=2)
    pass