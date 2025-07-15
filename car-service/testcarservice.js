const BASE_URL = "http://localhost:8010"; // User service port

// Test credentials


async function getCars() {
  const res = await fetch(`${BASE_URL}/cars`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "X-Client-ID": "test-client-id", 
    },
  });

  const data = await res.json();
  console.log(
    `Get cars response: ${res.status} - ${JSON.stringify(data, null, 2)}`
  );
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// this is to test the rate limit functionality
async function testRateLimit() {
  for (let i = 0; i < 10; i++) {
    try {
      const res = await fetch(`${BASE_URL}/cars`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-Client-ID": "test-client-id", //use ipaddress or user token if signed in
        },
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

getCars().then(() => {
  console.log("Get cars test completed.");
});
testRateLimit().then(() => {
  console.log("Rate limit test completed.");
});
