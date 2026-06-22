# Restaurant POS System - Setup & Troubleshooting

## Quick Start

### 1. Initialize the Database
Run this command once to set up the database with sample data:
```bash
python init_db.py
```

You should see:
```
✓ Database initialized with sample data
  - 10 menu items added
  - 5 tables created

Database ready to use!
```

### 2. Start the Flask Server
```bash
python app.py
```

You should see:
```
WARNING in app.run() * Running on http://0.0.0.0:5000
Press CTRL+C to quit
```

### 3. Open the Frontend
Open a web browser and go to:
```
file:///c:/Users/HP/Desktop/caissier/index.html
```

Or open `index.html` in VS Code with Live Server extension

---

## 404 Error Troubleshooting

If you see **404 Not Found** errors, check:

### ✓ Server is Running
- Flask must be running on `http://127.0.0.1:5000`
- Check Terminal - you should see "Running on http://0.0.0.0:5000"

### ✓ Database Exists
The file `restaurant.db` must exist in the caissier folder

### ✓ Frontend Points to Correct URL
In `script.js`, check:
```javascript
const API_URL = "http://127.0.0.1:5000";
```

### ✓ Test the API
Run the test script to verify all endpoints work:
```bash
python test_api.py
```

This will show which endpoints are working and which aren't.

---

## API Endpoints Reference

### Tables
- `GET /tables` - Get all tables
- `POST /tables/<id>/open` - Open a table
- `POST /tables/<id>/close` - Close a table

### Stock/Menu
- `GET /stock` - Get all menu items with inventory

### Orders
- `GET /orders` - Get all orders
- `POST /orders` - Create new order
  ```json
  {
    "order_id": 1,
    "table_number": 1
  }
  ```
- `PUT /orders/<id>/status` - Update order status
  ```json
  {
    "status": "SENT_TO_KITCHEN"
  }
  ```

### Order Items
- `GET /orders/<id>/items` - Get items in order
- `POST /orders/<id>/items` - Add item to order
  ```json
  {
    "name": "Burger",
    "id": 0,
    "price": 500,
    "count": 1,
    "options": ""
  }
  ```
- `PUT /orders/<id>/items/<name>` - Update item quantity
- `DELETE /orders/<id>/items/<name>` - Remove item from order

### Payments
- `POST /orders/<id>/pay` - Process payment
  ```json
  {
    "amount": 1000,
    "method": "CASH"
  }
  ```

---

## Common Issues

### Issue: "Connection refused" or "Cannot connect to server"
**Solution:** Make sure you ran `python app.py` in the terminal

### Issue: "Database not found"
**Solution:** Run `python init_db.py` to create and populate the database

### Issue: Flask shows "404 Not Found" for all routes
**Solution:** Check that all imports in app.py can find functions in logic.py

### Issue: "ModuleNotFoundError: No module named 'flask'"
**Solution:** Install required packages:
```bash
pip install flask flask-cors
```

---

## File Structure
```
caissier/
├── app.py              # Flask server with all API endpoints
├── logic.py            # Business logic functions
├── database.py         # Database schema
├── init_db.py          # Initialize database with sample data
├── test_api.py         # Test API endpoints
├── index.html          # Frontend UI
├── script.js           # Frontend JavaScript
├── style.css           # Frontend styles
└── restaurant.db       # SQLite database (created by init_db.py)
```

---

## Roles & Access

### Waiter (Serveur)
- View tables
- Take orders
- Add items to orders
- Send orders to kitchen

### Chef (Cuisinier)
- View kitchen orders
- Mark orders as preparing
- Mark orders as ready

### Cashier (Caisse)
- View tables and totals
- Process payments
- View calculator

### Manager (Manager)
- Dashboard with statistics
- See all order status
- View revenue

---

## Testing Steps

1. **Start the server:** `python app.py`
2. **In another terminal, test the API:** `python test_api.py`
3. **Open frontend:** Open `index.html` in browser
4. **Login as Waiter:** Click "Serveur"
5. **Click a table:** Select "Table 1"
6. **Add items:** Click "Burger" or other menu items
7. **Send to kitchen:** Click "Envoyer en Cuisine"
8. **Login as Chef:** Go back to login, click "Chef"
9. **Mark as ready:** Click "Prêt !" on the kitchen orders
10. **Login as Cashier:** Process payment

---

For more help, check the console in your browser (F12) for JavaScript errors!
