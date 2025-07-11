// car_booking_test.js
// Test script for Car Booking Service

const BASE_URL = "http://127.0.0.1:8001";
const TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaWQiOiIyM2NiYzUwZS04ZDFhLTQ5MjQtYjBlNS1iMzFhODNkNDRmYjIiLCJlbWFpbCI6ImpvaG4uZG9lQGV4YW1wbGUuY29tIn0.V4zVIh7NYP8QYNGX8BZCfbp6WtQ_CIW4lJP86G-iAv0";

// Test car data
const testCar = {
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
};

// Test insurance data
const testInsurance = {
    insType: "Comprehensive",
    insTotal: 15.99
};

// Test booking parameters
const testBookingParams = {
    total: 150.00,
    trip_id: "12345678-1234-1234-1234-123456789abc"
};

// Test function for booking a car
async function testCarBooking() {
    console.log("🚗 Testing Car Booking...");
    
    try {
        const requestBody = {
            car: testCar,
            insurance: testInsurance,
            total: testBookingParams.total,
            trip_id: testBookingParams.trip_id
        };

        const response = await fetch(`${BASE_URL}/car/book`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${TOKEN}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log(`📊 Status Code: ${response.status}`);
        const responseText = await response.text();
        console.log(`📝 Response:`, responseText);
        
        if (response.ok) {
            const data = JSON.parse(responseText);
            console.log("✅ Car booking successful!");
            console.log(`🎫 Booking ID: ${data.booking_id}`);
            console.log(`📋 Booking Reference: ${data.booking_reference}`);
            console.log(`👤 User: ${data.user.fname} (${data.user.email})`);
            console.log(`🚗 Car: ${data.car.make} ${data.car.model} (${data.car.year})`);
            console.log(`💰 Total Amount: $${testBookingParams.total}`);
            console.log(`🛡️ Insurance: ${testInsurance.insType} - $${testInsurance.insTotal}`);
            return data; // Return full data object
        } else {
            console.log("❌ Car booking failed!");
            const errorData = JSON.parse(responseText);
            console.log(`🚫 Error: ${errorData.detail}`);
            return null;
        }
        
    } catch (error) {
        console.error("💥 Error:", error.message);
        return null;
    }
}

// Test function for getting a car booking
async function testGetCarBooking(bookingId) {
    console.log("\n🔍 Testing Get Car Booking...");
    
    try {
        const response = await fetch(`${BASE_URL}/cars/booking/${bookingId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${TOKEN}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log(`📊 Status Code: ${response.status}`);
        const responseText = await response.text();
        console.log(`📝 Response:`, responseText);
        
        if (response.ok) {
            const data = JSON.parse(responseText);
            console.log("✅ Get car booking successful!");
            console.log(`📋 Car Details:`, data.car_details);
            return data;
        } else {
            console.log("❌ Get car booking failed!");
            const errorData = JSON.parse(responseText);
            console.log(`🚫 Error: ${errorData.detail}`);
            return null;
        }
        
    } catch (error) {
        console.error("💥 Error:", error.message);
        return null;
    }
}

// Test function for deleting a car booking
async function testDeleteCarBooking(bookingId) {
    console.log("\n🗑️ Testing Delete Car Booking...");
    
    try {
        const response = await fetch(`${BASE_URL}/cars/delete`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${TOKEN}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                carid: bookingId
            })
        });
        
        console.log(`📊 Status Code: ${response.status}`);
        const responseText = await response.text();
        console.log(`📝 Response:`, responseText);
        
        if (response.ok) {
            const data = JSON.parse(responseText);
            console.log("✅ Delete car booking successful!");
            console.log(`🗑️ Deleted Booking ID: ${data.deleted_booking_id}`);
            return data;
        } else {
            console.log("❌ Delete car booking failed!");
            const errorData = JSON.parse(responseText);
            console.log(`🚫 Error: ${errorData.detail}`);
            return null;
        }
        
    } catch (error) {
        console.error("💥 Error:", error.message);
        return null;
    }
}

// Test function for service info
async function testServiceInfo() {
    console.log("\n🏠 Testing Service Info...");
    
    try {
        const response = await fetch(`${BASE_URL}/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log(`📊 Status Code: ${response.status}`);
        const responseText = await response.text();
        console.log(`📝 Response:`, responseText);
        
        if (response.ok) {
            const data = JSON.parse(responseText);
            console.log("✅ Service info retrieved successfully!");
            console.log(`🏢 Service: ${data.service}`);
            console.log(`🔢 Version: ${data.version}`);
            console.log(`🔗 Endpoints:`, data.endpoints);
            return data;
        } else {
            console.log("❌ Get service info failed!");
            return null;
        }
        
    } catch (error) {
        console.error("💥 Error:", error.message);
        return null;
    }
}

// Test authentication without valid token
async function testInvalidAuth() {
    console.log("\n🔒 Testing Invalid Authentication...");
    
    try {
        const response = await fetch(`${BASE_URL}/car/book`, {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer invalid-token',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                car: testCar,
                total: testBookingParams.total
            })
        });
        
        console.log(`📊 Status Code: ${response.status}`);
        const responseText = await response.text();
        console.log(`📝 Response:`, responseText);
        
        if (response.status === 401) {
            console.log("✅ Invalid auth test passed - correctly rejected!");
            return true;
        } else {
            console.log("❌ Invalid auth test failed - should have been rejected!");
            return false;
        }
        
    } catch (error) {
        console.error("💥 Error:", error.message);
        return false;
    }
}

// Test missing authorization header
async function testMissingAuth() {
    console.log("\n🚫 Testing Missing Authorization...");
    
    try {
        const response = await fetch(`${BASE_URL}/car/book`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                car: testCar,
                total: testBookingParams.total
            })
        });
        
        console.log(`📊 Status Code: ${response.status}`);
        const responseText = await response.text();
        console.log(`📝 Response:`, responseText);
        
        if (response.status === 401) {
            console.log("✅ Missing auth test passed - correctly rejected!");
            return true;
        } else {
            console.log("❌ Missing auth test failed - should have been rejected!");
            return false;
        }
        
    } catch (error) {
        console.error("💥 Error:", error.message);
        return false;
    }
}

// Run all tests
async function runAllTests() {
    console.log("🚀 Starting Car Booking Service Tests...\n");
    
    // Test service info first
    await testServiceInfo();
    
    // Test authentication
    await testInvalidAuth();
    await testMissingAuth();
    
    // Test main functionality
    const bookingData = await testCarBooking();
    
    if (bookingData && bookingData.booking_id) {
        console.log(`\n📝 Using Booking ID for further tests: ${bookingData.booking_id}`);
        
        // Test getting the booking
        await testGetCarBooking(bookingData.booking_id);
        
        // Test deleting the booking
        // await testDeleteCarBooking(bookingData.booking_id);
        
        // Try to get the deleted booking (should fail)
        console.log("\n🔍 Testing Get Deleted Booking (should fail)...");
        await testGetCarBooking(bookingData.booking_id);
    }
    
    console.log("\n✅ All car booking tests completed!");
}

// Run the tests
runAllTests().catch((error) => {
    console.error("❌ Test suite failed:", error);
});
