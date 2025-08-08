import React, { useState } from "react";
import "./App.css";

console.log('SimpleApp loaded - OFFLINE MODE');

function SimpleApp() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [user, setUser] = useState(null);
  const [error, setError] = useState('');

  // Hardcoded users with passwords - NO BACKEND NEEDED
  const users = [
    {
      id: "1", 
      name: "Kitchen Manager", 
      username: "manager", 
      password: "admin123",
      role: "manager"
    },
    {
      id: "2", 
      name: "Chef Alice", 
      username: "chef_alice", 
      password: "chef123",
      role: "kitchen_staff"
    },
    {
      id: "3", 
      name: "Chef Bob", 
      username: "chef_bob", 
      password: "chef456",
      role: "kitchen_staff"
    },
    {
      id: "4", 
      name: "Downtown Cafe", 
      username: "downtown_cafe", 
      password: "venue123",
      role: "venue_staff"
    },
    {
      id: "5", 
      name: "Uptown Restaurant", 
      username: "uptown_restaurant", 
      password: "venue456",
      role: "venue_staff"
    }
  ];

  const handleLogin = (e) => {
    e.preventDefault();
    console.log('Attempting offline login for:', username);
    
    // Find user by username
    const foundUser = users.find(u => u.username === username);
    
    if (!foundUser) {
      setError('User not found');
      return;
    }
    
    // Check password
    if (foundUser.password !== password) {
      setError('Invalid password');
      return;
    }
    
    // Login successful
    console.log('Login successful for:', foundUser.name);
    setUser({
      id: foundUser.id,
      name: foundUser.name,
      username: foundUser.username,
      role: foundUser.role
    });
    setError('');
  };

  const handleLogout = () => {
    setUser(null);
    setUsername('');
    setPassword('');
    setError('');
  };

  if (user) {
    return (
      <div className="min-h-screen bg-gray-100">
        <div className="bg-blue-600 text-white p-4">
          <div className="max-w-4xl mx-auto flex justify-between items-center">
            <h1 className="text-2xl font-bold">Production Kitchen Management</h1>
            <button 
              onClick={handleLogout} 
              className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded text-white"
            >
              Logout
            </button>
          </div>
        </div>
        
        <div className="max-w-4xl mx-auto p-6">
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Welcome, {user.name}!</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded">
                <strong>Name:</strong> {user.name}
              </div>
              <div className="bg-green-50 p-4 rounded">
                <strong>Role:</strong> {user.role.replace('_', ' ').toUpperCase()}
              </div>
              <div className="bg-purple-50 p-4 rounded">
                <strong>Username:</strong> {user.username}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">
              {user.role === 'manager' ? 'Manager Dashboard' : 
               user.role === 'kitchen_staff' ? 'Kitchen Staff Dashboard' : 
               'Venue Staff Dashboard'}
            </h3>
            
            {user.role === 'manager' && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-100 p-4 rounded text-center">
                  <h4 className="font-semibold">Production Items</h4>
                  <p className="text-sm">Manage kitchen production</p>
                </div>
                <div className="bg-green-100 p-4 rounded text-center">
                  <h4 className="font-semibold">Orders</h4>
                  <p className="text-sm">View all venue orders</p>
                </div>
                <div className="bg-purple-100 p-4 rounded text-center">
                  <h4 className="font-semibold">Users</h4>
                  <p className="text-sm">Manage staff accounts</p>
                </div>
              </div>
            )}
            
            {user.role === 'kitchen_staff' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-orange-100 p-4 rounded text-center">
                  <h4 className="font-semibold">Active Orders</h4>
                  <p className="text-sm">Orders to prepare</p>
                </div>
                <div className="bg-yellow-100 p-4 rounded text-center">
                  <h4 className="font-semibold">Production Queue</h4>
                  <p className="text-sm">Items in production</p>
                </div>
              </div>
            )}
            
            {user.role === 'venue_staff' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-teal-100 p-4 rounded text-center">
                  <h4 className="font-semibold">Place Order</h4>
                  <p className="text-sm">Order from kitchen</p>
                </div>
                <div className="bg-cyan-100 p-4 rounded text-center">
                  <h4 className="font-semibold">Order History</h4>
                  <p className="text-sm">View past orders</p>
                </div>
              </div>
            )}

            <div className="mt-6 p-4 bg-green-50 rounded">
              <p className="text-green-700">
                ✅ <strong>Authentication Successful!</strong> Password-based login is working perfectly.
              </p>
              <p className="text-sm text-green-600 mt-2">
                This is an offline demo. All authentication is handled locally without backend connections.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600">
      <div className="bg-white p-8 rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="text-center mb-6">
          <h2 className="text-3xl font-bold text-gray-800">Production Kitchen</h2>
          <p className="text-gray-600 mt-2">Secure Login System</p>
        </div>
        
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select User
            </label>
            <select
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">Choose a user...</option>
              {users.map(user => (
                <option key={user.id} value={user.username}>
                  {user.name} ({user.role.replace('_', ' ')})
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <button 
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-md transition duration-200"
          >
            Login
          </button>
        </form>

        <div className="mt-6 p-4 bg-gray-50 rounded-md">
          <p className="text-sm font-semibold text-gray-700 mb-2">Test Credentials:</p>
          <div className="space-y-1 text-xs text-gray-600">
            <p><strong>Manager:</strong> manager / admin123</p>
            <p><strong>Chef Alice:</strong> chef_alice / chef123</p>
            <p><strong>Chef Bob:</strong> chef_bob / chef456</p>
            <p><strong>Downtown Cafe:</strong> downtown_cafe / venue123</p>
            <p><strong>Uptown Restaurant:</strong> uptown_restaurant / venue456</p>
          </div>
          <p className="text-xs text-blue-600 mt-2">
            🔒 All authentication is handled locally - no network required!
          </p>
        </div>
      </div>
    </div>
  );
}

export default SimpleApp;