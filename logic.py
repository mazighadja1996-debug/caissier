import sqlite3
from datetime import datetime

DB_NAME = "restaurant.db"

def init_database_if_needed():
    """Initialise la base de données - safe to call multiple times (uses IF NOT EXISTS)"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")

        # Table Item
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Item (
                Name TEXT PRIMARY KEY,
                Inventory_Count INTEGER DEFAULT 0
            )
        ''')
        
        # Table Order
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS `Order` (
                ID INTEGER PRIMARY KEY,
                itmNum INTEGER DEFAULT 0,
                totalPrice REAL DEFAULT 0,
                tableNumber INTEGER,
                status TEXT DEFAULT 'OPEN'
            )
        ''')
        
        # Table OrderItem
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS OrderItem (
                Name TEXT,
                ID TEXT,
                `order` INTEGER,
                Options TEXT DEFAULT '',
                Price REAL,
                count INTEGER,
                PRIMARY KEY (`order`, Name),
                FOREIGN KEY (`order`) REFERENCES `Order`(ID)
            )
        ''')
        
        # Table Tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Tables (
                Table_number INTEGER PRIMARY KEY,
                `order` INTEGER,
                active TEXT DEFAULT 'close',
                status TEXT DEFAULT 'available',
                FOREIGN KEY (`order`) REFERENCES `Order`(ID)
            )
        ''')
        
        # Table Payment
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Payment (
                `order` INTEGER,
                amount REAL,
                method TEXT,
                date TEXT,
                FOREIGN KEY (`order`) REFERENCES `Order`(ID)
            )
        ''')
        
        # Articles par défaut (UNIQUEMENT si la table est vide)
        cursor.execute("SELECT COUNT(*) FROM Item")
        if cursor.fetchone()[0] == 0:
            items = [
                ('Burger', 10), ('Pizza', 8), ('Pasta', 12),
                ('Salad', 15), ('Soda', 20), ('Fries', 15),
                ('Coffee', 25), ('Juice', 18)
            ]
            cursor.executemany("INSERT INTO Item (Name, Inventory_Count) VALUES (?, ?)", items)
        
        # Tables de 1 à 10 (UNIQUEMENT si la table est vide)
        cursor.execute("SELECT COUNT(*) FROM Tables")
        if cursor.fetchone()[0] == 0:
            for i in range(1, 11):
                cursor.execute("INSERT INTO Tables (Table_number, `order`, active, status) VALUES (?, NULL, 'close', 'available')", (i,))
        
        conn.commit()
        print("✅ Base de données initialisée")

# Appeler l'initialisation au chargement du module
init_database_if_needed()


########## 1 - Stock Management ##########

def get_current_inventory():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Name, Inventory_Count FROM Item ORDER BY Name")
        return cursor.fetchall()

def increase_inventory(name):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Inventory_Count FROM Item WHERE Name = ?", (name,))
        result = cursor.fetchone()
        if result:
            cursor.execute("UPDATE Item SET Inventory_Count = ? WHERE Name = ?", (result[0] + 1, name))
            return True
    return False

def decrease_inventory(name):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Inventory_Count FROM Item WHERE Name = ?", (name,))
        result = cursor.fetchone()
        if result and result[0] > 0:
            cursor.execute("UPDATE Item SET Inventory_Count = ? WHERE Name = ?", (result[0] - 1, name))
            return True
    return False

def set_inventory_count(name, count):
    if count >= 0:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE Item SET Inventory_Count = ? WHERE Name = ?", (count, name))
            return True
    return False

def get_inventory_count(name):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Inventory_Count FROM Item WHERE Name = ?", (name,))
        result = cursor.fetchone()
        return result[0] if result else None

def is_out_of_stock(name):
    count = get_inventory_count(name)
    return count == 0 if count is not None else True


########## 2 - Order Items Management ##########

def add_item(name, item_id, order_id, options, price, count):
    """Ajoute un article à une commande"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            
            # Vérifier si la commande existe
            cursor.execute("SELECT ID FROM `Order` WHERE ID = ?", (order_id,))
            if not cursor.fetchone():
                print(f"ERREUR: Commande {order_id} n'existe pas")
                return False
            
            # Vérifier si l'article existe déjà
            cursor.execute(
                "SELECT count FROM OrderItem WHERE `order` = ? AND Name = ?",
                (order_id, name)
            )
            existing = cursor.fetchone()
            
            if existing:
                new_count = existing[0] + count
                cursor.execute(
                    "UPDATE OrderItem SET count = ? WHERE `order` = ? AND Name = ?",
                    (new_count, order_id, name)
                )
            else:
                cursor.execute(
                    "INSERT INTO OrderItem (Name, ID, `order`, Options, Price, count) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, item_id, order_id, options, price, count)
                )
            
            # Mettre à jour itmNum
            cursor.execute(
                "UPDATE `Order` SET itmNum = (SELECT COALESCE(SUM(count), 0) FROM OrderItem WHERE `order` = ?) WHERE ID = ?",
                (order_id, order_id)
            )
            
            calculate_order_total(order_id)
            conn.commit()
            return True
            
    except Exception as e:
        print(f"ERREUR add_item: {e}")
        return False

def update_item(ord_id, name, count):
    """Met à jour la quantité d'un article"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            
            if count <= 0:
                cursor.execute(
                    "DELETE FROM OrderItem WHERE `order` = ? AND Name = ?",
                    (ord_id, name)
                )
            else:
                cursor.execute(
                    "UPDATE OrderItem SET count = ? WHERE `order` = ? AND Name = ?",
                    (count, ord_id, name)
                )
            
            cursor.execute(
                "UPDATE `Order` SET itmNum = (SELECT COALESCE(SUM(count), 0) FROM OrderItem WHERE `order` = ?) WHERE ID = ?",
                (ord_id, ord_id)
            )
            
            calculate_order_total(ord_id)
            conn.commit()
            return True
            
    except Exception as e:
        print(f"ERREUR update_item: {e}")
        return False

def delete_item(name, ord_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM OrderItem WHERE `order` = ? AND Name = ?", (ord_id, name))
        cursor.execute(
            "UPDATE `Order` SET itmNum = (SELECT COALESCE(SUM(count), 0) FROM OrderItem WHERE `order` = ?) WHERE ID = ?",
            (ord_id, ord_id)
        )
        calculate_order_total(ord_id)
        return True

def get_item(ord_id, name):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM OrderItem WHERE `order` = ? AND Name = ?", (ord_id, name))
        return cursor.fetchone()

def get_all_items(ord_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM OrderItem WHERE `order` = ?", (ord_id,))
        return cursor.fetchall()

def add_item_option(ord_id, name, op):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE OrderItem SET Options = ? WHERE `order` = ? AND Name = ?", (op, ord_id, name))
        return True

def remove_item_option(ord_id, name):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE OrderItem SET Options = '' WHERE `order` = ? AND Name = ?", (ord_id, name))
        return True


########## 3 - Table Management ##########

def open_table(tab_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE Tables SET active = ? WHERE Table_number = ?", ('open', tab_id))
        return True

def close_table(tab_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE Tables SET active = ? WHERE Table_number = ?", ('close', tab_id))
        return True

def create_table(table_id, order_id, active, status):
    """Crée une table UNIQUEMENT si elle n'existe pas - CORRIGÉ"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Vérification STRICTE
        cursor.execute("SELECT 1 FROM Tables WHERE Table_number = ?", (table_id,))
        if cursor.fetchone():
            print(f"⚠️ Table {table_id} existe déjà, création ignorée")
            return True  # Retourner True car ce n'est pas une erreur
        cursor.execute("INSERT INTO Tables (Table_number, `order`, active, status) VALUES (?, ?, ?, ?)", 
                      (table_id, order_id, active, status))
        return True

def delete_table(tab_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Tables WHERE Table_number = ?", (tab_id,))
        return True

def get_table(tab):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Tables WHERE Table_number = ?", (tab,))
        return cursor.fetchone()

def get_all_tables():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Tables ORDER BY Table_number")
        return cursor.fetchall()

def set_table_available(tab_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE Tables SET status = ? WHERE Table_number = ?", ('available', tab_id))
        return True

def set_table_occupied(tab_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE Tables SET status = ? WHERE Table_number = ?", ('occupied', tab_id))
        return True

def set_table_reserved(tab_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE Tables SET status = ? WHERE Table_number = ?", ('reserved', tab_id))
        return True

def set_table_cleaning(tab_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE Tables SET status = ? WHERE Table_number = ?", ('cleaning', tab_id))
        return True

def transfer_table(tab1, tab2):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT `order` FROM Tables WHERE Table_number = ?", (tab1,))
        t1 = cursor.fetchone()
        cursor.execute("SELECT `order` FROM Tables WHERE Table_number = ?", (tab2,))
        t2 = cursor.fetchone()
        if t1 and t2:
            cursor.execute("UPDATE Tables SET `order` = ? WHERE Table_number = ?", (t2[0], tab1))
            cursor.execute("UPDATE Tables SET `order` = ? WHERE Table_number = ?", (t1[0], tab2))
            return True
    return False


########## 4 - Order Management ##########

class OrderStatus:
    OPEN = "OPEN"
    SENT_TO_KITCHEN = "SENT_TO_KITCHEN"
    PREPARING = "PREPARING"
    READY = "READY"
    SERVED = "SERVED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"

def create_order(order_id, table_number):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO `Order` VALUES (?, ?, ?, ?, ?)", 
                      (order_id, 0, 0, table_number, OrderStatus.OPEN))
        cursor.execute("UPDATE Tables SET `order` = ? WHERE Table_number = ?", (order_id, table_number))
        return order_id

def open_order(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE `Order` SET status = ? WHERE ID = ?", (OrderStatus.OPEN, order_id))
        return True

def cancel_order(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE `Order` SET status = ? WHERE ID = ?", (OrderStatus.CANCELLED, order_id))
        return True

def delete_order(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM `Order` WHERE ID = ?", (order_id,))
        cursor.execute("DELETE FROM OrderItem WHERE `order` = ?", (order_id,))
        return True

def get_order(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM `Order` WHERE ID = ?", (order_id,))
        return cursor.fetchone()

def get_all_orders():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM `Order`")
        return cursor.fetchall()

def get_table_order(table_number):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT `order` FROM Tables WHERE Table_number = ?", (table_number,))
        result = cursor.fetchone()
        if result and result[0]:
            return get_order(result[0])
    return None

def calculate_order_total(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(price * count) FROM OrderItem WHERE `order` = ?", (order_id,))
        total = cursor.fetchone()[0] or 0
        cursor.execute("UPDATE `Order` SET totalPrice = ? WHERE ID = ?", (total, order_id))
        return total

def apply_discount(order_id, discount_percent):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT totalPrice FROM `Order` WHERE ID = ?", (order_id,))
        result = cursor.fetchone()
        if result:
            new_total = result[0] * (1 - discount_percent / 100)
            cursor.execute("UPDATE `Order` SET totalPrice = ? WHERE ID = ?", (new_total, order_id))
            return new_total
    return None

def remove_discount(order_id):
    return calculate_order_total(order_id)

def add_tax(order_id, tax_percent):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT totalPrice FROM `Order` WHERE ID = ?", (order_id,))
        result = cursor.fetchone()
        if result:
            new_total = result[0] * (1 + tax_percent / 100)
            cursor.execute("UPDATE `Order` SET totalPrice = ? WHERE ID = ?", (new_total, order_id))
            return new_total
    return None


########## 5 - Payment Management ##########

class PaymentMethod:
    CASH = "CASH"
    CARD = "CARD"
    MOBILE_PAYMENT = "MOBILE_PAYMENT"

def pay_order(order_id, amount, method):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT totalPrice, tableNumber FROM `Order` WHERE ID = ?", (order_id,))
        result = cursor.fetchone()
        if result and amount >= result[0]:
            cursor.execute("INSERT INTO Payment VALUES (?, ?, ?, ?)", 
                          (order_id, amount, method, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            cursor.execute("UPDATE `Order` SET status = ? WHERE ID = ?", (OrderStatus.PAID, order_id))
            cursor.execute("UPDATE Tables SET `order` = NULL, status = 'available' WHERE Table_number = ?", (result[1],))
            return {"success": True, "change": amount - result[0], "table_number": result[1]}
    return {"success": False, "error": "Payment failed"}

def partial_payment(order_id, amount, method):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT totalPrice FROM `Order` WHERE ID = ?", (order_id,))
        result = cursor.fetchone()
        if result:
            cursor.execute("INSERT INTO Payment VALUES (?, ?, ?, ?)", 
                          (order_id, amount, method, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            new_total = result[0] - amount
            cursor.execute("UPDATE `Order` SET totalPrice = ? WHERE ID = ?", (new_total, order_id))
            return {"success": True, "remaining": new_total}
    return {"success": False}

def refund_order(order_id, amount):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Payment VALUES (?, ?, ?, ?)", 
                      (order_id, -amount, "REFUND", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        return True

def generate_receipt(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ID, totalPrice, tableNumber, status FROM `Order` WHERE ID = ?", (order_id,))
        order = cursor.fetchone()
        if not order:
            return None
        cursor.execute("SELECT Name, Price, count, Options FROM OrderItem WHERE `order` = ?", (order_id,))
        items = cursor.fetchall()
        return {
            "order_id": order[0],
            "total": order[1],
            "table": order[2],
            "status": order[3],
            "items": [{"name": i[0], "price": i[1], "quantity": i[2], "options": i[3]} for i in items],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def pay_cash(order_id, amount):
    return pay_order(order_id, amount, PaymentMethod.CASH)

def pay_card(order_id, amount):
    return pay_order(order_id, amount, PaymentMethod.CARD)

def pay_mobile(order_id, amount):
    return pay_order(order_id, amount, PaymentMethod.MOBILE_PAYMENT)


########## 6 - Table Service ##########

def move_order_to_table(order_id, new_table):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Table_number FROM Tables WHERE `order` = ?", (order_id,))
        old = cursor.fetchone()
        if old:
            cursor.execute("UPDATE Tables SET `order` = ? WHERE Table_number = ?", (None, old[0]))
        cursor.execute("UPDATE Tables SET `order` = ? WHERE Table_number = ?", (order_id, new_table))
        cursor.execute("UPDATE `Order` SET tableNumber = ? WHERE ID = ?", (new_table, order_id))
        return True

def merge_orders(order_id_1, order_id_2):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Name, Options, Price, count FROM OrderItem WHERE `order` = ?", (order_id_2,))
        items = cursor.fetchall()
        for item in items:
            cursor.execute("INSERT INTO OrderItem (Name, ID, `order`, Options, Price, count) VALUES (?, ?, ?, ?, ?, ?)", 
                          (item[0], order_id_1, order_id_1, item[1], item[2], item[3]))
        cursor.execute("DELETE FROM OrderItem WHERE `order` = ?", (order_id_2,))
        cursor.execute("DELETE FROM `Order` WHERE ID = ?", (order_id_2,))
        calculate_order_total(order_id_1)
        return True

def split_order(order_id, items_to_split):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT tableNumber FROM `Order` WHERE ID = ?", (order_id,))
        result = cursor.fetchone()
        new_id = order_id + 1000
        create_order(new_id, result[0] if result else 1)
        for item_name in items_to_split:
            cursor.execute("UPDATE OrderItem SET `order` = ? WHERE `order` = ? AND Name = ?", (new_id, order_id, item_name))
        calculate_order_total(order_id)
        calculate_order_total(new_id)
        return new_id

def transfer_items_between_orders(from_order, to_order, items_to_transfer):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        for item_name in items_to_transfer:
            cursor.execute("UPDATE OrderItem SET `order` = ? WHERE `order` = ? AND Name = ?", (to_order, from_order, item_name))
        calculate_order_total(from_order)
        calculate_order_total(to_order)
        return True


########## 7 - KITCHEN MANAGEMENT ##########

def send_order_to_kitchen(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE `Order` SET status = ? WHERE ID = ?", (OrderStatus.SENT_TO_KITCHEN, order_id))
        return True

def mark_preparing(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE `Order` SET status = ? WHERE ID = ?", (OrderStatus.PREPARING, order_id))
        return True

def mark_ready(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE `Order` SET status = ? WHERE ID = ?", (OrderStatus.READY, order_id))
        return True

def mark_served(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE `Order` SET status = ? WHERE ID = ?", (OrderStatus.SERVED, order_id))
        return True

def get_kitchen_orders_with_items():
    """Récupère les commandes en cuisine avec leurs articles détaillés"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        kitchen_statuses = ['OPEN', 'SENT_TO_KITCHEN', 'PREPARING']
        placeholders = ','.join(['?'] * len(kitchen_statuses))
        cursor.execute(f"""
            SELECT o.ID, o.tableNumber, o.status, o.totalPrice 
            FROM `Order` o
            WHERE o.status IN ({placeholders})
            ORDER BY o.ID DESC
        """, kitchen_statuses)
        orders = cursor.fetchall()
        
        result = []
        for order in orders:
            cursor.execute("""
                SELECT Name, count, Options, Price 
                FROM OrderItem 
                WHERE `order` = ?
            """, (order[0],))
            items = cursor.fetchall()
            result.append({
                'id': order[0],
                'tableNumber': order[1],
                'status': order[2],
                'totalPrice': order[3],
                'items': [{'name': item[0], 'count': item[1], 'options': item[2] or '', 'price': item[3]} for item in items]
            })
        return result
########## 8 - Reports ##########

def get_daily_revenue(date):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM Payment WHERE date LIKE ? AND method != 'REFUND'", (date + "%",))
        return cursor.fetchone()[0] or 0

def get_monthly_revenue(year_month):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM Payment WHERE date LIKE ? AND method != 'REFUND'", (year_month + "%",))
        return cursor.fetchone()[0] or 0

def get_best_selling_items(limit=10):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Name, SUM(count) as total_sold 
            FROM OrderItem 
            GROUP BY Name 
            ORDER BY total_sold DESC 
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()

def get_inventory_report():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Name, Inventory_Count FROM Item ORDER BY Name")
        return cursor.fetchall()

def get_open_orders():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ID, tableNumber FROM `Order` WHERE status = ?", (OrderStatus.OPEN,))
        return cursor.fetchall()

def get_paid_orders():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ID, tableNumber, totalPrice FROM `Order` WHERE status = ?", (OrderStatus.PAID,))
        return cursor.fetchall()