from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

import models
from database import SessionLocal, engine

# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Security Config
SECRET_KEY = "supersecretkey" # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://marketplace1.dionlinein.com",
    "http://marketplace1.dionlinein.com",
    "*" # Keep wildcard for testing, remove for strict production if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth Utils & Dependencies
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have admin privileges"
        )
    return current_user

# Pydantic Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: str
    category: str
    image: str
    is_new: bool = False

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    phone: Optional[str] = None

class User(BaseModel):
    email: str
    role: str
    name: Optional[str] = None
    phone_number: Optional[str] = None

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

# Routes
@app.get("/")
def read_root():
    return {"Hello": "Adidaw Marketplace API"}

# Auth Routes
@app.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email, 
        hashed_password=hashed_password, 
        role="member",
        name=user.name,
        phone_number=user.phone
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "role": "member"}

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@app.get("/users/me", response_model=User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.put("/users/me/password")
def change_password(password_change: PasswordChange, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not verify_password(password_change.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    current_user.hashed_password = get_password_hash(password_change.new_password)
    db.commit()
    return {"message": "Password updated successfully"}

@app.get("/products", response_model=List[Product])
def read_products(skip: int = 0, limit: int = 100, category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Product)
    if category:
        query = query.filter(models.Product.category == category)
    products = query.offset(skip).limit(limit).all()
    return products

@app.post("/products", response_model=Product)
def create_product(product: ProductCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin)):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

# Upload Endpoint
from fastapi import File, UploadFile
import shutil
from pathlib import Path

# Setup upload directory in frontend/public/uploads
UPLOAD_DIR = Path("../frontend/public/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/upload")
async def upload_image(file: UploadFile = File(...), current_user: models.User = Depends(get_current_admin)):
    try:
        # Create unique filename
        filename = f"{datetime.now().timestamp()}_{file.filename}"
        file_path = UPLOAD_DIR / filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Return path relative to public folder (accessible by Next.js)
        return {"url": f"/uploads/{filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Wishlist Endpoints
@app.post("/wishlist/{product_id}")
def add_to_wishlist(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Check if exists
    exists = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == current_user.id,
        models.Wishlist.product_id == product_id
    ).first()
    
    if exists:
        return {"message": "Already in wishlist"}
        
    item = models.Wishlist(user_id=current_user.id, product_id=product_id)
    db.add(item)
    db.commit()
    return {"message": "Added to wishlist"}

@app.delete("/wishlist/{product_id}")
def remove_from_wishlist(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == current_user.id,
        models.Wishlist.product_id == product_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not in wishlist")
        
    db.delete(item)
    db.commit()
    return {"message": "Removed from wishlist"}

@app.get("/wishlist", response_model=List[Product])
def get_wishlist(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Join Product and Wishlist
    products = db.query(models.Product).join(models.Wishlist).filter(models.Wishlist.user_id == current_user.id).all()
    return products
