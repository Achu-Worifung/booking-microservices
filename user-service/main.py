from fastapi import FastAPI, HTTPException, Depends, status, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn
import uuid
import jwt
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
import psycopg2
from contextlib import contextmanager
import sys

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from redis_rate_limit import rate_limit

load_dotenv()

# JWT config
SECRET_KEY = os.getenv("JWT_SECRET") or "super-secret"
ALGORITHM = os.getenv("JWT_ALGORITHM") or "HS256"

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database connection configuration
DB_CONFIG = {
    "user": os.getenv("user"),
    "host": os.getenv("host"),
    "database": os.getenv("database"),
    "password": os.getenv("password"),
    "port": os.getenv("port")
}
BOOKING_CONFIG = {
    "user": os.getenv("user"),
    "host": os.getenv("host"),
    "database": 'bookings',
    "password": os.getenv("password"),
    "port": os.getenv("port")
}

def get_booking_db_connection():
    """
    Create and return a new database connection for bookings.
    """
    try:
        conn = psycopg2.connect(**BOOKING_CONFIG)
        return conn
    except Exception as e:
        print(f"Booking database connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Booking database connection failed"
        )

def get_db_connection():
    """
    Create and return a new database connection.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )

@contextmanager
def get_db_cursor():
    """
    Context manager for database operations.
    Automatically handles connection and cursor lifecycle.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        yield cursor, conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def test_db_connection():
    """
    Test database connection on startup.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        print("Database connection test successful")
        return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False

# Test database connection on startup
if not test_db_connection():
    print("Warning: Database connection failed. Service may not work properly.")

# FastAPI app
app = FastAPI(
    title="User Service",
    description="Microservice for user registration and authentication",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
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
async def root(request: Request):
    await rate_limit(request, limit=5, window=60, service="user-service")

    return {"message": "Welcome to the User Service!"}

@app.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, request: Request):
    """
    User signup endpoint with proper database connection management.
    """
    await rate_limit(request, limit=5, window=60, service="user-service")
    try:
        with get_db_cursor() as (cursor, conn):
            # Check if user already exists
            cursor.execute("SELECT * FROM users WHERE email = %s", (user.email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="User already exists")

            # Create new user with hashed password
            hashed = hash_password(user.password)
            cursor.execute(
                "INSERT INTO users (firstname, middlename, lastname, email, passwordhash, createdat, updatedat) VALUES (%s, %s, %s, %s, %s, NOW(), NOW()) RETURNING userid",
                (user.fname, user.mname, user.lname, user.email, hashed)
            )
            user_id = cursor.fetchone()[0]
            # Connection automatically committed via context manager

        # Create JWT token
        token = create_access_token({
            "user_id": user_id, 
            "email": user.email, 
            'fname': user.fname, 
            'lname': user.lname
        })
        
        return {
            "message": "User created successfully", 
            "user_id": user_id, 
            "token": token
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Signup error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error creating user: {e}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:

            conn.close()

@app.post("/signin", status_code=status.HTTP_200_OK)
async def signin(user: UserLogin, request: Request):
    await rate_limit(request, limit=5, window=60, service="user-service")
    """
    User signin endpoint with proper database connection management.
    """
    try:
        with get_db_cursor() as (cursor, conn):
            # Find user by email
            cursor.execute("SELECT * FROM users WHERE email = %s", (user.email,))
            existing_user = cursor.fetchone()
            
            # Verify user exists and password is correct
            if not existing_user or not verify_password(user.password, existing_user[5]):
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid email or password"
                )

        # Create JWT token
        token = create_access_token({
            "userid": existing_user[0], 
            "lname": existing_user[3], 
            "fname": existing_user[1],
            "email": existing_user[4]
        })
        
        return {
            "message": "Sign in successful", 
            "user_id": existing_user[0], 
            "token": token
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Signin error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error signing in: {e}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
def get_current_user(authorization: str = Header(None)) -> dict:
    """
    Extract and validate user from Authorization header.
    Expected format: "Bearer <token>"
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    return verify_token(token)
def verify_token(token: str) -> dict:
    """
    Verify and decode JWT token.
    Returns user data if token is valid, raises HTTPException if invalid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Map the token fields to expected fields
        # Handle both 'userid' and 'user_id' formats for compatibility
        if 'userid' in payload and 'user_id' not in payload:
            payload['user_id'] = payload['userid']
        
        # Add default values for missing fields
        if 'fname' not in payload:
            payload['fname'] = payload.get('email', '').split('@')[0]  # Use email prefix as default
        if 'lname' not in payload:
            payload['lname'] = ''  # Default empty last name
            
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError as e:
        # For debugging, let's also try without signature verification
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token signature. Token payload contains: {list(payload.keys())}"
            )
        except:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )

# Get bookings for the authenticated user using the Authorization header
@app.get('/bookings', status_code=status.HTTP_200_OK)
async def get_bookings(request: Request, authorization: str = Header(None)):
    """
    Get user bookings endpoint. Requires Authorization header with Bearer token.
    """
    await rate_limit(request, limit=5, window=60, service="user-service")
    cursor = None
    conn = None
    try:
        # Extract user from token
        current_user = get_current_user(authorization)
        user_id = current_user['user_id']
        conn = get_booking_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM user_bookings WHERE userid = %s", (user_id,))
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            bookings = [dict(zip(columns, row)) for row in rows]
            # print(f"Bookings fetched for user {user_id}: {bookings}")
            return {"bookings": bookings}
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Error fetching bookings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching bookings: {e}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    

# Run the app
if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8004, reload=True)
