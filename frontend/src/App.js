import React, { useState } from "react";
import "./App.css";
import axios from "axios";

const API = '/api';

// Simple Login Component
const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const users = [
    {id: "1", name: "Manager", username: "system_manager"},
    {id: "2", name: "Production Kitchen", username: "production_kitchen"},
    {id: "3", name: "Street Eats City", username: "yagansquare_streeteats"},
    {id: "4", name: "Street Eats Rockingham", username: "rockingham_streeteats"}
  ];

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      console.log('Attempting login to:', `${API}/login`);
      const response = await axios.post(`${API}/login`, {
        username,
        password
      });
      if (response.data && response.data.user) {
        onLogin(response.data.user);
      }
    } catch (error) {
      console.error('Login error:', error);
      setError('Login failed. Please try again.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-800">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full m-4">
        <h2 className="text-2xl font-bold text-gray-800 text-center mb-6">
          Production Kitchen Login
        </h2>
        
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select User
            </label>
            <select
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md"
              required
            >
              <option value="">Choose a user...</option>
              {users.map(user => (
                <option key={user.id} value={user.username}>
                  {user.name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md"
              required
            />
          </div>

          {error && (
            <div className="text-red-600 text-sm">
              {error}
            </div>
          )}

          <button 
            type="submit"
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700"
          >
            Login
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          <p><strong>Test Credentials:</strong></p>
          <p>Manager: system_manager / admin123</p>
          <p>Kitchen: production_kitchen / chef456</p>
        </div>
      </div>
    </div>
  );
};

// Simple App Component
function App() {
  const [user, setUser] = useState(null);

  if (!user) {
    return <Login onLogin={setUser} />;
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-xl font-semibold text-gray-800">
            Welcome, {user.name}! ({user.role})
          </h1>
          <button 
            onClick={() => setUser(null)}
            className="mt-2 bg-red-600 text-white px-4 py-2 rounded"
          >
            Logout
          </button>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Dashboard</h2>
          <p>Authentication successful! You are logged in as:</p>
          <ul className="mt-2">
            <li><strong>Name:</strong> {user.name}</li>
            <li><strong>Role:</strong> {user.role}</li>
            <li><strong>Username:</strong> {user.username}</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;