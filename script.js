// script.js - VERSION CORRIGÉE

// ========== CONFIGURATION ==========
const API_BASE_URL = 'http://localhost:5000';
let currentRole = null;
let currentOrderId = null;
let currentTableNumber = null;
let currentTicketItems = [];
let menuItems = [];

// ========== INITIALISATION ==========
document.addEventListener('DOMContentLoaded', () => {
    loadMenuFromAPI();
});

// ========== API CALLS ==========
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = { 
        method, 
        headers: { 'Content-Type': 'application/json' },
        mode: 'cors'
    };
    if (data) options.body = JSON.stringify(data);
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`API Error:`, error.message);
        return null;
    }
}

// ========== AUTHENTIFICATION ==========
function login(role) {
    currentRole = role;
    document.getElementById('login-screen').classList.remove('active');
    document.getElementById('app-screen').classList.add('active');
    
    document.getElementById('current-user-badge').innerHTML = `<i class="fas fa-user"></i> ${getRoleName(role)}`;
    document.getElementById('back-to-manager').style.display = role === 'manager' ? 'inline-block' : 'none';
    
    showView(getDefaultView(role));
    loadRoleData(role);
}

function logout() {
    currentRole = null;
    currentOrderId = null;
    currentTableNumber = null;
    currentTicketItems = [];
    document.getElementById('app-screen').classList.remove('active');
    document.getElementById('login-screen').classList.add('active');
}

function getRoleName(role) {
    const names = { waiter: 'Serveur', chef: 'Chef Cuisinier', cashier: 'Caisse', manager: 'Manager' };
    return names[role] || role;
}

function getDefaultView(role) {
    const views = { waiter: 'waiter-view', chef: 'chef-view', cashier: 'cashier-view', manager: 'manager-view' };
    return views[role] || 'waiter-view';
}

function showView(viewId, isManagerOverride = false) {
    document.querySelectorAll('.role-view').forEach(view => view.style.display = 'none');
    document.getElementById(viewId).style.display = 'block';
    
    if (currentRole === 'manager' && isManagerOverride) {
        document.getElementById('manager-view').style.display = 'block';
        document.getElementById(viewId).style.display = 'block';
    }
    
    if (viewId === 'waiter-view') loadWaiterData();
    else if (viewId === 'chef-view') loadChefData();
    else if (viewId === 'cashier-view') loadCashierData();
    else if (viewId === 'manager-view') loadManagerData();
}

function loadRoleData(role) {
    if (role === 'waiter') loadWaiterData();
    else if (role === 'chef') loadChefData();
    else if (role === 'cashier') loadCashierData();
    else if (role === 'manager') loadManagerData();
}

// ========== CHARGEMENT DES DONNÉES ==========
async function loadMenuFromAPI() {
    try {
        const stock = await apiCall('/stock');
        if (stock && stock.length > 0) {
            menuItems = stock.map(item => ({
                name: item.name,
                price: getPriceForItem(item.name),
                count: item.count
            }));
        } else {
            menuItems = getDefaultMenu();
        }
    } catch (error) {
        console.error('Erreur chargement menu:', error);
        menuItems = getDefaultMenu();
    }
}

function getPriceForItem(name) {
    const prices = { 'Burger': 500, 'Pizza': 800, 'Pasta': 600, 'Salad': 400, 'Soda': 200, 'Fries': 250, 'Coffee': 150, 'Juice': 300 };
    return prices[name] || 300;
}

function getDefaultMenu() {
    return [
        { name: 'Burger', price: 500, count: 10 },
        { name: 'Pizza', price: 800, count: 5 },
        { name: 'Pasta', price: 600, count: 7 },
        { name: 'Salad', price: 400, count: 8 },
        { name: 'Soda', price: 200, count: 20 }
    ];
}

// ========== 1 - SERVEUR (CORRIGÉ - PAS DE DOUBLONS) ==========

async function loadWaiterData() {
    await loadTablesForWaiter();
    await loadMenuForWaiter();
    updateTicketDisplay();
}

async function loadTablesForWaiter() {
    const tables = await apiCall('/tables');
    const container = document.getElementById('waiter-tables');
    if (!container) return;
    
    // NETTOYER COMPLÈTEMENT LE CONTENEUR
    container.innerHTML = '';
    
    if (!tables || tables.length === 0) {
        container.innerHTML = '<p class="text-muted">Aucune table disponible.</p>';
        return;
    }
    
    // Créer un Set pour éviter les doublons
    const uniqueTables = new Map();
    tables.forEach(table => {
        if (!uniqueTables.has(table.table_number)) {
            uniqueTables.set(table.table_number, table);
        }
    });
    
    const orderPromises = Array.from(uniqueTables.values()).map(table => 
        apiCall(`/tables/${table.table_number}/order`)
    );
    const orders = await Promise.all(orderPromises);
    
    let index = 0;
    for (const table of uniqueTables.values()) {
        const order = orders[index];
        const statusClass = table.status === 'available' ? 'status-available' : 
                           (table.status === 'occupied' ? 'status-occupied' : 'status-reserved');
        
        const isCurrentTable = (currentTableNumber === table.table_number);
        const highlightStyle = isCurrentTable ? 'border: 2px solid #065f46; background: #e8f5e9;' : '';
        
        const card = document.createElement('div');
        card.className = `table-card ${statusClass}`;
        card.style.cssText = highlightStyle;
        card.innerHTML = `
            <strong>T${table.table_number}</strong><br>
            ${table.status === 'available' ? 'Libre' : (table.status === 'occupied' ? 'Occupée' : 'Réservée')}
            ${order ? `<br><small>#${order.id}</small>` : ''}
            <br>
            <button type="button" onclick="selectTableForOrder(${table.table_number}, ${order?.id || 'null'})" class="btn-small btn-primary" style="margin-top:5px">
                ${order ? 'Continuer' : 'Nouvelle commande'}
            </button>
        `;
        container.appendChild(card);
        index++;
    }
}

async function selectTableForOrder(tableNumber, existingOrderId) {
    currentTableNumber = tableNumber;
    
    if (existingOrderId && existingOrderId !== null && existingOrderId !== 'null') {
        currentOrderId = existingOrderId;
        await loadOrderItems(currentOrderId);
    } else {
        const newOrderId = Date.now();
        const result = await apiCall('/orders', 'POST', { 
            order_id: newOrderId, 
            table_number: tableNumber 
        });
        
        if (result && result.success) {
            currentOrderId = result.order_id || newOrderId;
            currentTicketItems = [];
        } else {
            alert('Erreur lors de la création de la commande');
            return;
        }
    }
    
    const headerDiv = document.getElementById('ticket-table-header');
    if (headerDiv) {
        headerDiv.style.display = 'block';
        headerDiv.innerHTML = `<strong>Table ${tableNumber}</strong> - Commande #${currentOrderId}`;
    }
    
    updateTicketDisplay();
    await loadTablesForWaiter();
}

async function loadOrderItems(orderId) {
    const items = await apiCall(`/orders/${orderId}/items`);
    if (items && Array.isArray(items)) {
        currentTicketItems = items.map(item => ({
            name: item.name,
            id: item.id,
            price: item.price,
            count: item.count,
            options: item.options || ''
        }));
    } else {
        currentTicketItems = [];
    }
    updateTicketDisplay();
}

function loadMenuForWaiter() {
    const container = document.querySelector('#waiter-view .menu-grid');
    if (!container) return;
    
    container.innerHTML = '<h3>Menu</h3><div class="menu-items-grid"></div>';
    const grid = container.querySelector('.menu-items-grid');
    
    if (!menuItems || menuItems.length === 0) {
        grid.innerHTML = '<p class="text-muted">Chargement du menu...</p>';
        return;
    }
    
    grid.innerHTML = '';
    menuItems.forEach(item => {
        const menuCard = document.createElement('div');
        menuCard.className = 'menu-card';
        menuCard.innerHTML = `
            <h4>${item.name}</h4>
            <p>${item.price} DZD</p>
            <p><small>Stock: ${item.count}</small></p>
            <button type="button" onclick="addToTicket('${item.name}', ${item.price})" class="btn-primary btn-small">
                <i class="fas fa-plus"></i> Ajouter
            </button>
        `;
        grid.appendChild(menuCard);
    });
}

async function addToTicket(name, price) {
    if (!currentOrderId) {
        alert('Veuillez d\'abord sélectionner une table');
        return;
    }
    
    const existingItem = currentTicketItems.find(i => i.name === name);
    
    if (existingItem) {
        existingItem.count++;
    } else {
        const newItem = {
            name: name,
            id: `${name}_${Date.now()}_${Math.random()}`,
            price: price,
            count: 1,
            options: ''
        };
        currentTicketItems.push(newItem);
    }
    
    updateTicketDisplay();
    
    try {
        if (existingItem) {
            await apiCall(`/orders/${currentOrderId}/items/${encodeURIComponent(name)}`, 'PUT', { 
                count: existingItem.count 
            });
        } else {
            const newItem = currentTicketItems.find(i => i.name === name);
            await apiCall(`/orders/${currentOrderId}/items`, 'POST', {
                name: newItem.name,
                id: newItem.id,
                price: newItem.price,
                count: newItem.count,
                options: newItem.options
            });
        }
    } catch (error) {
        console.error('API error:', error);
    }
}

function updateTicketDisplay() {
    const container = document.getElementById('current-ticket-items');
    const totalSpan = document.getElementById('ticket-total');
    
    if (!container) return;
    
    if (!currentTicketItems || currentTicketItems.length === 0) {
        container.innerHTML = '<p class="text-muted">Aucun article ajouté</p>';
        if (totalSpan) totalSpan.textContent = '0 DZD';
        return;
    }
    
    let total = 0;
    container.innerHTML = '';
    
    currentTicketItems.forEach((item, index) => {
        const itemTotal = (item.price || 0) * (item.count || 0);
        total += itemTotal;
        
        const itemDiv = document.createElement('div');
        itemDiv.className = 'ticket-item';
        itemDiv.innerHTML = `
            <span><strong>${item.name}</strong> ${item.options ? `(${item.options})` : ''}</span>
            <div>
                <button type="button" onclick="updateItemCount(${index}, -1)" class="btn-small">-</button>
                <span style="margin:0 10px">${item.count}</span>
                <button type="button" onclick="updateItemCount(${index}, 1)" class="btn-small">+</button>
                <span style="margin-left:15px">${itemTotal} DZD</span>
                <button type="button" onclick="removeFromTicket(${index})" class="btn-danger btn-small" style="margin-left:10px">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        container.appendChild(itemDiv);
    });
    
    if (totalSpan) totalSpan.textContent = `${total} DZD`;
}

async function updateItemCount(index, delta) {
    if (!currentTicketItems[index]) return;
    
    const item = currentTicketItems[index];
    const newCount = (item.count || 0) + delta;
    
    if (newCount <= 0) {
        currentTicketItems.splice(index, 1);
    } else {
        item.count = newCount;
    }
    
    updateTicketDisplay();
    
    try {
        if (newCount <= 0) {
            await apiCall(`/orders/${currentOrderId}/items/${encodeURIComponent(item.name)}`, 'DELETE');
        } else {
            await apiCall(`/orders/${currentOrderId}/items/${encodeURIComponent(item.name)}`, 'PUT', { count: newCount });
        }
    } catch (error) {
        console.error('API error:', error);
    }
}

async function removeFromTicket(index) {
    if (!currentTicketItems[index]) return;
    
    const item = currentTicketItems[index];
    currentTicketItems.splice(index, 1);
    updateTicketDisplay();
    
    try {
        await apiCall(`/orders/${currentOrderId}/items/${encodeURIComponent(item.name)}`, 'DELETE');
    } catch (error) {
        console.error('API error:', error);
    }
}

async function submitOrderToKitchen() {
    if (!currentOrderId) {
        alert('Aucune commande sélectionnée');
        return;
    }
    
    if (!currentTicketItems || currentTicketItems.length === 0) {
        alert('Aucun article à envoyer');
        return;
    }
    
    const total = currentTicketItems.reduce((sum, item) => sum + ((item.price || 0) * (item.count || 0)), 0);
    
    await apiCall(`/orders/${currentOrderId}/calculate-total`, 'POST');
    const statusResult = await apiCall(`/orders/${currentOrderId}/status`, 'PUT', { status: 'SENT_TO_KITCHEN' });
    
    if (statusResult && statusResult.success) {
        alert(`Commande #${currentOrderId} envoyée en cuisine ! Total: ${total} DZD`);
        
        currentTicketItems = [];
        currentOrderId = null;
        currentTableNumber = null;
        updateTicketDisplay();
        
        const headerDiv = document.getElementById('ticket-table-header');
        if (headerDiv) headerDiv.style.display = 'none';
        
        await loadTablesForWaiter();
    } else {
        alert('Erreur lors de l\'envoi en cuisine');
    }
}

// ========== 2 - CHEF CUISINIER (CORRIGÉ) ==========

async function loadChefData() {
    await loadKitchenOrders();
    await loadStockForChef();
}

async function loadKitchenOrders() {
    const container = document.getElementById('kitchen-orders-container');
    if (!container) return;
    
    container.innerHTML = '<h3>Commandes à préparer</h3>';
    
    try {
        const kitchenOrders = await apiCall('/kitchen/orders');
        
        if (!kitchenOrders || kitchenOrders.length === 0) {
            container.innerHTML += '<div class="text-muted">Aucune commande en cuisine</div>';
            return;
        }
        
        for (const order of kitchenOrders) {
            const ticketDiv = document.createElement('div');
            ticketDiv.className = 'ticket';
            
            let statusText = '';
            switch(order.status) {
                case 'OPEN': statusText = '🆕 Nouvelle commande'; break;
                case 'SENT_TO_KITCHEN': statusText = '📋 Envoyée en cuisine'; break;
                case 'PREPARING': statusText = '🍳 En préparation'; break;
                default: statusText = order.status;
            }
            
            let itemsHtml = '<ul style="margin-top: 10px;">';
            if (order.items && order.items.length > 0) {
                order.items.forEach(item => {
                    itemsHtml += `
                        <li style="padding: 8px 0; border-bottom: 1px solid #e2e8f0;">
                            <strong>${item.count}x ${item.name}</strong>
                            ${item.options ? `<br><small style="color: #666;">📝 ${item.options}</small>` : ''}
                            <span style="float: right;">${item.price * item.count} DZD</span>
                        </li>
                    `;
                });
            } else {
                itemsHtml += '<li style="color: #999;">⚠️ Aucun article trouvé</li>';
            }
            itemsHtml += '</ul>';
            
            const total = order.totalPrice || order.items.reduce((sum, item) => sum + (item.price * item.count), 0);
            
            ticketDiv.innerHTML = `
                <div style="background: #065f46; color: white; padding: 8px; border-radius: 8px 8px 0 0; margin: -15px -15px 10px -15px;">
                    <strong>🍽️ Table ${order.tableNumber}</strong> - Commande #${order.id}
                    <span style="float: right;">💰 ${total} DZD</span>
                </div>
                <div style="margin-bottom: 10px; padding: 5px; background: #fef3c7; border-radius: 5px;">
                    ${statusText}
                </div>
                ${itemsHtml}
                <div class="ticket-actions" style="margin-top: 15px;">
                    <button type="button" onclick="updateKitchenOrderStatus(${order.id}, 'PREPARING')" class="btn-warning">
                        🍳 Marquer en préparation
                    </button>
                    <button type="button" onclick="updateKitchenOrderStatus(${order.id}, 'READY')" class="btn-success">
                        ✅ Prêt à servir
                    </button>
                </div>
            `;
            container.appendChild(ticketDiv);
        }
    } catch (error) {
        console.error('Error loading kitchen orders:', error);
        container.innerHTML += '<div class="text-muted">❌ Erreur de chargement</div>';
    }
}

async function updateKitchenOrderStatus(orderId, status) {
    const result = await apiCall(`/orders/${orderId}/status`, 'PUT', { status: status });
    if (result && result.success) {
        await loadKitchenOrders();
    } else {
        alert('Erreur lors de la mise à jour');
    }
}

async function loadStockForChef() {
    const container = document.getElementById('chef-stock-list');
    if (!container) return;
    
    container.innerHTML = '<h3>État du Stock</h3>';
    
    try {
        const stock = await apiCall('/stock');
        
        if (!stock || stock.length === 0) {
            container.innerHTML += '<p class="text-muted">Aucun article en stock</p>';
            return;
        }
        
        stock.forEach(item => {
            const stockDiv = document.createElement('div');
            stockDiv.className = 'stock-item';
            const isLow = item.count < 5;
            stockDiv.innerHTML = `
                <span>
                    <strong>${item.name}</strong><br>
                    <small>📦 ${item.count} unités</small>
                    ${isLow ? '<span style="color: #dc2626; margin-left: 10px;">⚠️ Stock bas!</span>' : ''}
                </span>
                <div style="display: flex; gap: 5px;">
                    <button type="button" onclick="updateStockFromChef('${item.name}', ${item.count + 1})" class="btn-small btn-success">+</button>
                    <button type="button" onclick="updateStockFromChef('${item.name}', ${item.count - 1})" class="btn-small btn-warning">-</button>
                </div>
            `;
            container.appendChild(stockDiv);
        });
    } catch (error) {
        console.error('Error loading stock:', error);
        container.innerHTML += '<p class="text-muted">❌ Erreur de chargement</p>';
    }
}

async function updateStockFromChef(itemName, newCount) {
    if (newCount < 0) return;
    await apiCall(`/stock/${itemName}`, 'PUT', { count: newCount });
    await loadStockForChef();
}

// ========== 3 - CAISSE ==========
async function loadCashierData() {
    await loadTablesForCashier();
}

async function loadTablesForCashier() {
    const tables = await apiCall('/tables');
    const container = document.getElementById('cashier-tables');
    if (!container) return;
    
    container.innerHTML = '';
    if (!tables || tables.length === 0) {
        container.innerHTML = '<p class="text-muted">Aucune table disponible</p>';
        return;
    }
    
    const orderPromises = tables.map(table => apiCall(`/tables/${table.table_number}/order`));
    const orders = await Promise.all(orderPromises);
    
    for (let i = 0; i < tables.length; i++) {
        const table = tables[i];
        const order = orders[i];
        const statusClass = table.status === 'available' ? 'status-available' : 
                           (table.status === 'occupied' ? 'status-occupied' : 'status-reserved');
        
        const card = document.createElement('div');
        card.className = `table-card ${statusClass}`;
        card.innerHTML = `
            <strong>T${table.table_number}</strong><br>
            ${table.status}
            ${order ? `<br><small>Commande #${order.id}</small><br><strong>${order.totalPrice || 0} DZD</strong>` : '<br>Libre'}
            <br>
            ${order ? `<button type="button" onclick="openPaymentModal(${order.id}, ${order.totalPrice || 0})" class="btn-primary btn-small">💰 Encaisser</button>` : ''}
        `;
        container.appendChild(card);
    }
}

function openPaymentModal(orderId, amount) {
    const display = document.getElementById('calc-display');
    if (display) display.value = amount;
    currentOrderId = orderId;
}

async function processPayment() {
    const display = document.getElementById('calc-display');
    const methodSelect = document.getElementById('payment-method');
    
    const amount = display ? parseFloat(display.value) : 0;
    const method = methodSelect ? methodSelect.value : 'CASH';
    
    if (!currentOrderId || isNaN(amount) || amount <= 0) {
        alert('Montant invalide');
        return;
    }
    
    const result = await apiCall(`/orders/${currentOrderId}/pay`, 'POST', { amount: amount, method: method });
    
    if (result && result.success) {
        alert(`✅ Paiement effectué ! Monnaie: ${result.change || 0} DZD`);
        await loadTablesForCashier();
        currentOrderId = null;
        if (display) display.value = '0';
    } else {
        alert(result?.error || '❌ Erreur de paiement');
    }
}

function calc(value) {
    const display = document.getElementById('calc-display');
    if (!display) return;
    
    if (value === '=') {
        try {
            display.value = eval(display.value);
        } catch { display.value = 'Error'; }
    } else if (value === 'C') {
        display.value = '0';
    } else {
        if (display.value === '0' || display.value === 'Error') display.value = value;
        else display.value += value;
    }
}

// ========== 4 - MANAGER ==========
async function loadManagerData() {
    await Promise.all([
        loadManagerStats(),
        loadAllTablesManager(),
        loadAllOrdersManager(),
        loadAllStockManager()
    ]);
}

async function loadManagerStats() {
    const today = new Date().toISOString().split('T')[0];
    const [dailyRevenue, openOrders, bestSellers, inventory] = await Promise.all([
        apiCall(`/reports/daily-revenue?date=${today}`),
        apiCall('/reports/open-orders'),
        apiCall('/reports/best-selling?limit=5'),
        apiCall('/reports/inventory')
    ]);
    
    const lowStock = (inventory || []).filter(i => i.count < 5).length;
    
    const statsContainer = document.querySelector('#manager-view .dashboard-stats');
    if (statsContainer) {
        statsContainer.innerHTML = `
            <div class="stat-card"><h3>📊 Revenu du jour</h3><p>${dailyRevenue?.revenue || 0} DZD</p></div>
            <div class="stat-card"><h3>📋 Commandes Ouvertes</h3><p>${openOrders?.length || 0}</p></div>
            <div class="stat-card"><h3>⚠️ Ruptures/Risques</h3><p>${lowStock}</p></div>
        `;
    }
    
    const bestSellerContainer = document.getElementById('best-sellers');
    if (bestSellerContainer && bestSellers) {
        bestSellerContainer.innerHTML = '<h3>🏆 Meilleures ventes</h3>' + (bestSellers.map(i => `<p>${i.name}: ${i.total_sold} vendus</p>`).join('') || '<p>Aucune vente</p>');
    }
}

async function loadAllTablesManager() {
    const tables = await apiCall('/tables');
    const container = document.getElementById('manager-tables-list');
    if (!container) return;
    
    container.innerHTML = '<h3>Toutes les tables</h3><div class="tables-grid small"></div>';
    const grid = container.querySelector('.tables-grid');
    
    if (!tables || tables.length === 0) {
        grid.innerHTML = '<p class="text-muted">Aucune table</p>';
        return;
    }
    
    for (const table of tables) {
        const card = document.createElement('div');
        card.className = `table-card status-${table.status}`;
        card.innerHTML = `
            <strong>T${table.table_number}</strong><br>
            Status: ${table.status}
            <div style="margin-top:5px">
                <button type="button" onclick="updateTableStatus(${table.table_number}, 'available')" class="btn-small btn-success">Libérer</button>
                <button type="button" onclick="updateTableStatus(${table.table_number}, 'occupied')" class="btn-small btn-warning">Occuper</button>
                <button type="button" onclick="updateTableStatus(${table.table_number}, 'reserved')" class="btn-small btn-primary">Réserver</button>
            </div>
        `;
        grid.appendChild(card);
    }
}

async function updateTableStatus(tableId, status) {
    let endpoint;
    if (status === 'available') endpoint = `/tables/${tableId}/available`;
    else if (status === 'occupied') endpoint = `/tables/${tableId}/occupied`;
    else endpoint = `/tables/${tableId}/reserved`;
    
    await apiCall(endpoint, 'PUT');
    await loadAllTablesManager();
}

async function loadAllOrdersManager() {
    const orders = await apiCall('/orders');
    const container = document.getElementById('manager-orders-list');
    if (!container) return;
    
    container.innerHTML = '<h3>Toutes les commandes</h3><div class="orders-list"></div>';
    const list = container.querySelector('.orders-list');
    
    if (!orders || orders.length === 0) {
        list.innerHTML = '<p class="text-muted">Aucune commande</p>';
        return;
    }
    
    orders.forEach(order => {
        const orderDiv = document.createElement('div');
        orderDiv.className = 'order-item';
        orderDiv.innerHTML = `
            <div>
                <strong>#${order.id}</strong> - Table ${order.tableNumber} - ${order.status}<br>
                Total: ${order.totalPrice || 0} DZD
            </div>
            <div>
                <button type="button" onclick="cancelOrder(${order.id})" class="btn-danger btn-small">Annuler</button>
            </div>
        `;
        list.appendChild(orderDiv);
    });
}

async function loadAllStockManager() {
    const stock = await apiCall('/stock');
    const container = document.getElementById('manager-stock-list');
    if (!container) return;
    
    container.innerHTML = '<h3>Gestion du stock</h3><div class="stock-management"></div>';
    const list = container.querySelector('.stock-management');
    
    if (!stock || stock.length === 0) {
        list.innerHTML = '<p class="text-muted">Aucun article</p>';
        return;
    }
    
    stock.forEach(item => {
        const stockDiv = document.createElement('div');
        stockDiv.className = 'stock-item';
        stockDiv.innerHTML = `
            <span><strong>${item.name}</strong> : ${item.count}</span>
            <div>
                <input type="number" id="stock-${item.name.replace(/\s/g, '')}" value="${item.count}" style="width:70px">
                <button type="button" onclick="setStock('${item.name}', document.getElementById('stock-${item.name.replace(/\s/g, '')}').value)" class="btn-primary btn-small">Mettre à jour</button>
            </div>
        `;
        list.appendChild(stockDiv);
    });
}

async function setStock(itemName, count) {
    await apiCall(`/stock/${itemName}`, 'PUT', { count: parseInt(count) });
    await loadAllStockManager();
    await loadManagerStats();
}

async function cancelOrder(orderId) {
    if (confirm('Annuler cette commande ?')) {
        await apiCall(`/orders/${orderId}/cancel`, 'PUT');
        await loadAllOrdersManager();
        await loadManagerStats();
    }
}

async function addNewItemToMenu() {
    const name = prompt('Nom de l\'article:');
    const stock = prompt('Stock initial:');
    
    if (name && stock) {
        await apiCall(`/stock/${name}`, 'PUT', { count: parseInt(stock) });
        alert(`${name} ajouté au menu !`);
        await loadAllStockManager();
        await loadMenuFromAPI();
    }
}

async function addNewTable() {
    const tableId = prompt('Numéro de table:');
    if (tableId) {
        await apiCall('/tables', 'POST', { table_id: parseInt(tableId), order_id: null, active: 'close', status: 'available' });
        await loadAllTablesManager();
    }
}

async function checkHealth() {
    const health = await apiCall('/health');
    alert(health ? '✅ API OK' : '❌ API non disponible');
}