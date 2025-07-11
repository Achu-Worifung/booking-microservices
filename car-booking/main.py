from fastapi import FastAPI, HTTPException, Depends, Query, status, Header
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict
import datetime
import uvicorn
import jwt
import os
import psycopg2
import uuid
from dotenv import load_dotenv
from contextlib import contextmanager
import json


load_dotenv() #loading env variables

# JWT config
SECRET_KEY = os.getenv("JWT_SECRET") or "super-secret"
ALGORITHM = os.getenv("JWT_ALGORITHM") or "HS256"

# Database connection configuration
DB_CONFIG = {
    "user": os.getenv("PGUSER"),
    "host": os.getenv("PGHOST"),
    "database": os.getenv("PGDATABASE"),
    "password": os.getenv("password"),
    "port": os.getenv("PGPORT")
}

# Bookings database configuration (separate database)
BOOKINGS_DB_CONFIG = {
    "user": os.getenv("PGUSER"),
    "host": os.getenv("PGHOST"),
    "database": "bookings",  # Different database name
    "password": os.getenv("password"),
    "port": os.getenv("PGPORT")
}

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

def get_bookings_db_connection():
    """
    Create and return a new bookings database connection.
    """
    try:
        conn = psycopg2.connect(**BOOKINGS_DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Bookings database connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bookings database connection failed"
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
        print("Car database connection test successful")
        return True
    except Exception as e:
        print(f"Car database connection test failed: {e}")
        return False

# Test database connection on startup
if not test_db_connection():
    print("Warning: Car database connection failed. Service may not work properly.")
    # You can choose to exit here if DB is critical: sys.exit(1)
    
    
#fastapi  app
app = FastAPI(
    title="Car Booking Service",
    description="Microservice for car rental booking and management",
    version="1.0.0"
)

#models
class Car(BaseModel):
    """
    Represents a car available for booking.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    make: str
    model: str
    year: int
    color: List[str]
    seat: int
    type: Literal['Sedan', 'SUV', 'Truck', 'Van', 'Convertible', 'Economy', 'Luxury', 'Hybrid', 'Electric', 'Coupe', 'Sports', 'Minivan']
    price_per_day: float
    feature: str
    transmission: Literal['Automatic', 'Manual']
    fuel_type: Literal['Petrol', 'Diesel', 'Electric', 'Hybrid']
    available: bool = True
    rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Rating of the car from 0 to 5")
class carTemplate(BaseModel):
    make: str
    model: List[str]
# Request models for body parameters
class CarBookingRequest(BaseModel):
    carid: str = Field(..., description="Car booking ID")

class DeleteBookingRequest(BaseModel):
    carid: str = Field(..., description="Car booking ID to delete")

# JWT Token Functions
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

# User model for response
class User(BaseModel):
    user_id: str  # Changed from int to str to handle UUID
    email: str
    fname: str
    lname: str

class Insurance(BaseModel):
    insType: str 
    insTotal: float = Field(..., description="Total insurance amount for the booking")

class BookingRequest(BaseModel):
    car: Car
    insurance: Optional[Insurance] = None
    total: float = Field(..., description="Total amount for the booking")
    trip_id: Optional[str] = None

class BookingResponse(BaseModel):
    message: str
    booking_id: str
    booking_reference: str
    user: User
    car: Car
    booking_timestamp: datetime.datetime

# Routes
@app.post("/car/book", response_model=BookingResponse)
async def book_car(
    booking_request: BookingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint to book a car rental with user authentication.
    Requires a valid JWT token in the Authorization header.
    
    Headers:
        Authorization: Bearer <jwt_token>
    
    Returns booking confirmation with user and car details.
    """
    car_conn = None
    bookings_conn = None
    car_cursor = None
    bookings_cursor = None
    
    try:
        # Extract data from request model
        car = booking_request.car
        insurance = booking_request.insurance
        total = booking_request.total
        trip_id = booking_request.trip_id
        
        # Create user object from token data
        user = User(
            user_id=current_user["user_id"],
            email=current_user["email"],
            fname=current_user["fname"],
            lname=current_user["lname"]
        )
        
        # Get database connections
        car_conn = get_db_connection()
        bookings_conn = get_bookings_db_connection()
        
        car_cursor = car_conn.cursor()
        bookings_cursor = bookings_conn.cursor()
        
        # Save the booking to database using two-phase commit
        try:
            # Create a shorter booking reference using just first 8 chars of UUID
            user_id_short = current_user['user_id'][:8]
            booking_reference = f"CR{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{user_id_short}"
            
            # Convert car object to JSON with datetime handling
            car_data = car.dict()

            user_id_short = current_user['user_id'][:8]
            booking_reference = f"BK{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{user_id_short}"
            
            # Insert into carbookings table
            car_cursor.execute("""
                INSERT INTO carbookings 
                (
                    userid,
                    bookingreference,
                    bookingdate,
                    bookingdetails,
                    paymentid,
                    insuranceamount,
                    insurancetype,
                    totalamount,
                    trip_id,
                    created_at, 
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING carbookingid
            """, (
                current_user["user_id"],
                booking_reference,
                datetime.datetime.now(),  # bookingdate
                json.dumps(car_data),  # bookingdetails as JSON
                "00000000-0000-0000-0000-000000000000",  # paymentid
                insurance.insTotal if insurance else 0.0,  # insuranceamount
                insurance.insType if insurance else None,  # insurancetype
                total if total else 0.0,  # totalamount
                trip_id if trip_id else None,  # trip_id
                datetime.datetime.now(),  # created_at
                datetime.datetime.now()  # updated_at
            ))
            
            booking_id = car_cursor.fetchone()[0]
            
            # Insert into user_bookings table in bookings database
            bookings_cursor.execute("""
                INSERT INTO user_bookings
                (
                    bookingid,
                    booking_reference,
                    paymentid,
                    userid,
                    bookingtype,
                    totalamount, 
                    created_at,
                    updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                booking_id,
                booking_reference,
                "00000000-0000-0000-0000-000000000000",  # Placeholder for payment ID
                current_user["user_id"],
                "Car",
                total  # totalamount
            ))
            
            # Two-phase commit: both transactions must succeed
            car_conn.commit()
            bookings_conn.commit()
            
        except Exception as db_error:
            # Rollback both transactions on any error
            if car_conn:
                car_conn.rollback()
            if bookings_conn:
                bookings_conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(db_error)}"
            )
        
        return BookingResponse(
            message="Car booked successfully",
            booking_id=str(booking_id),  # Return the actual UUID, not the reference
            booking_reference=booking_reference,
            user=user,
            car=car,
            booking_timestamp=datetime.datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Booking failed: {str(e)}"
        )
    finally:
        if car_cursor:
            car_cursor.close()
        if bookings_cursor:
            bookings_cursor.close()
        if car_conn:
            car_conn.close()
        if bookings_conn:
            bookings_conn.close()

@app.get("/cars/booking/{booking_id}")
async def get_user_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific car booking for the authenticated user using booking id (UUID).
    Requires a valid JWT token in the Authorization header.

    Path parameter:
        booking_id: The car booking UUID (e.g., 3ac77330-cade-4add-9a8c-3e4b3ea3bb81)
    """
    car_conn = None
    bookings_conn = None
    car_cursor = None
    bookings_cursor = None
    
    try:
        # Get database connections
        car_conn = get_db_connection()
        
        car_cursor = car_conn.cursor()
        
        # Get car details from cars database
        car_cursor.execute("""
            SELECT 
                carbookingid,
                userid,
                bookingdate,
                bookingdetails,
                paymentid,
                insuranceamount,
                insurancetype,
                totalamount,
                created_at
            FROM carbookings 
            WHERE carbookingid = %s AND userid = %s
        """, (booking_id, current_user["user_id"]))
        
        car_result = car_cursor.fetchone()
        
        if not car_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Car booking not found"
            )
        
        return {
            "message": "User car booking retrieved successfully",
            "car_details": car_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve booking: {str(e)}"
        )
    finally:
        # Always close database connections
        if car_cursor:
            car_cursor.close()
        if bookings_cursor:
            bookings_cursor.close()
        if car_conn:
            car_conn.close()
        if bookings_conn:
            bookings_conn.close()
        
@app.delete("/cars/delete")
async def delete_user_booking(
    request: DeleteBookingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a user's car booking.
    Requires a valid JWT token in the Authorization header.
    
    Request body should contain:
    {
        "carid": "12345678-1234-1234-1234-123456789012"
    }
    """
    car_conn = None
    bookings_conn = None
    car_cursor = None
    bookings_cursor = None
    
    try:
        # Get database connections
        car_conn = get_db_connection()
        bookings_conn = get_bookings_db_connection()
        
        car_cursor = car_conn.cursor()
        bookings_cursor = bookings_conn.cursor()
        
        # First check if the booking exists and belongs to the user
        car_cursor.execute("""
            SELECT carbookingid FROM carbookings
            WHERE carbookingid = %s AND userid = %s
        """, (request.carid, current_user["user_id"]))
        
        if not car_cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Car booking not found or does not belong to the user"
            )
        
        # Delete from both databases using two-phase commit
        try:
            # First, find the actual booking UUID from the booking reference
            # Check if the carid is a UUID or booking reference
            booking_id = None
            
            # Try to parse as UUID first
            try:
                uuid.UUID(request.carid)
                booking_id = request.carid  # It's already a UUID
            except ValueError:
                # It's a booking reference, need to look it up
                bookings_cursor.execute("""
                    SELECT bookingid FROM user_bookings 
                    WHERE booking_reference = %s AND userid = %s
                """, (request.carid, current_user["user_id"]))
                
                result = bookings_cursor.fetchone()
                if result:
                    booking_id = result[0]
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Booking not found with the provided reference"
                    )
            
            # Delete from carbookings table using the UUID
            car_cursor.execute("""
                DELETE FROM carbookings
                WHERE carbookingid = %s AND userid = %s
            """, (booking_id, current_user["user_id"]))
            
            # Delete from user_bookings table
            if booking_id == request.carid:
                # carid was already a UUID
                bookings_cursor.execute("""
                    DELETE FROM user_bookings
                    WHERE bookingid = %s AND userid = %s
                """, (booking_id, current_user["user_id"]))
            else:
                # carid was a booking reference
                bookings_cursor.execute("""
                    DELETE FROM user_bookings
                    WHERE booking_reference = %s AND userid = %s
                """, (request.carid, current_user["user_id"]))
            
            # Two-phase commit: both deletions must succeed
            car_conn.commit()
            bookings_conn.commit()
            
        except Exception as db_error:
            # Rollback both transactions on any error
            if car_conn:
                car_conn.rollback()
            if bookings_conn:
                bookings_conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during deletion: {str(db_error)}"
            )

        return {
            "message": "Car booking deleted successfully",
            "deleted_booking_id": request.carid,
            "user_id": current_user["user_id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        # Rollback both transactions on any error
        if car_conn:
            car_conn.rollback()
        if bookings_conn:
            bookings_conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete car booking: {str(e)}"
        )
    finally:
        # Always close database connections
        if car_cursor:
            car_cursor.close()
        if bookings_cursor:
            bookings_cursor.close()
        if car_conn:
            car_conn.close()
        if bookings_conn:
            bookings_conn.close()

@app.get("/")
async def root():
    """
    Root endpoint providing service information.
    """
    return {
        "service": "Car Booking Service",
        "version": "1.0.0",
        "endpoints": {
            "book_car": "POST /cars/book (requires authentication)",
            "get_booking": "GET /cars/booking/{booking_id} (requires authentication)",
            "delete_booking": "DELETE /cars/delete (requires authentication)"
        },
        "authentication": "Bearer token required in Authorization header"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)