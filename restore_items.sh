#!/bin/bash

# Your 19 production items based on the screenshots and deployed data
declare -a items=(
  '{"name":"Beef Patties","category":"Main Course","unit_of_measure":"kilo","base_cost":10}'
  '{"name":"Bolognese Sauce","category":"Sauces","unit_of_measure":"kilo","base_cost":10}'
  '{"name":"Carbonara Sauce","category":"Sauces","unit_of_measure":"kilo","base_cost":16}'
  '{"name":"Chibba'\''s Spiced Fried Chicken","category":"Appetizers","unit_of_measure":"kilo","base_cost":12.5}'
  '{"name":"Chicken Thigh For Wok","category":"Main Course","unit_of_measure":"kilo","base_cost":11}'
  '{"name":"Chimichurri Sauce","category":"Sauces","unit_of_measure":"kilo","base_cost":1}'
  '{"name":"Crispy Korean Chicken","category":"Appetizers","unit_of_measure":"kilo","base_cost":12}'
  '{"name":"Filipino BBQ Pork","category":"Skewers","unit_of_measure":"kilo","base_cost":15.5}'
  '{"name":"Jhol Sauce","category":"Sauces","unit_of_measure":"kilo","base_cost":1}'
  '{"name":"Lamb Kofta","category":"Skewers","unit_of_measure":"kilo","base_cost":14}'
  '{"name":"Marinated Grilled Chicken - Enchiladas","category":"Appetizers","unit_of_measure":"kilo","base_cost":10}'
  '{"name":"Nasi Goreng Sauce","category":"Sauces","unit_of_measure":"kilo","base_cost":8.5}'
  '{"name":"Nepalese Momo Dumplings","category":"Appetizers","unit_of_measure":"kilo","base_cost":11.5}'
  '{"name":"Satay Chicken","category":"Skewers","unit_of_measure":"kilo","base_cost":11.5}'
  '{"name":"Satay Chicken Sauce","category":"Sauces","unit_of_measure":"kilo","base_cost":1}'
  '{"name":"Slow Cooked Beef Brisket","category":"Appetizers","unit_of_measure":"kilo","base_cost":17.5}'
  '{"name":"Spicy Citrus Grilled Prawn","category":"Skewers","unit_of_measure":"kilo","base_cost":25}'
  '{"name":"Thai Beef","category":"Skewers","unit_of_measure":"kilo","base_cost":16}'
  '{"name":"Tofu","category":"Main Course","unit_of_measure":"kilo","base_cost":11.5}'
)

echo "🔄 Restoring your 19 production items..."

for item in "${items[@]}"; do
  name=$(echo "$item" | jq -r '.name')
  echo "Creating: $name"
  
  curl -s -X POST "http://localhost:8001/api/production-items?created_by=manager" \
    -H "Content-Type: application/json" \
    -d "$item" > /dev/null
done

echo ""
echo "✅ Restoration complete! Verifying..."
total=$(curl -s http://localhost:8001/api/production-items | jq 'length')
echo "Total items restored: $total"