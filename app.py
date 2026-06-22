from flask import Flask, jsonify, request
from flask_cors import CORS
from logic import *

app = Flask(__name__)
CORS(app)


# ========== 1 - STOCK MANAGEMENT ==========

@app.route("/stock", methods=["GET"])
def get_current_inventory_api():
    """Récupère tout l'inventaire actuel"""
    items = get_current_inventory()
    return jsonify([{"name": item[0], "count": item[1]} for item in items])


@app.route("/stock/<string:name>/increase", methods=["POST"])
def increase_inventory_api(name):
    """Augmente le stock d'un article de 1"""
    success = increase_inventory(name)
    return jsonify({"success": success})


@app.route("/stock/<string:name>/decrease", methods=["POST"])
def decrease_inventory_api(name):
    """Diminue le stock d'un article de 1"""
    success = decrease_inventory(name)
    return jsonify({"success": success})


@app.route("/stock/<string:name>", methods=["PUT"])
def set_inventory_count_api(name):
    """
    Définit la quantité exacte d'un article en stock
    Body: {"count": nombre}
    """
    data = request.get_json()
    count = data.get('count')
    if count is None:
        return jsonify({"error": "count is required"}), 400
    success = set_inventory_count(name, count)
    return jsonify({"success": success})


@app.route("/stock/<string:name>", methods=["GET"])
def get_inventory_count_api(name):
    """Récupère la quantité d'un article spécifique"""
    count = get_inventory_count(name)
    if count is None:
        return jsonify({"error": "item not found"}), 404
    return jsonify({"name": name, "count": count})


@app.route("/stock/<string:name>/check", methods=["GET"])
def is_out_of_stock_api(name):
    """Vérifie si un article est en rupture de stock"""
    is_out = is_out_of_stock(name)
    return jsonify({"name": name, "out_of_stock": is_out})


# ========== 2 - ORDER ITEMS MANAGEMENT ==========

@app.route("/orders/<int:ord_id>/items", methods=["POST"])
def add_item_api(ord_id):
    """
    Ajoute un article à une commande
    Body: {"name": string, "id": string, "options": string, "price": number, "count": number}
    """
    data = request.get_json()
    print(f"=== DEBUG add_item_api ===")
    print(f"Order ID: {ord_id}")
    print(f"Data received: {data}")
    
    name = data.get('name')
    item_id = data.get('id')
    options = data.get('options', '')
    price = data.get('price')
    count = data.get('count')
    
    if not all([name, item_id, price, count is not None]):
        return jsonify({"error": "missing required fields: name, id, price, count"}), 400
    
    success = add_item(name, item_id, ord_id, options, price, count)
    print(f"Add item result: {success}")
    return jsonify({"success": success})

@app.route("/orders/<int:ord_id>/items/<string:name>", methods=["PUT"])
def update_item_api(ord_id, name):
    """
    Met à jour la quantité d'un article dans une commande
    Body: {"count": nombre}
    
    FONCTION update_item:
    ---------------------
    def update_item(order_id: int, item_name: str, new_count: int) -> bool:
        '''
        Met à jour la quantité d'un article dans une commande.
        
        Args:
            order_id: L'identifiant de la commande
            item_name: Le nom de l'article à modifier
            new_count: La nouvelle quantité (si <= 0, l'article est supprimé)
        
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        
        Exemple d'implémentation dans logic.py:
        ---------------------------------------
        def update_item(order_id, item_name, new_count):
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                if new_count <= 0:
                    # Supprimer l'article si quantité <= 0
                    cursor.execute(
                        "DELETE FROM order_items WHERE order_id = ? AND name = ?",
                        (order_id, item_name)
                    )
                else:
                    # Mettre à jour la quantité
                    cursor.execute(
                        "UPDATE order_items SET count = ? WHERE order_id = ? AND name = ?",
                        (new_count, order_id, item_name)
                    )
                
                # Mettre à jour le nombre total d'articles dans la commande
                cursor.execute(
                    "UPDATE orders SET itemNum = (SELECT COALESCE(SUM(count), 0) FROM order_items WHERE order_id = ?) WHERE id = ?",
                    (order_id, order_id)
                )
                
                conn.commit()
                return True
            except Exception as e:
                print(f"Error updating item: {e}")
                return False
            finally:
                conn.close()
    """
    data = request.get_json()
    count = data.get('count')
    if count is None:
        return jsonify({"error": "count is required"}), 400
    success = update_item(ord_id, name, count)
    return jsonify({"success": success})


@app.route("/orders/<int:ord_id>/items/<string:name>", methods=["DELETE"])
def delete_item_api(ord_id, name):
    """
    Supprime un article d'une commande
    
    FONCTION delete_item:
    ---------------------
    def delete_item(name: str, order_id: int) -> bool:
        '''
        Supprime un article d'une commande.
        
        Args:
            name: Le nom de l'article à supprimer
            order_id: L'identifiant de la commande
        
        Returns:
            bool: True si la suppression a réussi, False sinon
        '''
    """
    success = delete_item(name, ord_id)
    return jsonify({"success": success})


@app.route("/orders/<int:ord_id>/items/<string:name>", methods=["GET"])
def get_item_api(ord_id, name):
    """Récupère un article spécifique d'une commande"""
    item = get_item(ord_id, name)
    if item is None:
        return jsonify({"error": "item not found"}), 404
    return jsonify({
        "name": item[0], 
        "id": item[1], 
        "order": item[2], 
        "options": item[3], 
        "price": item[4], 
        "count": item[5]
    })


@app.route("/orders/<int:ord_id>/items", methods=["GET"])
def get_all_items_api(ord_id):
    """Récupère tous les articles d'une commande"""
    items = get_all_items(ord_id)
    return jsonify([
        {
            "name": item[0], 
            "id": item[1], 
            "order": item[2], 
            "options": item[3], 
            "price": item[4], 
            "count": item[5]
        } for item in items
    ])


@app.route("/orders/<int:ord_id>/items/<string:name>/options", methods=["POST"])
def add_item_option_api(ord_id, name):
    """
    Ajoute une option à un article
    Body: {"options": string}
    """
    data = request.get_json()
    op = data.get('options', '')
    success = add_item_option(ord_id, name, op)
    return jsonify({"success": success})


@app.route("/orders/<int:ord_id>/items/<string:name>/options", methods=["DELETE"])
def remove_item_option_api(ord_id, name):
    """Supprime toutes les options d'un article"""
    success = remove_item_option(ord_id, name)
    return jsonify({"success": success})


# ========== 3 - TABLE MANAGEMENT ==========

@app.route("/tables/<int:tab_id>/open", methods=["POST"])
def open_table_api(tab_id):
    """Ouvre une table"""
    success = open_table(tab_id)
    return jsonify({"success": success})


@app.route("/tables/<int:tab_id>/close", methods=["POST"])
def close_table_api(tab_id):
    """Ferme une table"""
    success = close_table(tab_id)
    return jsonify({"success": success})


@app.route("/tables", methods=["POST"])
def create_table_api():
    """
    Crée une nouvelle table
    Body: {"table_id": int, "order_id": int|null, "active": string, "status": string}
    """
    data = request.get_json()
    table_id = data.get('table_id')
    order_id = data.get('order_id')
    active = data.get('active', 'close')
    status = data.get('status', 'available')
    
    if table_id is None:
        return jsonify({"error": "table_id is required"}), 400
    
    # VÉRIFICATION SUPPLEMENTAIRE avant d'appeler create_table
    existing_tables = get_all_tables()
    for table in existing_tables:
        if table[0] == table_id:
            return jsonify({"success": True, "message": "Table already exists"}), 200
    
    success = create_table(table_id, order_id, active, status)
    return jsonify({"success": success})


@app.route("/tables/<int:tab_id>", methods=["DELETE"])
def delete_table_api(tab_id):
    """Supprime une table"""
    success = delete_table(tab_id)
    return jsonify({"success": success})


@app.route("/tables/<int:tab_id>", methods=["GET"])
def get_table_api(tab_id):
    """Récupère les informations d'une table"""
    table = get_table(tab_id)
    if table is None:
        return jsonify({"error": "table not found"}), 404
    return jsonify({
        "table_number": table[0], 
        "order": table[1], 
        "active": table[2], 
        "status": table[3]
    })


@app.route("/tables", methods=["GET"])
def get_all_tables_api():
    """Récupère toutes les tables"""
    tables = get_all_tables()
    return jsonify([
        {
            "table_number": table[0], 
            "order": table[1], 
            "active": table[2], 
            "status": table[3]
        } for table in tables
    ])


@app.route("/tables/<int:tab_id>/available", methods=["PUT"])
def set_table_available_api(tab_id):
    """Définit une table comme disponible"""
    success = set_table_available(tab_id)
    return jsonify({"success": success})


@app.route("/tables/<int:tab_id>/occupied", methods=["PUT"])
def set_table_occupied_api(tab_id):
    """Définit une table comme occupée"""
    success = set_table_occupied(tab_id)
    return jsonify({"success": success})


@app.route("/tables/<int:tab_id>/reserved", methods=["PUT"])
def set_table_reserved_api(tab_id):
    """Définit une table comme réservée"""
    success = set_table_reserved(tab_id)
    return jsonify({"success": success})


@app.route("/tables/transfer", methods=["POST"])
def transfer_table_api():
    """
    Transfère les données d'une table à une autre
    Body: {"tab1": int, "tab2": int}
    """
    data = request.get_json()
    tab1 = data.get('tab1')
    tab2 = data.get('tab2')
    
    if tab1 is None or tab2 is None:
        return jsonify({"error": "tab1 and tab2 are required"}), 400
    
    success = transfer_table(tab1, tab2)
    return jsonify({"success": success})


# ========== 4 - ORDER MANAGEMENT ==========

@app.route("/orders", methods=["POST"])
def create_order_api():
    """
    Crée une nouvelle commande
    Body: {"order_id": int, "table_number": int}
    """
    data = request.get_json()
    order_id = data.get('order_id')
    table_number = data.get('table_number')
    
    if order_id is None or table_number is None:
        return jsonify({"error": "order_id and table_number are required"}), 400
    
    result = create_order(order_id, table_number)
    return jsonify({"success": True, "order_id": result})


@app.route("/orders/<int:order_id>/open", methods=["PUT"])
def open_order_api(order_id):
    """Ouvre une commande"""
    success = open_order(order_id)
    return jsonify({"success": success})


@app.route("/orders/<int:order_id>/cancel", methods=["PUT"])
def cancel_order_api(order_id):
    """Annule une commande"""
    success = cancel_order(order_id)
    return jsonify({"success": success})


@app.route("/orders/<int:order_id>", methods=["DELETE"])
def delete_order_api(order_id):
    """Supprime une commande"""
    success = delete_order(order_id)
    return jsonify({"success": success})


@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order_api(order_id):
    """Récupère les informations d'une commande"""
    order = get_order(order_id)
    if order is None:
        return jsonify({"error": "order not found"}), 404
    return jsonify({
        "id": order[0], 
        "itemNum": order[1], 
        "totalPrice": order[2], 
        "tableNumber": order[3], 
        "status": order[4]
    })


@app.route("/orders", methods=["GET"])
def get_all_orders_api():
    """Récupère toutes les commandes"""
    orders = get_all_orders()
    return jsonify([
        {
            "id": order[0], 
            "itemNum": order[1], 
            "totalPrice": order[2], 
            "tableNumber": order[3], 
            "status": order[4]
        } for order in orders
    ])


@app.route("/tables/<int:table_number>/order", methods=["GET"])
def get_table_order_api(table_number):
    """Récupère la commande associée à une table"""
    order = get_table_order(table_number)
    if order is None:
        return jsonify({"error": "no order for this table"}), 404
    return jsonify({
        "id": order[0], 
        "itemNum": order[1], 
        "totalPrice": order[2], 
        "tableNumber": order[3], 
        "status": order[4]
    })


@app.route("/orders/<int:order_id>/calculate-total", methods=["POST"])
def calculate_order_total_api(order_id):
    """Calcule le total d'une commande"""
    total = calculate_order_total(order_id)
    return jsonify({"success": True, "total": total})


@app.route("/orders/<int:order_id>/discount", methods=["POST"])
def apply_discount_api(order_id):
    """
    Applique une remise sur une commande
    Body: {"discount_percent": number}
    """
    data = request.get_json()
    discount_percent = data.get('discount_percent')
    
    if discount_percent is None:
        return jsonify({"error": "discount_percent is required"}), 400
    
    new_total = apply_discount(order_id, discount_percent)
    if new_total is None:
        return jsonify({"error": "order not found"}), 404
    return jsonify({"success": True, "new_total": new_total})


@app.route("/orders/<int:order_id>/remove-discount", methods=["POST"])
def remove_discount_api(order_id):
    """Supprime la remise d'une commande"""
    total = remove_discount(order_id)
    if total is None:
        return jsonify({"error": "order not found"}), 404
    return jsonify({"success": True, "total": total})


@app.route("/orders/<int:order_id>/tax", methods=["POST"])
def add_tax_api(order_id):
    """
    Ajoute une taxe à une commande
    Body: {"tax_percent": number}
    """
    data = request.get_json()
    tax_percent = data.get('tax_percent')
    
    if tax_percent is None:
        return jsonify({"error": "tax_percent is required"}), 400
    
    new_total = add_tax(order_id, tax_percent)
    if new_total is None:
        return jsonify({"error": "order not found"}), 404
    return jsonify({"success": True, "new_total": new_total})


# ========== 5 - PAYMENT MANAGEMENT ==========

@app.route("/orders/<int:order_id>/pay", methods=["POST"])
def pay_order_api(order_id):
    """
    Effectue le paiement d'une commande
    Body: {"amount": number, "method": string}
    """
    data = request.get_json()
    amount = data.get('amount')
    method = data.get('method', 'CASH')
    
    if amount is None:
        return jsonify({"error": "amount is required"}), 400
    
    result = pay_order(order_id, amount, method)
    return jsonify(result)


@app.route("/orders/<int:order_id>/partial-pay", methods=["POST"])
def partial_payment_api(order_id):
    """
    Effectue un paiement partiel
    Body: {"amount": number, "method": string}
    """
    data = request.get_json()
    amount = data.get('amount')
    method = data.get('method', 'CASH')
    
    if amount is None:
        return jsonify({"error": "amount is required"}), 400
    
    result = partial_payment(order_id, amount, method)
    return jsonify(result)


@app.route("/orders/<int:order_id>/refund", methods=["POST"])
def refund_order_api(order_id):
    """
    Effectue un remboursement
    Body: {"amount": number}
    """
    data = request.get_json()
    amount = data.get('amount')
    
    if amount is None:
        return jsonify({"error": "amount is required"}), 400
    
    success = refund_order(order_id, amount)
    return jsonify({"success": success})


@app.route("/orders/<int:order_id>/receipt", methods=["GET"])
def generate_receipt_api(order_id):
    """Génère un reçu pour une commande"""
    receipt = generate_receipt(order_id)
    if receipt is None:
        return jsonify({"error": "order not found"}), 404
    return jsonify(receipt)


@app.route("/orders/<int:order_id>/pay-cash", methods=["POST"])
def pay_cash_api(order_id):
    """
    Paiement en espèces
    Body: {"amount": number}
    """
    data = request.get_json()
    amount = data.get('amount')
    
    if amount is None:
        return jsonify({"error": "amount is required"}), 400
    
    result = pay_cash(order_id, amount)
    return jsonify(result)


@app.route("/orders/<int:order_id>/pay-card", methods=["POST"])
def pay_card_api(order_id):
    """
    Paiement par carte
    Body: {"amount": number}
    """
    data = request.get_json()
    amount = data.get('amount')
    
    if amount is None:
        return jsonify({"error": "amount is required"}), 400
    
    result = pay_card(order_id, amount)
    return jsonify(result)


@app.route("/orders/<int:order_id>/pay-mobile", methods=["POST"])
def pay_mobile_api(order_id):
    """
    Paiement mobile
    Body: {"amount": number}
    """
    data = request.get_json()
    amount = data.get('amount')
    
    if amount is None:
        return jsonify({"error": "amount is required"}), 400
    
    result = pay_mobile(order_id, amount)
    return jsonify(result)


# ========== 6 - TABLE SERVICE ==========

@app.route("/orders/<int:order_id>/move", methods=["POST"])
def move_order_to_table_api(order_id):
    """
    Déplace une commande vers une autre table
    Body: {"new_table": int}
    """
    data = request.get_json()
    new_table = data.get('new_table')
    
    if new_table is None:
        return jsonify({"error": "new_table is required"}), 400
    
    success = move_order_to_table(order_id, new_table)
    return jsonify({"success": success})


@app.route("/orders/merge", methods=["POST"])
def merge_orders_api():
    """
    Fusionne deux commandes
    Body: {"order_id_1": int, "order_id_2": int}
    """
    data = request.get_json()
    order_id_1 = data.get('order_id_1')
    order_id_2 = data.get('order_id_2')
    
    if order_id_1 is None or order_id_2 is None:
        return jsonify({"error": "order_id_1 and order_id_2 are required"}), 400
    
    success = merge_orders(order_id_1, order_id_2)
    return jsonify({"success": success})


@app.route("/orders/<int:order_id>/split", methods=["POST"])
def split_order_api(order_id):
    """
    Divise une commande en deux
    Body: {"items_to_split": list of strings}
    """
    data = request.get_json()
    items_to_split = data.get('items_to_split', [])
    
    if not items_to_split:
        return jsonify({"error": "items_to_split is required"}), 400
    
    new_id = split_order(order_id, items_to_split)
    return jsonify({"success": True, "new_order_id": new_id})


@app.route("/orders/transfer-items", methods=["POST"])
def transfer_items_between_orders_api():
    """
    Transfère des articles entre deux commandes
    Body: {"from_order": int, "to_order": int, "items_to_transfer": list}
    """
    data = request.get_json()
    from_order = data.get('from_order')
    to_order = data.get('to_order')
    items_to_transfer = data.get('items_to_transfer', [])
    
    if from_order is None or to_order is None or not items_to_transfer:
        return jsonify({"error": "from_order, to_order, and items_to_transfer are required"}), 400
    
    success = transfer_items_between_orders(from_order, to_order, items_to_transfer)
    return jsonify({"success": success})


# ========== 7 - KITCHEN MANAGEMENT ==========

@app.route("/orders/<int:order_id>/send-kitchen", methods=["PUT"])
def send_order_to_kitchen_api(order_id):
    """Envoie une commande en cuisine"""
    success = send_order_to_kitchen(order_id)
    return jsonify({"success": success})


@app.route("/orders/<int:order_id>/preparing", methods=["PUT"])
def mark_preparing_api(order_id):
    """Marque une commande comme étant en préparation"""
    success = mark_preparing(order_id)
    return jsonify({"success": success})


@app.route("/orders/<int:order_id>/ready", methods=["PUT"])
def mark_ready_api(order_id):
    """Marque une commande comme prête"""
    success = mark_ready(order_id)
    return jsonify({"success": success})


@app.route("/orders/<int:order_id>/served", methods=["PUT"])
def mark_served_api(order_id):
    """Marque une commande comme servie"""
    success = mark_served(order_id)
    return jsonify({"success": success})


@app.route("/kitchen/orders", methods=["GET"])
def get_kitchen_orders_api():
    """Récupère les commandes en cuisine avec leurs articles"""
    orders = get_kitchen_orders_with_items()
    return jsonify(orders)

# ========== 7b - ORDER STATUS (Unified Endpoint) ==========

@app.route("/orders/<int:order_id>/status", methods=["PUT"])
def update_order_status_api(order_id):
    """
    Endpoint unifié pour mettre à jour le statut d'une commande
    Body: {"status": string}
    
    Statuts possibles:
    - SENT_TO_KITCHEN: Envoyer en cuisine
    - PREPARING: Marquer comme en préparation
    - READY: Marquer comme prêt
    - SERVED: Marquer comme servi
    - OPEN: Ouvrir la commande
    - CANCELLED: Annuler la commande
    """
    data = request.get_json()
    status = data.get('status')
    
    if not status:
        return jsonify({"error": "status is required"}), 400
    
    status = status.upper()
    
    try:
        if status == 'SENT_TO_KITCHEN':
            success = send_order_to_kitchen(order_id)
        elif status == 'PREPARING':
            success = mark_preparing(order_id)
        elif status == 'READY':
            success = mark_ready(order_id)
        elif status == 'SERVED':
            success = mark_served(order_id)
        elif status == 'OPEN':
            success = open_order(order_id)
        elif status == 'CANCELLED':
            success = cancel_order(order_id)
        else:
            return jsonify({"error": f"Unknown status: {status}"}), 400
        
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========== 8 - REPORTS ==========

@app.route("/reports/daily-revenue", methods=["GET"])
def get_daily_revenue_api():
    """
    Calcule le chiffre d'affaires quotidien
    Query param: date (format YYYY-MM-DD)
    """
    date = request.args.get('date')
    if not date:
        return jsonify({"error": "date parameter is required"}), 400
    
    revenue = get_daily_revenue(date)
    return jsonify({"date": date, "revenue": revenue})


@app.route("/reports/monthly-revenue", methods=["GET"])
def get_monthly_revenue_api():
    """
    Calcule le chiffre d'affaires mensuel
    Query param: year_month (format YYYY-MM)
    """
    year_month = request.args.get('year_month')
    if not year_month:
        return jsonify({"error": "year_month parameter is required"}), 400
    
    revenue = get_monthly_revenue(year_month)
    return jsonify({"year_month": year_month, "revenue": revenue})


@app.route("/reports/best-selling", methods=["GET"])
def get_best_selling_items_api():
    """
    Récupère les articles les plus vendus
    Query param: limit (default: 10)
    """
    limit = request.args.get('limit', 10, type=int)
    items = get_best_selling_items(limit)
    return jsonify([{"name": item[0], "total_sold": item[1]} for item in items])


@app.route("/reports/inventory", methods=["GET"])
def get_inventory_report_api():
    """Rapport d'inventaire"""
    items = get_inventory_report()
    return jsonify([{"name": item[0], "count": item[1]} for item in items])


@app.route("/reports/open-orders", methods=["GET"])
def get_open_orders_api():
    """Récupère les commandes ouvertes"""
    orders = get_open_orders()
    return jsonify([{"id": order[0], "tableNumber": order[1]} for order in orders])


@app.route("/reports/paid-orders", methods=["GET"])
def get_paid_orders_api():
    """Récupère les commandes payées"""
    orders = get_paid_orders()
    return jsonify([{"id": order[0], "tableNumber": order[1], "totalPrice": order[2]} for order in orders])


# ========== HEALTH CHECK ==========

@app.route("/health", methods=["GET"])
def health_check():
    """Vérifie que l'API est opérationnelle"""
    return jsonify({"status": "ok", "message": "API is running"})


# ========== DÉMARRAGE DE L'APPLICATION ==========

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)