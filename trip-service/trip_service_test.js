// trip_service_test.js
// Test script for Trip Service

const BASE_URL = "http://127.0.0.1:8012";
const TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaWQiOiIyM2NiYzUwZS04ZDFhLTQ5MjQtYjBlNS1iMzFhODNkNDRmYjIiLCJlbWFpbCI6ImpvaG4uZG9lQGV4YW1wbGUuY29tIn0.V4zVIh7NYP8QYNGX8BZCfbp6WtQ_CIW4lJP86G-iAv0";

// Test trip data
const testTrip = {
    tripid: "12345678-1234-1234-1234-123456789abc", // This will be ignored by backend
    userid: "23cbc50e-8d1a-4924-b0e5-b31a83d44fb2", // This will be ignored by backend
    tripname: "Summer Vacation 2024",
    destination: "Miami, Florida",
    startdate: "2024-07-15",
    enddate: "2024-07-22",
    travelers: 4,
    budget: 2500.00,
    trip_status: "Planning",
    description: "Family vacation to sunny Miami with beach activities and city exploration",
    createdat: new Date().toISOString(), // This will be ignored by backend
    updatedat: new Date().toISOString()  // This will be ignored by backend
};

// Test function for creating a trip
async function testCreateTrip() {
    console.log("Testing Trip Creation...");
    
    try {
        const response = await fetch(`${BASE_URL}/trips/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${TOKEN}`,
                'X-Client-ID': 'test-client-id',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testTrip)
        });

        const result = await response.json();
        
        if (response.ok) {
            console.log("Trip creation successful!");
            console.log("Trip Details:", JSON.stringify(result, null, 2));
            return result;
        } else {
            console.log("Trip creation failed!");
            console.log("Error details:", JSON.stringify(result, null, 2));
            return null;
        }
    } catch (error) {
        console.log("Trip creation request failed!");
        console.log("Error:", error.message);
        return null;
    }
}

// Test function for service health check
async function testServiceHealth() {
    console.log("Testing Service Health...");
    
    try {
        const response = await fetch(`${BASE_URL}/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Client-ID': 'test-client-id'
            }
        });

        const result = await response.json();
        
        if (response.ok) {
            console.log("Service health check successful!");
            console.log("Service Info:", JSON.stringify(result, null, 2));
            return result;
        } else {
            console.log("Service health check failed!");
            console.log("Error details:", JSON.stringify(result, null, 2));
            return null;
        }
    } catch (error) {
        console.log("Service health check request failed!");
        console.log("Error:", error.message);
        return null;
    }
}

// Test function with different trip data
async function testCreateTripBusiness() {
    console.log("Testing Business Trip Creation...");
    
    const businessTrip = {
        tripname: "Business Conference NYC",
        destination: "New York City, NY",
        startdate: "2024-09-10",
        enddate: "2024-09-13",
        travelers: 2,
        budget: 1800.00,
        trip_status: "Confirmed",
        description: "Business conference and client meetings in Manhattan"
    };
    
    try {
        const response = await fetch(`${BASE_URL}/trips/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${TOKEN}`,
                'X-Client-ID': 'test-client-id',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(businessTrip)
        });

        const result = await response.json();
        
        if (response.ok) {
            console.log("Business trip creation successful!");
            console.log("Trip Details:", JSON.stringify(result, null, 2));
            return result;
        } else {
            console.log("Business trip creation failed!");
            console.log("Error details:", JSON.stringify(result, null, 2));
            return null;
        }
    } catch (error) {
        console.log("Business trip creation request failed!");
        console.log("Error:", error.message);
        return null;
    }
}

// test for ("/trips/book/{tripid}
async function testBookTrip(tripid) {
    console.log(`Testing Booking for Trip ID: ${tripid}...`);
    
    try {
        const response = await fetch(`${BASE_URL}/trips/book/${tripid}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${TOKEN}`,
                'X-Client-ID': 'test-client-id',
                'Content-Type': 'application/json'
            }, 
            body:JSON.stringify({
                car: {
                    make: "Toyota",
                    model: "Camry",
                    year: 2024,
                    color: ["White", "Silver"],
                    seat: 5,
                    type: "Sedan",
                    price_per_day: 45.99,
                    feature: "GPS, Air Conditioning, Bluetooth",
                    transmission: "Automatic",
                    fuel_type: "Petrol",
                    available: true,
                    rating: 4.5
                },
                flight: {
                    airline: "Delta",
                    flightNumber: "DL1234",
                    departureAirport: "LAX",
                    destinationAirport: "JFK",
                    departureTime: "2025-07-15T08:00:00",
                    arrivalTime: "2025-07-15T14:30:00",
                    duration: "6h 30m",
                    numberOfStops: 1,
                    stops: [],
                    status: "On Time",
                    aircraft: "Boeing 737",
                    gate: "A12",
                    terminal: "A",
                    meal: true,
                    availableSeats: {
                        Economy: 50,
                        Business: 15,
                        First: 5
                    },
                    prices: {
                        Economy: 299.99,
                        Business: 799.99,
                        First: 1499.99
                    },
                    bookingUrl: "#",
                    choosenSeat: "Economy"
                }
            })
        });

        const result = await response.json();
        
        if (response.ok) {
            console.log("Trip booking successful!");
            console.log("Booking Details:", JSON.stringify(result, null, 2));
            return result;
        } else {
            console.log("Trip booking failed!");
            console.log("Error details:", JSON.stringify(result, null, 2));
            return null;
        }
    } catch (error) {
        console.log("Trip booking request failed!");
        console.log("Error:", error.message);
        return null;
    }
}


// Main test runner
async function runTripServiceTests() {
    console.log("Starting Trip Service Tests...");
    console.log("=" .repeat(50));
    
    // Test 1: Service Health Check
    console.log("\nTest 1: Service Health Check");
    await testServiceHealth();
    
    // Test 2: Valid Trip Creation
    console.log("\nTest 2: Valid Trip Creation");
    const tripResult = await testCreateTrip();
    
    // Test 3: Business Trip Creation
    console.log("\nTest 3: Business Trip Creation");
    await testCreateTripBusiness();
    
    
    console.log("\n" + "=" .repeat(50));
    console.log("Trip Service Tests Completed!");
    
    if (tripResult && tripResult.tripid) {
        console.log(`\nCreated trip with ID: ${tripResult.tripid}`);
    }
}

// Run the tests
runTripServiceTests().catch(console.error);
