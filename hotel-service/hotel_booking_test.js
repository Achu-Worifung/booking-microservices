// hotel_booking_test.js
// Test script for Hotel Booking Service

const BASE_URL = "http://127.0.0.1:8002";
const TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaWQiOiIyM2NiYzUwZS04ZDFhLTQ5MjQtYjBlNS1iMzFhODNkNDRmYjIiLCJlbWFpbCI6ImpvaG4uZG9lQGV4YW1wbGUuY29tIn0.V4zVIh7NYP8QYNGX8BZCfbp6WtQ_CIW4lJP86G-iAv0";

// Test hotel data
const testHotel = {
    id: "hotel-12345",
    name: "Azure Coast Retreat",
    vendor: "Marriott",
    address: "123 Ocean Blvd, Miami, FL",
    city: "Miami",
    state: "FL",
    country: "USA",
    description: "A luxurious beachfront hotel with stunning ocean views",
    postalCode: "33139",
    phoneNumber: "+1-305-555-0123",
    email: "info@azurecoastretreat.com",
    website: "https://www.azurecoastretreat.com",
    rating: 4.8,
    reviews: [
        {
            username: "TravelLover",
            rating: 5.0,
            comment: "Amazing ocean view and very clean! Woke up to paradise every day.",
            date: "2024-01-15T10:00:00.000Z"
        }
    ],
    roomDetails: [
        {
            type: "Standard",
            pricePerNight: 150.00,
            mostPopular: false,
            cancellationPolicy: "Flexible",
            availableRooms: 5
        },
        {
            type: "Deluxe",
            pricePerNight: 225.00,
            mostPopular: true,
            cancellationPolicy: "Moderate",
            availableRooms: 3
        },
        {
            type: "Suite",
            pricePerNight: 450.00,
            mostPopular: false,
            cancellationPolicy: "Strict",
            availableRooms: 2
        }
    ],
    amenities: ["Free Wi-Fi", "Swimming Pool", "Spa", "Restaurant", "Bar/Lounge", "Fitness Center"],
    nearbyAttractions: [
        {
            name: "South Beach",
            type: "Beach",
            distance: 0.3
        },
        {
            name: "Art Deco Historic District",
            type: "Historical Site",
            distance: 0.8
        }
    ],
    policies: {
        checkin: {
            startTime: "15:00",
            endTime: "20:00",
            contactless: true,
            express: true,
            minAge: 21
        },
        checkout: {
            time: "11:00",
            contactless: true,
            express: true,
            lateFeeApplicable: true
        },
        petsAllowed: true,
        childrenPolicy: "Children welcome",
        extraBeds: "Available upon request",
        cribAvailability: "Available upon request",
        accessMethods: ["Key Card", "Mobile App", "Digital Key"],
        safetyFeatures: ["Smoke Detectors", "Fire Extinguishers", "Security Cameras", "24/7 Front Desk"],
        houseKeepingPolicy: "Daily housekeeping"
    },
    faq: [
        {
            question: "What time is check-in?",
            answer: "Check-in is available from 3:00 PM."
        },
        {
            question: "Is parking available?",
            answer: "Yes, complimentary parking is available for all guests."
        }
    ]
};

// Test insurance data
const testInsurance = {
    insType: "Travel Protection",
    insTotal: 25.99
};

// Test booking parameters
const testBookingParams = {
    total: 200.00,
    trip_id: "12345678-1234-1234-1234-123456789abc"
};

// Test function for booking a hotel
async function testHotelBooking() {
    console.log("Testing Hotel Booking...");
    
    try {
        const requestBody = {
            hotel: testHotel,
            insurance: testInsurance,
            total: testBookingParams.total,
            trip_id: testBookingParams.trip_id
        };

        const response = await fetch(`${BASE_URL}/hotel/book`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${TOKEN}`,
                "X-Client-ID": "test-client-id", 
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        const result = await response.json();
        
        if (response.ok) {
            console.log("Hotel booking successful!");
            console.log("Booking Details:", JSON.stringify(result, null, 2));
            return result;
        } else {
            console.log("Hotel booking failed!");
            console.log("Error details:", JSON.stringify(result, null, 2));
            return null;
        }
    } catch (error) {
        console.log("Hotel booking request failed!");
        console.log("Error:", error.message);
        return null;
    }
}

// Test function for getting a hotel booking
async function testGetHotelBooking(bookingId) {
    console.log("Testing Get Hotel Booking...");
    
    try {
        const response = await fetch(`${BASE_URL}/hotels/booking/${bookingId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${TOKEN}`,
                "X-Client-ID": "test-client-id",
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();
        
        if (response.ok) {
            console.log("Hotel booking retrieval successful!");
            console.log("Booking Details:", JSON.stringify(result, null, 2));
            return result;
        } else {
            console.log("Hotel booking retrieval failed!");
            console.log("Error details:", JSON.stringify(result, null, 2));
            return null;
        }
    } catch (error) {
        console.log("Hotel booking retrieval request failed!");
        console.log("Error:", error.message);
        return null;
    }
}

// Test function for deleting a hotel booking
async function testDeleteHotelBooking(bookingId) {
    console.log("Testing Delete Hotel Booking...", bookingId);
    
    try {
        const response = await fetch(`${BASE_URL}/hotels/delete`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${TOKEN}`,
                "X-Client-ID": "test-client-id",
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                hotelid: bookingId
            })
        });

        const result = await response.json();
        
        if (response.ok) {
            console.log("Hotel booking deletion successful!");
            console.log("Deletion Details:", JSON.stringify(result, null, 2));
            return result;
        } else {
            console.log("Hotel booking deletion failed!");
            console.log("Error details:", JSON.stringify(result, null, 2));
            return null;
        }
    } catch (error) {
        console.log("Hotel booking deletion request failed!");
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
                'Content-Type': 'application/json'
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

async function getAvailableHotels() {
    console.log("Testing Get Available Hotels...");
    try {
        const response = await fetch(`${BASE_URL}/hotels`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${TOKEN}`,
                "X-Client-ID": "test-client-id",
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (response.ok) {
            console.log("Available hotels retrieved successfully!");
            console.log("Available Hotels:", JSON.stringify(result, null, 2));
            return result;
        } else {
            console.log("Failed to retrieve available hotels!");
            console.log("Error details:", JSON.stringify(result, null, 2));
            return null;
        }
    } catch (error) {
        console.log("Get available hotels request failed!");
        console.log("Error:", error.message);
        return null;
    }
}

// Main test runner
async function runHotelBookingTests() {
    console.log("Starting Hotel Booking Service Tests...");
    console.log("=" .repeat(50));
    
    // Test 1: Service Health Check
    console.log("\nTest 1: Service Health Check");
    // await testServiceHealth();

    // await getAvailableHotels();
    
    // Test 2: Hotel Booking
    console.log("\nTest 2: Hotel Booking");
    const bookingResult = await testHotelBooking();
    
    if (bookingResult && bookingResult.booking_id) {
        // Test 3: Get Hotel Booking
        console.log("\nTest 3: Get Hotel Booking");
        await testGetHotelBooking(bookingResult.booking_id);
        
        // Test 4: Delete Hotel Booking
        console.log("\nTest 4: Delete Hotel Booking");
        await testDeleteHotelBooking(bookingResult.booking_id);
    } else {
        console.log("\nSkipping Get and Delete tests due to booking failure");
    }
    
    console.log("\n" + "=" .repeat(50));
    console.log("Hotel Booking Service Tests Completed!");
}

// Run the tests
runHotelBookingTests().catch(console.error);
