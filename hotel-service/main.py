
from fastapi import FastAPI, HTTPException, Depends, Query, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict
import datetime
import uvicorn
import jwt
import os
import psycopg2
import uuid
import random
from dotenv import load_dotenv
from contextlib import contextmanager
import json


load_dotenv() #loading env variables

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)

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
        print("Hotel database connection test successful")
        return True
    except Exception as e:
        print(f"Hotel database connection test failed: {e}")
        return False

# Test database connection on startup
if not test_db_connection():
    print("Warning: Hotel database connection failed. Service may not work properly.")
    # You can choose to exit here if DB is critical: sys.exit(1)
    
    
#fastapi  app
app = FastAPI(
    title="Hotel Booking Service",
    description="Microservice for hotel booking and management",
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
vendorNames = Literal['Marriott', 'Hilton', 'Hyatt', 'Sheraton', 'Radisson', 'InterContinental', 'Holiday Inn', 'Ritz-Carlton', 'Four Seasons', 'Wyndham', 'Best Western', 'Motel 6', 'Super 8', 'Comfort Inn', 'Quality Inn', 'Days Inn', 'Econo Lodge', 'Red Roof Inn', 'La Quinta Inn', 'Sleep Inn']
attraction = Literal['Beach', 'Park', 'Museum', 'Shopping Mall', 'Restaurant', 'Theater', 'Zoo', 'Aquarium', 'Historical Site', 'Amusement Park', 'Sports Stadium', 'Concert Hall', 'Art Gallery', 'Botanical Garden', 'Nature Reserve', 'Scenic Viewpoint', 'Cultural Center', 'Nightlife District', 'Festival Venue']

class RoomDetails(BaseModel):
    """
    Represents details of a room in a hotel.
    """
    type: str
    pricePerNight: float
    mostPopular: bool
    cancellationPolicy: str
    availableRooms: int

class Attraction(BaseModel):
    """
    Represents nearby attraction for a hotel.
    """
    name: str
    type: attraction
    distance: float

class Review(BaseModel):
    """
    Represents a review for a hotel.
    """
    username: str
    rating: float
    comment: str
    date: datetime.datetime

class CheckIn(BaseModel):
    """
    Represents the check-in details for a hotel stay.
    """
    startTime: str
    endTime: str
    contactless: bool
    express: bool
    minAge: int

class Checkout(BaseModel):
    """
    Represents the checkout details for a hotel stay.
    """
    time: str
    contactless: bool
    express: bool
    lateFeeApplicable: bool

class HotelPolicy(BaseModel):
    """
    Represents the policy details for a hotel.
    """
    checkin: CheckIn
    checkout: Checkout
    petsAllowed: bool
    childrenPolicy: str
    extraBeds: str
    cribAvailability: str
    accessMethods: List[str]
    safetyFeatures: List[str]
    houseKeepingPolicy: str

class FAQ(BaseModel):
    """
    Represents a frequently asked question for a hotel.
    """
    question: str
    answer: str

class Hotel(BaseModel):
    """
    Represents a hotel available for booking.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str
    vendor: vendorNames
    address: str
    city: str
    state: str
    country: str
    description: str
    postalCode: str
    phoneNumber: str
    email: str
    website: str
    rating: float
    reviews: List[Review]
    roomDetails: List[RoomDetails]
    amenities: List[str]
    nearbyAttractions: List[Attraction]
    policies: HotelPolicy
    faq: List[FAQ]
    
class HotelTemplate(BaseModel):
    name: str
    vendor: List[str]

# Request models for body parameters
class HotelBookingRequest(BaseModel):
    hotelid: str = Field(..., description="Hotel booking ID")

class DeleteBookingRequest(BaseModel):
    hotelid: str = Field(..., description="Hotel booking ID to delete")

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
    hotel: Hotel
    insurance: Optional[Insurance] = None
    total: float = Field(..., description="Total amount for the booking")
    trip_id: Optional[str] = None

class BookingResponse(BaseModel):
    message: str
    booking_id: str
    booking_reference: str
    user: User
    hotel: Hotel
    booking_timestamp: datetime.datetime

# Routes
@app.post("/hotel/book", response_model=BookingResponse)
async def book_hotel(
    booking_request: BookingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint to book a hotel with user authentication.
    Requires a valid JWT token in the Authorization header.
    
    Headers:
        Authorization: Bearer <jwt_token>
    
    Returns booking confirmation with user and hotel details.
    """
    hotel_conn = None
    bookings_conn = None
    hotel_cursor = None
    bookings_cursor = None
    
    try:
        # Extract data from request model
        hotel = booking_request.hotel
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
        hotel_conn = get_db_connection()
        bookings_conn = get_bookings_db_connection()
        
        hotel_cursor = hotel_conn.cursor()
        bookings_cursor = bookings_conn.cursor()
        
        # Save the booking to database using two-phase commit
        try:
            # Create a shorter booking reference using just first 8 chars of UUID
            user_id_short = current_user['user_id'][:8]
            booking_reference = f"HT{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{user_id_short}"
            
            # Convert hotel object to JSON with datetime handling
            hotel_data = hotel.dict()

            user_id_short = current_user['user_id'][:8]
            booking_reference = f"BK{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{user_id_short}"
            
            # Insert into hotelbookings table
            hotel_cursor.execute("""
                INSERT INTO hotelbookings 
                (
                    userid,
                    bookingreference,
                    bookingdate,
                    bookingdetails,
                    paymentid,
                    totalamount,
                    trip_id,
                    created_at, 
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING hotelbookingid
            """, (
                current_user["user_id"],
                booking_reference,
                datetime.datetime.now(),  # bookingdate
                json.dumps(hotel_data, cls=DateTimeEncoder),  # bookingdetails as JSON with datetime handling
                "00000000-0000-0000-0000-000000000000",  # paymentid
                total if total else 0.0,  # totalamount
                trip_id if trip_id else None,  # trip_id
                datetime.datetime.now(),  # created_at
                datetime.datetime.now()  # updated_at
            ))
            
            booking_id = hotel_cursor.fetchone()[0]
            
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
                    trip_id
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
            """, (
                booking_id,
                booking_reference,
                "00000000-0000-0000-0000-000000000000",  # Placeholder for payment ID
                current_user["user_id"],
                "Hotel",
                total,  # totalamount
                trip_id if trip_id else None  # trip_id (optional, can be None if not provided
            ))
            
            # Two-phase commit: both transactions must succeed
            hotel_conn.commit()
            bookings_conn.commit()
            
        except Exception as db_error:
            # Rollback both transactions on any error
            if hotel_conn:
                hotel_conn.rollback()
            if bookings_conn:
                bookings_conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(db_error)}"
            )
        
        return BookingResponse(
            message="Hotel booked successfully",
            booking_id=str(booking_id),  # Return the actual UUID, not the reference
            booking_reference=booking_reference,
            user=user,
            hotel=hotel,
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
        if hotel_cursor:
            hotel_cursor.close()
        if bookings_cursor:
            bookings_cursor.close()
        if hotel_conn:
            hotel_conn.close()
        if bookings_conn:
            bookings_conn.close()

@app.get("/hotels/booking/{booking_id}")
async def get_user_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific hotel booking for the authenticated user using booking id (UUID).
    Requires a valid JWT token in the Authorization header.

    Path parameter:
        booking_id: The hotel booking UUID (e.g., 3ac77330-cade-4add-9a8c-3e4b3ea3bb81)
    """
    hotel_conn = None
    bookings_conn = None
    hotel_cursor = None
    bookings_cursor = None
    
    try:
        # Get database connections
        hotel_conn = get_db_connection()
        
        hotel_cursor = hotel_conn.cursor()
        
        # Get hotel details from hotels database
        hotel_cursor.execute("""
            SELECT 
                hotelbookingid,
                bookingreference,
                userid,
                bookingdate,
                bookingdetails,
                paymentid,
                totalamount,
                created_at
            FROM hotelbookings 
            WHERE hotelbookingid = %s AND userid = %s
        """, (booking_id, current_user["user_id"]))
        
        hotel_result = hotel_cursor.fetchone()
        
        if not hotel_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hotel booking not found"
            )
        
        return {
            "message": "User hotel booking retrieved successfully",
            "hotel_details": hotel_result
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
        if hotel_cursor:
            hotel_cursor.close()
        if bookings_cursor:
            bookings_cursor.close()
        if hotel_conn:
            hotel_conn.close()
        if bookings_conn:
            bookings_conn.close()
        
@app.delete("/hotels/delete")
async def delete_user_booking(
    request: DeleteBookingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a user's hotel booking.
    Requires a valid JWT token in the Authorization header.
    
    Request body should contain:
    {
        "hotelid": "12345678-1234-1234-1234-123456789012"
    }
    """
    hotel_conn = None
    bookings_conn = None
    hotel_cursor = None
    bookings_cursor = None
    
    try:
        # Get database connections
        hotel_conn = get_db_connection()
        bookings_conn = get_bookings_db_connection()
        
        hotel_cursor = hotel_conn.cursor()
        bookings_cursor = bookings_conn.cursor()
        
        # First check if the booking exists and belongs to the user
        hotel_cursor.execute("""
            SELECT hotelbookingid FROM hotelbookings
            WHERE hotelbookingid = %s AND userid = %s
        """, (request.hotelid, current_user["user_id"]))
        
        if not hotel_cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hotel booking not found or does not belong to the user"
            )
        
        # Delete from both databases using two-phase commit
        try:
            # First, find the actual booking UUID from the booking reference
            # Check if the hotelid is a UUID or booking reference
            booking_id = None
            
            # Try to parse as UUID first
            try:
                uuid.UUID(request.hotelid)
                booking_id = request.hotelid  # It's already a UUID
            except ValueError:
                # It's a booking reference, need to look it up
                bookings_cursor.execute("""
                    SELECT bookingid FROM user_bookings 
                    WHERE booking_reference = %s AND userid = %s
                """, (request.hotelid, current_user["user_id"]))
                
                result = bookings_cursor.fetchone()
                if result:
                    booking_id = result[0]
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Booking not found with the provided reference"
                    )
            
            # Delete from hotelbookings table using the UUID
            hotel_cursor.execute("""
                DELETE FROM hotelbookings
                WHERE hotelbookingid = %s AND userid = %s
            """, (booking_id, current_user["user_id"]))
            
            # Delete from user_bookings table
            if booking_id == request.hotelid:
                # hotelid was already a UUID
                bookings_cursor.execute("""
                    DELETE FROM user_bookings
                    WHERE bookingid = %s AND userid = %s
                """, (booking_id, current_user["user_id"]))
            else:
                # hotelid was a booking reference
                bookings_cursor.execute("""
                    DELETE FROM user_bookings
                    WHERE booking_reference = %s AND userid = %s
                """, (request.hotelid, current_user["user_id"]))
            
            # Two-phase commit: both deletions must succeed
            hotel_conn.commit()
            bookings_conn.commit()
            
        except Exception as db_error:
            # Rollback both transactions on any error
            if hotel_conn:
                hotel_conn.rollback()
            if bookings_conn:
                bookings_conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during deletion: {str(db_error)}"
            )

        return {
            "message": "Hotel booking deleted successfully",
            "deleted_booking_id": request.hotelid,
            "user_id": current_user["user_id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        # Rollback both transactions on any error
        if hotel_conn:
            hotel_conn.rollback()
        if bookings_conn:
            bookings_conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete hotel booking: {str(e)}"
        )
    finally:
        # Always close database connections
        if hotel_cursor:
            hotel_cursor.close()
        if bookings_cursor:
            bookings_cursor.close()
        if hotel_conn:
            hotel_conn.close()
        if bookings_conn:
            bookings_conn.close()

@app.get("/")
async def root():
    """
    Root endpoint providing service information.
    """
    return {
        "service": "Hotel Booking Service",
        "version": "1.0.0",
        "endpoints": {
            "book_hotel": "POST /hotel/book (requires authentication)",
            "get_booking": "GET /hotels/booking/{booking_id} (requires authentication)",
            "delete_booking": "DELETE /hotels/delete (requires authentication)"
        },
        "authentication": "Bearer token required in Authorization header"
    }
    



def getRandom(items: List[str]) -> str:
    """
    Returns a random element from the provided list.
    """
    return random.choice(items)

hotelNames = [
  'Azure Coast Retreat', 'Golden Bay Suites', 'CityView Inn', 'Palm Garden Lodge',
  'Ocean Breeze Hotel', 'Downtown Deluxe', 'Harbor Haven', 'Skyline Resort',
  'Desert Rose Oasis', 'Mountain Crest Lodge', 'Riverside Rendezvous',
  'The Grand Central', 'Sunset Serenity Suites', 'Aqua Vista Resort',
  'The Urban Nook', 'Tranquil Pines Inn', 'Crimson Sky Hotel',
  'Sapphire Sands Resort', 'Emerald Gardens Hotel', 'Pinnacle Peak Lodge',
  'Canyon Ridge Inn', 'Starfall Hotel & Suites', 'Lakeview Manor',
  'The Gilded Compass', 'Vivid Bloom Resort', 'Orchid Heights Hotel',
  'Moonlit Cove Inn', 'Terra Nova Suites',
  'The Obsidian Palace', 'Whispering Pines Resort', 'Metropolitan Grand',
  'Coral Sands Beachfront', 'Stone Creek Inn', 'The Beacon Hotel',
  'Harmony Heights Retreat', 'Silver Stream Lodge', 'Olympus Towers',
  'Mystic Falls Hotel', 'The Royal Bloom', 'Copperleaf Residences',
  'Zephyr Sands Resort', 'Polaris Grand Hotel', 'Ironwood Manor',
  'The Sanctuary Suites', 'Cascading Waters Hotel', 'The Velvet Sparrow Inn'
]

descriptions = [
  'A luxurious stay near the city’s heart, featuring modern rooms and exceptional service.',
  'Coastal bliss with scenic views and beach access.',
  'Budget-friendly comfort close to major attractions and public transit.',
  'Perfect for families and business travelers alike.',
  'Contemporary hotel with full-service dining and rooftop views.',
  'Nestled in a peaceful desert landscape, offering a serene escape with stunning views.',
  'An eco-friendly retreat with lush gardens and sustainable practices.',
  'Historic charm meets modern convenience in this beautifully restored hotel.',
  'Ideal for adventurers, with easy access to hiking trails and outdoor activities.',
  'Sophisticated urban living with state-of-the-art facilities and vibrant nightlife nearby.',
  'Family-friendly resort featuring a water park, kids\' club, and diverse dining options.',
  'Exclusive boutique hotel offering personalized service and unique, artfully designed rooms.',
  'Overlooking the tranquil lake, a perfect spot for relaxation and water sports.',
  'Experience unparalleled luxury with personalized concierge service and gourmet dining.',
  'A vibrant and artistic hotel, perfect for creatives and those seeking inspiration.',
  'Comfortable and convenient, located just minutes from the airport with shuttle service.',
  'Charming countryside inn offering a cozy atmosphere and delicious home-cooked meals.',
  'Modern design meets ultimate comfort in this new downtown hotspot.',
  'Discover a hidden gem offering unparalleled tranquility, complete with a private beach and holistic wellness programs.',
  'The quintessential business hotel, providing state-of-the-art conference facilities, executive lounges, and seamless connectivity.',
  'Immerse yourself in local culture at this charming guesthouse, a short walk from historical landmarks and bustling markets.',
  'An all-inclusive paradise designed for ultimate relaxation, featuring multiple pools, gourmet restaurants, and evening entertainment.',
  'Your home away from home, these spacious suites come with fully equipped kitchens and separate living areas, perfect for extended stays.',
  'Perched high above the city, enjoy panoramic skyline views from every room, complemented by a Michelin-starred restaurant and a rooftop bar.',
  'A pet-friendly establishment that goes above and beyond, offering pet amenities, designated play areas, and special treats for your furry friends.',
  'Experience sustainable luxury at its finest, with locally sourced cuisine, solar-powered facilities, and a commitment to environmental preservation.',
  'This vibrant and trendy hotel boasts unique themed rooms, a lively lobby bar, and is situated in the heart of the city\'s entertainment district.',
  'Designed for the discerning traveler, our hotel features bespoke services, an exclusive members-only lounge, and direct access to high-end shopping.',
]

reviewsPool = [
  {'text': 'Exceptional service and spotless rooms. Truly a five-star experience!', 'rating': 5},
  {'text': 'Amazing ocean view and very clean! Woke up to paradise every day.', 'rating': 5},
  {'text': 'Would definitely stay again. Loved the breakfast spread; so many options!', 'rating': 4},
  {'text': 'Not bad for the price, especially given the good location. A solid choice.', 'rating': 3},
  {'text': 'Super friendly staff and cozy rooms. Felt very welcomed from arrival to departure.', 'rating': 4},
  {'text': 'Close to everything important. Comfortable beds ensured a great night\'s sleep.', 'rating': 4},
  {'text': 'Decent amenities overall, and elevator access was really helpful for our luggage.', 'rating': 3},
  {'text': 'A bit noisy at night due to its very central location, but otherwise excellent.', 'rating': 3},
  {'text': 'Loved the smart locks and seamless check-in process. Very modern and efficient.', 'rating': 5},
  {'text': 'Fantastic pool area and friendly poolside service. The kids absolutely loved it!', 'rating': 5},
  {'text': 'The hotel restaurant had delicious food and a truly great atmosphere for dinner.', 'rating': 4},
  {'text': 'Quiet and relaxing, perfect for a peaceful getaway. Just what we needed.', 'rating': 5},
  {'text': 'Great value for money, genuinely exceeded my expectations for a budget stay.', 'rating': 4},
  {'text': 'Rooms were spacious and very well maintained, felt fresh and clean.', 'rating': 4},
  {'text': 'The concierge was incredibly helpful with local tips and reservations. Top-notch assistance.', 'rating': 5},
  {'text': 'Internet was fast and reliable, which was a huge plus for work and streaming.', 'rating': 4},
  {'text': 'Parking was a bit tight, especially on busy nights, but we always found a spot eventually.', 'rating': 3},
  {'text': 'Beautiful decor and very comfortable beds. Felt like a luxury stay without the huge price tag.', 'rating': 5},
  {'text': 'An excellent choice for business travel; quiet, efficient, and well-equipped for meetings.', 'rating': 4},
  {'text': 'Loved the direct beach access, truly wonderful to step right onto the sand!', 'rating': 5},
  {'text': 'My only complaint was the slow check-in process; took longer than expected.', 'rating': 2},
  {'text': 'The breakfast buffet was absolutely outstanding! Best I\'ve had in a hotel in years.', 'rating': 5},
  {'text': 'Perfect for a family vacation, lots for the kids to do and great family-friendly amenities.', 'rating': 4},
  {'text': 'Surprisingly quiet given its central location. Managed to get good rest despite being downtown.', 'rating': 4},
  {'text': 'Could use an update in some areas, but still very clean and functional for a short stay.', 'rating': 3},
  {'text': 'The gym facilities were top-notch and well-maintained. A great bonus for fitness enthusiasts.', 'rating': 4},
  {'text': 'Hassle-free stay from start to finish. Staff went above and beyond to assist us.', 'rating': 5},
  {'text': 'The view from our balcony was absolutely breathtaking. Worth every penny!', 'rating': 5},
  {'text': 'Definitely recommend this place for a romantic escape; very charming and private.', 'rating': 5},
  {'text': 'A bit far from major attractions, requiring taxis or public transport, but very peaceful.', 'rating': 3},
  {'text': 'Excellent amenities for pets, truly pet-friendly with dedicated areas and treats.', 'rating': 5},
  {'text': 'Room service was quick and the food was hot and delicious every time.', 'rating': 4},
  {'text': 'Enjoyed the evening entertainment in the lobby, added a nice touch to the stay.', 'rating': 4},
  {'text': 'Minor issue with the AC, but it was quickly resolved by maintenance.', 'rating': 3},
  {'text': 'The beds were incredibly comfortable, honestly the best sleep I\'ve had in ages!', 'rating': 5},
  {'text': 'Walking distance to many shops and restaurants, made exploring easy and fun.', 'rating': 4},
  {'text': 'Good security measures in place, felt very safe throughout our stay.', 'rating': 4},
  {'text': 'Loved the complimentary happy hour! A great way to unwind after a day of sightseeing.', 'rating': 5},
  {'text': 'Friendly front desk staff but the wait for elevators was often long, especially during peak hours.', 'rating': 3},
  {'text': 'The hotel grounds are beautiful and meticulously kept, felt very luxurious.', 'rating': 5},
  {'text': 'Housekeeping was inconsistent; skipped our room one day, which was disappointing.', 'rating': 2},
  {'text': 'The spa facilities were a wonderful addition, very relaxing and well-managed.', 'rating': 5},
  {'text': 'Our room had a slight mildew smell, but it wasn\'t terrible enough to complain.', 'rating': 2},
  {'text': 'The kids\' club was a lifesaver! Our children had a fantastic time and were well cared for.', 'rating': 5},
  {'text': 'Located right next to a busy road, so expect some traffic noise, even on higher floors.', 'rating': 2},
  {'text': 'The bar staff were incredibly attentive and made excellent cocktails.', 'rating': 4},
  {'text': 'Pillows were a bit too soft for my liking, but that\'s a minor personal preference.', 'rating': 3},
  {'text': 'The shuttle service was punctual and very convenient for getting to the convention center.', 'rating': 4},
  {'text': 'We had an issue with a noisy neighbor, but the front desk handled it promptly and professionally.', 'rating': 4},
  {'text': 'The decor felt a bit dated, but everything was clean and functional.', 'rating': 3},
  {'text': 'Absolutely loved the rooftop pool and bar! Perfect for enjoying the sunset.', 'rating': 5},
  {'text': 'The coffee shop in the lobby was a great perk for a quick morning pick-me-up.', 'rating': 4},
  {'text': 'Valet parking was efficient and friendly, though a bit pricey.', 'rating': 3},
  {'text': 'The view was partially obstructed by another building, which wasn\'t clear from the booking description.', 'rating': 2},
  {'text': 'Every staff member we encountered was genuinely kind and helpful. Outstanding hospitality!', 'rating': 5},
  {'text': 'The restaurant portions were small for the price, but the quality of food was high.', 'rating': 3},
  {'text': 'Had a wonderful time exploring the nearby attractions, very convenient location for tourists.', 'rating': 4},
  {'text': 'The check-out process was quick and smooth, no complaints there.', 'rating': 4},
  {'text': 'Unfortunately, the hot water pressure was quite low during our stay.', 'rating': 2},
  {'text': 'The communal areas were beautifully designed and comfortable.', 'rating': 4}
]
getAddress = lambda: str(random.randint(100, 999)) + ' ' + random.choice(['Main St', 'Ocean Blvd', '5th Ave', 'Sunset Rd', 'Market St', 'Elm St', 'Maple Ave', 'Broadway', 'Park Pl', 'Pine Ln', 'Grand Ave', 'University Dr', 'Highland Rd', 'Riverfront Pkwy', 'Liberty St', 'Willow Creek Ln', 'Cedarwood Blvd', 'Mill Pond Rd', 'Silverleaf Way', 'Forest Ridge Dr'])

amenitiesList = ['Free Wi-Fi', 'Swimming Pool', 'Fitness Center', 'Spa', 'Restaurant',
        'Bar/Lounge', 'Business Center', 'Conference Facilities', 'Room Service',
        'Laundry Services', 'Gym', 'Indoor Pool', 'Outdoor Pool', 'Jacuzzi',
        'Air Conditioning', 'Minibar', 'TV', 'Cable TV', 'Satellite TV', 'Internet']

attractionsPool = [
    {'name': 'Central Beach', 'type': 'Beach', 'distance': 0.5},
    {'name': 'City Museum', 'type': 'Museum', 'distance': 1.2},
    {'name': 'Downtown Park', 'type': 'Park', 'distance': 0.8},
    {'name': 'Shopping Center', 'type': 'Shopping Mall', 'distance': 1.5},
    {'name': 'Historic Theater', 'type': 'Theater', 'distance': 2.0},
    {'name': 'Waterfront Zoo', 'type': 'Zoo', 'distance': 3.0},
    {'name': 'Art Gallery', 'type': 'Art Gallery', 'distance': 1.1},
    {'name': 'Sports Stadium', 'type': 'Sports Stadium', 'distance': 2.5}
]

faqPool = [
    {'question': 'What time is check-in?', 'answer': 'Check-in is available from 3:00 PM.'},
    {'question': 'Is parking available?', 'answer': 'Yes, complimentary parking is available for all guests.'},
    {'question': 'Do you allow pets?', 'answer': 'Yes, we are a pet-friendly hotel with a small additional fee.'},
    {'question': 'Is WiFi included?', 'answer': 'Yes, high-speed WiFi is complimentary throughout the hotel.'},
    {'question': 'What amenities are available?', 'answer': 'We offer a fitness center, pool, spa, and restaurant.'},
    {'question': 'Is there room service?', 'answer': 'Yes, 24-hour room service is available.'},
    {'question': 'What is your cancellation policy?', 'answer': 'Cancellation policies vary by room type and booking rate.'}
]

usernamePool = ['TravelLover', 'AdventureSeeker', 'BusinessTraveler', 'FamilyFun', 'CoupleGetaway', 
               'SoloExplorer', 'VacationVibes', 'CityBreaker', 'BeachBum', 'MountainHiker']
def available_hotels(count: int, city: str, state: str) -> List[Hotel]:
    """
    Returns a list of available hotels based on the count provided.
    """
    if not (1 <= count <= 20):
        raise HTTPException(status_code=400, detail="Count must be between 1 and 20.")
    
    hotels = []
    
    for i in range(count):
        # Generate basic hotel info
        hotel_name = getRandom(hotelNames)
        
        # Generate reviews
        review_count = random.randint(1, 10)
        reviews = []
        for _ in range(review_count):
            review_data = getRandom(reviewsPool)
            reviews.append(Review(
                username=getRandom(usernamePool),
                rating=float(review_data['rating']),
                comment=review_data['text'],
                date=datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 365))
            ))
        
        # Generate room details
        room_details = []
        rooms = ['Standard', 'Deluxe', 'Suite']
        for idx, room in enumerate(rooms):
            room_details.append(RoomDetails(
                type=room,
                pricePerNight=float(random.randint(50, 99) * (idx + 1)),
                mostPopular=(idx == 1),  # Deluxe is most popular
                cancellationPolicy=random.choice(['Flexible', 'Moderate', 'Strict']),
                availableRooms=random.randint(1, 10)
            ))
        
        # Generate attractions
        attractions = []
        selected_attractions = random.sample(attractionsPool, random.randint(1, 5))
        for attr in selected_attractions:
            attractions.append(Attraction(
                name=attr['name'],
                type=attr['type'],
                distance=attr['distance']
            ))
        
        # Generate FAQ
        faqs = []
        selected_faqs = random.sample(faqPool, random.randint(2, 5))
        for faq in selected_faqs:
            faqs.append(FAQ(
                question=faq['question'],
                answer=faq['answer']
            ))
        
        # Create hotel object
        hotel = Hotel(
            name=hotel_name,
            vendor=getRandom(['Marriott', 'Hilton', 'Hyatt', 'Sheraton', 'Radisson', 'InterContinental', 'Holiday Inn', 'Ritz-Carlton', 'Four Seasons', 'Wyndham']),
            address=f"{getAddress()}, {city}, {state}",
            city=city,
            state=state,
            country="USA",
            description=getRandom(descriptions),
            postalCode=f"{random.randint(10000, 99999)}",
            phoneNumber=f"+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            email=f"info@{hotel_name.lower().replace(' ', '').replace('&', 'and')}.com",
            website=f"https://www.{hotel_name.lower().replace(' ', '').replace('&', 'and')}.com",
            rating=round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else 0.0,
            reviews=reviews,
            roomDetails=room_details,
            amenities=random.sample(amenitiesList, random.randint(3, 8)),
            nearbyAttractions=attractions,
            policies=HotelPolicy(
                checkin=CheckIn(
                    startTime=f"{random.randint(14, 16)}:00",
                    endTime=f"{random.randint(18, 22)}:00",
                    contactless=random.choice([True, False]),
                    express=random.choice([True, False]),
                    minAge=random.randint(18, 21)
                ),
                checkout=Checkout(
                    time=f"{random.randint(10, 12)}:00",
                    contactless=random.choice([True, False]),
                    express=random.choice([True, False]),
                    lateFeeApplicable=random.choice([True, False])
                ),
                petsAllowed=random.choice([True, False]),
                childrenPolicy=getRandom(['Children welcome', 'Adults only', 'Children allowed with supervision']),
                extraBeds=getRandom(['Available upon request', 'Not available', 'Available for additional fee']),
                cribAvailability=getRandom(['Available upon request', 'Not available', 'Available for additional fee']),
                accessMethods=['Key Card', 'Mobile App', 'Digital Key'],
                safetyFeatures=['Smoke Detectors', 'Fire Extinguishers', 'Security Cameras', '24/7 Front Desk'],
                houseKeepingPolicy=getRandom(['Daily housekeeping', 'Housekeeping upon request', 'Every other day'])
            ),
            faq=faqs
        )
        
        hotels.append(hotel)
    
    return hotels

        
@app.get("/hotels", response_model=List[Hotel])
async def get_hotels(
    count: int = Query(5, ge=1, le=20, description="Number of hotels to generate (1-20)."),
    city: str = Query("New York", description="City name for hotel location"),
    state: str = Query("NY", description="State for hotel location")
):
    """returns a list of available hotels based on the count provided."""
    try:
        return available_hotels(count, city, state)
    except Exception as e:
        print(f"Error in get_hotels: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)