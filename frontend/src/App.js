import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Login Component
const Login = ({ onLogin }) => {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState('');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const handleLogin = () => {
    const user = users.find(u => u.username === selectedUser);
    if (user) {
      onLogin(user);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-center text-gray-800 mb-6">
          Production Kitchen Login
        </h2>
        <div className="space-y-4">
          <select 
            value={selectedUser} 
            onChange={(e) => setSelectedUser(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select User</option>
            {users.map(user => (
              <option key={user.id} value={user.username}>
                {user.name} ({user.role})
              </option>
            ))}
          </select>
          <button 
            onClick={handleLogin}
            disabled={!selectedUser}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
          >
            Login
          </button>
        </div>
      </div>
    </div>
  );
};

// Manager Dashboard
const ManagerDashboard = ({ user }) => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [productionItems, setProductionItems] = useState([]);
  const [orders, setOrders] = useState([]);
  const [newItem, setNewItem] = useState({
    name: '',
    quantity: '',
    target_time: '',
    production_date: new Date().toISOString().split('T')[0],
    cost: ''
  });

  useEffect(() => {
    fetchStats();
    fetchProductionItems();
    fetchOrders();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchProductionItems = async () => {
    try {
      const response = await axios.get(`${API}/production-items`);
      setProductionItems(response.data);
    } catch (error) {
      console.error('Error fetching production items:', error);
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders`);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const handleCreateItem = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/production-items?created_by=${user.username}`, {
        ...newItem,
        quantity: parseInt(newItem.quantity),
        cost: newItem.cost ? parseFloat(newItem.cost) : null
      });
      setNewItem({
        name: '',
        quantity: '',
        target_time: '',
        production_date: new Date().toISOString().split('T')[0],
        cost: ''
      });
      fetchProductionItems();
      fetchStats();
    } catch (error) {
      console.error('Error creating production item:', error);
    }
  };

  const updateOrderStatus = async (orderId, status) => {
    try {
      await axios.put(`${API}/orders/${orderId}/status?status=${status}`);
      fetchOrders();
    } catch (error) {
      console.error('Error updating order status:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-xl font-semibold text-gray-800">Manager Dashboard</h1>
            <span className="text-gray-600">Welcome, {user.name}</span>
          </div>
          <div className="flex space-x-6">
            {['dashboard', 'production', 'orders'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-2 px-4 border-b-2 ${activeTab === tab ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'dashboard' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {stats && (
              <>
                <div className="bg-white p-6 rounded-lg shadow">
                  <h3 className="text-lg font-semibold text-gray-800">Today's Production</h3>
                  <p className="text-3xl font-bold text-blue-600">{stats.production.total_items_today}</p>
                  <p className="text-sm text-gray-600">Total Items</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <h3 className="text-lg font-semibold text-gray-800">Completed</h3>
                  <p className="text-3xl font-bold text-green-600">{stats.production.completed_items_today}</p>
                  <p className="text-sm text-gray-600">Items Done</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <h3 className="text-lg font-semibold text-gray-800">Completion Rate</h3>
                  <p className="text-3xl font-bold text-purple-600">{stats.production.completion_rate.toFixed(1)}%</p>
                  <p className="text-sm text-gray-600">Today</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <h3 className="text-lg font-semibold text-gray-800">Pending Orders</h3>
                  <p className="text-3xl font-bold text-orange-600">{stats.orders.pending_orders}</p>
                  <p className="text-sm text-gray-600">Need Processing</p>
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === 'production' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Add Production Item</h3>
              <form onSubmit={handleCreateItem} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <input
                  type="text"
                  placeholder="Item Name"
                  value={newItem.name}
                  onChange={(e) => setNewItem({...newItem, name: e.target.value})}
                  className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
                <input
                  type="number"
                  placeholder="Quantity"
                  value={newItem.quantity}
                  onChange={(e) => setNewItem({...newItem, quantity: e.target.value})}
                  className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
                <input
                  type="time"
                  value={newItem.target_time}
                  onChange={(e) => setNewItem({...newItem, target_time: e.target.value})}
                  className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
                <input
                  type="date"
                  value={newItem.production_date}
                  onChange={(e) => setNewItem({...newItem, production_date: e.target.value})}
                  className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
                <input
                  type="number"
                  step="0.01"
                  placeholder="Cost (optional)"
                  value={newItem.cost}
                  onChange={(e) => setNewItem({...newItem, cost: e.target.value})}
                  className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  className="bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 transition-colors"
                >
                  Add Item
                </button>
              </form>
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
              <h3 className="text-lg font-semibold text-gray-800 p-4 border-b">Production Items</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Target Time</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cost</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {productionItems.map(item => (
                      <tr key={item.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.quantity}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.target_time}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.production_date}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            item.status === 'completed' ? 'bg-green-100 text-green-800' :
                            item.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {item.status.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          ${item.cost ? item.cost.toFixed(2) : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'orders' && (
          <div className="bg-white rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-800 p-4 border-b">Orders Management</h3>
            <div className="space-y-4 p-4">
              {orders.map(order => (
                <div key={order.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-semibold text-gray-800">{order.venue_name}</h4>
                      <p className="text-sm text-gray-600">Order Date: {new Date(order.order_date).toLocaleDateString()}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-semibold text-gray-800">${order.final_cost.toFixed(2)}</p>
                      <p className="text-sm text-gray-600">({order.markup}% markup)</p>
                    </div>
                  </div>
                  <div className="mb-3">
                    <h5 className="font-medium text-gray-700 mb-2">Items:</h5>
                    {order.items.map((item, index) => (
                      <div key={index} className="text-sm text-gray-600">
                        {item.production_item_name} - Qty: {item.quantity} @ ${item.unit_cost.toFixed(2)}
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-between items-center">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      order.status === 'delivered' ? 'bg-green-100 text-green-800' :
                      order.status === 'ready' ? 'bg-blue-100 text-blue-800' :
                      order.status === 'preparing' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {order.status}
                    </span>
                    <select
                      value={order.status}
                      onChange={(e) => updateOrderStatus(order.id, e.target.value)}
                      className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="pending">Pending</option>
                      <option value="preparing">Preparing</option>
                      <option value="ready">Ready</option>
                      <option value="delivered">Delivered</option>
                    </select>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Kitchen Staff Dashboard
const KitchenStaffDashboard = ({ user }) => {
  const [productionItems, setProductionItems] = useState([]);

  useEffect(() => {
    fetchProductionItems();
  }, []);

  const fetchProductionItems = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await axios.get(`${API}/production-items?production_date=${today}`);
      setProductionItems(response.data);
    } catch (error) {
      console.error('Error fetching production items:', error);
    }
  };

  const updateItemStatus = async (itemId, status) => {
    try {
      await axios.put(`${API}/production-items/${itemId}/status?status=${status}`);
      fetchProductionItems();
    } catch (error) {
      console.error('Error updating item status:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-xl font-semibold text-gray-800">Kitchen Production</h1>
            <span className="text-gray-600">Welcome, {user.name}</span>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="bg-white rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-800 p-4 border-b">Today's Production Items</h3>
          <div className="space-y-4 p-4">
            {productionItems.map(item => (
              <div key={item.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="text-lg font-semibold text-gray-800">{item.name}</h4>
                    <p className="text-gray-600">Quantity: {item.quantity}</p>
                    <p className="text-gray-600">Target Time: {item.target_time}</p>
                  </div>
                  <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${
                    item.status === 'completed' ? 'bg-green-100 text-green-800' :
                    item.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {item.status.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex space-x-3">
                  {item.status === 'pending' && (
                    <button
                      onClick={() => updateItemStatus(item.id, 'in_progress')}
                      className="bg-yellow-600 text-white px-4 py-2 rounded-md hover:bg-yellow-700 transition-colors"
                    >
                      Start Production
                    </button>
                  )}
                  {item.status === 'in_progress' && (
                    <button
                      onClick={() => updateItemStatus(item.id, 'completed')}
                      className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
                    >
                      Mark Complete
                    </button>
                  )}
                  {item.status === 'completed' && (
                    <span className="text-green-600 font-medium">✓ Completed</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Venue Staff Dashboard
const VenueStaffDashboard = ({ user }) => {
  const [completedItems, setCompletedItems] = useState([]);
  const [cart, setCart] = useState([]);
  const [orders, setOrders] = useState([]);
  const [activeTab, setActiveTab] = useState('order');

  useEffect(() => {
    fetchCompletedItems();
    fetchOrders();
  }, []);

  const fetchCompletedItems = async () => {
    try {
      const response = await axios.get(`${API}/production-items/completed`);
      setCompletedItems(response.data);
    } catch (error) {
      console.error('Error fetching completed items:', error);
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders?venue_name=${user.name}`);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const addToCart = (item) => {
    const existingItem = cart.find(cartItem => cartItem.id === item.id);
    if (existingItem) {
      setCart(cart.map(cartItem => 
        cartItem.id === item.id 
          ? {...cartItem, orderQuantity: cartItem.orderQuantity + 1}
          : cartItem
      ));
    } else {
      setCart([...cart, {...item, orderQuantity: 1}]);
    }
  };

  const updateCartQuantity = (itemId, quantity) => {
    if (quantity === 0) {
      setCart(cart.filter(item => item.id !== itemId));
    } else {
      setCart(cart.map(item => 
        item.id === itemId ? {...item, orderQuantity: quantity} : item
      ));
    }
  };

  const placeOrder = async () => {
    if (cart.length === 0) return;

    try {
      const orderItems = cart.map(item => ({
        production_item_id: item.id,
        production_item_name: item.name,
        quantity: item.orderQuantity,
        unit_cost: item.cost || 10 // Default cost if not set
      }));

      await axios.post(`${API}/orders`, {
        venue_name: user.name,
        items: orderItems
      });

      setCart([]);
      fetchOrders();
      alert('Order placed successfully!');
    } catch (error) {
      console.error('Error placing order:', error);
      alert('Error placing order');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-xl font-semibold text-gray-800">Venue Dashboard</h1>
            <span className="text-gray-600">Welcome, {user.name}</span>
          </div>
          <div className="flex space-x-6">
            {['order', 'cart', 'orders'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-2 px-4 border-b-2 ${activeTab === tab ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)} {tab === 'cart' && cart.length > 0 && `(${cart.length})`}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'order' && (
          <div className="bg-white rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-800 p-4 border-b">Available Items</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
              {completedItems.map(item => (
                <div key={item.id} className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-800 mb-2">{item.name}</h4>
                  <p className="text-gray-600 mb-2">Available: {item.quantity}</p>
                  <p className="text-gray-600 mb-3">Cost: ${item.cost ? (item.cost * 1.15).toFixed(2) : '11.50'} (with 15% markup)</p>
                  <button
                    onClick={() => addToCart(item)}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Add to Cart
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'cart' && (
          <div className="bg-white rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-800 p-4 border-b">Shopping Cart</h3>
            <div className="p-4">
              {cart.length === 0 ? (
                <p className="text-gray-600">Your cart is empty</p>
              ) : (
                <div className="space-y-4">
                  {cart.map(item => (
                    <div key={item.id} className="flex justify-between items-center border-b pb-4">
                      <div>
                        <h4 className="font-semibold text-gray-800">{item.name}</h4>
                        <p className="text-gray-600">Cost: ${item.cost ? (item.cost * 1.15).toFixed(2) : '11.50'}</p>
                      </div>
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={() => updateCartQuantity(item.id, item.orderQuantity - 1)}
                          className="bg-gray-200 text-gray-700 px-2 py-1 rounded"
                        >
                          -
                        </button>
                        <span className="font-medium">{item.orderQuantity}</span>
                        <button
                          onClick={() => updateCartQuantity(item.id, item.orderQuantity + 1)}
                          className="bg-gray-200 text-gray-700 px-2 py-1 rounded"
                        >
                          +
                        </button>
                      </div>
                    </div>
                  ))}
                  <div className="pt-4">
                    <div className="text-right mb-4">
                      <p className="text-lg font-semibold">
                        Total: ${cart.reduce((total, item) => 
                          total + (item.cost ? item.cost * 1.15 : 11.50) * item.orderQuantity, 0
                        ).toFixed(2)}
                      </p>
                    </div>
                    <button
                      onClick={placeOrder}
                      className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 transition-colors"
                    >
                      Place Order
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'orders' && (
          <div className="bg-white rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-800 p-4 border-b">My Orders</h3>
            <div className="space-y-4 p-4">
              {orders.map(order => (
                <div key={order.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <p className="text-sm text-gray-600">Order Date: {new Date(order.order_date).toLocaleDateString()}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-semibold text-gray-800">${order.final_cost.toFixed(2)}</p>
                    </div>
                  </div>
                  <div className="mb-3">
                    <h5 className="font-medium text-gray-700 mb-2">Items:</h5>
                    {order.items.map((item, index) => (
                      <div key={index} className="text-sm text-gray-600">
                        {item.production_item_name} - Qty: {item.quantity}
                      </div>
                    ))}
                  </div>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    order.status === 'delivered' ? 'bg-green-100 text-green-800' :
                    order.status === 'ready' ? 'bg-blue-100 text-blue-800' :
                    order.status === 'preparing' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {order.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [currentUser, setCurrentUser] = useState(null);

  const handleLogin = (user) => {
    setCurrentUser(user);
  };

  const handleLogout = () => {
    setCurrentUser(null);
  };

  if (!currentUser) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="App">
      <div className="absolute top-4 right-4">
        <button 
          onClick={handleLogout}
          className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors"
        >
          Logout
        </button>
      </div>
      
      {currentUser.role === 'manager' && <ManagerDashboard user={currentUser} />}
      {currentUser.role === 'kitchen_staff' && <KitchenStaffDashboard user={currentUser} />}
      {currentUser.role === 'venue_staff' && <VenueStaffDashboard user={currentUser} />}
    </div>
  );
}

export default App;