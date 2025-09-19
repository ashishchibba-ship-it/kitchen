// Individual item completion tracking for kitchen staff
  const toggleItemCompletion = (orderId, itemIndex) => {
    const key = `${orderId}-${itemIndex}`;
    setItemCompletion(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const isItemCompleted = (orderId, itemIndex) => {
    const key = `${orderId}-${itemIndex}`;
    return itemCompletion[key] || false;
  };

  const isOrderCompleted = (orderId, itemsCount) => {
    for (let i = 0; i < itemsCount; i++) {
      if (!isItemCompleted(orderId, i)) {
        return false;
      }
    }
    return true;
  };

  const formatDeliveryDate = (deliveryDate) => {
    if (!deliveryDate) return 'Not specified';
    try {
      const date = new Date(deliveryDate);
      return date.toLocaleDateString() + ' at ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    } catch (error) {
      return deliveryDate;
    }
  };