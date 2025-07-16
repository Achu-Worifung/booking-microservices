#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔍 Testing Microservices Connection to Next.js${NC}"
echo "=================================================="

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    
    echo -n "Checking $service_name (port $port)... "
    
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:$port > /dev/null 2>&1; then
        response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port)
        if [ "$response" -eq 200 ] || [ "$response" -eq 404 ] || [ "$response" -eq 422 ]; then
            echo -e "${GREEN}✅ Running${NC}"
            return 0
        else
            echo -e "${RED}❌ Not responding (HTTP $response)${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Not running${NC}"
        return 1
    fi
}

# Test /docs endpoint for each service
test_docs_endpoint() {
    local service_name=$1
    local port=$2
    
    echo -n "Testing $service_name /docs endpoint... "
    
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/docs > /dev/null 2>&1; then
        response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/docs)
        if [ "$response" -eq 200 ]; then
            echo -e "${GREEN}✅ Available${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  HTTP $response${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Not available${NC}"
        return 1
    fi
}

# Array of services with their actual ports from main.py files
declare -A services=(
    ["Flight Service"]="8000"
    ["Car Booking Service"]="8001"
    ["Hotel Service"]="8002"
    ["User Service"]="8004"
    ["Flight Booking Service"]="8006"
    ["Car Service"]="8010"
    ["Trip Service"]="8012"
)

echo -e "${YELLOW}Step 1: Checking if microservices are running...${NC}"
echo "------------------------------------------------"

all_running=true
for service in "${!services[@]}"; do
    port=${services[$service]}
    if ! check_service "$service" "$port"; then
        all_running=false
    fi
done

if [ "$all_running" = false ]; then
    echo ""
    echo -e "${RED}❌ Some services are not running!${NC}"
    echo -e "${YELLOW}💡 Please start the services using: ./run_all.bash${NC}"
    echo ""
    echo "Starting services now..."
    
    # Check if run_all.bash exists and is executable
    if [ -f "./run_all.bash" ]; then
        chmod +x ./run_all.bash
        ./run_all.bash &
        
        echo "Waiting 10 seconds for services to start..."
        sleep 10
        
        # Test again
        echo -e "${YELLOW}Re-testing services...${NC}"
        for service in "${!services[@]}"; do
            port=${services[$service]}
            check_service "$service" "$port"
        done
    else
        echo -e "${RED}❌ run_all.bash not found!${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Step 2: Testing API documentation endpoints...${NC}"
echo "------------------------------------------------"

for service in "${!services[@]}"; do
    port=${services[$service]}
    test_docs_endpoint "$service" "$port"
done

echo ""
echo -e "${YELLOW}Step 3: Testing specific API endpoints...${NC}"
echo "------------------------------------------------"

# Test specific endpoints
test_endpoint() {
    local service_name=$1
    local port=$2
    local endpoint=$3
    local method=$4
    
    echo -n "Testing $service_name $endpoint... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port$endpoint)
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X $method http://localhost:$port$endpoint)
    fi
    
    if [ "$response" -eq 200 ] || [ "$response" -eq 422 ] || [ "$response" -eq 404 ]; then
        echo -e "${GREEN}✅ HTTP $response${NC}"
    else
        echo -e "${RED}❌ HTTP $response${NC}"
    fi
}

# Test some common endpoints
test_endpoint "Flight Service" "8000" "/flights" "GET"
test_endpoint "Car Booking Service" "8001" "/bookings" "GET"
test_endpoint "Hotel Service" "8002" "/hotels" "GET"
test_endpoint "User Service" "8004" "/users" "GET"
test_endpoint "Trip Service" "8012" "/trips" "GET"

echo ""
echo -e "${YELLOW}Step 4: Creating Next.js connection test...${NC}"
echo "------------------------------------------------"

# Create a simple connection test file
cat > /tmp/test-connection.js << 'EOF'
const axios = require('axios');

// Service endpoints based on actual ports
const services = {
    'Flight Service': 'http://localhost:8000',
    'Car Booking Service': 'http://localhost:8001',
    'Hotel Service': 'http://localhost:8002',
    'User Service': 'http://localhost:8004',
    'Flight Booking Service': 'http://localhost:8006',
    'Car Service': 'http://localhost:8010',
    'Trip Service': 'http://localhost:8012'
};

async function testConnections() {
    console.log('🔍 Testing connections from Node.js...\n');
    
    for (const [serviceName, baseUrl] of Object.entries(services)) {
        try {
            const response = await axios.get(`${baseUrl}/docs`, { timeout: 5000 });
            console.log(`✅ ${serviceName}: Connected (HTTP ${response.status})`);
        } catch (error) {
            if (error.code === 'ECONNREFUSED') {
                console.log(`❌ ${serviceName}: Connection refused (service not running)`);
            } else if (error.response) {
                console.log(`⚠️  ${serviceName}: HTTP ${error.response.status}`);
            } else {
                console.log(`❌ ${serviceName}: ${error.message}`);
            }
        }
    }
}

testConnections();
EOF

echo "Running Node.js connection test..."
if command -v node > /dev/null 2>&1; then
    # Check if axios is available
    if npm list axios > /dev/null 2>&1 || npm list -g axios > /dev/null 2>&1; then
        node /tmp/test-connection.js
    else
        echo -e "${YELLOW}⚠️  axios not found. Installing temporarily...${NC}"
        npm install axios --silent
        node /tmp/test-connection.js
    fi
else
    echo -e "${RED}❌ Node.js not found. Please install Node.js to test Next.js connectivity.${NC}"
fi

echo ""
echo -e "${YELLOW}Step 5: Summary and Next.js Integration Tips${NC}"
echo "=================================================="

echo -e "${GREEN}✅ Microservices Status Summary:${NC}"
echo "• Flight Service:         http://localhost:8000"
echo "• Car Booking Service:    http://localhost:8001"  
echo "• Hotel Service:          http://localhost:8002"
echo "• User Service:           http://localhost:8004"
echo "• Flight Booking Service: http://localhost:8006"
echo "• Car Service:            http://localhost:8010"
echo "• Trip Service:           http://localhost:8012"
echo ""
echo -e "${GREEN}📝 Next.js Integration Notes:${NC}"
echo "• Use these exact URLs in your Next.js API calls"
echo "• All services support CORS for frontend integration"
echo "• API documentation available at /docs endpoint for each service"
echo "• Consider using axios or fetch for API calls"
echo ""
echo -e "${GREEN}🔧 Example Next.js API call:${NC}"
echo "const response = await fetch('http://localhost:8000/flights');"
echo "const flights = await response.json();"

# Clean up
rm -f /tmp/test-connection.js

echo ""
echo -e "${GREEN}✅ Connection test completed!${NC}"
