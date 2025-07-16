// Example Next.js component using the API config
import { useState, useEffect } from 'react';
import { apiHelpers, API_ENDPOINTS } from '../lib/api-config';

export default function BookingServices() {
  const [flights, setFlights] = useState([]);
  const [hotels, setHotels] = useState([]);
  const [cars, setCars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        
        // Fetch data from all services
        const [flightData, hotelData, carData] = await Promise.all([
          apiHelpers.get(API_ENDPOINTS.FLIGHTS),
          apiHelpers.get(API_ENDPOINTS.HOTELS),
          apiHelpers.get(API_ENDPOINTS.CARS)
        ]);

        setFlights(flightData);
        setHotels(hotelData);
        setCars(carData);
        
      } catch (err) {
        setError(err.message);
        console.error('Failed to fetch data:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) return <div>Loading booking services...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="booking-services">
      <h1>Booking Services Dashboard</h1>
      
      {/* Flights Section */}
      <section>
        <h2>✈️ Available Flights ({flights.length})</h2>
        <div className="grid">
          {flights.slice(0, 3).map((flight, index) => (
            <div key={index} className="card">
              <h3>{flight.airline} {flight.flightNumber}</h3>
              <p>{flight.departureAirport} → {flight.destinationAirport}</p>
              <p>Price: ${flight.prices?.Economy}</p>
              <p>Status: {flight.status}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Hotels Section */}
      <section>
        <h2>🏨 Available Hotels ({hotels.length})</h2>
        <div className="grid">
          {hotels.slice(0, 3).map((hotel, index) => (
            <div key={index} className="card">
              <h3>{hotel.name}</h3>
              <p>{hotel.city}, {hotel.state}</p>
              <p>Rating: {hotel.rating}/5</p>
              <p>From: ${hotel.roomDetails?.[0]?.pricePerNight}/night</p>
            </div>
          ))}
        </div>
      </section>

      {/* Cars Section */}
      <section>
        <h2>🚗 Available Cars ({cars.length})</h2>
        <div className="grid">
          {cars.slice(0, 3).map((car, index) => (
            <div key={index} className="card">
              <h3>{car.make} {car.model}</h3>
              <p>Year: {car.year}</p>
              <p>Price: ${car.pricePerDay}/day</p>
              <p>Available: {car.available ? 'Yes' : 'No'}</p>
            </div>
          ))}
        </div>
      </section>

      <style jsx>{`
        .booking-services {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
        }
        
        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 20px;
          margin: 20px 0;
        }
        
        .card {
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 20px;
          background: white;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .card h3 {
          margin-top: 0;
          color: #333;
        }
        
        section {
          margin: 40px 0;
        }
        
        h2 {
          color: #0070f3;
          border-bottom: 2px solid #0070f3;
          padding-bottom: 10px;
        }
      `}</style>
    </div>
  );
}
