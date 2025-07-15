const BASE_URL = "http://127.0.0.1:8000"; // User service port


async function getFlight() {
  const res = await fetch(`${BASE_URL}/flights?departure_date=2023-10-01&count=5`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "X-Client-ID": "test-client-id",
    },
  });

  const data = await res.json();
  console.log(
    `Get flights response: ${res.status} - ${JSON.stringify(data, null, 2)}`
  );
}



function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// this is to test the rate limit functionality
async function testRateLimit() {
  for (let i = 0; i < 5; i++) {
    try {
        // Example request to get flights with specific parameters
      const res = await fetch(`${BASE_URL}/flights?departure_date=2023-10-01&count=5`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-Client-ID": "test-client-id", //use ipaddress or user token if signed in
        },
        // body: JSON.stringify({
        //   departure_date: "2023-10-01", // Example date
        //   count: 5, // Example count
        // }),
      });

      const data = await res.json();

      if (!res.ok) {
        console.error(`Request ${i + 1}: Error`, res.status, data.detail);
      } else {
        console.log(`Request ${i + 1}: Success`, data);
      }
    } catch (err) {
      console.error(`Request ${i + 1}: Network Error`, err.message);
    }

    await sleep(1000);
  }
    
  
}

getFlight().then(() => {
  console.log("Get flights test completed.");
});
testRateLimit().then(() => {
  console.log("Rate limit test completed.");
});
