// test_flight_booking.js
// Test script for Flight Booking Service authentication

const BASE_URL = "http://localhost:8006";
const TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaWQiOiIyM2NiYzUwZS04ZDFhLTQ5MjQtYjBlNS1iMzFhODNkNDRmYjIiLCJlbWFpbCI6ImpvaG4uZG9lQGV4YW1wbGUuY29tIn0.V4zVIh7NYP8QYNGX8BZCfbp6WtQ_CIW4lJP86G-iAv0";

// Test flight data
const testFlight = {
    // airline: "Delta",
    // flightNumber: "DL1234",
    // departureAirport: "LAX",
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
};

// Test function for booking a flight
async function testFlightBooking() {
    console.log("🚀 Testing Flight Booking Authentication...");
    
    try {
        const response = await fetch(`${BASE_URL}/flights/book`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${TOKEN}`,
                "X-Client-ID": "test-client-id",
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testFlight)
        });
        
        const data = await response.json();
        
        console.log(`📊 Status Code: ${response.status}`);
        console.log(`📝 Response:`, data);
        
        if (response.ok) {
            console.log("✅ Authentication successful!");
            console.log(`🎫 Booking Reference: ${data.booking_reference}`);
            console.log(`🆔 Booking ID: ${data.booking_id}`);
            console.log(`👤 User: ${data.user.fname} (${data.user.email})`);
            console.log(`✈️ Flight: ${data.flight.airline} ${data.flight.flightNumber}`);
            return data; // Return full data object with booking_reference and booking_id
        } else {
            console.log("❌ Authentication failed!");
            console.log(`🚫 Error: ${data.detail}`);
        }
        
    } catch (error) {
        console.error("💥 Error:", error.message);
    }
}

// Test function for getting a booking
async function testGetBooking(bookingId) {
    console.log("\n🔍 Testing Get Booking...");
    
    try {
        const response = await fetch(`${BASE_URL}/flights/booking/${bookingId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${TOKEN}`,
                "X-Client-ID": "test-client-id",
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        console.log(`📊 Status Code: ${response.status}`);
        console.log(`📝 Response:`, data);
        
        if (response.ok) {
            console.log("✅ Get booking successful!");
        } else {
            console.log("❌ Get booking failed!");
        }
        
    } catch (error) {
        console.error("💥 Error:", error.message);
    }
}

// Test function for deleting a booking
async function testDeleteBooking(bookingId) {
    console.log("\n🗑️ Testing Delete Booking...");
    
    try {
        const response = await fetch(`${BASE_URL}/flights/delete`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${TOKEN}`,
                "X-Client-ID": "test-client-id",
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                flightid: bookingId
            })
        });
        
        const data = await response.json();
        
        console.log(`📊 Status Code: ${response.status}`);
        console.log(`📝 Response:`, data);
        
        if (response.ok) {
            console.log("✅ Delete booking successful!");
        } else {
            console.log("❌ Delete booking failed!");
        }
        
    } catch (error) {
        console.error("💥 Error:", error.message);
    }
}

// Test function for checking service info



//just run the test booking
async function runTests() {
    const bookingData = await testFlightBooking();
    console.log("\n🚀 Testing Flight Booking...", bookingData);
    
    if (bookingData && bookingData.booking_id) {
        console.log(`\nBooking Reference: ${bookingData.booking_reference}`);
        console.log(`Booking ID: ${bookingData.booking_id}`);

        // Test with booking ID (preferred method)
        await testGetBooking(bookingData.booking_id);
        await testDeleteBooking(bookingData.booking_id);
    }
}

runTests().then(() => {
    console.log("\n✅ All tests completed.");
}).catch(error => {
    console.error("💥 Error during tests:", error.message);
}    );