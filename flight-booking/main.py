from fastapi import FastAPI, HTTPException, Depends, Query, Request, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict
import datetime
import uvicorn
import jwt
import os
import psycopg2
from dotenv import load_dotenv
from contextlib import contextmanager
import json
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from redis_rate_limit import rate_limit


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
        print("Database connection test successful")
        return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False

# Test database connection on startup
if not test_db_connection():
    print("Warning: Database connection failed. Service may not work properly.")
    # You can choose to exit here if DB is critical: sys.exit(1)
    
    
#fastapi  app
app = FastAPI(
    title="User Service",
    description="Microservice for flight booking and cancellation",
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

#models
# We'll use Literal for type safety in Python
FlightClass = Literal['Economy', 'Business', 'First']

class StopDetail(BaseModel):
    """
    Represents details of a stopover in a flight.
    """
    airport: str = Field(default="ORD", description="Airport code")
    arrivalTime: datetime.datetime = Field(default_factory=lambda: datetime.datetime(2025, 7, 15, 10, 30, 0), description="Arrival time at stop")
    departureTime: datetime.datetime = Field(default_factory=lambda: datetime.datetime(2025, 7, 15, 11, 30, 0), description="Departure time from stop")
    layoverDuration: str = Field(default="1h 0m", description="Layover duration")

class Flight(BaseModel):
    """
    Represents a single simulated flight.
    """
    airline: str = Field(default="Delta", description="Airline name")
    flightNumber: str = Field(default="DL1234", description="Flight number")
    departureAirport: str = Field(default="LAX", description="Departure airport code")
    destinationAirport: str = Field(default="JFK", description="Destination airport code")
    departureTime: datetime.datetime = Field(default_factory=lambda: datetime.datetime(2025, 7, 15, 8, 0, 0), description="Departure time")
    arrivalTime: datetime.datetime = Field(default_factory=lambda: datetime.datetime(2025, 7, 15, 14, 30, 0), description="Arrival time")
    duration: str = Field(default="6h 30m", description="Flight duration")
    numberOfStops: int = Field(default=1, description="Number of stops")
    stops: List[StopDetail] = Field(default=[], description="List of stops")
    status: Literal['On Time', 'Delayed', 'Cancelled'] = Field(default='On Time', description="Flight status")
    aircraft: str = Field(default="Boeing 737", description="Aircraft type")
    gate: str = Field(default="A12", description="Gate number")
    terminal: str = Field(default="A", description="Terminal")
    meal: bool = Field(default=True, description="Meal included")
    availableSeats: Dict[FlightClass, int] = Field(
        default={"Economy": 50, "Business": 15, "First": 5}, 
        description="Available seats by class"
    )
    prices: Dict[FlightClass, float] = Field(
        default={"Economy": 299.99, "Business": 799.99, "First": 1499.99}, 
        description="Prices by class"
    )
    bookingUrl: str = Field(default="#", description="Booking URL")
    choosenSeat: str = Field(default="Economy", description="Choosen seat type")
    
# Request models for body parameters
class FlightBookingRequest(BaseModel):
    flightid: str = Field(..., description="Flight booking ID")

class DeleteBookingRequest(BaseModel):
    flightid: str = Field(..., description="Flight booking ID to delete")

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
    except jwt.PyJWTError as e:
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

class BookingResponse(BaseModel):
    message: str
    booking_id: str
    user: User
    flight: Flight
    booking_timestamp: datetime.datetime

# Routes
@app.post("/flights/book", response_model=BookingResponse)
async def book_flight(
    request: Request,
    flight: Flight,
    trip_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint to book a flight with user authentication.
    Requires a valid JWT token in the Authorization header.
    
    Headers:
        Authorization: Bearer <jwt_token>
    
    Returns booking confirmation with user and flight details.
    """
    await rate_limit(request, limit=5, window=60, service="flight-booking")
    flight_conn = None
    bookings_conn = None
    flight_cursor = None
    bookings_cursor = None
    
    try:
        # Create user object from token data
        user = User(
            user_id=current_user["user_id"],
            email=current_user["email"],
            fname=current_user["fname"],
            lname=current_user["lname"]
        )
        
        # Get database connections
        flight_conn = get_db_connection()
        bookings_conn = get_bookings_db_connection()
        
        flight_cursor = flight_conn.cursor()
        bookings_cursor = bookings_conn.cursor()
        
        # Save the booking to database using two-phase commit
        try:
            # Create a shorter booking reference using just first 8 chars of UUID
            user_id_short = current_user['user_id'][:8]
            booking_reference = f"BK{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{user_id_short}"
            
            # Convert flight object to JSON with datetime handling
            flight_data = flight.dict()
            # Convert datetime objects to ISO format strings
            if isinstance(flight_data.get('departureTime'), datetime.datetime):
                flight_data['departureTime'] = flight_data['departureTime'].isoformat()
            if isinstance(flight_data.get('arrivalTime'), datetime.datetime):
                flight_data['arrivalTime'] = flight_data['arrivalTime'].isoformat()
            
            # Convert stops datetime objects if any
            if flight_data.get('stops'):
                for stop in flight_data['stops']:
                    if isinstance(stop.get('arrivalTime'), datetime.datetime):
                        stop['arrivalTime'] = stop['arrivalTime'].isoformat()
                    if isinstance(stop.get('departureTime'), datetime.datetime):
                        stop['departureTime'] = stop['departureTime'].isoformat()
            
            # Insert into flightbookings table
            flight_cursor.execute("""
                INSERT INTO flightbookings 
                (
                    userid,
                    inventoryid,
                    numberseats,
                    seatprice,
                    flightdetails,
                    trip_id,
                    created_at, 
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING flightbookingid
            """, (
                current_user["user_id"],
                "00000000-0000-0000-0000-000000000000",  # Placeholder inventory ID
                1,  # Default 1 seat
                flight.prices[flight.choosenSeat],  # Price for chosen seat class
                json.dumps(flight_data),  # Convert flight object to JSON with proper datetime handling
                trip_id if trip_id else None  
            ))
            
            booking_id = flight_cursor.fetchone()[0]
            
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
                    updated_at,
                    trip_id, 
                    provider_id,
                    location
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s, %s)
            """, (
                booking_id,
                booking_reference,
                "00000000-0000-0000-0000-000000000000",  # Placeholder for payment ID
                current_user["user_id"],
                "Flight",
                flight.prices[flight.choosenSeat],
                trip_id if trip_id else None,
                flight.airline,
                flight.departureAirport
            ))
            
            # Two-phase commit: both transactions must succeed
            flight_conn.commit()
            bookings_conn.commit()
            
        except Exception as db_error:
            # Rollback both transactions on any error
            if flight_conn:
                flight_conn.rollback()
            if bookings_conn:
                bookings_conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(db_error)}"
            )
        
        return BookingResponse(
            message="Flight booked successfully",
            booking_id=str(booking_id),  # Return the actual UUID, not the reference
            user=user,
            flight=flight,
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
        # Always close database connections
        if flight_cursor:
            flight_cursor.close()
        if bookings_cursor:
            bookings_cursor.close()
        if flight_conn:
            flight_conn.close()
        if bookings_conn:
            bookings_conn.close()

@app.get("/flights/booking/{booking_id}")
async def get_user_booking(
    request: Request,
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific booking for the authenticated user using booking id (UUID).
    Requires a valid JWT token in the Authorization header.

    Path parameter:
        booking_id: The flight booking UUID (e.g., 3ac77330-cade-4add-9a8c-3e4b3ea3bb81)
    """
    await rate_limit(request, limit=5, window=60, service="flight-booking")
    flight_conn = None
    bookings_conn = None
    flight_cursor = None
    bookings_cursor = None
    
    try:
        # Get database connections
        flight_conn = get_db_connection()
        
        flight_cursor = flight_conn.cursor()
        
        # Get flight details from flights database
        flight_cursor.execute("""
            SELECT 
                flightbookingid,
                userid,
                inventoryid,
                numberseats,
                seatprice,
                flightdetails,
                tripid,
                created_at,
                updated_at
            FROM flightbookings 
            WHERE flightbookingid = %s AND userid = %s
        """, (booking_id, current_user["user_id"]))
        
        flight_result = flight_cursor.fetchone()
        
        if not flight_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flight details not found"
            )
        
        return {
            "message": "User booking retrieved successfully",
            "flight_details": flight_result
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
        if flight_cursor:
            flight_cursor.close()
        if bookings_cursor:
            bookings_cursor.close()
        if flight_conn:
            flight_conn.close()
        if bookings_conn:
            bookings_conn.close()
        
@app.delete("/flights/delete")
async def delete_user_booking(
    delete_request: DeleteBookingRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a user's flight booking.
    Requires a valid JWT token in the Authorization header.
    
    Request body should contain:
    {
        "flightid": "12345678-1234-1234-1234-123456789012"
    }
    """
    await rate_limit(request, limit=5, window=60, service="flight-booking")
    flight_conn = None
    bookings_conn = None
    flight_cursor = None
    bookings_cursor = None
    
    try:
        # Get database connections
        flight_conn = get_db_connection()
        bookings_conn = get_bookings_db_connection()
        
        flight_cursor = flight_conn.cursor()
        bookings_cursor = bookings_conn.cursor()
        
        # First check if the booking exists and belongs to the user
        flight_cursor.execute("""
            SELECT flightbookingid FROM flightbookings
            WHERE flightbookingid = %s AND userid = %s
        """, (delete_request.flightid, current_user["user_id"]))
        
        if not flight_cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found or does not belong to the user"
            )
        
        # Delete from both databases using two-phase commit
        try:
            # First, find the actual booking UUID from the booking reference
            # Check if the flightid is a UUID or booking reference
            booking_id = None
            
            # Try to parse as UUID first
            try:
                import uuid
                uuid.UUID(delete_request.flightid)
                booking_id = delete_request.flightid  # It's already a UUID
            except ValueError:
                # It's a booking reference, need to look it up
                bookings_cursor.execute("""
                    SELECT bookingid FROM user_bookings 
                    WHERE booking_reference = %s AND userid = %s
                """, (delete_request.flightid, current_user["user_id"]))
                
                result = bookings_cursor.fetchone()
                if result:
                    booking_id = result[0]
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Booking not found with the provided reference"
                    )
            
            # Delete from flightbookings table using the UUID
            flight_cursor.execute("""
                DELETE FROM flightbookings
                WHERE flightbookingid = %s AND userid = %s
            """, (booking_id, current_user["user_id"]))
            
            # Delete from user_bookings table
            if booking_id == delete_request.flightid:
                # flightid was already a UUID
                bookings_cursor.execute("""
                    DELETE FROM user_bookings
                    WHERE bookingid = %s AND userid = %s
                """, (booking_id, current_user["user_id"]))
            else:
                # flightid was a booking reference
                bookings_cursor.execute("""
                    DELETE FROM user_bookings
                    WHERE booking_reference = %s AND userid = %s
                """, (delete_request.flightid, current_user["user_id"]))
            
            # Two-phase commit: both deletions must succeed
            flight_conn.commit()
            bookings_conn.commit()
            
        except Exception as db_error:
            # Rollback both transactions on any error
            if flight_conn:
                flight_conn.rollback()
            if bookings_conn:
                bookings_conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during deletion: {str(db_error)}"
            )

        return {
            "message": "Booking deleted successfully",
            "deleted_booking_id": delete_request.flightid,
            "user_id": current_user["user_id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        # Rollback both transactions on any error
        if flight_conn:
            flight_conn.rollback()
        if bookings_conn:
            bookings_conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete booking: {str(e)}"
        )
    finally:
        # Always close database connections
        if flight_cursor:
            flight_cursor.close()
        if bookings_cursor:
            bookings_cursor.close()
        if flight_conn:
            flight_conn.close()
        if bookings_conn:
            bookings_conn.close()


@app.get("/")
async def root():
    """
    Root endpoint providing service information.
    """
    return {
        "service": "Flight Booking Service",
        "version": "1.0.0",
        "endpoints": {
            "book_flight": "POST /flights/book (requires authentication)",
            "get_bookings": "GET /flights/bookings (requires authentication)"
        },
        "authentication": "Bearer token required in Authorization header"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8006, reload=True)