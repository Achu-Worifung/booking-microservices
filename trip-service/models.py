from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from fastapi import FastAPI, HTTPException, Depends, Query, status
import uuid 
import datetime
# --------------------------- MODELS FOR THE CAR ----------------------
class carTemplate(BaseModel):
    make: str
    model: List[str]

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
# ------------------------------------- FLIGHT MODELS---------------------
FlightClass = Literal['Economy', 'Business', 'First']
class StopDetail(BaseModel):
    """
    Represents details of a stopover in a flight.
    """
    airport: str
    arrivalTime: datetime.datetime # Use datetime for internal handling
    departureTime: datetime.datetime # Use datetime for internal handling
    layoverDuration: str # String format like "1h 30m"

class Flight(BaseModel):
    """
    Represents a single simulated flight.
    """
    airline: str
    flightNumber: str
    departureAirport: str
    destinationAirport: str
    departureTime: datetime.datetime # Use datetime for internal handling
    arrivalTime: datetime.datetime # Use datetime for internal handling
    duration: str # String format like "5h 45m"
    numberOfStops: int
    stops: List[StopDetail]
    status: Literal['On Time', 'Delayed', 'Cancelled']
    aircraft: str
    gate: str
    terminal: str
    meal: bool
    availableSeats: Dict[FlightClass, int] # Use Dict with FlightClass Literal
    prices: Dict[FlightClass, float] # Use Dict with FlightClass Literal
    bookingUrl: str
    
    # -------------------------------------MODELS FOR THE HOTEL------------------------
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
