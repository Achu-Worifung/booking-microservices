import React, { useState, useEffect } from 'react';

interface ServiceStatus {
  name: string;
  url: string;
  status: 'loading' | 'connected' | 'error';
  response?: any;
  error?: string;
}

export default function MicroservicesTest() {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: 'Flight Service', url: 'http://localhost:8000', status: 'loading' },
    { name: 'Car Booking Service', url: 'http://localhost:8001', status: 'loading' },
    { name: 'Hotel Service', url: 'http://localhost:8002', status: 'loading' },
    { name: 'User Service', url: 'http://localhost:8004', status: 'loading' },
    { name: 'Flight Booking Service', url: 'http://localhost:8006', status: 'loading' },
    { name: 'Car Service', url: 'http://localhost:8010', status: 'loading' },
    { name: 'Trip Service', url: 'http://localhost:8012', status: 'loading' },
  ]);

  const testService = async (service: ServiceStatus): Promise<ServiceStatus> => {
    try {
      // Test the /docs endpoint first
      const response = await fetch(`${service.url}/docs`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        return {
          ...service,
          status: 'connected',
          response: `HTTP ${response.status}`,
        };
      } else {
        return {
          ...service,
          status: 'error',
          error: `HTTP ${response.status}`,
        };
      }
    } catch (error) {
      return {
        ...service,
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  };

  const testAllServices = async () => {
    setServices(prev => prev.map(s => ({ ...s, status: 'loading' })));
    
    const promises = services.map(service => testService(service));
    const results = await Promise.all(promises);
    
    setServices(results);
  };

  useEffect(() => {
    testAllServices();
  }, []);

  const getStatusColor = (status: ServiceStatus['status']) => {
    switch (status) {
      case 'loading':
        return 'text-yellow-600';
      case 'connected':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: ServiceStatus['status']) => {
    switch (status) {
      case 'loading':
        return '⏳';
      case 'connected':
        return '✅';
      case 'error':
        return '❌';
      default:
        return '⚪';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          Microservices Connection Test
        </h1>
        <p className="text-gray-600">
          Testing connectivity between Next.js and booking microservices
        </p>
      </div>

      <div className="mb-6">
        <button
          onClick={testAllServices}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          🔄 Test All Services
        </button>
      </div>

      <div className="grid gap-4">
        {services.map((service, index) => (
          <div
            key={index}
            className="border rounded-lg p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{getStatusIcon(service.status)}</span>
                <div>
                  <h3 className="font-semibold text-gray-800">{service.name}</h3>
                  <p className="text-sm text-gray-500">{service.url}</p>
                </div>
              </div>
              <div className={`text-sm font-medium ${getStatusColor(service.status)}`}>
                {service.status === 'loading' && 'Testing...'}
                {service.status === 'connected' && `Connected ${service.response}`}
                {service.status === 'error' && `Error: ${service.error}`}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <h3 className="font-semibold text-blue-800 mb-2">📝 Integration Notes:</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• All services run on localhost with different ports</li>
          <li>• Services support CORS for frontend integration</li>
          <li>• API documentation available at /docs endpoint</li>
          <li>• Use fetch() or axios for API calls from Next.js</li>
        </ul>
      </div>

      <div className="mt-6 p-4 bg-green-50 rounded-lg">
        <h3 className="font-semibold text-green-800 mb-2">🔧 Example API Usage:</h3>
        <pre className="text-sm text-green-700 bg-green-100 p-2 rounded overflow-x-auto">
{`// Example: Fetch flights
const response = await fetch('http://localhost:8000/flights');
const flights = await response.json();

// Example: Create booking
const booking = await fetch('http://localhost:8001/bookings', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ /* booking data */ })
});`}
        </pre>
      </div>
    </div>
  );
}
