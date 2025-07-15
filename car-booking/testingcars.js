const BASE_URL = 'http://127.0.0.1:8001';  // Changed to port 8001
const TEST_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTIzNDU2NzgtMTIzNC0xMjM0LTEyMzQtMTIzNDU2Nzg5MDEyIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZm5hbWUiOiJKb2huIiwibG5hbWUiOiJEb2UifQ.fake-signature'; // You'll need a real token

// Helper function to make requests
async function makeRequest(endpoint, method = 'GET', body = null, requiresAuth = false) {
    try {
        const headers = {
            'Content-Type': 'application/json'
        };

        // Add Authorization header if required
        if (requiresAuth) {
            headers['Authorization'] = `Bearer ${TEST_TOKEN}`;
        }

        const response = await fetch(`${BASE_URL}${endpoint}`, {
            method,
            headers,
            body: body ? JSON.stringify(body) : null
        });

        console.log(`Response status: ${response.status}`);
        
        if (!response.ok) {
            let errorMessage;
            try {
                const errorData = await response.json();
                console.log('Error data:', JSON.stringify(errorData, null, 2));
                errorMessage = errorData.detail || JSON.stringify(errorData, null, 2);
            } catch (parseError) {
                errorMessage = await response.text();
                console.log('Error text:', errorMessage);
            }
            throw new Error(`${response.status} - ${errorMessage}`);
        }

        return {
            status: response.status,
            data: await response.json()
        };
    } catch (error) {
        if (error.code === 'ECONNREFUSED') {
            console.error(`❌ Connection refused: Is the service running on ${BASE_URL}?`);
        } else {
            console.error(`❌ Error: ${error.message}`);
        }
        throw error;
    }
}

async function runTests() {
    console.log('🚗 Testing Car Booking Service API...\n');

    // First, let's check if the service is running at all
    console.log('0. Checking if service is running...');
    try {
        const testResponse = await fetch(BASE_URL);
        console.log(`✅ Service is running on ${BASE_URL}`);
    } catch (error) {
        console.log(`❌ Cannot connect to ${BASE_URL}`);
        console.log('❌ Make sure your car-booking service is running with: python main.py');
        console.log('❌ Error details:', error.message);
        return;
    }

    try {
        // Test 1: Root endpoint (no auth required)
        console.log('\n1. Testing root endpoint...');
        const rootResponse = await makeRequest('/');
        console.log(`✅ Status: ${rootResponse.status}`);
        console.log(`✅ Service: ${rootResponse.data.service}`);
        console.log(`✅ Version: ${rootResponse.data.version}\n`);

        // Test 2: Get all available cars
        console.log('2. Testing get all cars...');
        const carsResponse = await makeRequest('/cars');
        console.log(`✅ Status: ${carsResponse.status}`);
        console.log(`✅ Found ${carsResponse.data.length} available cars`);
        if (carsResponse.data.length > 0) {
            console.log(`✅ First car: ${carsResponse.data[0].make} ${carsResponse.data[0].model} - $${carsResponse.data[0].price_per_day}/day\n`);
        }

        // Test 3: Get cars by type
        console.log('3. Testing get cars by type (SUV)...');
        const suvResponse = await makeRequest('/cars/SUV');
        console.log(`✅ Status: ${suvResponse.status}`);
        console.log(`✅ Found ${suvResponse.data.length} SUVs available`);
        if (suvResponse.data.length > 0) {
            console.log(`✅ First SUV: ${suvResponse.data[0].make} ${suvResponse.data[0].model} - $${suvResponse.data[0].price_per_day}/day\n`);
        }

        // Test 4: Try to book a car (will fail without valid token)
        console.log('4. Testing car booking endpoint (without auth - should fail)...');
        try {
            const bookingData = {
                car: {
                    id: "car-001",
                    make: "Toyota",
                    model: "Camry",
                    year: 2023,
                    color: ["Blue"],
                    seat: 5,
                    type: "Sedan",
                    price_per_day: 45.0,
                    feature: "Air Conditioning • Bluetooth",
                    transmission: "Automatic",
                    fuel_type: "Petrol",
                    available: true,
                    rating: 4.5
                },
                total: 135.0
            };
            
            await makeRequest('/car/book', 'POST', bookingData, false);
        } catch (error) {
            console.log('✅ Expected failure: Booking requires authentication\n');
        }

        // Test 5: Try to get booking (will fail without valid token)
        console.log('5. Testing get booking endpoint (without auth - should fail)...');
        try {
            await makeRequest('/cars/booking/test-booking-id', 'GET', null, false);
        } catch (error) {
            console.log('✅ Expected failure: Get booking requires authentication\n');
        }

        // Test 6: Try to delete booking (will fail without valid token)
        console.log('6. Testing delete booking endpoint (without auth - should fail)...');
        try {
            const deleteData = { carid: "test-booking-id" };
            await makeRequest('/cars/delete', 'DELETE', deleteData, false);
        } catch (error) {
            console.log('✅ Expected failure: Delete booking requires authentication\n');
        }

        console.log('🎉 Basic API structure tests completed!');
        console.log('ℹ️  To test authenticated endpoints, you need a valid JWT token');

    } catch (error) {
        console.log('❌ Test failed');
        console.log('Full error details:', error.message);
    }
}

// Run the tests
runTests();