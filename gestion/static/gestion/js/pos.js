// Point of Sale JavaScript
class POS {
    constructor() {
        this.cart = [];
        this.currentCategory = 'all';
        this.init();
    }

    init() {
        this.loadCart();
        this.attachEventListeners();
        this.renderCart();
        this.updateTicketNumber();
    }

    attachEventListeners() {
        // Product cards click
        document.querySelectorAll('.product-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const productId = card.dataset.productId;
                const productName = card.dataset.productName;
                const productPrice = parseFloat(card.dataset.productPrice);
                this.addToCart(productId, productName, productPrice);
            });
        });

        // Category tabs
        document.querySelectorAll('.category-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.filterByCategory(tab.dataset.category);
            });
        });

        // Search
        const searchInput = document.querySelector('.search-input');
        const searchBtn = document.querySelector('.btn-search');
        if (searchInput && searchBtn) {
            searchBtn.addEventListener('click', () => this.searchProducts());
            searchInput.addEventListener('keyup', (e) => {
                if (e.key === 'Enter') this.searchProducts();
            });
        }

        // Payment button
        const payBtn = document.querySelector('.btn-pay');
        if (payBtn) {
            payBtn.addEventListener('click', () => this.processPayment());
        }
    }

    addToCart(productId, productName, productPrice) {
        const existingItem = this.cart.find(item => item.id === productId);

        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.cart.push({
                id: productId,
                name: productName,
                price: productPrice,
                quantity: 1
            });
        }

        this.saveCart();
        this.renderCart();
        this.showNotification(`${productName} agregado al pedido`);
    }

    removeFromCart(productId) {
        this.cart = this.cart.filter(item => item.id !== productId);
        this.saveCart();
        this.renderCart();
    }

    updateQuantity(productId, change) {
        const item = this.cart.find(item => item.id === productId);
        if (item) {
            item.quantity += change;
            if (item.quantity <= 0) {
                this.removeFromCart(productId);
            } else {
                this.saveCart();
                this.renderCart();
            }
        }
    }

    renderCart() {
        const orderItems = document.querySelector('.order-items');
        const emptyState = document.querySelector('.empty-order');

        if (this.cart.length === 0) {
            if (orderItems) orderItems.innerHTML = '';
            if (emptyState) emptyState.style.display = 'block';
            this.updateTotals(0, 0);
            return;
        }

        if (emptyState) emptyState.style.display = 'none';

        let html = '';
        let subtotal = 0;

        this.cart.forEach(item => {
            const itemTotal = item.price * item.quantity;
            subtotal += itemTotal;

            html += `
                <div class="order-item" data-product-id="${item.id}">
                    <div class="col-name" title="${item.name}">${item.name}</div>
                    <div class="col-qty">
                        <div class="qty-controls">
                            <button class="btn-qty-minus" onclick="pos.updateQuantity('${item.id}', -1)" title="Disminuir cantidad">-</button>
                            <span class="qty-value">${item.quantity}</span>
                            <button class="btn-qty-plus" onclick="pos.updateQuantity('${item.id}', 1)" title="Aumentar cantidad">+</button>
                        </div>
                    </div>
                    <div class="col-price">Bs. ${item.price.toFixed(2)}</div>
                    <div class="col-total">Bs. ${itemTotal.toFixed(2)}</div>
                    <div class="col-actions">
                        <button class="btn-remove" onclick="pos.removeFromCart('${item.id}')" title="Eliminar producto">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
            `;
        });

        if (orderItems) orderItems.innerHTML = html;
        this.updateTotals(subtotal, subtotal);
    }

    updateTotals(subtotal, total) {
        const subtotalEl = document.querySelector('.subtotal-amount');
        const totalEl = document.querySelector('.total-amount');

        if (subtotalEl) subtotalEl.textContent = `Bs. ${subtotal.toFixed(2)}`;
        if (totalEl) totalEl.textContent = `Bs. ${total.toFixed(2)}`;
    }

    filterByCategory(category) {
        this.currentCategory = category;

        // Update active tab
        document.querySelectorAll('.category-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.category === category);
        });

        // Filter products
        document.querySelectorAll('.product-card').forEach(card => {
            if (category === 'all' || card.dataset.category === category) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    searchProducts() {
        const searchInput = document.querySelector('.search-input');
        const searchTerm = searchInput.value.toLowerCase();

        document.querySelectorAll('.product-card').forEach(card => {
            const productName = card.dataset.productName.toLowerCase();
            if (productName.includes(searchTerm)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });

        // Reset category filter
        this.currentCategory = 'all';
        document.querySelectorAll('.category-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.category === 'all');
        });
    }

    processPayment() {
        if (this.cart.length === 0) {
            alert('El carrito está vacío');
            return;
        }

        // Calculate total
        const total = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

        // Update modal totals
        document.querySelector('.modal-subtotal').textContent = `Bs. ${total.toFixed(2)}`;
        document.querySelector('.modal-total').textContent = `Bs. ${total.toFixed(2)}`;

        // Show modal
        this.openPaymentModal();
    }

    openPaymentModal() {
        const modal = document.getElementById('paymentModal');
        if (modal) {
            modal.style.display = 'block';

            // Setup form submission
            const form = document.getElementById('paymentForm');
            form.onsubmit = (e) => {
                e.preventDefault();
                this.submitPayment();
            };
        }
    }

    closePaymentModal() {
        const modal = document.getElementById('paymentModal');
        if (modal) {
            modal.style.display = 'none';
            document.getElementById('paymentForm').reset();
        }
    }

    async submitPayment() {
        const clienteId = document.getElementById('cliente_select').value;
        const metodoPagoId = document.getElementById('metodo_pago_select').value;

        if (!clienteId || !metodoPagoId) {
            alert('Por favor complete todos los campos');
            return;
        }

        const confirmBtn = document.querySelector('.btn-confirm');
        const originalText = confirmBtn.innerHTML;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        confirmBtn.disabled = true;

        try {
            const response = await fetch(window.posData.procesarPagoUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.posData.csrfToken
                },
                body: JSON.stringify({
                    cliente_id: clienteId,
                    metodo_pago_id: metodoPagoId,
                    items: this.cart
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('✓ Venta procesada exitosamente');
                this.closePaymentModal();

                // Clear cart
                this.cart = [];
                this.saveCart();
                this.renderCart();

                // Show success message
                setTimeout(() => {
                    alert(`Venta #${data.venta_id} completada\nTotal: Bs. ${data.total}`);
                }, 300);
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al procesar el pago. Por favor intente nuevamente.');
        } finally {
            confirmBtn.innerHTML = originalText;
            confirmBtn.disabled = false;
        }
    }


    saveCart() {
        localStorage.setItem('posCart', JSON.stringify(this.cart));
    }

    loadCart() {
        const saved = localStorage.getItem('posCart');
        if (saved) {
            this.cart = JSON.parse(saved);
        }
    }

    updateTicketNumber() {
        const ticketEl = document.querySelector('.ticket-number');
        if (ticketEl) {
            const ticketNum = Math.floor(Math.random() * 1000) + 1;
            ticketEl.textContent = `Ticket N°${ticketNum}`;
        }
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    showNotification(message) {
        // Simple notification - could be enhanced with a toast library
        const notification = document.createElement('div');
        notification.className = 'pos-notification';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 9999;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
    .btn-qty-minus, .btn-qty-plus {
        background: var(--panchita-yellow);
        border: none;
        padding: 0.25rem 0.5rem;
        margin: 0 0.25rem;
        border-radius: 4px;
        cursor: pointer;
        font-weight: bold;
    }
    .btn-qty-minus:hover, .btn-qty-plus:hover {
        background: #f4c430;
    }
`;
document.head.appendChild(style);

// Initialize POS when DOM is ready
let pos;
document.addEventListener('DOMContentLoaded', () => {
    pos = new POS();
});
