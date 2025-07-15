from fastapi import FastAPI, HTTPException, Query, Request, Depends
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Optional
import uuid
import datetime
import random
import uvicorn
import sys
import os

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from redis_rate_limit import rate_limit


app = FastAPI(
    title="Infosys | Booking: Car Micro Service",
    description="A microservice to obtain the list of available cars at a specific location and date.",
    version="1.0.0",
)

#can you make a list of cars available for booking i want it to be as close to accurate as possible


class carTemplate(BaseModel):
    make: str
    model: List[str]
    
all_cars: Dict[str, List[carTemplate]] = {
    'Sports': [
        carTemplate(make='Porsche', model=['911', 'Cayenne', 'Macan', 'Panamera', 'Taycan', 'Boxster', 'Cayman', '918 Spyder']),
        carTemplate(make='Lamborghini', model=['Aventador', 'Huracán', 'Urus', 'Gallardo', 'Diablo', 'Countach']),
        carTemplate(make='Ferrari', model=['488', 'F8 Tributo', 'Portofino', 'Roma', 'SF90 Stradale', 'LaFerrari']),
    ],
    'Luxury': [
        carTemplate(make='Rolls-Royce', model=['Phantom', 'Ghost', 'Wraith', 'Dawn', 'Cullinan']),
        carTemplate(make='Bentley', model=['Continental GT', 'Flying Spur', 'Bentayga']),
        carTemplate(make='Aston Martin', model=['DB11', 'Vantage', 'DBS Superleggera']),
    ],
    'Sedan': [
        carTemplate(make='Honda', model=['Civic', 'Accord', 'CR-V', 'Fit', 'Odyssey', 'Pilot', 'Ridgeline', 'Crosstour', 'Passport']),
        carTemplate(make='Toyota', model=['Camry', 'Corolla', 'RAV4', 'Highlander', 'Tacoma', 'Tundra', 'Sienna', 'Prius', 'C-HR']),
        carTemplate(make='Ford', model=['F-150', 'F-250', 'F-350', 'F-450', 'F-550', 'F-650', 'F-750', 'F-850', 'F-950']),
    ],
    'SUV': [
        carTemplate(make='Tesla', model=['Model S', 'Model X', 'Model 3', 'Model Y']),
        carTemplate(make='Honda', model=['Civic', 'Accord', 'CR-V', 'Fit', 'Odyssey', 'Pilot', 'Ridgeline', 'Crosstour', 'Passport']),
        carTemplate(make='Toyota', model=['Camry', 'Corolla', 'RAV4', 'Highlander', 'Tacoma', 'Tundra', 'Sienna', 'Prius', 'C-HR']),
    ],
    'Truck': [
        carTemplate(make='Ford', model=['F-150', 'F-250', 'F-350', 'F-450', 'F-550', 'F-650', 'F-750', 'F-850', 'F-950']),
        carTemplate(make='Chevrolet', model=['Silverado', 'Camaro', 'Corvette', 'Equinox', 'Impala', 'Malibu', 'Sonic', 'Spark', 'Tahoe']),
        carTemplate(make='GMC', model=['Sierra', 'Yukon', 'Acadia', 'Canyon', 'Savana', 'Terrain', 'Yukon XL', 'Yukon XL 1500', 'Yukon XL 2500']),
    ],
    'Economy': [
        carTemplate(make='Hyundai', model=['Elantra', 'Sonata', 'Tucson', 'Veloster', 'Genesis', 'Santa Fe', 'Kona', 'Ioniq', 'Kona Electric']),
        carTemplate(make='Honda', model=['Civic', 'Accord', 'CR-V', 'Fit', 'Odyssey', 'Pilot', 'Ridgeline', 'Crosstour', 'Passport']),
        carTemplate(make='Toyota', model=['Camry', 'Corolla', 'RAV4', 'Highlander', 'Tacoma', 'Tundra', 'Sienna', 'Prius', 'C-HR']),
    ],
    'Van': [
        carTemplate(make='Honda', model=['Odyssey', 'Pilot', 'Ridgeline', 'Crosstour', 'Passport']),
        carTemplate(make='Toyota', model=['Sienna', 'Prius', 'C-HR']),
        carTemplate(make='Chrysler', model=['Pacifica', 'Voyager']),
    ],
    'Hybrid': [
        carTemplate(make='Toyota', model=['Prius', 'Camry Hybrid', 'RAV4 Hybrid', 'Highlander Hybrid', 'Avalon Hybrid']),
        carTemplate(make='Honda', model=['Insight', 'Clarity Plug-In Hybrid']),
        carTemplate(make='Ford', model=['Fusion Hybrid', 'Escape Hybrid']),
    ],
    'Electric': [
        carTemplate(make='Tesla', model=['Model S', 'Model 3', 'Model X', 'Model Y']),
        carTemplate(make='Nissan', model=['Leaf']),
        carTemplate(make='Chevrolet', model=['Bolt EV']),
    ],
    'Coupe': [
        carTemplate(make='Ford', model=['Mustang']),
        carTemplate(make='Chevrolet', model=['Camaro', 'Corvette']),
        carTemplate(make='Dodge', model=['Challenger', 'Charger']),
    ],
    'Minivan': [
        carTemplate(make='Honda', model=['Odyssey']),
        carTemplate(make='Toyota', model=['Sienna']),
        carTemplate(make='Chrysler', model=['Pacifica']),
    ]

}


def getSeatCount(car_type: str) -> int:
    """
    Returns the number of seats based on the car type.
    """
    if car_type in ['Sedan', 'Coupe', 'Sports']:
        return random.choice([4, 5])
    elif car_type in ['SUV', 'Truck', 'Van', 'Minivan']:
        return random.choice([5, 6, 7, 8])
    elif car_type in ['Luxury']:
        return random.choice([4, 5, 6])
    elif car_type in ['Economy', 'Hybrid', 'Electric']:
        return random.choice([4, 5])
    else:
        return 4  
def getDailPrice(car_type: str) -> float:
    """
    Returns a random daily price based on the car type.
    """
    if car_type in ['Sports', 'Luxury']:
        return round(random.uniform(100.0, 500.0), 2)
    elif car_type in ['SUV', 'Truck']:
        return round(random.uniform(50.0, 300.0), 2)
    elif car_type in ['Sedan', 'Economy']:
        return round(random.uniform(30.0, 150.0), 2)
    elif car_type in ['Van', 'Minivan']:
        return round(random.uniform(40.0, 200.0), 2)
    elif car_type in ['Hybrid', 'Electric']:
        return round(random.uniform(60.0, 250.0), 2)
    else:
        return round(random.uniform(20.0, 100.0), 2)

def getFuelType(car_type: str) -> Literal['Petrol', 'Diesel', 'Electric', 'Hybrid']:
    """
    Returns a random fuel type based on the car type.
    """
    if car_type in ['Electric']:
        return 'Electric'
    elif car_type in ['Hybrid']:
        return 'Hybrid'
    elif car_type in ['Diesel', 'Truck']:
        return 'Diesel'
    else:
        return 'Petrol'  # Default for most cars
list_of_feautures = [
    'Sunroof', 'Leather Seats', 'Bluetooth Connectivity', 'Navigation System',
    'Backup Camera', 'Blind Spot Monitoring', 'Adaptive Cruise Control',
    'Air Conditioning', 'Heated Seats', 'Power Windows', 'Rear View Camera',
    'Panorama Sunroof', 'Sunroof', 'Leather Seats', 'Bluetooth Connectivity',
    'Navigation System', 'Backup Camera', 'Blind Spot Monitoring',
]
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

@app.get('/')
async def root(request: Request):
    """
    Root endpoint for the car availability microservice.
    """
    await rate_limit(request, limit=10, window=60, service="car-service")
    return {"message": "Welcome to the car availability microservice!"}

@app.get('/cars', response_model=List[Car])
async def get_cars(request: Request):
    """
    Get a list of all available cars.
    """
    await rate_limit(request, limit=5, window=60, service="car-service")
    available_cars: List[Car] = []
    
    # Get all car types and their templates
    for car_type, car_templates in all_cars.items():
        # Select a few cars from each type
        selected_templates = random.sample(car_templates, min(3, len(car_templates)))
        
        for template in selected_templates:
            # Pick a random model from the template
            selected_model = random.choice(template.model)
            get_feature = random.sample(list_of_feautures, k=4)
            
            available_cars.append(Car(
                id=str(uuid.uuid4()),
                make=template.make,
                model=selected_model,
                year=random.randint(2018, 2024),
                color=random.sample(['Red', 'Blue', 'Black', 'White', 'Silver', 'Green', 'Gray', 'Yellow'], k=random.randint(1, 3)),
                seat=getSeatCount(car_type),
                type=car_type,
                price_per_day=getDailPrice(car_type),
                feature='• '.join(get_feature),
                transmission=random.choice(['Automatic', 'Manual']),
                fuel_type=getFuelType(car_type),
                rating=round(random.uniform(3.5, 5.0), 1)
            ))
    
    # Shuffle and limit to reasonable number
    random.shuffle(available_cars)
    return available_cars[:20]

@app.get('/cars/{car_type}', response_model=List[Car])
async def get_cars_by_type(car_type: str, request: Request):
    """
    Get a list of cars of a specific type.
    """
    await rate_limit(request, limit=5, window=60, service="car-service")

    if car_type not in all_cars:
        raise HTTPException(status_code=404, detail=f"Car type '{car_type}' not found")
    
    available_cars: List[Car] = []
    car_templates = all_cars[car_type]
    
    for template in car_templates:
        # Create multiple cars for each template with different models
        for model in template.model[:3]:  # Limit to first 3 models per make
            get_feature = random.sample(list_of_feautures, k=4)
            
            available_cars.append(Car(
                id=str(uuid.uuid4()),
                make=template.make,
                model=model,
                year=random.randint(2018, 2024),
                color=random.sample(['Red', 'Blue', 'Black', 'White', 'Silver', 'Green', 'Gray', 'Yellow'], k=random.randint(1, 3)),
                seat=getSeatCount(car_type),
                type=car_type,
                price_per_day=getDailPrice(car_type),
                feature='• '.join(get_feature),
                transmission=random.choice(['Automatic', 'Manual']),
                fuel_type=getFuelType(car_type),
                rating=round(random.uniform(3.5, 5.0), 1)
            ))
    
    random.shuffle(available_cars)
    return available_cars


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8010, reload=True)