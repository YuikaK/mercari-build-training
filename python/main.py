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

    conn = sqlite3.connect(db, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()

# STEP 5-1: set up the database connection
def setup_database():
    if not db.exists():
        with sqlite3.connect(db) as conn:
            with open(pathlib.Path(__file__).parent / "db/items.sql", "r") as f:
                conn.executescript(f.read())  # Execute SQL script to create tables


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
    db: sqlite3.Connection = Depends(get_db)
):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    if not category:
        raise HTTPException(status_code=400, detail="category is required")
    
    # Get category ID, or insert if not found
    cursor = db.cursor()
    cursor.execute("SELECT id FROM categories WHERE category = ?", (category,))
    category_row = cursor.fetchone()
    
    if category_row is None:
        # If category not found, insert new category
        cursor.execute("INSERT INTO categories (category) VALUES (?)", (category,))
        db.commit()
        category_id = cursor.lastrowid 

    category_id = category_row["id"]
    
    image_bytes = await image.read()
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    image_name = f"{image_hash}.jpg"
    image_path = images / image_name

    # Save image
    with open(image_path, "wb") as img_file:
        img_file.write(image_bytes)

    # Insert new product into items table
    item = Item(name=name, category_id=category_id, image_name=image_name)
    insert_item(item, db)

    return AddItemResponse(**{"message": f"item received: {name}, category: {category}, image: {image_name}"})

# Fixed data model for adding items
class Item(BaseModel):
    name: str
    category_id: int
    image_name: str

def insert_item(item: Item, db_conn: sqlite3.Connection):
    db_conn.cursor().execute(
        "INSERT INTO items (name, category_id, image_name) VALUES (?, ?, ?)",
        (item.name, item.category_id, item.image_name)
        )
    db_conn.commit()


# get_items is a handler to get a new item for POST /items .
@app.get("/items")
async def get_items(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    try:
        # SQLクエリでitemsとcategoriesをJOINして、category名を取得
        cursor.execute("""
            SELECT items.id, items.name, categories.category AS category, items.image_name
            FROM items
            JOIN categories ON items.category_id = categories.id
        """)
        items = [
            {"id": row["id"], "name": row["name"], "category": row["category"], "image_name": row["image_name"]}
            for row in cursor.fetchall()
        ]
        return {"items": items}
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()

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
async def get_item(
    item_id: int = Path(..., title="Item ID", description="Unique item ID"),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    try:
        cursor.execute("SELECT name, category_id, image_name FROM items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"name": row["name"], "category": row["category"], "image_name": row["image_name"]}
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()

#5-2
@app.get("/search")
async def search_items(keyword: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    try:
       # SQL query to find products with keyword in name
        cursor.execute("""
            SELECT items.name, categories.category
            FROM items
            JOIN categories ON items.category_id = categories.id
            WHERE items.name LIKE ?
        """, ('%' + keyword + '%',))
        
        items = [
            {"name": row["name"], "category": row["category"]}
            for row in cursor.fetchall()
        ]
        return {"items": items}
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
