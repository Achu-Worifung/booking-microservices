# main.py
from fastapi import FastAPI, HTTPException, Query, Request, Depends
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Optional
import uuid
import datetime
import random
import json
import sys
import os

import uvicorn

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from redis_rate_limit import rate_limit


# Initialize FastAPI application
app = FastAPI(
    title="Fake Flight Generator Microservice",
    description="A microservice to obtain  flight data based on provided JavaScript logic.",
    version="1.0.0",
)

# --- Pydantic Models for Data Validation and Response ---

# Equivalent of TypeScript FlightClass
# We'll use Literal for type safety in Python
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

# --- Flight Data Generation Logic (Ported from JavaScript) ---

def generate_fake_flights(departure_date_str: str, count: int = 5) -> List[Flight]:
    """
    Generates mock flight data based on the provided departure date,
    porting the logic from the JavaScript function.
    """
    airlines = ['Delta', 'United', 'American Airlines', 'Southwest', 'JetBlue', 'Alaska Airlines', 'Spirit']
    airport_codes = ['LAX', 'JFK', 'ORD', 'ATL', 'DFW', 'DEN', 'SFO', 'SEA', 'MIA', 'BOS']
    aircraft_types = ['Boeing 737', 'Airbus A320', 'Boeing 777', 'Airbus A350', 'Embraer E190', 'Boeing 787']
    statuses = ['On Time', 'Delayed', 'Cancelled']
    terminals = ['A', 'B', 'C', 'D', 'E']

    flights: List[Flight] = []

    try:
        # Parse the departure_date_str into a date object
        departure_date_obj = datetime.datetime.strptime(departure_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD.")

    for _ in range(count):
        airline = random.choice(airlines)
        # Ensure flight number is unique enough for mock data
        flight_number = f"{airline.replace(' ', '')[:2].upper()}{random.randint(100, 9999)}"

        departure_airport = random.choice(airport_codes)
        destination_airport: str
        while True:
            destination_airport = random.choice(airport_codes)
            if destination_airport != departure_airport:
                break

        number_of_stops = random.randint(0, 2) # 0 to 2 stops
        stop_airports = set()
        stops: List[StopDetail] = []

        # Generate initial departure time for the main flight
        dep_hour = random.randint(0, 23)
        dep_minute = random.randint(0, 59)
        departure_time = datetime.datetime(
            departure_date_obj.year, departure_date_obj.month, departure_date_obj.day,
            dep_hour, dep_minute, 0
        )
        current_time = departure_time

        # Create stops if needed
        for s in range(number_of_stops):
            stop_airport: str
            while True:
                stop_airport = random.choice(airport_codes)
                if (stop_airport != departure_airport and
                    stop_airport != destination_airport and
                    stop_airport not in stop_airports):
                    break
            stop_airports.add(stop_airport)

            flight_duration_to_stop_minutes = random.randint(60, 180) # 1-3h to stop
            current_time += datetime.timedelta(minutes=flight_duration_to_stop_minutes)
            arrival_time_at_stop = current_time

            layover_minutes = random.randint(30, 150) # 30-150 mins layover
            current_time += datetime.timedelta(minutes=layover_minutes)
            departure_time_from_stop = current_time

            layover_duration_str = f"{layover_minutes // 60}h {layover_minutes % 60}m"

            stops.append(StopDetail(
                airport=stop_airport,
                arrivalTime=arrival_time_at_stop,
                departureTime=departure_time_from_stop,
                layoverDuration=layover_duration_str
            ))

        flight_duration_to_dest_minutes = random.randint(60, 240) # 1-4h final leg
        current_time += datetime.timedelta(minutes=flight_duration_to_dest_minutes)
        arrival_time = current_time

        total_duration_minutes = (arrival_time - departure_time).total_seconds() / 60
        duration_str = f"{int(total_duration_minutes // 60)}h {int(total_duration_minutes % 60)}m"

        # Ensure prices are floats as per Pydantic model
        prices: Dict[FlightClass, float] = {
            'Economy': round(random.uniform(50.0, 450.0), 2),
            'Business': round(random.uniform(400.0, 1000.0), 2),
            'First': round(random.uniform(1000.0, 2500.0), 2)
        }

        available_seats: Dict[FlightClass, int] = {
            'Economy': random.randint(0, 100),
            'Business': random.randint(0, 30),
            'First': random.randint(0, 10)
        }

        flights.append(Flight(
            airline=airline,
            flightNumber=flight_number,
            departureAirport=departure_airport,
            destinationAirport=destination_airport,
            departureTime=departure_time,
            arrivalTime=arrival_time,
            duration=duration_str,
            numberOfStops=number_of_stops,
            stops=stops,
            status=random.choice(statuses), # type: ignore - Literal type check
            aircraft=random.choice(aircraft_types),
            gate=f"{random.choice('ABCDEF')}{random.randint(1, 30)}",
            terminal=random.choice(terminals),
            meal=random.random() > 0.3, # 70% chance of meal
            availableSeats=available_seats,
            prices=prices,
            bookingUrl="#"
        ))

    return flights

# --- API Endpoints ---

@app.get("/flights", response_model=List[Flight])
async def generate_flights_endpoint(
    departure_date: str = Query(..., description="The desired departure date in YYYY-MM-DD format."),
    count: int = Query(5, ge=1, le=20, description="The number of fake flights to generate (1-20)."),
    request: Request = None,
    _: bool = Depends(lambda req: rate_limit(req, limit=5, window=60, service="flight-service"))
):
    """
    Endpoint for the list of flights for a given departure date.
    """
    return generate_fake_flights(departure_date, count)

@app.get("/")
async def root(request: Request, _: bool = Depends(lambda req: rate_limit(req, limit=10, window=60, service="flight-service"))):
    """
    Root endpoint for the  flight  microservice.
    Provides a welcome message and directs to documentation.
    """
    return {
        "message": "Welcome to the Fake Flight Generator Microservice!",
        "documentation_url": "/docs",
        "generate_flights_example": "/flights/generate?departure_date=2025-09-01&count=5"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)