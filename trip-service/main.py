from fastapi import FastAPI, HTTPException, Depends, Query, status, Header, Request
from fastapi.middleware.cors import CORSMiddleware
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
from models import Car, Flight, Hotel
import uvicorn
import requests
import sys

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from redis_rate_limit import rate_limit


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

# Microservice URLs
CAR_SERVICE_URL = "http://localhost:8001"
HOTEL_SERVICE_URL = "http://localhost:8002"
FLIGHT_SERVICE_URL = "http://localhost:8004"  # Updated to fligh-booking service port

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

class TripBookingRequest(BaseModel):
    car: Optional[Car] = None
    hotel: Optional[Hotel] = None
    flight: Optional[Flight] = None
    car_insurance: Optional[Dict] = None
    hotel_insurance: Optional[Dict] = None
    flight_insurance: Optional[Dict] = None
    total_amount: float = Field(..., description="Total amount for all bookings")

class BookingResult(BaseModel):
    success: bool
    booking_id: Optional[str] = None
    booking_reference: Optional[str] = None
    error: Optional[str] = None

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
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

async def book_car(car: Car, insurance: Optional[Dict], total: float, trip_id: str, token: str) -> BookingResult:
    """Book a car via car service"""
    try:
        payload = {
            "car": car.dict(),
            "insurance": insurance,
            "total": total,
            "trip_id": trip_id
        }
        
        response = requests.post(
            f"{CAR_SERVICE_URL}/car/book",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return BookingResult(
                success=True,
                booking_id=result.get("booking_id"),
                booking_reference=result.get("booking_reference")
            )
        else:
            return BookingResult(success=False, error=f"Car booking failed: {response.text}")
            
    except Exception as e:
        return BookingResult(success=False, error=f"Car booking error: {str(e)}")

async def book_hotel(hotel: Hotel, insurance: Optional[Dict], total: float, trip_id: str, token: str) -> BookingResult:
    """Book a hotel via hotel service"""
    try:
        payload = {
            "hotel": hotel.dict(),
            "insurance": insurance,
            "total": total,
            "trip_id": trip_id
        }
        
        response = requests.post(
            f"{HOTEL_SERVICE_URL}/hotel/book",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return BookingResult(
                success=True,
                booking_id=result.get("booking_id"),
                booking_reference=result.get("booking_reference")
            )
        else:
            return BookingResult(success=False, error=f"Hotel booking failed: {response.text}")
            
    except Exception as e:
        return BookingResult(success=False, error=f"Hotel booking error: {str(e)}")

async def book_flight(flight: Flight, insurance: Optional[Dict], total: float, trip_id: str, token: str) -> BookingResult:
    """Book a flight via flight service"""
    try:
        payload = {
            "flight": flight.dict(),
            "insurance": insurance,
            "total": total,
            "trip_id": trip_id
        }
        
        response = requests.post(
            f"{FLIGHT_SERVICE_URL}/flight/book",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return BookingResult(
                success=True,
                booking_id=result.get("booking_id"),
                booking_reference=result.get("booking_reference")
            )
        else:
            return BookingResult(success=False, error=f"Flight booking failed: {response.text}")
            
    except Exception as e:
        return BookingResult(success=False, error=f"Flight booking error: {str(e)}")

async def cancel_booking(service_url: str, booking_id: str, token: str) -> bool:
    """Cancel a booking via its service"""
    try:
        if "car" in service_url:
            endpoint = f"{service_url}/cars/delete"
            payload = {"carid": booking_id}
        elif "hotel" in service_url:
            endpoint = f"{service_url}/hotels/delete"
            payload = {"hotelid": booking_id}
        elif "flight" in service_url:
            endpoint = f"{service_url}/flights/delete"
            payload = {"flightid": booking_id}
        else:
            return False
            
        response = requests.delete(
            endpoint,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Failed to cancel booking {booking_id}: {str(e)}")
        return False

@app.post("/trips/book/{tripid}")
async def book_trip_items(
    tripid: uuid.UUID,
    booking_request: TripBookingRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    authorization: str = Header(None)):
    """
    Book all trip items (car, hotel, flight) with distributed transaction.
    Either ALL bookings succeed or ALL are rolled back.
    """
    await rate_limit(request, limit=5, window=60, service="user-service")


    # Verify trip exists and belongs to user
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
    
    # Extract token from authorization header
    token = authorization.split(" ")[1] if authorization else ""
    trip_id_str = str(tripid)
    
    # Track successful bookings for rollback if needed
    successful_bookings = []
    booking_results = {}
    
    try:
        # Phase 1: Attempt all bookings concurrently
        booking_tasks = []
        service_types = []
        
        # Prepare booking tasks
        if booking_request.car:
            print("Preparing car booking...")
            booking_tasks.append(book_car(
                booking_request.car, 
                booking_request.car_insurance, 
                booking_request.total_amount, 
                trip_id_str, 
                token
            ))
            service_types.append("car")
        
        if booking_request.hotel:
            print("Preparing hotel booking...")
            booking_tasks.append(book_hotel(
                booking_request.hotel, 
                booking_request.hotel_insurance, 
                booking_request.total_amount, 
                trip_id_str, 
                token
            ))
            service_types.append("hotel")
        
        if booking_request.flight:
            print("Preparing flight booking...")
            booking_tasks.append(book_flight(
                booking_request.flight, 
                booking_request.flight_insurance, 
                booking_request.total_amount, 
                trip_id_str, 
                token
            ))
            service_types.append("flight")
        
        # Execute all bookings concurrently
        if booking_tasks:
            print(f"Executing {len(booking_tasks)} bookings concurrently...")
            import asyncio
            booking_results_list = await asyncio.gather(*booking_tasks)
            
            # Process results
            for i, result in enumerate(booking_results_list):
                service_type = service_types[i]
                
                if result.success:
                    successful_bookings.append((service_type, result.booking_id))
                    booking_results[service_type] = result.dict()
                    print(f"{service_type.capitalize()} booking successful: {result.booking_id}")
                else:
                    raise Exception(f"{service_type.capitalize()} booking failed: {result.error}")
        else:
            raise Exception("No booking items provided")
        
        # Phase 2: All bookings successful - Update trip with booking details
        with get_db_cursor() as (cursor, conn):
            # Build dynamic update query based on what was booked
            update_fields = []
            update_values = []
            
            if "car" in booking_results:
                update_fields.extend([
                    "carincluded = %s",
                    "carbookingid = %s", 
                    "carbookingreference = %s"
                ])
                update_values.extend([
                    True,
                    booking_results["car"]["booking_id"],
                    booking_results["car"]["booking_reference"]
                ])
            
            if "hotel" in booking_results:
                update_fields.extend([
                    "hotelincluded = %s",
                    "hotelbookingid = %s",
                    "hotelbookingreference = %s"
                ])
                update_values.extend([
                    True,
                    booking_results["hotel"]["booking_id"],
                    booking_results["hotel"]["booking_reference"]
                ])
            
            if "flight" in booking_results:
                update_fields.extend([
                    "flightincluded = %s",
                    "flightbookingid = %s",
                    "flightbookingreference = %s"
                ])
                update_values.extend([
                    True,
                    booking_results["flight"]["booking_id"],
                    booking_results["flight"]["booking_reference"]
                ])
            
            if update_fields:
                update_fields.append("updatedat = NOW()")
                update_values.append(tripid)
                
                query = f"""
                    UPDATE trips SET {', '.join(update_fields)}
                    WHERE tripid = %s
                """
                cursor.execute(query, update_values)
                conn.commit()
        
        return {
            "message": "All trip items booked successfully",
            "trip_id": str(tripid),
            "bookings": booking_results,
            "total_amount": booking_request.total_amount
        }
        
    except Exception as e:
        # Phase 3: Rollback - Cancel all successful bookings
        print(f"Booking failed, rolling back: {str(e)}")
        
        rollback_failures = []
        for service_type, booking_id in successful_bookings:
            print(f"Rolling back {service_type} booking: {booking_id}")
            
            if service_type == "car":
                success = await cancel_booking(CAR_SERVICE_URL, booking_id, token)
            elif service_type == "hotel":
                success = await cancel_booking(HOTEL_SERVICE_URL, booking_id, token)
            elif service_type == "flight":
                success = await cancel_booking(FLIGHT_SERVICE_URL, booking_id, token)
            else:
                success = False
                
            if not success:
                rollback_failures.append(f"{service_type}:{booking_id}")
        
        # Prepare error response
        error_message = f"Trip booking failed: {str(e)}"
        if rollback_failures:
            error_message += f". WARNING: Failed to rollback bookings: {', '.join(rollback_failures)}"
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )

@app.post("/trips/create")
async def create_trip(
    trip: Trip,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    CREATE A NEW TRIP
    """
    await rate_limit(request, limit=5, window=60, service="trip-service")
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
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    DELETE A TRIP
    """
    await rate_limit(request, limit=5, window=60, service="trip-service")

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
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    UPDATE A TRIP
    """
    await rate_limit(request, limit=5, window=60, service="trip-service")
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


@app.post('/trips/saveitems/{tripid}')
async def save_trip_items(
    request: Request,
    tripid: uuid.UUID,
    cars: Optional[List[Car]] = None,
    flights: Optional[List[Flight]] = None,
    hotels: Optional[List[Hotel]] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Save items (cars, flights, hotels) for a trip.
    """
    await rate_limit(request, limit=5, window=60, service="trip-service")
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

        # Save each item to the database
        
        conn.commit()
    return {"message": "Trip items saved successfully"}

@app.get("/")
async def root():
    """
    Root endpoint to check if the service is running.
    """
    return {"message": "Trip Service is running!"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8012, reload=True)