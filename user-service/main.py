from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn
import uuid
import jwt
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
import psycopg2

load_dotenv()

# JWT config
SECRET_KEY = os.getenv("JWT_SECRET") or "super-secret"
ALGORITHM = os.getenv("JWT_ALGORITHM") or "HS256"

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database connection
try:
    conn = psycopg2.connect(
        user=os.getenv("user"),
        host=os.getenv("host"),
        database=os.getenv("database"),
        password=os.getenv("password"),
        port=os.getenv("port")
    )
    cursor = conn.cursor()
    print("Database connection successful")
    cursor.execute("""SELECT * FROM users""")
    print(cursor.fetchall())
except Exception as e:
    print(f"Database connection failed: {e}")
    raise

# FastAPI app
app = FastAPI(
    title="User Service",
    description="Microservice for user registration and authentication",
    version="1.0.0"
)

# Pydantic models
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    fname: str = Field(default="John", description="First name")
    lname: str = Field(default="Doe", description="Last name")
    mname: str = Field(default="A", description="Middle name")
    email: str = Field(default="john.doe@example.com", description="Email address")
    password: str = Field(default="securepassword123", description="Password")



class UserLogin(BaseModel):
    email: str = Field(default="john.doe@example.com", description="Email address")
    password: str = Field(default="securepassword123", description="Password")

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

# Routes
@app.get("/")
def root():
    return {"message": "Welcome to the User Service!"}

@app.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate):
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="User already exists")

        hashed = hash_password(user.password)
        cursor.execute(
            "INSERT INTO users (firstname, middlename, lastname, email, passwordhash, createdat, updatedat) VALUES (%s, %s, %s, %s, %s, NOW(), NOW()) RETURNING userid",
            (user.fname, user.mname, user.lname, user.email, hashed)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()

        token = create_access_token({"user_id": user_id, "email": user.email, 'firstname': user.fname, 'lastname': user.lname})
        return {"message": "User created successfully", "user_id": user_id, "token": token}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {e}")

@app.post("/signin", status_code=status.HTTP_200_OK)
def signin(user: UserLogin):
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (user.email,))
        existing_user = cursor.fetchone()
        if not existing_user or not verify_password(user.password, existing_user[5]):
            raise HTTPException(status_code=400, detail="Invalid email or password")

        token = create_access_token({"userid": existing_user[0], "email": existing_user[4]})
        return {"message": "Sign in successful", "user_id": existing_user[0], "token": token}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error signing in: {e}")

# Run the app
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8004, reload=True)
