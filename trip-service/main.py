from fastapi import FastAPI, HTTPException, Depends, Query, status, Header
from pydantic import BaseModel, Field 
from typing import Optional, List, Dict 
import jwt 
import os 
import psycopg2
import datetime
from dotenv import load_dotenv
from contextlib import contextmanager
import json 
import uuid

import uvicorn


load_dotenv()  # Load environment variables

# JWT config
SECRET_KEY = os.getenv("JWT_SECRET") or "super-secret"
ALGORITHM = os.getenv("JWT_ALGORITHM") or "HS256"

# Database connection configuration for trips
DB_CONFIG = {
        "user": os.getenv("PGUSER"),
        "host": os.getenv("PGHOST"),
        "database": os.getenv("PGDATABASE"),
        "password": os.getenv("password"),
        "port": os.getenv("PGPORT")
}

def get_db_connection(CONFIG=DB_CONFIG):
    """
    Create and return a new database connection.
    """
    try:
        conn = psycopg2.connect(**CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )

class Trip(BaseModel):
    tripid: uuid.UUID
    userid: uuid.UUID
    tripname: str
    destination: str
    startdate: datetime.date
    enddate: datetime.date
    travelers: int
    budget: float
    trip_status: str
    description: str
    createdat: datetime.datetime
    updatedat: datetime.datetime

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

# FastAPI app instance
app = FastAPI(
    title="Trip Service",
    description="Service for managing trip bookings including car, hotel, and flight.",
    version="1.0.0"
)


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

@app.post("/trips/create")
async def create_trip(
    trip: Trip,
    current_user: dict = Depends(get_current_user)
):
    """
    CREATE A NEW TRIP
    """
    # Create the trip in the database
    with get_db_cursor() as (cursor, conn):
        cursor.execute(
            """
            INSERT INTO trips (userid, tripname, destination, startdate, enddate, travelers, budget, trip_status, description, createdat, updatedat)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING tripid
            """,
            (current_user["user_id"], trip.tripname, trip.destination, trip.startdate, trip.enddate, trip.travelers, trip.budget, trip.trip_status, trip.description)
        )
        tripid = cursor.fetchone()[0]
        conn.commit()
    return {"tripid": tripid}

@app.delete("/trips/delete/{tripid}")
async def delete_trip(
    tripid: uuid.UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    DELETE A TRIP
    """

    #in the frontend call the delete for everything car, flight and hotel, the the trips uuid
    # Check if the trip exists and belongs to the user
    with get_db_cursor() as (cursor, conn):
        cursor.execute(
            "SELECT * FROM trips WHERE tripid = %s AND userid = %s",
            (tripid, current_user["user_id"])
        )
        trip = cursor.fetchone()
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found or does not belong to the user"
            )
        
        # Delete the trip
        cursor.execute("DELETE FROM trips WHERE tripid = %s", (tripid,))

@app.post("/trips/update/{tripid}")
async def update_trip(
    tripid: uuid.UUID,
    trip: Trip,
    current_user: dict = Depends(get_current_user)
):
    """
    UPDATE A TRIP
    """
    # Check if the trip exists and belongs to the user
    with get_db_cursor() as (cursor, conn):
        cursor.execute(
            "SELECT * FROM trips WHERE tripid = %s AND userid = %s",
            (tripid, current_user["user_id"])
        )
        existing_trip = cursor.fetchone()
        if not existing_trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found or does not belong to the user"
            )

        # Update the trip
        cursor.execute(
            """
            UPDATE trips SET tripname = %s, destination = %s, startdate = %s, enddate = %s,
            travelers = %s, budget = %s, trip_status = %s, description = %s, updatedat = NOW()
            WHERE tripid = %s
            """,
            (trip.tripname, trip.destination, trip.startdate, trip.enddate,
             trip.travelers, trip.budget, trip.trip_status, trip.description, tripid)
        )
        conn.commit()
    return {"message": "Trip updated successfully"}

@app.get("/")
async def root():
    """
    Root endpoint to check if the service is running.
    """
    return {"message": "Trip Service is running!"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8012, reload=True)