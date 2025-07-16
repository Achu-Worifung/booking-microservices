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
    local service_name="$1"
    local port=$2
    
    echo -n "Checking $service_name (port $port)... "
    
    if curl -s -m 5 http://localhost:$port/docs > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Running${NC}"
        return 0
    else
        echo -e "${RED}❌ Not running${NC}"
        return 1
    fi
}

echo -e "${YELLOW}Step 1: Checking if microservices are running...${NC}"
echo "------------------------------------------------"

# Check each service
services_running=0
total_services=7

check_service "Flight Service" 8000 && ((services_running++))
check_service "Car Booking Service" 8001 && ((services_running++))
check_service "Hotel Service" 8002 && ((services_running++))
check_service "User Service" 8004 && ((services_running++))
check_service "Flight Booking Service" 8006 && ((services_running++))
check_service "Car Service" 8010 && ((services_running++))
check_service "Trip Service" 8012 && ((services_running++))

echo ""
echo -e "${YELLOW}📊 Results: $services_running/$total_services services are running${NC}"

if [ $services_running -eq 0 ]; then
    echo -e "${RED}❌ No services are running!${NC}"
    echo -e "${YELLOW}💡 Start services with: ./run_all.bash${NC}"
elif [ $services_running -lt $total_services ]; then
    echo -e "${YELLOW}⚠️  Some services are not running${NC}"
    echo -e "${YELLOW}💡 Start missing services with: ./run_all.bash${NC}"
else
    echo -e "${GREEN}✅ All services are running!${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2: Testing API endpoints...${NC}"
echo "------------------------------------------------"

test_endpoint() {
    local name="$1"
    local url="$2"
    
    echo -n "Testing $name... "
    
    response=$(curl -s -m 5 -w "%{http_code}" -o /dev/null $url 2>/dev/null)
    
    if [ "$response" -eq 200 ] || [ "$response" -eq 404 ] || [ "$response" -eq 422 ]; then
        echo -e "${GREEN}✅ HTTP $response${NC}"
    else
        echo -e "${RED}❌ HTTP $response${NC}"
    fi
}

test_endpoint "Flight Service /docs" "http://localhost:8000/docs"
test_endpoint "Car Booking Service /docs" "http://localhost:8001/docs"
test_endpoint "Hotel Service /docs" "http://localhost:8002/docs"
test_endpoint "User Service /docs" "http://localhost:8004/docs"
test_endpoint "Flight Booking Service /docs" "http://localhost:8006/docs"
test_endpoint "Car Service /docs" "http://localhost:8010/docs"
test_endpoint "Trip Service /docs" "http://localhost:8012/docs"

echo ""
echo -e "${YELLOW}Step 3: Next.js Integration Status${NC}"
echo "------------------------------------------------"

if [ $services_running -gt 0 ]; then
    echo -e "${GREEN}✅ Ready for Next.js integration!${NC}"
    echo ""
    echo -e "${GREEN}🔧 Next.js API Configuration:${NC}"
    echo "• Base URLs are configured in nextjs-integration/api-config.js"
    echo "• Test page available at nextjs-integration/test-page.html"
    echo "• React component at nextjs-integration/microservices-test.tsx"
    echo ""
    echo -e "${GREEN}📝 Example fetch calls:${NC}"
    echo "  const flights = await fetch('http://localhost:8000/flights')"
    echo "  const hotels = await fetch('http://localhost:8002/hotels')"
    echo "  const users = await fetch('http://localhost:8004/users')"
else
    echo -e "${RED}❌ Services not running - cannot test Next.js integration${NC}"
fi

echo ""
echo -e "${YELLOW}Step 4: Opening test page...${NC}"
echo "------------------------------------------------"

# Open the test page in the browser
if command -v open > /dev/null 2>&1; then
    echo "Opening test page in browser..."
    open "file:///Users/alanrivera/booking-microservices/nextjs-integration/test-page.html"
elif command -v xdg-open > /dev/null 2>&1; then
    echo "Opening test page in browser..."
    xdg-open "file:///Users/alanrivera/booking-microservices/nextjs-integration/test-page.html"
else
    echo "Please open this file in your browser:"
    echo "file:///Users/alanrivera/booking-microservices/nextjs-integration/test-page.html"
fi

echo ""
echo -e "${GREEN}✅ Test completed!${NC}"
echo "Check the browser test page for detailed connectivity results."
