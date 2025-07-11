from fastapi import FastAPI, HTTPException, Depends, Query, status, Header
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict
import datetime
import uvicorn
import jwt
import os
import psycopg2
from dotenv import load_dotenv
import json


load_dotenv() #loading env variables
# JWT config
SECRET_KEY = os.getenv("JWT_SECRET") or "super-secret"
ALGORITHM = os.getenv("JWT_ALGORITHM") or "HS256"

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
    cursor.execute("""SELECT * FROM flightbookings""")
    print(cursor.fetchall())
except Exception as e:
    print(f"Database connection failed: {e}")
    raise
    
    
#fastapi  app
app = FastAPI(
    title="User Service",
    description="Microservice for flight booking and cancellation",
    version="1.0.0"
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
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
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
    user_id: int
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
    flight: Flight,
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint to book a flight with user authentication.
    Requires a valid JWT token in the Authorization header.
    
    Headers:
        Authorization: Bearer <jwt_token>
    
    Returns booking confirmation with user and flight details.
    """
    try:

        
        # Create user object from token data
        user = User(
            user_id=current_user["user_id"],
            email=current_user["email"],
            fname=current_user["fname"],
            lname=current_user["lname"]
        )
        
        # Save the booking to database
        try:
            booking_reference = f"BK{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{current_user['user_id']}"
            cursor.execute("""
                INSERT INTO flightbookings 
                (
                    userid,
                    inventoryid,
                    numberseats,
                    seatprice,
                    flightdetails,
                    tripid,
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
                json.dumps(flight.dict()),  # Convert flight object to JSON
                None  # trip_id
            ))
            
            booking_id = cursor.fetchone()[0]
           #writing to the booking page
            cursor.execute("""
                           INSERT INTO bookings.user_bookings
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
                "Flight",
                flight.prices[flight.choosenSeat]
            ))
            conn.commit()
            
        except Exception as db_error:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(db_error)}"
            )
        
        return BookingResponse(
            message="Flight booked successfully",
            booking_id=booking_reference,
            user=user,
            flight=flight,
            booking_timestamp=datetime.datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Booking failed: {str(e)}"
        )

@app.get("/flights/booking/{flightid}")
async def get_user_booking(
    flightid: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific booking for the authenticated user.
    Requires a valid JWT token in the Authorization header.
    
    Path parameter:
        flightid: The flight booking ID
    """
    try:
        # Fetch bookings from database
        cursor.execute("""
            SELECT 
                flightdetails
            FROM flightbookings 
            WHERE flightbookingid = %s AND userid = %s
        """, (flightid, current_user["user_id"]))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found or does not belong to the user"
            )
        
        flight_booking = result[0]
        
        return {
            "message": "User booking retrieved successfully",
            "booking_id": flightid,
            "user_id": current_user["user_id"],
            "booking_details": flight_booking
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve booking: {str(e)}"
        )
        
@app.delete("/flights/delete")
async def delete_user_booking(
    request: DeleteBookingRequest,
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
    try:
        # First check if the booking exists and belongs to the user
        cursor.execute("""
            SELECT flightbookingid FROM flightbookings
            WHERE flightbookingid = %s AND userid = %s
        """, (request.flightid, current_user["user_id"]))
        
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found or does not belong to the user"
            )
        
        # Delete from both tables
        cursor.execute("""
            DELETE FROM flightbookings
            WHERE flightbookingid = %s AND userid = %s
        """, (request.flightid, current_user["user_id"]))
        
        cursor.execute("""
            DELETE FROM managebookings.user_bookings
            WHERE bookingid = %s AND userid = %s
        """, (request.flightid, current_user["user_id"]))
        
        conn.commit()

        return {
            "message": "Booking deleted successfully",
            "deleted_booking_id": request.flightid,
            "user_id": current_user["user_id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete booking: {str(e)}"
        )

# @app.get("/flights/bookings")
# async def get_all_user_bookings(current_user: dict = Depends(get_current_user)):
#     """
#     Get all bookings for the authenticated user.
#     Requires a valid JWT token in the Authorization header.
#     """
#     try:
#         # Fetch all bookings from database
#         cursor.execute("""
#             SELECT 
#                 flightbookingid,
#                 numberseats,
#                 seatprice,
#                 bookingdatetime,
#                 flightdetails
#             FROM flightbookings 
#             WHERE userid = %s 
#             ORDER BY bookingdatetime DESC
#         """, (current_user["user_id"],))
        
#         results = cursor.fetchall()
        
#         bookings = []
#         for booking in results:
#             bookings.append({
#                 "booking_id": str(booking[0]),
#                 "number_seats": booking[1],
#                 "seat_price": float(booking[2]),
#                 "booking_datetime": booking[3].isoformat() if booking[3] else None,
#                 "flight_details": booking[4]
#             })
        
#         return {
#             "message": "User bookings retrieved successfully",
#             "user_id": current_user["user_id"],
#             "total_bookings": len(bookings),
#             "bookings": bookings
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to retrieve bookings: {str(e)}"
#         )

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
    uvicorn.run("main:app", host="127.0.0.1", port=8006, reload=True)