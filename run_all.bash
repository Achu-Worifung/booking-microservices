#!/bin/bash

# Activate the shared virtual environment if it exists
if [ -d "microservices" ]; then
    source microservices/Scripts/activate
    echo "✅ Activated shared virtual environment"
else
    echo "⚠️ No shared virtual environment found, using system Python"
fi

echo "🚀 Starting all microservices..."
echo "========================================"

# Start each microservice with uvicorn, from its own folder
echo "Starting Car Booking Service on port 8001..."
(cd car-booking && python main.py &)

echo "Starting Car Service on port 8010..."
(cd car-service && python main.py &)

echo "Starting Flight Booking Service on port 8002..."
(cd flight-booking && python main.py &)

echo "Starting Flight Service on port 8003..."
(cd flight-service && python main.py &)

echo "Starting Hotel Service on port 8020..."
(cd hotel-service && python main.py &)

echo "Starting User Service on port 8004..."
(cd user-service && python main.py &)

echo "Starting Trip Service on port 8005..."
(cd trip-service && python main.py &)

echo ""
echo "✅ All services started!"
echo "========================================"
echo "🚗 Car Booking Service:  http://localhost:8001"
echo "🚙 Car Service:          http://localhost:8010"
echo "✈️  Flight Booking:       http://localhost:8002"
echo "🛫 Flight Service:       http://localhost:8003"
echo "🏨 Hotel Service:        http://localhost:8020"
echo "👤 User Service:         http://localhost:8004"
echo "🗺️  Trip Service:         http://localhost:8005"
echo "========================================"
echo ""
echo "💡 To stop all services, press Ctrl+C"
echo "📝 Check individual service logs above for any startup errors"

# Wait for all background processes
wait


#command to run all services
# ./run_all.bash