#!/bin/bash

# Based on your screenshots - restoring with correct units and categories
declare -a items=(
  '{"name":"Beef Patties","category":"Main Course","unit_of_measure":"each","base_cost":4.89}'
  '{"name":"Bolognese Sauce","category":"Sauces","unit_of_measure":"litre","base_cost":10}'
  '{"name":"Carbonara Sauce","category":"Sauces","unit_of_measure":"litre","base_cost":16}'
  '{"name":"Chibba'\''s Spiced Fried Chicken","category":"Appetizers","unit_of_measure":"kilo","base_cost":12.5}'
  '{"name":"Chicken Thigh For Wok","category":"Asian groceries","unit_of_measure":"kilo","base_cost":11}'
  '{"name":"Chimichurri Sauce","category":"Sauces","unit_of_measure":"litre","base_cost":1}'
  '{"name":"Crispy Korean Chicken","category":"Appetizers","unit_of_measure":"kilo","base_cost":12}'
  '{"name":"Filipino BBQ Pork","category":"Skewers","unit_of_measure":"kilo","base_cost":15.5}'
  '{"name":"Jhol Sauce","category":"Sauces","unit_of_measure":"litre","base_cost":1}'
  '{"name":"Lamb Kofta","category":"Skewers","unit_of_measure":"each","base_cost":14}'
  '{"name":"Marinated Grilled Chicken - Enchiladas","category":"Appetizers","unit_of_measure":"each","base_cost":10}'
  '{"name":"Nasi Goreng Sauce","category":"Asian groceries","unit_of_measure":"litre","base_cost":8.5}'
  '{"name":"Nepalese Momo Dumplings","category":"Asian groceries","unit_of_measure":"each","base_cost":11.5}'
  '{"name":"Satay Chicken","category":"Skewers","unit_of_measure":"each","base_cost":11.5}'
  '{"name":"Satay Chicken Sauce","category":"Asian groceries","unit_of_measure":"litre","base_cost":1}'
  '{"name":"Slow Cooked Beef Brisket","category":"Main Course","unit_of_measure":"kilo","base_cost":17.5}'
  '{"name":"Spicy Citrus Grilled Prawn","category":"Skewers","unit_of_measure":"each","base_cost":25}'
  '{"name":"Thai Beef","category":"Asian groceries","unit_of_measure":"kilo","base_cost":16}'
  '{"name":"Tofu","category":"Asian groceries","unit_of_measure":"kilo","base_cost":11.5}'
)

echo "🔄 Restoring your 19 production items with CORRECT units and Asian groceries category..."

for item in "${items[@]}"; do
  name=$(echo "$item" | jq -r '.name')
  unit=$(echo "$item" | jq -r '.unit_of_measure')
  category=$(echo "$item" | jq -r '.category')
  echo "Creating: $name ($category, $unit)"
  
  curl -s -X POST "http://localhost:8001/api/production-items?created_by=manager" \
    -H "Content-Type: application/json" \
    -d "$item" > /dev/null
done

echo ""
echo "✅ Restoration complete with correct units and categories!"