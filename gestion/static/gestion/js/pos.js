// Point of Sale JavaScript
class POS {
    constructor() {
        this.cart = [];
        this.currentCategory = 'all';
        this.clienteSearchTimeout = null;
        this.init();
    }

    init() {
        this.loadCart();
        this.attachEventListeners();
        this.renderCart();
        this.updateTicketNumber(); // Usa siguiente_ticket del servidor (consecutivo con ventas)
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

        // Un solo campo: buscar y elegir cliente (dropdown de resultados)
        const clienteSearch = document.getElementById('cliente_search');
        const clienteDropdown = document.getElementById('cliente_dropdown');
        if (clienteSearch) {
            clienteSearch.addEventListener('input', () => {
                const hid = document.getElementById('cliente_id_hidden');
                if (hid) hid.value = '';
                clearTimeout(this.clienteSearchTimeout);
                this.clienteSearchTimeout = setTimeout(() => {
                    this.searchClientesDropdown(clienteSearch.value.trim());
                }, 300);
            });
            clienteSearch.addEventListener('focus', () => {
                if (clienteSearch.value.trim()) this.searchClientesDropdown(clienteSearch.value.trim());
                else this.searchClientesDropdown('');
            });
        }
        document.addEventListener('click', (e) => {
            const wrap = document.querySelector('.cliente-search-wrap');
            const dd = document.getElementById('cliente_dropdown');
            if (dd && wrap && !wrap.contains(e.target) && !dd.contains(e.target)) this.hideClienteDropdown();
        });

        // Crear cliente nuevo - mostrar formulario
        const btnNuevoCliente = document.getElementById('btnNuevoCliente');
        if (btnNuevoCliente) {
            btnNuevoCliente.addEventListener('click', () => this.toggleNuevoClienteForm(true));
        }
        const btnCancelarCliente = document.getElementById('btnCancelarCliente');
        if (btnCancelarCliente) {
            btnCancelarCliente.addEventListener('click', () => this.toggleNuevoClienteForm(false));
        }
        const btnGuardarCliente = document.getElementById('btnGuardarCliente');
        if (btnGuardarCliente) {
            btnGuardarCliente.addEventListener('click', () => this.saveNewCliente());
        }
        // Venta Mostrador: pre-selecciona cliente para ventas rápidas
        const btnVentaMostrador = document.getElementById('btnVentaMostrador');
        if (btnVentaMostrador && window.posData && window.posData.clienteMostradorId) {
            btnVentaMostrador.addEventListener('click', () => {
                const tipoDoc = document.querySelector('input[name="tipo_documento"]:checked');
                if (tipoDoc && tipoDoc.value === 'factura') {
                    if (typeof showAlertModal === 'function') showAlertModal('Para factura debe seleccionar un cliente con NIT/CI. No puede usar Mostrador.', 'warning');
                    else alert('Para factura debe seleccionar un cliente con NIT/CI. No puede usar Mostrador.');
                    return;
                }
                document.getElementById('cliente_id_hidden').value = window.posData.clienteMostradorId;
                document.getElementById('cliente_search').value = 'Mostrador';
                this.hideClienteDropdown();
                this.toggleNuevoClienteForm(false);
            });
        }
        // Tipo documento: mostrar requisito para factura
        document.querySelectorAll('input[name="tipo_documento"]').forEach(radio => {
            radio.addEventListener('change', () => {
                const facturaRequisito = document.getElementById('factura_requisito');
                if (facturaRequisito) facturaRequisito.style.display = radio.value === 'factura' ? 'block' : 'none';
                if (radio.value === 'factura') {
                    const clienteId = document.getElementById('cliente_id_hidden').value;
                    if (clienteId && clienteId == window.posData?.clienteMostradorId) {
                        document.getElementById('cliente_id_hidden').value = '';
                        document.getElementById('cliente_search').value = '';
                    }
                }
            });
        });
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
            if (typeof showAlertModal === 'function') showAlertModal('El carrito está vacío', 'warning');
            else alert('El carrito está vacío');
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
            this.toggleNuevoClienteForm(false);
            const clienteSearch = document.getElementById('cliente_search');
            const clienteIdHidden = document.getElementById('cliente_id_hidden');
            if (clienteSearch) clienteSearch.value = '';
            if (clienteIdHidden) clienteIdHidden.value = '';
            this.hideClienteDropdown();

            const form = document.getElementById('paymentForm');
            form.onsubmit = (e) => {
                e.preventDefault();
                this.submitPayment();
            };
        }
    }

    showVentaCompletadaModal(ventaId, total) {
        const modal = document.getElementById('ventaCompletadaModal');
        const idEl = document.getElementById('ventaCompletadaId');
        const totalEl = document.getElementById('ventaCompletadaTotal');
        const btnTicket = document.getElementById('btnVerImprimirTicket');
        if (modal && idEl && totalEl) {
            idEl.textContent = '#' + ventaId;
            totalEl.textContent = total || '0.00';
            if (btnTicket && window.posData && window.posData.ventaDetailUrl) {
                const path = window.posData.ventaDetailUrl.replace(/\/0\/$/, '/' + ventaId + '/');
                btnTicket.href = path.startsWith('http') ? path : (window.location.origin + path);
            }
            modal.style.display = 'block';
        }
    }

    closeVentaCompletadaModal() {
        const modal = document.getElementById('ventaCompletadaModal');
        if (modal) modal.style.display = 'none';
    }

    closePaymentModal() {
        const modal = document.getElementById('paymentModal');
        if (modal) {
            modal.style.display = 'none';
            document.getElementById('paymentForm').reset();
            const clienteSearch = document.getElementById('cliente_search');
            const clienteIdHidden = document.getElementById('cliente_id_hidden');
            if (clienteSearch) clienteSearch.value = '';
            if (clienteIdHidden) clienteIdHidden.value = '';
            this.toggleNuevoClienteForm(false);
            this.hideClienteDropdown();
        }
    }

    hideClienteDropdown() {
        const dd = document.getElementById('cliente_dropdown');
        if (dd) dd.style.display = 'none';
    }

    async searchClientesDropdown(q) {
        const dropdown = document.getElementById('cliente_dropdown');
        if (!dropdown || !window.posData || !window.posData.buscarClientesUrl) return;
        try {
            const url = window.posData.buscarClientesUrl + (q ? '?q=' + encodeURIComponent(q) : '');
            const response = await fetch(url);
            const data = await response.json();
            const clientes = data.clientes || [];
            dropdown.innerHTML = '';
            if (clientes.length === 0) {
                dropdown.innerHTML = '<div class="cliente-dropdown-empty">No hay clientes. Use el botón + para crear uno.</div>';
            } else {
                clientes.forEach(c => {
                    const item = document.createElement('div');
                    item.className = 'cliente-dropdown-item';
                    item.dataset.id = c.id;
                    item.textContent = c.nombre_completo + (c.telefono ? ' — ' + c.telefono : '');
                    item.addEventListener('click', () => {
                        document.getElementById('cliente_id_hidden').value = c.id;
                        document.getElementById('cliente_search').value = c.nombre_completo + (c.telefono ? ' — ' + c.telefono : '');
                        this.hideClienteDropdown();
                    });
                    dropdown.appendChild(item);
                });
            }
            dropdown.style.display = 'block';
        } catch (err) {
            console.error('Error buscando clientes:', err);
            dropdown.innerHTML = '<div class="cliente-dropdown-empty">Error al buscar.</div>';
            dropdown.style.display = 'block';
        }
    }

    toggleNuevoClienteForm(show) {
        const form = document.getElementById('nuevoClienteForm');
        if (form) form.style.display = show ? 'block' : 'none';
    }

    async saveNewCliente() {
        const nombre = (document.getElementById('nuevo_cliente_nombre') || {}).value.trim();
        if (!nombre) {
            if (typeof showAlertModal === 'function') showAlertModal('El nombre del cliente es obligatorio.', 'error');
            else alert('El nombre del cliente es obligatorio.');
            return;
        }

        const telefono = (document.getElementById('nuevo_cliente_telefono') || {}).value.trim();
        const ci = (document.getElementById('nuevo_cliente_ci') || {}).value.trim();
        const email = (document.getElementById('nuevo_cliente_email') || {}).value.trim();

        const btn = document.getElementById('btnGuardarCliente');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
        }

        try {
            const response = await fetch(window.posData.crearClienteUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.posData.csrfToken
                },
                body: JSON.stringify({
                    nombre_completo: nombre,
                    telefono: telefono || '',
                    ci_nit: ci || '',
                    email: email || ''
                })
            });
            const data = await response.json();

            if (data.success && data.cliente) {
                document.getElementById('cliente_id_hidden').value = data.cliente.id;
                document.getElementById('cliente_search').value = data.cliente.nombre_completo;
                this.toggleNuevoClienteForm(false);
                this.hideClienteDropdown();
                document.getElementById('nuevo_cliente_nombre').value = '';
                document.getElementById('nuevo_cliente_telefono').value = '';
                document.getElementById('nuevo_cliente_ci').value = '';
                document.getElementById('nuevo_cliente_email').value = '';
                this.showNotification('Cliente creado correctamente');
            } else {
                if (typeof showAlertModal === 'function') showAlertModal('Error: ' + (data.error || 'No se pudo crear el cliente'), 'error');
                else alert('Error: ' + (data.error || 'No se pudo crear el cliente'));
            }
        } catch (err) {
            console.error(err);
            if (typeof showAlertModal === 'function') showAlertModal('Error al crear el cliente. Intente de nuevo.', 'error');
            else alert('Error al crear el cliente. Intente de nuevo.');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-save"></i> Guardar cliente';
            }
        }
    }

    async submitPayment() {
        const clienteId = document.getElementById('cliente_id_hidden').value;
        const metodoPagoId = document.getElementById('metodo_pago_select').value;

        if (!clienteId || !metodoPagoId) {
            if (typeof showAlertModal === 'function') showAlertModal('Por favor busque y seleccione un cliente, o cree uno con el botón +', 'warning');
            else alert('Por favor busque y seleccione un cliente, o cree uno con el botón +');
            return;
        }

        const confirmBtn = document.querySelector('.btn-confirm');
        const originalText = confirmBtn.innerHTML;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        confirmBtn.disabled = true;

        const modoConsumoEl = document.querySelector('input[name="modo_consumo"]:checked');
        const modoConsumo = modoConsumoEl ? modoConsumoEl.value : 'local';
        const tipoDocEl = document.querySelector('input[name="tipo_documento"]:checked');
        const tipoDocumento = tipoDocEl ? tipoDocEl.value : 'ticket';

        if (tipoDocumento === 'factura' && clienteId == window.posData?.clienteMostradorId) {
            if (typeof showAlertModal === 'function') showAlertModal('Para factura debe seleccionar un cliente con NIT/CI. No puede usar Mostrador.', 'warning');
            else alert('Para factura debe seleccionar un cliente con NIT/CI. No puede usar Mostrador.');
            return;
        }

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
                    modo_consumo: modoConsumo,
                    tipo_documento: tipoDocumento,
                    items: this.cart
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('✓ Venta procesada exitosamente');
                this.closePaymentModal();

                // Clear cart and advance ticket number for next order
                this.cart = [];
                this.saveCart();
                this.renderCart();
                this.setSiguienteTicket(data.venta_id + 1);

                // Mostrar modal de confirmación en la página (en lugar del alert del navegador)
                this.showVentaCompletadaModal(data.venta_id, data.total);
            } else {
                if (typeof showAlertModal === 'function') showAlertModal('Error: ' + data.error, 'error');
                else alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            if (typeof showAlertModal === 'function') showAlertModal('Error al procesar el pago. Por favor intente nuevamente.', 'error');
            else alert('Error al procesar el pago. Por favor intente nuevamente.');
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
        const ticketEl = document.querySelector('.ticket-number') || document.getElementById('ticketNumberDisplay');
        if (!ticketEl) return;
        const num = window.posData && window.posData.siguienteTicket != null ? window.posData.siguienteTicket : 1;
        ticketEl.textContent = `Ticket N°${num}`;
    }

    setSiguienteTicket(num) {
        if (window.posData) window.posData.siguienteTicket = num;
        this.updateTicketNumber();
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
