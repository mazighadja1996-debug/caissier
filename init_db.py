# reset_db.py - Exécutez ce script pour réinitialiser la base de données
import sqlite3

DB_NAME = "restaurant.db"

# Supprimer l'ancienne base de données
import os
if os.path.exists(DB_NAME):
    os.remove(DB_NAME)
    print(f"Ancienne base {DB_NAME} supprimée")

# Créer la nouvelle base de données
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Table Item (Stock)
cursor.execute('''
    CREATE TABLE Item (
        Name TEXT PRIMARY KEY,
        Inventory_Count INTEGER DEFAULT 0
    )
''')

# Table Order
cursor.execute('''
    CREATE TABLE `Order` (
        ID INTEGER PRIMARY KEY,
        itmNum INTEGER DEFAULT 0,
        totalPrice REAL DEFAULT 0,
        tableNumber INTEGER,
        status TEXT DEFAULT 'OPEN'
    )
''')

# Table OrderItem
cursor.execute('''
    CREATE TABLE OrderItem (
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
    CREATE TABLE Tables (
        Table_number INTEGER PRIMARY KEY,
        `order` INTEGER,
        active TEXT DEFAULT 'close',
        status TEXT DEFAULT 'available',
        FOREIGN KEY (`order`) REFERENCES `Order`(ID)
    )
''')

# Table Payment
cursor.execute('''
    CREATE TABLE Payment (
        `order` INTEGER,
        amount REAL,
        method TEXT,
        date TEXT,
        FOREIGN KEY (`order`) REFERENCES `Order`(ID)
    )
''')

# Insertion des articles par défaut
default_items = [
    ('Burger', 10),
    ('Pizza', 8),
    ('Pasta', 12),
    ('Salad', 15),
    ('Soda', 20),
    ('Fries', 15),
    ('Coffee', 25),
    ('Juice', 18)
]
cursor.executemany("INSERT INTO Item (Name, Inventory_Count) VALUES (?, ?)", default_items)

# Insertion des tables (1 à 10)
for i in range(1, 11):
    cursor.execute("INSERT INTO Tables (Table_number, `order`, active, status) VALUES (?, NULL, 'close', 'available')", (i,))

conn.commit()
conn.close()

print("✅ Base de données recréée avec succès !")
print("Tables créées : Item, Order, OrderItem, Tables, Payment")
print("Articles par défaut : Burger, Pizza, Pasta, Salad, Soda, Fries, Coffee, Juice")
print("Tables créées : 1 à 10")