import React, { useState } from "react";
import "./App.css";
import axios from "axios";

console.log('SimpleApp loaded with API:', '/api');

function SimpleApp() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [user, setUser] = useState(null);
  const [error, setError] = useState('');

  const users = [
    {id: "1", name: "Manager", username: "updated_manager"},
    {id: "2", name: "Chef Alice", username: "chef_alice"}
  ];

  const handleLogin = async (e) => {
    e.preventDefault();
    console.log('Login attempt to:', '/api/login');
    try {
      const response = await axios.post('/api/login', {
        username,
        password
      });
      console.log('Login success:', response.data);
      setUser(response.data.user);
    } catch (error) {
      console.error('Login error:', error);
      setError('Login failed: ' + error.message);
    }
  };

  if (user) {
    return (
      <div className="min-h-screen bg-gray-100 p-8">
        <h1>Welcome {user.name}!</h1>
        <p>Role: {user.role}</p>
        <button onClick={() => setUser(null)} className="bg-red-500 text-white px-4 py-2 rounded">
          Logout
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-800">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
        <h2 className="text-2xl font-bold text-center mb-6">Simple Login Test</h2>
        
        <form onSubmit={handleLogin} className="space-y-4">
          <select
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full p-3 border rounded"
            required
          >
            <option value="">Choose user...</option>
            {users.map(user => (
              <option key={user.id} value={user.username}>
                {user.name}
              </option>
            ))}
          </select>
          
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className="w-full p-3 border rounded"
            required
          />

          {error && <div className="text-red-600">{error}</div>}

          <button 
            type="submit"
            className="w-full bg-blue-600 text-white py-3 rounded"
          >
            Login
          </button>
        </form>

        <div className="mt-4 text-sm text-gray-600">
          <p>Test: Manager / admin123</p>
          <p>Test: Chef Alice / chef123</p>
        </div>
      </div>
    </div>
  );
}

export default SimpleApp;