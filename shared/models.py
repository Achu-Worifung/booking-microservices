from pydantic import BaseModel,Field
from typing import List, Literal, Dict, Optional
import uuid 
import datetime

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