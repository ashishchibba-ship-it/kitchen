// Quick debug script to test environment variables in Node.js context
console.log('Environment check:');
console.log('REACT_APP_BACKEND_URL:', process.env.REACT_APP_BACKEND_URL);
console.log('NODE_ENV:', process.env.NODE_ENV);

// Test if we can reach the API
const axios = require('axios');

async function testAPI() {
  try {
    const url = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
    console.log('Testing API at:', `${url}/api/users`);
    
    const response = await axios.get(`${url}/api/users`);
    console.log('API test successful, got', response.data.length, 'users');
    console.log('First user:', response.data[0]);
  } catch (error) {
    console.error('API test failed:', error.message);
  }
}

testAPI();