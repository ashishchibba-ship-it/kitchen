import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

// HYBRID MODE - Database authentication with frontend data loading
// Use the correct deployed backend URL
const API = '/api';

console.log('Street Eats Planner App - DATABASE AUTHENTICATION MODE');
console.log('API URL:', API);

// Utility function to convert file to base64
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = error => reject(error);
  });
};

// Image Upload Component
const ImageUpload = ({ onImageSelect, currentImage }) => {
  const [preview, setPreview] = useState(currentImage);

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (file) {
      try {
        const base64 = await fileToBase64(file);
        setPreview(base64);
        onImageSelect(base64);
      } catch (error) {
        console.error('Error converting file to base64:', error);
      }
    }
  };

  return (
    <div className="image-upload">
      <input
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
        className="hidden"
        id="image-upload"
      />
      <label
        htmlFor="image-upload"
        className="cursor-pointer block w-full p-3 border-2 border-dashed border-gray-300 rounded-md text-center hover:border-blue-500 transition-colors"
      >
        {preview ? (
          <div className="space-y-2">
            <img src={preview} alt="Preview" className="w-full h-32 object-cover rounded" />
            <p className="text-sm text-gray-600">Click to change image</p>
          </div>
        ) : (
          <div className="space-y-2">
            <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
              <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <p className="text-sm text-gray-600">Click to upload image</p>
          </div>
        )}
      </label>
    </div>
  );
};

// Login Component
const Login = ({ onLogin, appSettings }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [users, setUsers] = useState([]);

  // Load users from database on component mount
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        console.log('Fetching users for login dropdown from:', `${API}/users`);
        const response = await axios.get(`${API}/users`);
        console.log('Users loaded for login:', response.data.length, 'users');
        setUsers(response.data);
      } catch (error) {
        console.error('Error fetching users for login:', error);
        // No fallback needed - if API fails, user will see empty dropdown
        setUsers([]);
      }
    };
    fetchUsers();
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      console.log('Attempting login for:', username);
      
      // First get the user from the database to check real password
      const userResponse = await axios.get(`${API}/users`);
      const users = userResponse.data;
      
      // Find user by username
      const foundUser = users.find(u => u.username === username);
      
      if (!foundUser) {
        setError('User not found');
        setIsLoading(false);
        return;
      }
      
      // Check the actual password from database
      if (foundUser.password !== password) {
        setError('Invalid password');
        setIsLoading(false);
        return;
      }
      
      // Login successful with real database password
      console.log('Login successful for:', foundUser.name);
      onLogin(foundUser);
      
    } catch (error) {
      console.error('Login error:', error);
      setError('Login failed. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const containerStyle = {
    backgroundColor: appSettings?.secondary_color || '#1f2937',
    fontFamily: appSettings?.font_family || 'Inter'
  };

  const primaryButtonStyle = {
    backgroundColor: appSettings?.primary_color || '#3b82f6'
  };

  return (
    <div className="min-h-screen flex items-center justify-center" style={containerStyle}>
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full m-4" style={{ fontFamily: appSettings?.font_family }}>
        <div className="text-center mb-6">
          {appSettings?.logo_url && (
            <img src={appSettings.logo_url} alt="Logo" className="mx-auto h-16 w-16 mb-4" />
          )}
          <h2 className="text-2xl font-bold text-gray-800" style={{ fontFamily: appSettings?.font_family }}>
            {appSettings?.app_name || 'Street Eats Planner'} Login
          </h2>
        </div>
        
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select User
            </label>
            <select
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              disabled={isLoading}
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
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              disabled={isLoading}
            />
          </div>

          {error && (
            <div className="text-red-600 text-sm bg-red-50 p-3 rounded-md">
              {error}
            </div>
          )}

          <button 
            type="submit"
            disabled={isLoading || !username || !password}
            className="w-full text-white py-3 px-4 rounded-md hover:opacity-90 disabled:bg-gray-400 transition-colors"
            style={primaryButtonStyle}
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
};

// Manager Dashboard
const ManagerDashboard = ({ user, appSettings }) => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [productionItems, setProductionItems] = useState([]);
  const [orders, setOrders] = useState([]);
  const [archivedOrders, setArchivedOrders] = useState([]);
  const [users, setUsers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [detailedCategories, setDetailedCategories] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [settings, setSettings] = useState(appSettings || {});
  const [notificationPreferences, setNotificationPreferences] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [localNotificationPreferences, setLocalNotificationPreferences] = useState([]);
  const [localProductionItems, setLocalProductionItems] = useState([]);
  const [localUsers, setLocalUsers] = useState([]);
  const [localSettings, setLocalSettings] = useState({});
  const [passwordVisibility, setPasswordVisibility] = useState({});
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [pendingChanges, setPendingChanges] = useState({
    productionItems: [],
    users: [],
    notifications: [],
    settings: false
  });

  const [newItem, setNewItem] = useState({
    name: '',
    category: '',
    unit_of_measure: 'kg',
    assigned_staff: '',
    image: null,
    base_cost: 10.0
  });
  const [editingItem, setEditingItem] = useState(null);

  const [newUser, setNewUser] = useState({
    name: '',
    username: '',
    password: '',
    role: 'kitchen_staff',
    address: ''
  });

  const [newCategory, setNewCategory] = useState({
    name: '',
    description: ''
  });

  const [editingUser, setEditingUser] = useState(null);
  const [editingCategory, setEditingCategory] = useState(null);

  useEffect(() => {
    fetchStats();
    fetchProductionItems();
    fetchOrders();
    fetchArchivedOrders();
    fetchUsers();
    fetchCategories();
    fetchDetailedCategories();
    fetchInvoices();
    fetchPurchaseOrders();
    fetchNotificationPreferences();
    
    // Poll for dashboard stats every 30 seconds for real-time notifications
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleArchiveOrder = async (orderId) => {
    try {
      await axios.put(`${API}/orders/${orderId}/archive`);
      alert('Order archived successfully!');
      fetchOrders(); // Refresh active orders
      fetchArchivedOrders(); // Refresh archived orders
    } catch (error) {
      console.error('Error archiving order:', error);
      alert('Error archiving order.');
    }
  };

  const handleUnarchiveOrder = async (orderId) => {
    try {
      await axios.put(`${API}/orders/${orderId}/unarchive`);
      alert('Order unarchived successfully!');
      fetchOrders(); // Refresh active orders
      fetchArchivedOrders(); // Refresh archived orders
    } catch (error) {
      console.error('Error unarchiving order:', error);
      alert('Error unarchiving order.');
    }
  };

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
      console.log('Fetching production items from:', `${API}/production-items`);
      const response = await axios.get(`${API}/production-items`, {
        timeout: 10000,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
      console.log('Production items loaded:', response.data.length, 'items');
      console.log('First item:', response.data[0]);
      setProductionItems(response.data);
      setLocalProductionItems(response.data); // Initialize local state
    } catch (error) {
      console.error('Error fetching production items:', error.message);
      console.error('Error details:', error.response?.status, error.response?.data);
      
      // Fallback: show mock data so user can see the interface
      const mockData = [
        {
          id: 'mock1',
          name: 'Demo Item (Backend Connection Failed)',
          category: 'Main Course',
          unit_of_measure: 'portions',
          base_cost: 15.0,
          unit_price: 17.25,
          availability: true
        }
      ];
      setProductionItems(mockData);
      setLocalProductionItems(mockData);
    }
  };

  const fetchOrders = async () => {
    try {
      console.log('Fetching active orders from:', `${API}/orders/active`);
      const response = await axios.get(`${API}/orders/active`);
      console.log('Active orders loaded:', response.data.length, 'orders');
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching active orders:', error);
    }
  };

  const fetchArchivedOrders = async () => {
    try {
      console.log('Fetching archived orders from:', `${API}/orders/archived`);
      const response = await axios.get(`${API}/orders/archived`);
      console.log('Archived orders loaded:', response.data.length, 'orders');
      setArchivedOrders(response.data);
    } catch (error) {
      console.error('Error fetching archived orders:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
      setLocalUsers(response.data); // Initialize local state
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      console.log('Fetching categories from:', `${API}/categories`);
      const response = await axios.get(`${API}/categories`);
      console.log('Categories response:', response.data);
      if (response.data.categories) {
        setCategories(response.data.categories);
        console.log('Categories loaded:', response.data.categories.length, 'categories');
      } else {
        console.error('No categories property in response');
      }
    } catch (error) {
      console.error('Error fetching categories:', error.message);
      console.error('Error details:', error.response?.status, error.response?.data);
      
      // Fallback to basic categories so user can work
      const basicCategories = ['Main Course', 'Appetizer', 'Dessert', 'Beverage', 'Side Dish', 'Salad'];
      setCategories(basicCategories);
      console.log('Using fallback categories:', basicCategories);
    }
  };

  const fetchDetailedCategories = async () => {
    try {
      const response = await axios.get(`${API}/categories/detailed`);
      setDetailedCategories(response.data);
    } catch (error) {
      console.error('Error fetching detailed categories:', error);
    }
  };

  const fetchInvoices = async () => {
    try {
      const response = await axios.get(`${API}/invoices`);
      setInvoices(response.data);
    } catch (error) {
      console.error('Error fetching invoices:', error);
    }
  };

  const fetchPurchaseOrders = async () => {
    try {
      const response = await axios.get(`${API}/purchase-orders`);
      setPurchaseOrders(response.data);
    } catch (error) {
      console.error('Error fetching purchase orders:', error);
    }
  };

  const fetchNotificationPreferences = async () => {
    try {
      const response = await axios.get(`${API}/notification-preferences`);
      setNotificationPreferences(response.data);
      setLocalNotificationPreferences(response.data); // Initialize local state
    } catch (error) {
      console.error('Error fetching notification preferences:', error);
    }
  };

  const markChangesUnsaved = (changeType, itemId = null) => {
    setHasUnsavedChanges(true);
    setPendingChanges(prev => {
      const newChanges = { ...prev };
      if (itemId && !newChanges[changeType].includes(itemId)) {
        newChanges[changeType] = [...newChanges[changeType], itemId];
      } else if (!itemId && changeType === 'settings') {
        newChanges.settings = true;
      }
      return newChanges;
    });
  };

  // Local state update functions
  const updateLocalProductionItem = (itemId, updates) => {
    setLocalProductionItems(prev => 
      prev.map(item => item.id === itemId ? { ...item, ...updates } : item)
    );
    markChangesUnsaved('productionItems', itemId);
  };

  const addLocalProductionItem = (newItem) => {
    const itemWithId = { ...newItem, id: `temp_${Date.now()}` };
    setLocalProductionItems(prev => [...prev, itemWithId]);
    markChangesUnsaved('productionItems', itemWithId.id);
    return itemWithId;
  };

  const removeLocalProductionItem = (itemId) => {
    setLocalProductionItems(prev => prev.filter(item => item.id !== itemId));
    markChangesUnsaved('productionItems', itemId);
  };

  const updateLocalUser = (userId, updates) => {
    setLocalUsers(prev => 
      prev.map(user => user.id === userId ? { ...user, ...updates } : user)
    );
    markChangesUnsaved('users', userId);
  };

  const addLocalUser = (newUser) => {
    const userWithId = { ...newUser, id: `temp_${Date.now()}` };
    setLocalUsers(prev => [...prev, userWithId]);
    markChangesUnsaved('users', userWithId.id);
    return userWithId;
  };

  const removeLocalUser = (userId) => {
    setLocalUsers(prev => prev.filter(user => user.id !== userId));
    markChangesUnsaved('users', userId);
  };

  const updateLocalSettings = (updates) => {
    setLocalSettings(prev => ({ ...prev, ...updates }));
    markChangesUnsaved('settings');
  };

  const updateUserPassword = async (userId, newPassword) => {
    try {
      await axios.put(`${API}/users/${userId}/password`, { password: newPassword });
      alert('Password updated successfully!');
    } catch (error) {
      console.error('Error updating password:', error);
      alert('Error updating password. Please try again.');
    }
  };

  const togglePasswordVisibility = (userId) => {
    setPasswordVisibility(prev => ({
      ...prev,
      [userId]: !prev[userId]
    }));
  };

  const updateLocalNotificationPreferences = (userId, preferences) => {
    setLocalNotificationPreferences(prevLocal => 
      prevLocal.map(pref => 
        pref.user_id === userId ? { ...pref, ...preferences } : pref
      )
    );
    markChangesUnsaved('notifications', userId);
  };

  const updateUserNotificationPreferences = async (userId, preferences) => {
    try {
      // Update local state first
      updateLocalNotificationPreferences(userId, preferences);
      
      // Save to backend
      await axios.put(`${API}/notification-preferences/${userId}`, preferences);
      
      // Update the main state
      setNotificationPreferences(prev => 
        prev.map(pref => 
          pref.user_id === userId ? { ...pref, ...preferences } : pref
        )
      );
      
      alert('Email notification preferences saved successfully!');
    } catch (error) {
      console.error('Error saving notification preferences:', error);
      alert('Error saving notification preferences. Please try again.');
    }
  };

  const saveAllChanges = async () => {
    setIsSaving(true);
    let successCount = 0;
    let errorCount = 0;
    const errors = [];

    try {
      // Save Production Items
      if (pendingChanges.productionItems.length > 0) {
        console.log('Saving production items:', pendingChanges.productionItems);
        for (const itemId of pendingChanges.productionItems) {
          try {
            const localItem = localProductionItems.find(item => item.id === itemId);
            if (!localItem) {
              console.log(`Skipping missing item: ${itemId}`);
              continue;
            }

            if (itemId.startsWith('temp_')) {
              // New item - create
              console.log('Creating new item:', localItem.name);
              const { id, unit_price, created_at, updated_at, ...itemData } = localItem;
              const response = await axios.post(`${API}/production-items?created_by=${user.username}`, itemData);
              
              // Update local state with real ID
              setLocalProductionItems(prev => 
                prev.map(item => item.id === itemId ? { ...item, id: response.data.id } : item)
              );
              console.log('Created item with ID:', response.data.id);
            } else {
              // Existing item - update
              const originalItem = productionItems.find(item => item.id === itemId);
              if (originalItem) {
                console.log('Updating existing item:', localItem.name, 'ID:', itemId);
                // Filter to only send fields expected by backend ProductionItemCreate model
                const updateData = {
                  name: localItem.name,
                  category: localItem.category,
                  unit_of_measure: localItem.unit_of_measure || 'kg',
                  assigned_staff: localItem.assigned_staff,
                  image: localItem.image,
                  base_cost: localItem.base_cost
                };
                console.log('Update data being sent:', updateData);
                const response = await axios.put(`${API}/production-items/${itemId}`, updateData);
                console.log('Update response status:', response.status);
              }
            }
            successCount++;
          } catch (error) {
            console.error(`Error saving production item ${itemId}:`, error);
            console.error('Error response:', error.response?.data);
            errors.push(`Production item: ${error.response?.data?.detail || error.message}`);
            errorCount++;
          }
        }
      }

      // Save Users
      if (pendingChanges.users.length > 0) {
        for (const userId of pendingChanges.users) {
          try {
            const localUser = localUsers.find(user => user.id === userId);
            if (!localUser) continue;

            if (userId.startsWith('temp_')) {
              // New user - create
              const { id, ...userData } = localUser;
              const response = await axios.post(`${API}/users`, userData);
              
              // Update local state with real ID
              setLocalUsers(prev => 
                prev.map(user => user.id === userId ? { ...user, id: response.data.id } : user)
              );
            } else {
              // Existing user - update
              const originalUser = users.find(user => user.id === userId);
              if (originalUser) {
                await axios.put(`${API}/users/${userId}`, localUser);
              }
            }
            successCount++;
          } catch (error) {
            console.error(`Error saving user ${userId}:`, error);
            errors.push(`User: ${error.response?.data?.detail || error.message}`);
            errorCount++;
          }
        }
      }

      // Save Notification Preferences
      if (pendingChanges.notifications.length > 0) {
        for (const userId of pendingChanges.notifications) {
          try {
            const localPref = localNotificationPreferences.find(pref => pref.user_id === userId);
            if (localPref) {
              await axios.put(`${API}/notification-preferences/${userId}`, localPref);
              successCount++;
            }
          } catch (error) {
            console.error(`Error saving notification preferences for ${userId}:`, error);
            errors.push(`Notifications: ${error.response?.data?.detail || error.message}`);
            errorCount++;
          }
        }
      }

      // Save Settings
      if (pendingChanges.settings) {
        try {
          await axios.put(`${API}/settings`, localSettings);
          successCount++;
        } catch (error) {
          console.error('Error saving settings:', error);
          errors.push(`Settings: ${error.response?.data?.detail || error.message}`);
          errorCount++;
        }
      }

      // Update main state with saved changes and reset pending changes
      if (successCount > 0) {
        setProductionItems([...localProductionItems]);
        setUsers([...localUsers]);
        setNotificationPreferences([...localNotificationPreferences]);
        setSettings({ ...localSettings });
        
        setHasUnsavedChanges(false);
        setPendingChanges({
          productionItems: [],
          users: [],
          notifications: [],
          settings: false
        });

        if (errorCount === 0) {
          alert(`✅ All changes saved successfully! (${successCount} items updated)`);
        } else {
          alert(`⚠️ Partially saved: ${successCount} items saved, ${errorCount} failed.\n\nErrors:\n${errors.join('\n')}`);
        }
      } else if (errorCount > 0) {
        alert(`❌ Save failed: ${errorCount} errors occurred.\n\nErrors:\n${errors.join('\n')}`);
      }

    } catch (error) {
      console.error('Error saving changes:', error);
      alert('❌ Unexpected error occurred while saving. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const discardAllChanges = () => {
    if (window.confirm('Are you sure you want to discard all unsaved changes? This cannot be undone.')) {
      // Reset all local state to original values
      setLocalProductionItems([...productionItems]);
      setLocalUsers([...users]);
      setLocalNotificationPreferences([...notificationPreferences]);
      setLocalSettings({ ...settings });
      
      setHasUnsavedChanges(false);
      setPendingChanges({
        productionItems: [],
        users: [],
        notifications: [],
        settings: false
      });
    }
  };

  const saveAllNotificationChanges = async () => {
    setIsSaving(true);
    try {
      // Find all users with changes and save them
      const savePromises = localNotificationPreferences.map(async (localPref) => {
        const originalPref = notificationPreferences.find(p => p.user_id === localPref.user_id);
        
        // Check if there are changes
        const hasChanges = !originalPref || JSON.stringify(localPref) !== JSON.stringify(originalPref);
        
        if (hasChanges) {
          await axios.put(`${API}/notification-preferences/${localPref.user_id}`, localPref);
        }
      });

      await Promise.all(savePromises);
      
      // Update the main state with saved changes
      setNotificationPreferences([...localNotificationPreferences]);
      setHasUnsavedChanges(false);
      alert('All notification preferences saved successfully!');
    } catch (error) {
      console.error('Error saving notification preferences:', error);
      alert('Error saving notification preferences. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const discardNotificationChanges = () => {
    setLocalNotificationPreferences([...notificationPreferences]);
    setHasUnsavedChanges(false);
  };

  const handleCreateItem = async (e) => {
    e.preventDefault();
    try {
      // Add to local state instead of immediately saving
      const newItemData = {
        ...newItem,
        base_cost: parseFloat(newItem.base_cost),
        unit_price: parseFloat(newItem.base_cost) * 1.15,
        created_at: new Date().toISOString()
      };
      
      addLocalProductionItem(newItemData);
      
      // Reset form
      setNewItem({
        name: '',
        category: '',
        unit_of_measure: 'kg',
        assigned_staff: '',
        image: null,
        base_cost: 10.0
      });
      
    } catch (error) {
      console.error('Error adding item to local state:', error);
      alert('Error adding production item locally.');
    }
  };

  const handleCreateCategory = async (e) => {
    e.preventDefault();
    
    if (!newCategory.name.trim()) {
      alert('Please enter a category name.');
      return;
    }

    try {
      console.log('Adding category:', newCategory.name);
      const response = await axios.post(`${API}/categories`, {
        name: newCategory.name.trim(),
        description: newCategory.description.trim() || null
      });
      console.log('Category added successfully:', response.data);
      
      // Refresh categories list
      await fetchCategories();
      setNewCategory({
        name: '',
        description: ''
      });
      alert('Category added successfully!');
    } catch (error) {
      console.error('Error adding category:', error);
      if (error.response?.status === 400 && error.response?.data?.detail?.includes('already exists')) {
        alert(`Category "${newCategory.name}" already exists. Please choose a different name.`);
      } else {
        alert('Error adding category. Please try again.');
      }
    }
  };

  const handleUpdateCategory = async (categoryId, categoryData) => {
    try {
      await axios.put(`${API}/categories/${categoryId}`, categoryData);
      setEditingCategory(null);
      fetchCategories();
      fetchDetailedCategories();
    } catch (error) {
      console.error('Error updating category:', error);
      alert('Error updating category.');
    }
  };

  const handleDeleteCategory = async (categoryId) => {
    if (window.confirm('Are you sure you want to delete this category?')) {
      try {
        await axios.delete(`${API}/categories/${categoryId}`);
        fetchCategories();
        fetchDetailedCategories();
      } catch (error) {
        console.error('Error deleting category:', error);
        if (error.response?.status === 400) {
          alert('Cannot delete category that is being used by production items.');
        } else {
          alert('Error deleting category.');
        }
      }
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      // Add to local state instead of immediately saving
      addLocalUser(newUser);
      
      // Reset form
      setNewUser({
        name: '',
        username: '',
        password: '',
        role: 'kitchen_staff',
        address: ''
      });
    } catch (error) {
      console.error('Error adding user to local state:', error);
      alert('Error adding user locally.');
    }
  };

  const handleUpdateUser = async (userId, userData) => {
    try {
      await axios.put(`${API}/users/${userId}`, userData);
      setEditingUser(null);
      fetchUsers();
    } catch (error) {
      console.error('Error updating user:', error);
      alert('Error updating user.');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await axios.delete(`${API}/users/${userId}`);
        fetchUsers();
      } catch (error) {
        console.error('Error deleting user:', error);
        alert('Error deleting user.');
      }
    }
  };

  const handleDeleteProductionItem = async (itemId, itemName, forceDelete = false) => {
    const confirmMessage = forceDelete 
      ? `Are you sure you want to FORCE DELETE "${itemName}"? This will remove it from all orders and cannot be undone.`
      : `Are you sure you want to delete "${itemName}"?`;
    
    if (window.confirm(confirmMessage)) {
      try {
        const url = `${API}/production-items/${itemId}${forceDelete ? '?force=true' : ''}`;
        await axios.delete(url);
        fetchProductionItems();
        alert(forceDelete ? 'Item force deleted successfully!' : 'Item deleted successfully!');
      } catch (error) {
        console.error('Error deleting production item:', error);
        if (error.response?.status === 400) {
          // Show force delete option
          const forceConfirm = window.confirm(
            `${error.response.data.detail}\n\nWould you like to FORCE DELETE this item? This will remove it from all orders and cannot be undone.`
          );
          if (forceConfirm) {
            handleDeleteProductionItem(itemId, itemName, true);
          }
        } else {
          alert('Error deleting production item.');
        }
      }
    }
  };

  const handleEditProductionItem = async (itemId, updatedData) => {
    try {
      await axios.put(`${API}/production-items/${itemId}`, updatedData);
      fetchProductionItems();
      setEditingItem(null);
    } catch (error) {
      console.error('Error updating production item:', error);
      alert('Error updating production item.');
    }
  };

  const exportInvoicePDF = async (invoiceId, invoiceNumber) => {
    try {
      const response = await axios.get(`${API}/invoices/${invoiceId}/pdf`, {
        responseType: 'blob'
      });
      
      // Create download link
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `invoice_${invoiceNumber}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting PDF:', error);
      alert('Error exporting PDF. Please try again.');
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

  const updateDeliveryDate = async (orderId, deliveryDate) => {
    try {
      await axios.put(`${API}/orders/${orderId}/delivery-date`, deliveryDate, {
        headers: { 'Content-Type': 'application/json' }
      });
      fetchOrders();
    } catch (error) {
      console.error('Error updating delivery date:', error);
    }
  };

  const updateItemAvailability = async (itemId, availableForOrder, baseCost, unitOfMeasure = null) => {
    try {
      const updateData = {
        available_for_order: parseInt(availableForOrder),
        base_cost: parseFloat(baseCost)
      };
      
      if (unitOfMeasure !== null) {
        updateData.unit_of_measure = unitOfMeasure;
      }
      
      await axios.put(`${API}/production-items/${itemId}/availability`, updateData);
      fetchProductionItems();
    } catch (error) {
      console.error('Error updating item availability:', error);
    }
  };

  const updateAppSettings = async (newSettings) => {
    try {
      const response = await axios.put(`${API}/settings`, newSettings);
      setSettings(response.data);
      window.location.reload(); // Refresh to apply new styles
    } catch (error) {
      console.error('Error updating settings:', error);
    }
  };

  const containerStyle = {
    backgroundColor: settings?.secondary_color || '#f9fafb',
    fontFamily: settings?.font_family || 'Inter'
  };

  const primaryButtonStyle = {
    backgroundColor: settings?.primary_color || '#3b82f6'
  };

  const accentStyle = {
    color: settings?.accent_color || '#10b981'
  };

  return (
    <div className="min-h-screen" style={containerStyle}>
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-xl font-semibold text-gray-800" style={{ fontFamily: settings?.font_family }}>
              {settings?.app_name || 'Street Eats Planner'} - Manager Dashboard
            </h1>
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Welcome, {user.name}</span>
              
              {hasUnsavedChanges && (
                <div className="flex items-center space-x-3">
                  <div className="flex items-center text-orange-600 bg-orange-50 px-3 py-2 rounded-lg">
                    <span className="w-2 h-2 bg-orange-500 rounded-full mr-2 animate-pulse"></span>
                    <span className="text-sm font-medium">
                      {Object.values(pendingChanges).flat().length + (pendingChanges.settings ? 1 : 0)} unsaved changes
                    </span>
                  </div>
                  <button
                    onClick={discardAllChanges}
                    disabled={isSaving}
                    className="px-3 py-1 text-sm text-gray-600 bg-gray-200 rounded hover:bg-gray-300 transition-colors disabled:opacity-50"
                  >
                    Discard
                  </button>
                  <button
                    onClick={saveAllChanges}
                    disabled={isSaving}
                    className={`px-4 py-1 text-sm text-white rounded transition-colors disabled:opacity-50 ${
                      isSaving ? 'bg-green-400' : 'bg-green-600 hover:bg-green-700'
                    }`}
                  >
                    {isSaving ? 'Saving...' : 'Save All'}
                  </button>
                </div>
              )}
            </div>
          </div>
          <div className="flex space-x-6">
            {['dashboard', 'production', 'orders', 'archived-orders', 'users', 'notifications', 'categories', 'invoices', 'purchase-orders', 'settings'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-2 px-4 border-b-2 ${activeTab === tab ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                style={activeTab === tab ? { borderColor: settings?.primary_color, color: settings?.primary_color } : {}}
              >
                {tab.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'dashboard' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Today's Production</h3>
              <div className="text-3xl font-bold text-blue-600">{stats?.production?.total_items_today || 0}</div>
              <p className="text-sm text-gray-600">
                {stats?.production?.completed_items_today || 0} completed ({(stats?.production?.completion_rate || 0).toFixed(1)}%)
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Orders Today</h3>
              <div className="text-3xl font-bold text-green-600">{stats?.orders?.total_orders_today || 0}</div>
              <p className="text-sm text-gray-600">{stats?.orders?.pending_orders || 0} pending</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Daily Revenue</h3>
              <div className="text-3xl font-bold text-purple-600">${(stats?.orders?.daily_revenue || 0).toFixed(2)}</div>
              <p className="text-sm text-gray-600">Including tax</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Pending Invoices</h3>
              <div className="text-3xl font-bold text-orange-600">{stats?.financial?.pending_invoices || 0}</div>
              <p className="text-sm text-gray-600">Awaiting payment</p>
            </div>
          </div>
        )}

        {activeTab === 'dashboard' && stats?.orders?.recent_orders?.length > 0 && (
          <div className="bg-white rounded-lg shadow mb-8">
            <div className="p-4 border-b bg-yellow-50">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                <span className="bg-red-500 text-white px-2 py-1 rounded-full text-sm mr-2">
                  {stats?.orders?.recent_orders?.length}
                </span>
                New Orders - Action Required
              </h3>
            </div>
            <div className="p-4">
              <div className="space-y-3">
                {stats?.orders?.recent_orders?.map(order => (
                  <div key={order.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-800">{order.venue_name}</div>
                      <div className="text-sm text-gray-600">
                        {order.items_count} items • ${order.total_amount.toFixed(2)} • {new Date(order.order_date).toLocaleString()}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        order.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        order.status === 'preparing' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {order.status}
                      </span>
                      <button
                        onClick={() => setActiveTab('orders')}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        View Details
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'production' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Add Production Item</h3>
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
                <p className="text-sm text-blue-800">
                  <strong>Required Fields:</strong> Item Name, Category, and Base Cost are required to create a production item.
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  💡 All items use <strong>kg</strong> as the unit of measure and are always available for ordering.
                </p>
              </div>
              <form onSubmit={handleCreateItem} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Item Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      placeholder="e.g., Grilled Chicken Breast"
                      value={newItem.name}
                      onChange={(e) => setNewItem({...newItem, name: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                    {!newItem.name && <p className="text-xs text-red-500 mt-1">Item name is required</p>}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Category <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={newItem.category}
                      onChange={(e) => setNewItem({...newItem, category: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      <option value="">Select Category</option>
                      {categories.map(category => (
                        <option key={category} value={category}>{category}</option>
                      ))}
                    </select>
                    {!newItem.category && <p className="text-xs text-red-500 mt-1">Category is required</p>}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Unit of Measure
                    </label>
                    <input
                      type="text"
                      value="kg"
                      disabled
                      className="w-full p-3 border border-gray-300 rounded-md bg-gray-100 text-gray-600"
                    />
                    <p className="text-xs text-gray-500 mt-1">All items use kilograms (kg)</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Base Cost <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="e.g., 12.50"
                      value={newItem.base_cost}
                      onChange={(e) => setNewItem({...newItem, base_cost: parseFloat(e.target.value) || ''})}
                      className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                      min="0.01"
                    />
                    {!newItem.base_cost && <p className="text-xs text-red-500 mt-1">Base cost is required</p>}
                    <p className="text-xs text-gray-500 mt-1">Selling price will be calculated with 15% markup</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Assigned Staff (Optional)
                    </label>
                    <select
                      value={newItem.assigned_staff}
                      onChange={(e) => setNewItem({...newItem, assigned_staff: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Staff (Optional)</option>
                      {users.filter(user => user.role === 'kitchen_staff').map(user => (
                        <option key={user.id} value={user.username}>{user.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Item Image (Optional)
                  </label>
                  <ImageUpload 
                    onImageSelect={(image) => setNewItem({...newItem, image})}
                    currentImage={newItem.image}
                  />
                  <p className="text-xs text-gray-500 mt-1">Upload an image to display in the ordering interface</p>
                </div>
                
                <button
                  type="submit"
                  disabled={!newItem.name || !newItem.category || !newItem.base_cost}
                  className={`w-full py-3 px-4 rounded-md transition-colors ${
                    (!newItem.name || !newItem.category || !newItem.base_cost)
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'text-white hover:opacity-90'
                  }`}
                  style={(!newItem.name || !newItem.category || !newItem.base_cost) ? {} : primaryButtonStyle}
                >
                  {(!newItem.name || !newItem.category || !newItem.base_cost) 
                    ? 'Please fill in all required fields' 
                    : 'Add Production Item'
                  }
                </button>
              </form>
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
              <h3 className="text-lg font-semibold text-gray-800 p-4 border-b">Production Items & Order Management</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Image</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unit of Measure</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Base Cost</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Selling Price</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {localProductionItems.map(item => (
                      <tr key={item.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {item.image ? (
                            <img src={item.image} alt={item.name} className="w-12 h-12 object-cover rounded" />
                          ) : (
                            <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center">
                              <span className="text-gray-500 text-xs">No img</span>
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.category}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="text"
                            value={item.unit_of_measure || 'kg'}
                            onChange={(e) => {
                              updateLocalProductionItem(item.id, { 
                                unit_of_measure: e.target.value || 'kg'
                              });
                            }}
                            className="w-20 p-1 border border-gray-300 rounded text-sm"
                            placeholder="kg"
                          />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="number"
                            value={item.available_for_order || 0}
                            max={1000}
                            min={0}
                            onChange={(e) => {
                              const newAvailable = parseInt(e.target.value) || 0;
                              updateLocalProductionItem(item.id, { 
                                available_for_order: newAvailable
                              });
                            }}
                            className="w-20 p-1 border border-gray-300 rounded text-sm"
                          />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="number"
                            step="0.01"
                            value={item.base_cost || 10.0}
                            onChange={(e) => {
                              const newBaseCost = parseFloat(e.target.value) || 10.0;
                              updateLocalProductionItem(item.id, { 
                                base_cost: newBaseCost,
                                unit_price: newBaseCost * 1.15 
                              });
                            }}
                            className="w-20 p-1 border border-gray-300 rounded text-sm"
                          />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className="font-medium text-green-600">
                            ${((item.base_cost || 10.0) * 1.15).toFixed(2)}
                          </span>
                          <br />
                          <span className="text-xs text-gray-400">(+15%)</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                            Available
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => setEditingItem(item)}
                            className="text-blue-600 hover:text-blue-900 transition-colors mr-3"
                            title="Edit production item"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteProductionItem(item.id, item.name)}
                            className="text-red-600 hover:text-red-900 transition-colors"
                            title="Delete production item"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

          {editingItem && (
            <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white p-6 rounded-lg shadow-lg max-w-2xl w-full m-4">
                <h3 className="text-lg font-semibold mb-4">Edit Production Item</h3>
                <form onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.target);
                  const updatedData = {
                    name: formData.get('name'),
                    category: formData.get('category'),
                    unit_of_measure: 'kg',
                    assigned_staff: formData.get('assigned_staff'),
                    base_cost: parseFloat(formData.get('base_cost')),
                    image: editingItem.image // Keep existing image for now
                  };
                  handleEditProductionItem(editingItem.id, updatedData);
                }} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input
                      name="name"
                      type="text"
                      placeholder="Item Name"
                      defaultValue={editingItem.name}
                      className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                    <select
                      name="category"
                      defaultValue={editingItem.category}
                      className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      <option value="">Select Category</option>
                      {categories.map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                    <input
                      name="unit_of_measure"
                      type="text" 
                      value="kg"
                      disabled
                      className="p-3 border border-gray-300 rounded-md bg-gray-100 text-gray-600"
                    />
                    <input
                      name="base_cost"
                      type="number"
                      step="0.01"
                      placeholder="Base Cost"
                      defaultValue={editingItem.base_cost}
                      className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                    <select
                      name="assigned_staff"
                      defaultValue={editingItem.assigned_staff}
                      className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Staff (Optional)</option>
                      {users.filter(user => user.role === 'kitchen_staff').map(user => (
                        <option key={user.id} value={user.username}>{user.name}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="flex space-x-3">
                    <button
                      type="submit"
                      className="flex-1 text-white py-3 px-4 rounded-md hover:opacity-90 transition-colors"
                      style={primaryButtonStyle}
                    >
                      Update Item
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingItem(null)}
                      className="flex-1 bg-gray-300 text-gray-700 py-3 px-4 rounded-md hover:bg-gray-400 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
          </div>
        )}

        {activeTab === 'users' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Add New User</h3>
              <form onSubmit={handleCreateUser} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <input
                  type="text"
                  placeholder="Full Name"
                  value={newUser.name}
                  onChange={(e) => setNewUser({...newUser, name: e.target.value})}
                  className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
                <input
                  type="text"
                  placeholder="Username"
                  value={newUser.username}
                  onChange={(e) => setNewUser({...newUser, username: e.target.value})}
                  className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
                <input
                  type="password"
                  placeholder="Password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                  className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                  className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="kitchen_staff">Kitchen Staff</option>
                  <option value="venue_staff">Venue Staff</option>
                  <option value="manager">Manager</option>
                </select>
                <input
                  type="text"
                  placeholder="Address (for venues)"
                  value={newUser.address}
                  onChange={(e) => setNewUser({...newUser, address: e.target.value})}
                  className="md:col-span-2 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  className="md:col-span-3 text-white py-3 px-4 rounded-md hover:opacity-90 transition-colors"
                  style={primaryButtonStyle}
                >
                  Add User
                </button>
              </form>
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
              <h3 className="text-lg font-semibold text-gray-800 p-4 border-b">Manage Users</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Username</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Address</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {users.map(userItem => (
                      <tr key={userItem.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{userItem.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{userItem.username}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{userItem.role}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{userItem.address || 'N/A'}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                          <button
                            onClick={() => setEditingUser(userItem)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteUser(userItem.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {editingUser && (
              <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center">
                <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
                  <h3 className="text-lg font-semibold mb-4">Edit User</h3>
                  <form onSubmit={(e) => {
                    e.preventDefault();
                    handleUpdateUser(editingUser.id, {
                      name: e.target.name.value,
                      username: e.target.username.value,
                      address: e.target.address.value
                    });
                  }} className="space-y-4">
                    <input
                      name="name"
                      type="text"
                      placeholder="Full Name"
                      defaultValue={editingUser.name}
                      className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                    <input
                      name="username"
                      type="text"
                      placeholder="Username"
                      defaultValue={editingUser.username}
                      className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                    <input
                      name="address"
                      type="text"
                      placeholder="Address"
                      defaultValue={editingUser.address || ''}
                      className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="flex space-x-3">
                      <button
                        type="submit"
                        className="flex-1 text-white py-2 px-4 rounded-md hover:opacity-90 transition-colors"
                        style={primaryButtonStyle}
                      >
                        Save
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingUser(null)}
                        className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'notifications' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-800">Notification Management</h3>
                <div className="text-sm text-gray-600">
                  Configure notification preferences for all users
                </div>
              </div>
              
              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-semibold text-blue-800 mb-2">📱 Notification System Status</h4>
                <p className="text-sm text-blue-700 mb-2">
                  <strong>✅ Active Features:</strong> In-app notifications, email & phone contact management
                </p>
                <p className="text-xs text-blue-600">
                  💡 <strong>Ready for Integration:</strong> Contact information is saved and ready for email/SMS service integration when needed.
                </p>
              </div>

              <div className="space-y-4">
                <div className="grid gap-4">
                  {localNotificationPreferences.map(pref => (
                    <div key={pref.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-medium text-gray-800">{pref.user_name}</h4>
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            pref.user_role === 'manager' ? 'bg-purple-100 text-purple-800' :
                            pref.user_role === 'kitchen_staff' ? 'bg-green-100 text-green-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {pref.user_role.replace('_', ' ')}
                          </span>
                        </div>
                        <div className="text-sm text-gray-500">
                          Last updated: {new Date(pref.updated_at).toLocaleDateString()}
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Notification Types */}
                        <div>
                          <h5 className="text-sm font-medium text-gray-700 mb-2">📋 Order Notifications</h5>
                          <div className="space-y-2">
                            <label className="flex items-center">
                              <input
                                type="checkbox"
                                checked={pref.order_placed}
                                onChange={(e) => updateLocalNotificationPreferences(pref.user_id, {
                                  ...pref,
                                  order_placed: e.target.checked
                                })}
                                className="mr-2"
                              />
                              <span className="text-sm">🔔 When food is ordered</span>
                            </label>
                            <label className="flex items-center">
                              <input
                                type="checkbox"
                                checked={pref.order_preparing}
                                onChange={(e) => updateLocalNotificationPreferences(pref.user_id, {
                                  ...pref,
                                  order_preparing: e.target.checked
                                })}
                                className="mr-2"
                              />
                              <span className="text-sm">👨‍🍳 When order is being prepared</span>
                            </label>
                            <label className="flex items-center">
                              <input
                                type="checkbox"
                                checked={pref.order_ready}
                                onChange={(e) => updateLocalNotificationPreferences(pref.user_id, {
                                  ...pref,
                                  order_ready: e.target.checked
                                })}
                                className="mr-2"
                              />
                              <span className="text-sm">✅ When order is ready for delivery</span>
                            </label>
                            <label className="flex items-center">
                              <input
                                type="checkbox"
                                checked={pref.order_delivered}
                                onChange={(e) => updateLocalNotificationPreferences(pref.user_id, {
                                  ...pref,
                                  order_delivered: e.target.checked
                                })}
                                className="mr-2"
                              />
                              <span className="text-sm">🚚 When order is delivered</span>
                            </label>
                          </div>
                        </div>

                        {/* Contact Methods (Future Features) */}
                        <div>
                          <h5 className="text-sm font-medium text-gray-700 mb-2">📞 Contact Methods</h5>
                          <div className="space-y-3">
                            <div>
                              <label className="block text-xs text-gray-600 mb-1">Email Address</label>
                              <input
                                type="email"
                                placeholder="user@example.com"
                                value={pref.email || ''}
                                onChange={(e) => updateLocalNotificationPreferences(pref.user_id, {
                                  ...pref,
                                  email: e.target.value
                                })}
                                className="w-full text-xs p-2 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                              />
                            </div>
                            <div>
                              <label className="block text-xs text-gray-600 mb-1">Phone Number</label>
                              <input
                                type="tel"
                                placeholder="+1 (555) 123-4567"
                                value={pref.phone || ''}
                                onChange={(e) => updateLocalNotificationPreferences(pref.user_id, {
                                  ...pref,
                                  phone: e.target.value
                                })}
                                className="w-full text-xs p-2 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                              />
                            </div>
                            <div className="space-y-1">
                              <label className="flex items-center text-xs text-gray-600">
                                <input
                                  type="checkbox"
                                  checked={pref.notify_email}
                                  onChange={(e) => updateLocalNotificationPreferences(pref.user_id, {
                                    ...pref,
                                    notify_email: e.target.checked
                                  })}
                                  className="mr-2"
                                />
                                📧 Email notifications (Ready for future integration)
                              </label>
                              <label className="flex items-center text-xs text-gray-600">
                                <input
                                  type="checkbox"
                                  checked={pref.notify_sms}
                                  onChange={(e) => updateLocalNotificationPreferences(pref.user_id, {
                                    ...pref,
                                    notify_sms: e.target.checked
                                  })}
                                  className="mr-2"
                                />
                                📱 SMS notifications (Ready for future integration)
                              </label>
                              <label className="flex items-center text-xs">
                                <input
                                  type="checkbox"
                                  checked={pref.notify_in_app}
                                  onChange={(e) => updateLocalNotificationPreferences(pref.user_id, {
                                    ...pref,
                                    notify_in_app: e.target.checked
                                  })}
                                  className="mr-2"
                                />
                                <span className="text-green-600">💻 In-app notifications (Active)</span>
                              </label>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {notificationPreferences.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <div className="text-lg mb-2">📭</div>
                    <p>No notification preferences found.</p>
                    <p className="text-sm">Preferences will be created automatically for all users.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Email Notification Preferences */}
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="border-b pb-4 mb-6">
                <h3 className="text-lg font-semibold text-gray-800">Email Notification Preferences</h3>
                <p className="text-sm text-gray-600 mt-1">Configure email notifications for order status changes. Set email addresses for users and enable/disable email alerts.</p>
              </div>
              
              <div className="space-y-4">
                {localUsers.map(user => (
                  <div key={user.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-medium text-gray-800">{user.name}</h4>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className="text-sm text-gray-600">@{user.username}</span>
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            user.role === 'manager' ? 'bg-purple-100 text-purple-800' :
                            user.role === 'kitchen_staff' ? 'bg-green-100 text-green-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {user.role.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex flex-col space-y-3 w-80">
                        <div>
                          <label className="block text-sm text-gray-700 mb-1">Email Address</label>
                          <input
                            type="email"
                            placeholder="Enter email address"
                            className="w-full text-sm p-2 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                            id={`email-${user.id}`}
                            defaultValue=""
                          />
                        </div>
                        
                        <div className="space-y-2">
                          <label className="block text-sm text-gray-700">Notification Types</label>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <label className="flex items-center space-x-2">
                              <input
                                type="checkbox"
                                className="rounded border-gray-300 text-blue-600"
                                id={`order-placed-${user.id}`}
                                defaultChecked={true}
                              />
                              <span>Order Placed</span>
                            </label>
                            <label className="flex items-center space-x-2">
                              <input
                                type="checkbox"
                                className="rounded border-gray-300 text-blue-600"
                                id={`order-preparing-${user.id}`}
                                defaultChecked={true}
                              />
                              <span>Preparing</span>
                            </label>
                            <label className="flex items-center space-x-2">
                              <input
                                type="checkbox"
                                className="rounded border-gray-300 text-blue-600"
                                id={`order-ready-${user.id}`}
                                defaultChecked={true}
                              />
                              <span>Ready</span>
                            </label>
                            <label className="flex items-center space-x-2">
                              <input
                                type="checkbox"
                                className="rounded border-gray-300 text-blue-600"
                                id={`order-delivered-${user.id}`}
                                defaultChecked={true}
                              />
                              <span>Delivered</span>
                            </label>
                          </div>
                          
                          <label className="flex items-center space-x-2 pt-1">
                            <input
                              type="checkbox"
                              className="rounded border-gray-300 text-blue-600"
                              id={`notify-email-${user.id}`}
                              defaultChecked={false}
                            />
                            <span className="text-sm font-medium text-gray-700">Enable Email Notifications</span>
                          </label>
                        </div>
                        
                        <button
                          onClick={() => {
                            const emailInput = document.getElementById(`email-${user.id}`);
                            const emailValue = emailInput.value.trim();
                            const orderPlaced = document.getElementById(`order-placed-${user.id}`).checked;
                            const orderPreparing = document.getElementById(`order-preparing-${user.id}`).checked;
                            const orderReady = document.getElementById(`order-ready-${user.id}`).checked;
                            const orderDelivered = document.getElementById(`order-delivered-${user.id}`).checked;
                            const notifyEmail = document.getElementById(`notify-email-${user.id}`).checked;
                            
                            if (notifyEmail && !emailValue) {
                              alert('Please enter an email address to enable email notifications.');
                              return;
                            }
                            
                            if (!emailValue && !notifyEmail) {
                              alert('Please enter an email address or disable email notifications.');
                              return;
                            }
                            
                            // Update notification preferences
                            const preferences = {
                              order_placed: orderPlaced,
                              order_preparing: orderPreparing,
                              order_ready: orderReady,
                              order_delivered: orderDelivered,
                              email: emailValue || null,
                              notify_email: notifyEmail,
                              notify_in_app: true,
                              notify_sms: false
                            };
                            
                            updateUserNotificationPreferences(user.id, preferences);
                          }}
                          className="w-full px-3 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
                        >
                          Save Email Preferences
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
                
                {localUsers.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <div className="text-lg mb-2">📧</div>
                    <p>No users found.</p>
                  </div>
                )}
              </div>
              
              {/* Gmail API Status */}
              <div className="mt-6 p-4 bg-gray-50 rounded-lg border">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-800">Gmail API Status</h4>
                    <p className="text-sm text-gray-600">Check Gmail API connection for sending email notifications</p>
                  </div>
                  <div className="space-x-2">
                    <button
                      onClick={async () => {
                        try {
                          const response = await axios.get(`${API}/gmail/status`);
                          const status = response.data;
                          alert(`Gmail API Status: ${status.authorized ? 'Connected' : 'Not Connected'}\n${status.message}`);
                        } catch (error) {
                          alert('Error checking Gmail status: ' + error.message);
                        }
                      }}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                    >
                      Check Status
                    </button>
                    <button
                      onClick={async () => {
                        try {
                          const response = await axios.get(`${API}/gmail/auth-url`);
                          if (response.data.auth_url) {
                            window.open(response.data.auth_url, '_blank');
                            alert('Please authorize Gmail access in the new window, then come back and click "Check Status"');
                          }
                        } catch (error) {
                          alert('Error getting Gmail authorization URL: ' + error.message);
                        }
                      }}
                      className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
                    >
                      Setup Gmail
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'categories' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Add New Category</h3>
              <form onSubmit={handleCreateCategory} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input
                  type="text"
                  placeholder="Category Name"
                  value={newCategory.name}
                  onChange={(e) => setNewCategory({...newCategory, name: e.target.value})}
                  className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
                <input
                  type="text"
                  placeholder="Description (optional)"
                  value={newCategory.description}
                  onChange={(e) => setNewCategory({...newCategory, description: e.target.value})}
                  className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  className="text-white py-3 px-4 rounded-md hover:opacity-90 transition-colors"
                  style={primaryButtonStyle}
                >
                  Add Category
                </button>
              </form>
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
              <h3 className="text-lg font-semibold text-gray-800 p-4 border-b">Manage Categories</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {detailedCategories.map(category => (
                      <tr key={category.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{category.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{category.description || 'N/A'}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(category.created_at).toLocaleDateString()}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                          <button
                            onClick={() => setEditingCategory(category)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteCategory(category.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {editingCategory && (
              <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center">
                <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
                  <h3 className="text-lg font-semibold mb-4">Edit Category</h3>
                  <form onSubmit={(e) => {
                    e.preventDefault();
                    handleUpdateCategory(editingCategory.id, {
                      name: e.target.name.value,
                      description: e.target.description.value
                    });
                  }} className="space-y-4">
                    <input
                      name="name"
                      type="text"
                      placeholder="Category Name"
                      defaultValue={editingCategory.name}
                      className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                    <input
                      name="description"
                      type="text"
                      placeholder="Description"
                      defaultValue={editingCategory.description || ''}
                      className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="flex space-x-3">
                      <button
                        type="submit"
                        className="flex-1 text-white py-2 px-4 rounded-md hover:opacity-90 transition-colors"
                        style={primaryButtonStyle}
                      >
                        Save
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingCategory(null)}
                        className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}
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
                      <p className="text-sm text-gray-600">Invoice: {order.invoice_number}</p>
                      <p className="text-sm text-gray-600">PO: {order.po_number}</p>
                      <p className="text-sm text-gray-600">Delivery Address: {order.delivery_address}</p>
                      <p className="text-sm text-gray-600">Order Date: {new Date(order.order_date).toLocaleDateString()}</p>
                      {order.delivery_date && (
                        <p className="text-sm text-gray-600">Delivery Date: {new Date(order.delivery_date).toLocaleDateString()}</p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-semibold text-gray-800">${order.total_amount?.toFixed(2) || '0.00'}</p>
                      <p className="text-sm text-gray-600">Total (incl. tax)</p>
                    </div>
                  </div>
                  <div className="mb-3">
                    <h5 className="font-medium text-gray-700 mb-2">Items:</h5>
                    {order.items.map((item, index) => (
                      <div key={index} className="text-sm text-gray-600">
                        {item.production_item_name} - Qty: {item.quantity} {item.unit_of_measure} @ ${item.unit_price?.toFixed(2) || '15.00'}
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-between items-center mb-3">
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
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <label className="text-sm text-gray-600">Delivery Date:</label>
                      <input
                        type="date"
                        value={order.delivery_date || ''}
                        onChange={(e) => updateDeliveryDate(order.id, e.target.value)}
                        className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <button
                      onClick={() => handleArchiveOrder(order.id)}
                      className="bg-gray-500 hover:bg-gray-600 text-white px-3 py-1 rounded text-sm transition-colors"
                      title="Archive this order"
                    >
                      Archive
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'archived-orders' && (
          <div className="bg-white rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-800 p-4 border-b">Archived Orders</h3>
            <div className="space-y-4 p-4">
              {archivedOrders.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No archived orders found.</p>
              ) : (
                archivedOrders.map(order => (
                  <div key={order.id} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-semibold text-gray-800">{order.venue_name}</h4>
                        <p className="text-sm text-gray-600">Invoice: {order.invoice_number}</p>
                        <p className="text-sm text-gray-600">PO: {order.po_number}</p>
                        <p className="text-sm text-gray-600">Delivery Address: {order.delivery_address}</p>
                        <p className="text-sm text-gray-600">Order Date: {new Date(order.order_date).toLocaleDateString()}</p>
                        {order.delivery_date && (
                          <p className="text-sm text-gray-600">Delivery Date: {new Date(order.delivery_date).toLocaleDateString()}</p>
                        )}
                        {order.archived_at && (
                          <p className="text-sm text-gray-500">Archived: {new Date(order.archived_at).toLocaleDateString()}</p>
                        )}
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-semibold text-gray-800">${order.total_amount?.toFixed(2) || '0.00'}</p>
                        <p className="text-sm text-gray-600">Total (incl. tax)</p>
                      </div>
                    </div>
                    <div className="mb-3">
                      <h5 className="font-medium text-gray-700 mb-2">Items:</h5>
                      {order.items.map((item, index) => (
                        <div key={index} className="text-sm text-gray-600">
                          {item.production_item_name} - Qty: {item.quantity} {item.unit_of_measure} @ ${item.unit_price?.toFixed(2) || '15.00'}
                        </div>
                      ))}
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                        Archived
                      </span>
                      <button
                        onClick={() => handleUnarchiveOrder(order.id)}
                        className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition-colors"
                        title="Restore this order"
                      >
                        Unarchive
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'invoices' && (
          <div className="bg-white rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-800 p-4 border-b">Invoices</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Invoice #</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Venue</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issue Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Due Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {invoices.map(invoice => (
                    <tr key={invoice.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{invoice.invoice_number}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{invoice.venue_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(invoice.issue_date).toLocaleDateString()}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{invoice.due_date ? new Date(invoice.due_date).toLocaleDateString() : 'N/A'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${invoice.total_amount.toFixed(2)}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          invoice.status === 'paid' ? 'bg-green-100 text-green-800' :
                          invoice.status === 'overdue' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {invoice.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => exportInvoicePDF(invoice.id, invoice.invoice_number)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                          title="Export PDF for Xero"
                        >
                          Export PDF
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'purchase-orders' && (
          <div className="bg-white rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-800 p-4 border-b">Purchase Orders</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PO #</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Venue</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issue Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Delivery Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {purchaseOrders.map(po => (
                    <tr key={po.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{po.po_number}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{po.venue_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(po.issue_date).toLocaleDateString()}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{po.delivery_date ? new Date(po.delivery_date).toLocaleDateString() : 'N/A'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${po.total_amount.toFixed(2)}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          po.status === 'completed' ? 'bg-green-100 text-green-800' :
                          po.status === 'approved' ? 'bg-blue-100 text-blue-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {po.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            {/* Current Passwords Display Section */}
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="border-b pb-4 mb-6">
                <h3 className="text-lg font-semibold text-gray-800">Current User Passwords</h3>
                <p className="text-sm text-gray-600 mt-1">View current passwords for all users. Click the eye icon to show/hide passwords.</p>
              </div>
              
              <div className="space-y-3">
                {localUsers.map(user => (
                  <div key={user.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                    <div className="flex items-center space-x-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${
                        user.role === 'manager' ? 'bg-purple-500' :
                        user.role === 'kitchen_staff' ? 'bg-green-500' :
                        'bg-blue-500'
                      }`}>
                        {user.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="font-medium text-gray-800">{user.name}</div>
                        <div className="text-sm text-gray-600">@{user.username} • {user.role.replace('_', ' ')}</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-600">Password:</span>
                        <div className="relative">
                          <span className={`font-mono text-sm px-2 py-1 rounded ${
                            passwordVisibility[user.id] ? 'bg-white border' : 'bg-gray-200 border'
                          }`}>
                            {passwordVisibility[user.id] ? user.password || 'No password set' : '••••••••'}
                          </span>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => togglePasswordVisibility(user.id)}
                        className="text-gray-400 hover:text-gray-600 p-1"
                        title={passwordVisibility[user.id] ? "Hide password" : "Show password"}
                      >
                        {passwordVisibility[user.id] ? (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L8.465 8.465M14.12 14.12l1.415 1.415M14.12 14.12L9.878 9.878m4.242 4.242L8.465 8.465" />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>
                ))}
                
                {localUsers.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <div className="text-lg mb-2">👥</div>
                    <p>No users found.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Password Management Section */}
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="border-b pb-4 mb-6">
                <h3 className="text-lg font-semibold text-gray-800">Change User Passwords</h3>
                <p className="text-sm text-gray-600 mt-1">Update passwords for users. No password requirements - you can set any password.</p>
              </div>
              
              <div className="space-y-4">
                {localUsers.map(user => (
                  <div key={user.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="font-medium text-gray-800">{user.name}</h4>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className="text-sm text-gray-600">@{user.username}</span>
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            user.role === 'manager' ? 'bg-purple-100 text-purple-800' :
                            user.role === 'kitchen_staff' ? 'bg-green-100 text-green-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {user.role.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        <div className="flex items-center space-x-2">
                          <div className="relative">
                            <input
                              type={passwordVisibility[user.id] ? "text" : "password"}
                              placeholder="New password"
                              className="w-40 text-sm p-2 pr-8 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                              id={`password-${user.id}`}
                            />
                            <button
                              type="button"
                              onClick={() => togglePasswordVisibility(user.id)}
                              className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                              title={passwordVisibility[user.id] ? "Hide password" : "Show password"}
                            >
                              {passwordVisibility[user.id] ? (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L8.465 8.465M14.12 14.12l1.415 1.415M14.12 14.12L9.878 9.878m4.242 4.242L8.465 8.465" />
                                </svg>
                              ) : (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                </svg>
                              )}
                            </button>
                          </div>
                          <button
                            onClick={() => {
                              const passwordInput = document.getElementById(`password-${user.id}`);
                              const newPassword = passwordInput.value.trim();
                              if (!newPassword) {
                                alert('Please enter a password.');
                                return;
                              }
                              if (window.confirm(`Update password for ${user.name}?`)) {
                                updateUserPassword(user.id, newPassword);
                                passwordInput.value = '';
                                // Reset password visibility after update
                                setPasswordVisibility(prev => ({
                                  ...prev,
                                  [user.id]: false
                                }));
                              }
                            }}
                            className="px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                          >
                            Update Password
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                {localUsers.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <div className="text-lg mb-2">👥</div>
                    <p>No users found.</p>
                  </div>
                )}
              </div>
            </div>

            {/* App Customization Settings */}
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="border-b pb-4 mb-6">
                <h3 className="text-lg font-semibold text-gray-800">App Customization</h3>
                <p className="text-sm text-gray-600 mt-1">Customize the appearance and branding of your application.</p>
              </div>
              <form onSubmit={async (e) => {
                e.preventDefault();
                
                // Handle logo upload if present
                let logoUrl = settings.logo_url || '';
                const logoFile = e.target.logo_file.files[0];
                if (logoFile) {
                  try {
                    const base64Logo = await fileToBase64(logoFile);
                    logoUrl = base64Logo;
                  } catch (error) {
                    console.error('Error uploading logo:', error);
                    alert('Error uploading logo. Please try again.');
                    return;
                  }
                }
                
                updateAppSettings({
                  app_name: e.target.app_name.value,
                  logo_url: logoUrl,
                  primary_color: e.target.primary_color.value,
                  secondary_color: e.target.secondary_color.value,
                  accent_color: e.target.accent_color.value,
                  font_family: e.target.font_family.value,
                  layout_style: e.target.layout_style.value
                });
              }} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input
                  name="app_name"
                  type="text"
                  placeholder="Street Eats Planner"
                  defaultValue={settings.app_name || 'Street Eats Planner'}
                  className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                
                {/* Logo Upload Section */}
                <div className="md:col-span-2">
                  <label className="block text-sm text-gray-600 mb-2">Company Logo</label>
                  <div className="flex items-center space-x-4">
                    {settings.logo_url && (
                      <div className="flex-shrink-0">
                        <img src={settings.logo_url} alt="Current Logo" className="h-16 w-16 object-contain border rounded" />
                        <p className="text-xs text-gray-500 mt-1">Current Logo</p>
                      </div>
                    )}
                    <div className="flex-1">
                      <input
                        name="logo_file"
                        type="file"
                        accept="image/*"
                        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                      />
                      <p className="text-xs text-gray-500 mt-1">Upload PNG, JPG, or GIF (recommended: 64x64px)</p>
                    </div>
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Primary Color</label>
                  <input
                    name="primary_color"
                    type="color"
                    defaultValue={settings.primary_color}
                    className="w-full h-12 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Secondary Color</label>
                  <input
                    name="secondary_color"
                    type="color"
                    defaultValue={settings.secondary_color}
                    className="w-full h-12 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Accent Color</label>
                  <input
                    name="accent_color"
                    type="color"
                    defaultValue={settings.accent_color}
                    className="w-full h-12 border border-gray-300 rounded-md"
                  />
                </div>
                <select
                  name="font_family"
                  defaultValue={settings.font_family}
                  className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Inter">Inter</option>
                  <option value="Roboto">Roboto</option>
                  <option value="Open Sans">Open Sans</option>
                  <option value="Poppins">Poppins</option>
                  <option value="Montserrat">Montserrat</option>
                </select>
                <select
                  name="layout_style"
                  defaultValue={settings.layout_style}
                  className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="modern">Modern</option>
                  <option value="classic">Classic</option>
                  <option value="compact">Compact</option>
                </select>
                <button
                  type="submit"
                  className="md:col-span-2 text-white py-3 px-4 rounded-md hover:opacity-90 transition-colors"
                  style={primaryButtonStyle}
                >
                  Save Settings
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Kitchen Staff Dashboard
const KitchenStaffDashboard = ({ user, appSettings }) => {
  const [pendingOrders, setPendingOrders] = useState([]);
  const [preparingOrders, setPreparingOrders] = useState([]);
  const [readyOrders, setReadyOrders] = useState([]);
  const [deliveredOrders, setDeliveredOrders] = useState([]);
  const [archivedOrders, setArchivedOrders] = useState([]);
  const [activeTab, setActiveTab] = useState('active');

  useEffect(() => {
    fetchAllOrders();
    fetchArchivedOrders();
    
    // Poll for orders every 30 seconds
    const interval = setInterval(() => {
      fetchAllOrders();
      if (activeTab === 'archived') {
        fetchArchivedOrders();
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [activeTab]);

  const fetchAllOrders = async () => {
    try {
      const [pendingRes, preparingRes, readyRes, deliveredRes] = await Promise.all([
        axios.get(`${API}/orders?status=pending`),
        axios.get(`${API}/orders?status=preparing`),
        axios.get(`${API}/orders?status=ready`),
        axios.get(`${API}/orders?status=delivered`)
      ]);
      
      setPendingOrders(pendingRes.data);
      setPreparingOrders(preparingRes.data);
      setReadyOrders(readyRes.data);
      setDeliveredOrders(deliveredRes.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const fetchArchivedOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders/archived`);
      setArchivedOrders(response.data);
    } catch (error) {
      console.error('Error fetching archived orders:', error);
    }
  };

  const handleArchiveOrder = async (orderId) => {
    try {
      await axios.put(`${API}/orders/${orderId}/archive`);
      fetchAllOrders(); // Refresh active orders
      fetchArchivedOrders(); // Refresh archived orders
    } catch (error) {
      console.error('Error archiving order:', error);
    }
  };

  const handleUnarchiveOrder = async (orderId) => {
    try {
      await axios.put(`${API}/orders/${orderId}/unarchive`);
      fetchAllOrders(); // Refresh active orders
      fetchArchivedOrders(); // Refresh archived orders
    } catch (error) {
      console.error('Error unarchiving order:', error);
    }
  };

  const updateOrderStatus = async (orderId, status) => {
    try {
      await axios.put(`${API}/orders/${orderId}/status?status=${status}`);
      fetchAllOrders(); // Refresh all orders
    } catch (error) {
      console.error('Error updating order status:', error);
    }
  };

  const containerStyle = {
    backgroundColor: appSettings?.secondary_color || '#f9fafb',
    fontFamily: appSettings?.font_family || 'Inter'
  };

  return (
    <div className="min-h-screen" style={containerStyle}>
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-xl font-semibold text-gray-800" style={{ fontFamily: appSettings?.font_family }}>
              {appSettings?.app_name || 'Street Eats Planner'} - Kitchen Production
            </h1>
            <span className="text-gray-600">Welcome, {user.name}</span>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Tab Navigation */}
        <div className="mb-6">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('active')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'active'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Active Orders
            </button>
            <button
              onClick={() => setActiveTab('archived')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'archived'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Archived Orders ({archivedOrders.length})
            </button>
          </nav>
        </div>

        {activeTab === 'active' && (
          <>
            {/* New Orders Section */}
            {pendingOrders.length > 0 && (
          <div className="bg-white rounded-lg shadow mb-6">
            <div className="p-4 border-b bg-red-50">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                <span className="bg-red-500 text-white px-2 py-1 rounded-full text-sm mr-2">
                  {pendingOrders.length}
                </span>
                🔔 New Orders - Start Preparation
              </h3>
            </div>
            <div className="p-4">
              <div className="space-y-4">
                {pendingOrders.map(order => (
                  <div key={order.id} className="p-4 bg-red-50 rounded-lg border-l-4 border-red-500">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex justify-between items-center mb-2">
                          <div className="font-medium text-gray-800">Order #{order.invoice_number}</div>
                          <div className="text-sm text-gray-600">
                            {new Date(order.order_date).toLocaleString()}
                          </div>
                        </div>
                        <div className="font-medium text-blue-600 mb-2">From: {order.venue_name}</div>
                        <div className="text-sm mb-3">
                          <strong>Items to prepare:</strong>
                          <div className="bg-white p-3 rounded mt-2">
                            {order.items.map((item, index) => (
                              <div key={index} className="flex justify-between items-center py-1 border-b last:border-b-0">
                                <span>{item.production_item_name}</span>
                                <span className="font-medium">{item.quantity} {item.unit_of_measure}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                        <div className="text-sm text-gray-600">
                          <strong>Delivery Address:</strong> {order.delivery_address}
                        </div>
                      </div>
                      <div className="text-right ml-4">
                        <div className="text-lg font-semibold text-green-600 mb-2">
                          ${order.total_amount.toFixed(2)}
                        </div>
                        <button
                          onClick={() => updateOrderStatus(order.id, 'preparing')}
                          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
                        >
                          Start Preparing
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Currently Preparing Section */}
        {preparingOrders.length > 0 && (
          <div className="bg-white rounded-lg shadow mb-6">
            <div className="p-4 border-b bg-yellow-50">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                <span className="bg-yellow-500 text-white px-2 py-1 rounded-full text-sm mr-2">
                  {preparingOrders.length}
                </span>
                👨‍🍳 Currently Preparing
              </h3>
            </div>
            <div className="p-4">
              <div className="space-y-4">
                {preparingOrders.map(order => (
                  <div key={order.id} className="p-4 bg-yellow-50 rounded-lg border-l-4 border-yellow-500">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex justify-between items-center mb-2">
                          <div className="font-medium text-gray-800">Order #{order.invoice_number}</div>
                          <div className="text-sm text-gray-600">
                            Started: {new Date(order.order_date).toLocaleString()}
                          </div>
                        </div>
                        <div className="font-medium text-blue-600 mb-2">For: {order.venue_name}</div>
                        <div className="text-sm mb-3">
                          <div className="bg-white p-3 rounded">
                            {order.items.map((item, index) => (
                              <div key={index} className="flex justify-between items-center py-1">
                                <span>{item.production_item_name}</span>
                                <span className="font-medium">{item.quantity} {item.unit_of_measure}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                      <div className="text-right ml-4">
                        <button
                          onClick={() => updateOrderStatus(order.id, 'ready')}
                          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors"
                        >
                          Mark Ready
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Ready for Delivery Section */}
        {readyOrders.length > 0 && (
          <div className="bg-white rounded-lg shadow mb-6">
            <div className="p-4 border-b bg-green-50">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                <span className="bg-green-500 text-white px-2 py-1 rounded-full text-sm mr-2">
                  {readyOrders.length}
                </span>
                ✅ Ready for Pickup/Delivery
              </h3>
            </div>
            <div className="p-4">
              <div className="space-y-4">
                {readyOrders.map(order => (
                  <div key={order.id} className="p-4 bg-green-50 rounded-lg border-l-4 border-green-500">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex justify-between items-center mb-2">
                          <div className="font-medium text-gray-800">Order #{order.invoice_number}</div>
                          <div className="text-sm text-gray-600">
                            Ready since: {new Date().toLocaleString()}
                          </div>
                        </div>
                        <div className="font-medium text-blue-600 mb-2">For: {order.venue_name}</div>
                        <div className="text-sm text-gray-600 mb-2">
                          <strong>Delivery Address:</strong> {order.delivery_address}
                        </div>
                        <div className="text-sm">
                          <div className="bg-white p-2 rounded">
                            {order.items.map((item, index) => (
                              <span key={index} className="inline-block mr-3 mb-1">
                                {item.quantity} {item.unit_of_measure} {item.production_item_name}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                      <div className="text-right ml-4">
                        <div className="text-lg font-semibold text-green-600 mb-2">
                          ${order.total_amount.toFixed(2)}
                        </div>
                        <button
                          onClick={() => updateOrderStatus(order.id, 'delivered')}
                          className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition-colors"
                        >
                          Mark Delivered
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Completed Orders Section */}
        {deliveredOrders.length > 0 && (
          <div className="bg-white rounded-lg shadow mb-6">
            <div className="p-4 border-b bg-gray-50">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                <span className="bg-gray-500 text-white px-2 py-1 rounded-full text-sm mr-2">
                  {deliveredOrders.length}
                </span>
                🚚 Completed Orders (Today)
              </h3>
            </div>
            <div className="p-4">
              <div className="space-y-3">
                {deliveredOrders.slice(0, 10).map(order => (
                  <div key={order.id} className="p-3 bg-gray-50 rounded-lg border-l-4 border-gray-400">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium text-gray-800">Order #{order.invoice_number} - {order.venue_name}</div>
                        <div className="text-sm text-gray-600">
                          Delivered: {order.delivered_at ? new Date(order.delivered_at).toLocaleString() : 'Recently'}
                        </div>
                      </div>
                      <div className="text-right flex items-center space-x-2">
                        <div>
                          <div className="text-sm font-medium text-green-600">${order.total_amount.toFixed(2)}</div>
                          <span className="text-xs text-gray-500">{order.items.length} items</span>
                        </div>
                        <button
                          onClick={() => handleArchiveOrder(order.id)}
                          className="bg-gray-500 hover:bg-gray-600 text-white px-2 py-1 rounded text-xs transition-colors"
                          title="Archive this order"
                        >
                          Archive
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
          </>
        )}

        {activeTab === 'archived' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b bg-gray-50">
              <h3 className="text-lg font-semibold text-gray-800">
                📦 Archived Orders ({archivedOrders.length})
              </h3>
            </div>
            <div className="p-4">
              {archivedOrders.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No archived orders found.</p>
              ) : (
                <div className="space-y-4">
                  {archivedOrders.map(order => (
                    <div key={order.id} className="p-4 bg-gray-50 rounded-lg border-l-4 border-gray-400">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex justify-between items-center mb-2">
                            <div className="font-medium text-gray-800">Order #{order.invoice_number}</div>
                            <div className="text-sm text-gray-600">
                              Archived: {order.archived_at ? new Date(order.archived_at).toLocaleString() : 'Unknown'}
                            </div>
                          </div>
                          <div className="font-medium text-blue-600 mb-2">From: {order.venue_name}</div>
                          <div className="text-sm mb-3">
                            <strong>Items:</strong>
                            <div className="grid grid-cols-2 gap-2 mt-1">
                              {order.items.map((item, index) => (
                                <div key={index} className="text-gray-600">
                                  • {item.production_item_name} ({item.quantity} {item.unit_of_measure})
                                </div>
                              ))}
                            </div>
                          </div>
                          <div className="flex justify-between items-center">
                            <div className="text-sm text-gray-600">
                              Total: <span className="font-medium">${order.total_amount?.toFixed(2) || '0.00'}</span>
                            </div>
                            <button
                              onClick={() => handleUnarchiveOrder(order.id)}
                              className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition-colors"
                            >
                              Unarchive
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

// Enhanced Venue Staff Dashboard with Visual Ordering
const VenueStaffDashboard = ({ user, appSettings }) => {
  const [orderableItems, setOrderableItems] = useState({});
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState('');
  const [cart, setCart] = useState([]);
  const [orders, setOrders] = useState([]);
  const [orderHistory, setOrderHistory] = useState({ most_ordered: [], recently_ordered: [] });
  const [activeTab, setActiveTab] = useState('recently-ordered');
  const [deliveryAddress, setDeliveryAddress] = useState(user.address || '');
  const [deliveryDate, setDeliveryDate] = useState('');

  useEffect(() => {
    fetchOrderableItems();
    fetchOrders();
    fetchOrderHistory();
  }, []);

  const fetchOrderableItems = async () => {
    try {
      const response = await axios.get(`${API}/orderable-items/by-category`);
      setOrderableItems(response.data);
      setCategories(Object.keys(response.data));
      if (Object.keys(response.data).length > 0 && !activeCategory) {
        setActiveCategory(Object.keys(response.data)[0]);
      }
    } catch (error) {
      console.error('Error fetching orderable items:', error);
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders?venue_id=${user.id}`);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const fetchOrderHistory = async () => {
    try {
      const response = await axios.get(`${API}/order-history/${user.id}`);
      setOrderHistory(response.data);
    } catch (error) {
      console.error('Error fetching order history:', error);
    }
  };

  const addToCart = (item, quantity = 1) => {
    const existingItem = cart.find(cartItem => cartItem.id === item.id);
    if (existingItem) {
      setCart(cart.map(cartItem => 
        cartItem.id === item.id 
          ? {...cartItem, orderQuantity: Math.min(cartItem.orderQuantity + quantity, item.available_quantity)}
          : cartItem
      ));
    } else {
      setCart([...cart, {...item, orderQuantity: quantity}]);
    }
  };

  const updateCartQuantity = (itemId, quantity) => {
    if (quantity === 0) {
      setCart(cart.filter(item => item.id !== itemId));
    } else {
      setCart(cart.map(item => 
        item.id === itemId ? {...item, orderQuantity: Math.min(quantity, item.available_quantity)} : item
      ));
    }
  };

  const placeOrder = async () => {
    if (cart.length === 0 || !deliveryAddress) {
      alert('Please add items to cart and provide delivery address');
      return;
    }

    try {
      const orderItems = cart.map(item => ({
        production_item_id: item.id,
        production_item_name: item.name,
        quantity: item.orderQuantity,
        unit_of_measure: item.unit_of_measure,
        unit_price: item.unit_price
      }));

      const orderData = {
        venue_name: user.name,
        venue_id: user.id,
        delivery_address: deliveryAddress,
        items: orderItems
      };

      if (deliveryDate) {
        orderData.delivery_date = deliveryDate;
      }

      await axios.post(`${API}/orders`, orderData);

      setCart([]);
      setDeliveryDate('');
      fetchOrders();
      fetchOrderableItems(); // Refresh to update available quantities
      alert('Order placed successfully!');
    } catch (error) {
      console.error('Error placing order:', error);
      alert('Error placing order');
    }
  };

  const containerStyle = {
    backgroundColor: appSettings?.secondary_color || '#f9fafb',
    fontFamily: appSettings?.font_family || 'Inter'
  };

  const primaryButtonStyle = {
    backgroundColor: appSettings?.primary_color || '#3b82f6'
  };

  return (
    <div className="min-h-screen" style={containerStyle}>
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-xl font-semibold text-gray-800" style={{ fontFamily: appSettings?.font_family }}>
              {appSettings?.app_name || 'Production Kitchen'} - Order Items
            </h1>
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Welcome, {user.name}</span>
              {cart.length > 0 && (
                <div className="relative">
                  <button 
                    onClick={() => setActiveTab('cart')}
                    className="bg-blue-600 text-white px-4 py-2 rounded-md flex items-center space-x-2"
                    style={primaryButtonStyle}
                  >
                    <span>Cart ({cart.length})</span>
                  </button>
                </div>
              )}
            </div>
          </div>
          <div className="flex space-x-6 overflow-x-auto">
            {['recently-ordered', 'most-ordered', ...categories, 'cart', 'orders'].map(tab => (
              <button
                key={tab}
                onClick={() => {
                  if (categories.includes(tab)) {
                    setActiveCategory(tab);
                    setActiveTab('category');
                  } else {
                    setActiveTab(tab);
                  }
                }}
                className={`py-2 px-4 border-b-2 whitespace-nowrap ${
                  (activeTab === tab || (activeTab === 'category' && activeCategory === tab)) 
                    ? 'border-blue-500 text-blue-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
                style={(activeTab === tab || (activeTab === 'category' && activeCategory === tab)) ? 
                  { borderColor: appSettings?.primary_color, color: appSettings?.primary_color } : {}}
              >
                {tab.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())} 
                {tab === 'cart' && cart.length > 0 && ` (${cart.length})`}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {(activeTab === 'recently-ordered' || activeTab === 'most-ordered') && (
          <div>
            <h2 className="text-2xl font-bold text-gray-800 mb-6">
              {activeTab === 'recently-ordered' ? 'Recently Ordered Items' : 'Your Most Ordered Items'}
            </h2>
            <div className="grid grid-cols-3 gap-4">
              {(activeTab === 'recently-ordered' ? orderHistory.recently_ordered : orderHistory.most_ordered).map(historyItem => {
                const currentItem = Object.values(orderableItems).flat().find(item => item.id === historyItem.item_id);
                if (!currentItem) return null;
                
                return (
                  <div key={historyItem.item_id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
                    {currentItem.image && (
                      <img src={currentItem.image} alt={currentItem.name} className="w-full h-32 object-cover" />
                    )}
                    <div className="p-3">
                      <h3 className="text-md font-semibold text-gray-800 mb-1">{currentItem.name}</h3>
                      <p className="text-xs text-gray-600 mb-2">{currentItem.category}</p>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-md font-bold text-green-600">${currentItem.unit_price.toFixed(2)}</span>
                        <span className="text-xs text-gray-500">per {currentItem.unit_of_measure}</span>
                      </div>
                      <div className="text-xs text-gray-500 mb-3">
                        <p>Previously: {historyItem.total_ordered} {currentItem.unit_of_measure}</p>
                        <p>Ordered {historyItem.times_ordered} times</p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input
                          type="number"
                          min="1"
                          max={currentItem.available_quantity}
                          defaultValue="1"
                          className="w-12 p-1 border border-gray-300 rounded text-xs"
                          id={`quantity-${historyItem.item_id}`}
                        />
                        <span className="text-xs text-gray-600">{currentItem.unit_of_measure}</span>
                        <button
                          onClick={() => {
                            const quantity = parseInt(document.getElementById(`quantity-${historyItem.item_id}`).value);
                            addToCart(currentItem, quantity);
                          }}
                          className="flex-1 text-white py-1 px-2 rounded-md hover:opacity-90 transition-colors text-xs"
                          style={primaryButtonStyle}
                          disabled={currentItem.available_quantity === 0}
                        >
                          {currentItem.available_quantity === 0 ? 'Out of Stock' : 'Add to Cart'}
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {activeTab === 'category' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-800 mb-6">{activeCategory}</h2>
            <div className="grid grid-cols-3 gap-4">
              {(orderableItems[activeCategory] || []).map(item => (
                <div key={item.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
                  {item.image && (
                    <img src={item.image} alt={item.name} className="w-full h-32 object-cover" />
                  )}
                  <div className="p-3">
                    <h3 className="text-md font-semibold text-gray-800 mb-1">{item.name}</h3>
                    <div className="flex justify-between items-center mb-3">
                      <span className="text-md font-bold text-green-600">${item.unit_price.toFixed(2)}</span>
                      <span className="text-xs text-gray-500">per {item.unit_of_measure}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        type="number"
                        min="1"
                        max={item.available_quantity}
                        defaultValue="1"
                        className="w-12 p-1 border border-gray-300 rounded text-xs"
                        id={`quantity-${item.id}`}
                      />
                      <span className="text-xs text-gray-600">{item.unit_of_measure}</span>
                      <button
                        onClick={() => {
                          const quantity = parseInt(document.getElementById(`quantity-${item.id}`).value);
                          addToCart(item, quantity);
                        }}
                        className="flex-1 text-white py-1 px-2 rounded-md hover:opacity-90 transition-colors text-xs"
                        style={primaryButtonStyle}
                        disabled={item.available_quantity === 0}
                      >
                        {item.available_quantity === 0 ? 'Out of Stock' : 'Add to Cart'}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'cart' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Shopping Cart</h2>
            {cart.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-600 mb-4">Your cart is empty</p>
                <button
                  onClick={() => setActiveTab('recently-ordered')}
                  className="text-white py-2 px-4 rounded-md hover:opacity-90 transition-colors"
                  style={primaryButtonStyle}
                >
                  Browse Items
                </button>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Delivery Address</label>
                    <textarea
                      value={deliveryAddress}
                      onChange={(e) => setDeliveryAddress(e.target.value)}
                      placeholder="Enter delivery address"
                      rows="3"
                      className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Preferred Delivery Date (Optional)</label>
                    <input
                      type="date"
                      value={deliveryDate}
                      onChange={(e) => setDeliveryDate(e.target.value)}
                      className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  {cart.map(item => (
                    <div key={item.id} className="flex items-center space-x-4 border-b pb-4">
                      {item.image && (
                        <img src={item.image} alt={item.name} className="w-16 h-16 object-cover rounded" />
                      )}
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-800">{item.name}</h4>
                        <p className="text-gray-600 text-sm">{item.category}</p>
                        <p className="text-green-600 font-semibold">${item.unit_price.toFixed(2)} per {item.unit_of_measure}</p>
                      </div>
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={() => updateCartQuantity(item.id, item.orderQuantity - 1)}
                          className="bg-gray-200 text-gray-700 px-2 py-1 rounded hover:bg-gray-300"
                        >
                          -
                        </button>
                        <span className="font-medium w-8 text-center">{item.orderQuantity}</span>
                        <button
                          onClick={() => updateCartQuantity(item.id, item.orderQuantity + 1)}
                          className="bg-gray-200 text-gray-700 px-2 py-1 rounded hover:bg-gray-300"
                          disabled={item.orderQuantity >= item.available_quantity}
                        >
                          +
                        </button>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">${(item.unit_price * item.orderQuantity).toFixed(2)}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="border-t pt-4">
                  <div className="text-right space-y-2">
                    <p className="text-lg">
                      Subtotal: ${cart.reduce((total, item) => total + (item.unit_price * item.orderQuantity), 0).toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-600">
                      Tax (8%): ${(cart.reduce((total, item) => total + (item.unit_price * item.orderQuantity), 0) * 0.08).toFixed(2)}
                    </p>
                    <p className="text-xl font-bold">
                      Total: ${(cart.reduce((total, item) => total + (item.unit_price * item.orderQuantity), 0) * 1.08).toFixed(2)}
                    </p>
                  </div>
                  <button
                    onClick={placeOrder}
                    disabled={!deliveryAddress}
                    className="w-full mt-4 text-white py-3 px-4 rounded-md hover:opacity-90 disabled:bg-gray-400 transition-colors text-lg font-semibold"
                    style={primaryButtonStyle}
                  >
                    Place Order
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'orders' && (
          <div className="bg-white rounded-lg shadow">
            <h2 className="text-2xl font-bold text-gray-800 p-6 border-b">My Orders</h2>
            <div className="space-y-4 p-6">
              {orders.map(order => (
                <div key={order.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <p className="text-sm text-gray-600">Order #{order.po_number}</p>
                      <p className="text-sm text-gray-600">Order Date: {new Date(order.order_date).toLocaleDateString()}</p>
                      <p className="text-sm text-gray-600">Delivery Address: {order.delivery_address}</p>
                      {order.delivery_date && (
                        <p className="text-sm text-gray-600">Delivery Date: {new Date(order.delivery_date).toLocaleDateString()}</p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-semibold text-gray-800">${order.total_amount?.toFixed(2) || '0.00'}</p>
                      <p className="text-sm text-gray-600">Total (incl. tax)</p>
                    </div>
                  </div>
                  <div className="mb-3">
                    <h5 className="font-medium text-gray-700 mb-2">Items:</h5>
                    {order.items.map((item, index) => (
                      <div key={index} className="text-sm text-gray-600">
                        {item.production_item_name} - Qty: {item.quantity} {item.unit_of_measure} @ ${item.unit_price?.toFixed(2)}
                      </div>
                    ))}
                  </div>
                  <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${
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

// Venue Staff Dashboard (Original - keeping for reference)
const VenueStaffDashboardOriginal = ({ user, appSettings }) => {
  const [completedItems, setCompletedItems] = useState([]);
  const [cart, setCart] = useState([]);
  const [orders, setOrders] = useState([]);
  const [activeTab, setActiveTab] = useState('order');
  const [deliveryAddress, setDeliveryAddress] = useState(user.address || '');
  const [deliveryDate, setDeliveryDate] = useState('');

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
      setCart([...cart, {...item, orderQuantity: 1, unit_price: 15.0}]);
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
    if (cart.length === 0 || !deliveryAddress) {
      alert('Please add items to cart and provide delivery address');
      return;
    }

    try {
      const orderItems = cart.map(item => ({
        production_item_id: item.id,
        production_item_name: item.name,
        quantity: item.orderQuantity,
        unit_of_measure: item.unit_of_measure,
        unit_price: item.unit_price
      }));

      const orderData = {
        venue_name: user.name,
        delivery_address: deliveryAddress,
        items: orderItems
      };

      if (deliveryDate) {
        orderData.delivery_date = deliveryDate;
      }

      await axios.post(`${API}/orders`, orderData);

      setCart([]);
      setDeliveryDate('');
      fetchOrders();
      alert('Order placed successfully!');
    } catch (error) {
      console.error('Error placing order:', error);
      alert('Error placing order');
    }
  };

  const containerStyle = {
    backgroundColor: appSettings?.secondary_color || '#f9fafb',
    fontFamily: appSettings?.font_family || 'Inter'
  };

  const primaryButtonStyle = {
    backgroundColor: appSettings?.primary_color || '#3b82f6'
  };

  return (
    <div className="min-h-screen" style={containerStyle}>
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-xl font-semibold text-gray-800" style={{ fontFamily: appSettings?.font_family }}>
              {appSettings?.app_name || 'Street Eats Planner'} - Venue Dashboard
            </h1>
            <span className="text-gray-600">Welcome, {user.name}</span>
          </div>
          <div className="flex space-x-6">
            {['order', 'cart', 'orders'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-2 px-4 border-b-2 ${activeTab === tab ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                style={activeTab === tab ? { borderColor: appSettings?.primary_color, color: appSettings?.primary_color } : {}}
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
                  {item.image && (
                    <img src={item.image} alt={item.name} className="w-full h-32 object-cover rounded mb-3" />
                  )}
                  <h4 className="font-semibold text-gray-800 mb-2">{item.name}</h4>
                  <p className="text-gray-600 mb-1">Category: {item.category}</p>
                  <p className="text-gray-600 mb-3">Available: {item.quantity} {item.unit_of_measure}</p>
                  <button
                    onClick={() => addToCart(item)}
                    className="w-full text-white py-2 px-4 rounded-md hover:opacity-90 transition-colors"
                    style={primaryButtonStyle}
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
                  <div className="space-y-3 mb-6">
                    <label className="block text-sm font-medium text-gray-700">Delivery Address</label>
                    <textarea
                      value={deliveryAddress}
                      onChange={(e) => setDeliveryAddress(e.target.value)}
                      placeholder="Enter delivery address"
                      rows="3"
                      className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Preferred Delivery Date (Optional)</label>
                    <input
                      type="date"
                      value={deliveryDate}
                      onChange={(e) => setDeliveryDate(e.target.value)}
                      className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  {cart.map(item => (
                    <div key={item.id} className="flex justify-between items-center border-b pb-4">
                      <div className="flex space-x-4">
                        {item.image && (
                          <img src={item.image} alt={item.name} className="w-16 h-16 object-cover rounded" />
                        )}
                        <div>
                          <h4 className="font-semibold text-gray-800">{item.name}</h4>
                          <p className="text-gray-600 text-sm">{item.category}</p>
                          <p className="text-gray-600 text-sm">Unit: {item.unit_of_measure}</p>
                          <p className="text-gray-600 text-sm">${item.unit_price.toFixed(2)} each</p>
                        </div>
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
                        Subtotal: ${cart.reduce((total, item) => total + (item.unit_price * item.orderQuantity), 0).toFixed(2)}
                      </p>
                      <p className="text-sm text-gray-600">Tax (8%): ${(cart.reduce((total, item) => total + (item.unit_price * item.orderQuantity), 0) * 0.08).toFixed(2)}</p>
                      <p className="text-xl font-bold">
                        Total: ${(cart.reduce((total, item) => total + (item.unit_price * item.orderQuantity), 0) * 1.08).toFixed(2)}
                      </p>
                    </div>
                    <button
                      onClick={placeOrder}
                      disabled={!deliveryAddress}
                      className="w-full text-white py-3 px-4 rounded-md hover:opacity-90 disabled:bg-gray-400 transition-colors"
                      style={primaryButtonStyle}
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
                      <p className="text-sm text-gray-600">Invoice: {order.invoice_number}</p>
                      <p className="text-sm text-gray-600">PO: {order.po_number}</p>
                      <p className="text-sm text-gray-600">Order Date: {new Date(order.order_date).toLocaleDateString()}</p>
                      <p className="text-sm text-gray-600">Delivery Address: {order.delivery_address}</p>
                      {order.delivery_date && (
                        <p className="text-sm text-gray-600">Delivery Date: {new Date(order.delivery_date).toLocaleDateString()}</p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-semibold text-gray-800">${order.total_amount?.toFixed(2) || '0.00'}</p>
                      <p className="text-sm text-gray-600">Total (incl. tax)</p>
                    </div>
                  </div>
                  <div className="mb-3">
                    <h5 className="font-medium text-gray-700 mb-2">Items:</h5>
                    {order.items.map((item, index) => (
                      <div key={index} className="text-sm text-gray-600">
                        {item.production_item_name} - Qty: {item.quantity} {item.unit_of_measure} @ ${item.unit_price?.toFixed(2) || '15.00'}
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
  const [appSettings, setAppSettings] = useState({});

  useEffect(() => {
    fetchAppSettings();
  }, []);

  const fetchAppSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setAppSettings(response.data);
    } catch (error) {
      console.error('Error fetching app settings:', error);
    }
  };

  const handleLogin = (user) => {
    setCurrentUser(user);
  };

  const handleLogout = () => {
    setCurrentUser(null);
  };

  if (!currentUser) {
    return <Login onLogin={handleLogin} appSettings={appSettings} />;
  }

  return (
    <div className="App">
      <div className="absolute top-4 right-4 z-50">
        <button 
          onClick={handleLogout}
          className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors"
        >
          Logout
        </button>
      </div>
      
      {currentUser.role === 'manager' && <ManagerDashboard user={currentUser} appSettings={appSettings} />}
      {currentUser.role === 'kitchen_staff' && <KitchenStaffDashboard user={currentUser} appSettings={appSettings} />}
      {currentUser.role === 'venue_staff' && <VenueStaffDashboard user={currentUser} appSettings={appSettings} />}
    </div>
  );
}

export default App;