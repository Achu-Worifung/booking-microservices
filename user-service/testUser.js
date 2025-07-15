const BASE_URL = "http://127.0.0.1:8004"; // User service port

// Test credentials
const TEST_CREDENTIALS = {
  email: "john.doe@example.com",
  password: "securepassword123",
};

async function signIn() {
  const res = await fetch(`${BASE_URL}/signin`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Client-ID": "test-client-id", //use ipaddress or user token if signed in
    },
    body: JSON.stringify(TEST_CREDENTIALS),
  });

  const data = await res.json();
  console.log(
    `Sign-in response: ${res.status} - ${JSON.stringify(data, null, 2)}`
  );
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// this is to test the rate limit functionality
async function testRateLimit() {
  for (let i = 0; i < 10; i++) {
    try {
      const res = await fetch(`${BASE_URL}/signin`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Client-ID": "test-client-id", //use ipaddress or user token if signed in
        },
        body: JSON.stringify(TEST_CREDENTIALS),
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

testRateLimit().then(() => {
  console.log("Rate limit test completed.");
});
