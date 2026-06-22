=============================================================================
                      RESTAURANT CAISSIER SYSTEM
=============================================================================

PROJECT OVERVIEW
----------------
This project is a custom-built Point of Sale (POS) system designed for 
restaurant management. It features a role-based interface catering to 
Waiters, Chefs, Cashiers, and Managers, all powered by a Python backend 
and a lightweight web frontend.


SYSTEM FEATURES & OPTIONS
-------------------------
The system offers tailored views and operations depending on the user's role,
alongside core automation features:

1. Role-Based Options:
   * Waiter Interface:
     - Open active dining tables[cite: 10].
     - Create new customer orders and select table numbers[cite: 10].
     - Add specific menu items to an order with quantities and prices[cite: 10].
   * Chef / Kitchen Dashboard:
     - View incoming orders sent to the kitchen in real time[cite: 10].
     - Update order statuses (e.g., SENT_TO_KITCHEN) as they clear[cite: 10].
   * Cashier Interface:
     - Close out completed tables[cite: 10].
     - View full order summaries and calculate total bills.
     - Process payments and handle bill-splitting operations.
   * Manager Dashboard:
     - Track live inventory levels and stock availability[cite: 10].
     - Access financial reporting (daily revenue metrics and analytics).

2. Core Database & API Controls:
   * Live Table Tracking: Monitor which tables are currently open or free[cite: 10].
   * Stock Management: Auto-fetch full menus alongside current inventory counts[cite: 10].
   * Dynamic Order Logs: Query historical or current active orders instantaneously[cite: 10].


REQUIRED DEPENDENCIES
---------------------
To run this project, you need Python 3.x installed on your system along 
with the following Python packages:

1. Flask: The web framework used to build the API.
2. Flask-CORS: Used to handle Cross-Origin Resource Sharing so the frontend 
   can communicate with the backend.

Installation command:
> pip install flask flask-cors

Note: SQLite3 is used for the database, which is included by default 
in the standard Python library, so no extra installation is required.


HOW I MADE IT (DEVELOPMENT STEPS)
---------------------------------
The development of this POS system was broken down into four main phases, 
separating the data, business logic, API routing, and user interface.

STEP 1: Database Architecture & Setup (init_db.py)
- Designed a relational SQLite database structure to track restaurant data.
- Created tables for `Item` (inventory), `Order`, `OrderItem`, `Tables`, 
  and `Payment`.
- Wrote an initialization script to automatically generate the database 
  schema and populate it with default menu items and 5 tables[cite: 10].

STEP 2: Core Business Logic (logic.py)
- Developed the backend logic entirely in Python to interact with the SQLite 
  database.
- Implemented modular functions for distinct restaurant operations:
  * Stock & Menu Management (increasing/decreasing inventory)
  * Order Operations (adding items, calculating totals, splitting orders)
  * Table Management (opening, closing, transferring tables)
  * Kitchen Flow (updating order statuses from 'Sent' to 'Served')
  * Financial Reporting (daily/monthly revenue, best-selling items)

STEP 3: RESTful API Development (app.py)
- Wrapped the core logic functions in a Flask application to create a 
  communication bridge[cite: 10].
- Defined clear, RESTful HTTP endpoints (GET, POST, PUT) for every 
  action in the system[cite: 10].
- Integrated `flask-cors` to ensure the local HTML files could make requests 
  to the local Flask server without browser security blocks.

STEP 4: Frontend Implementation (index.html, style.css, script.js)
- Built a lightweight, single-page application (SPA) without heavy frameworks[cite: 10].
- Designed a role-based login system that hides/shows specific UI panels 
  depending on the selected job (Waiter, Chef, Cashier, Manager).
- Wrote asynchronous JavaScript using `fetch()` to call the Flask API, 
  updating the DOM dynamically so the app feels fast and responsive[cite: 10].


HOW TO RUN THE PROJECT
----------------------
1. Open your terminal or command prompt.
2. Navigate to the project folder.
3. Initialize the database by running:[cite: 10]
   python init_db.py[cite: 10]
4. Start the Flask backend server by running:[cite: 10]
   python app.py[cite: 10]
5. Open the `index.html` file in any modern web browser to access the system[cite: 10].