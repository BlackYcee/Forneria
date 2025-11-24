// Lógica simple de carrito usando localStorage
const CART_KEY = 'forneria_cart_v1';

function loadCart() {
  try {
    return JSON.parse(localStorage.getItem(CART_KEY) || '[]');
  } catch (e) {
    return [];
  }
}

function saveCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
}

function renderCart() {
  const cart = loadCart();
  const ul = document.getElementById('cart-items');
  const totalEl = document.getElementById('cart-total');
  ul.innerHTML = '';
  let total = 0;
  cart.forEach(item => {
    const li = document.createElement('li');
    li.innerHTML = `<span>${item.nombre} x${item.qty}</span><span>${formatCLP(item.precio*item.qty)} <button data-id="${item.id}" class="remove-item">x</button></span>`;
    ul.appendChild(li);
    total += item.precio * item.qty;
  });
  totalEl.textContent = formatCLP(total);
}

function addToCart(id, nombre, precio) {
  const cart = loadCart();
  const existing = cart.find(i => String(i.id) === String(id));
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ id: id, nombre: nombre, precio: parseFloat(precio), qty: 1 });
  }
  saveCart(cart);
  renderCart();
}

function clearCart() {
  localStorage.removeItem(CART_KEY);
  renderCart();
}

document.addEventListener('DOMContentLoaded', () => {
  renderCart();

  // añadir eventos a botones existentes
  document.querySelectorAll('.add-to-cart').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const id = btn.getAttribute('data-id');
      const nombre = btn.getAttribute('data-nombre');
      const precio = parseFloat(btn.getAttribute('data-precio')) || 0;
      addToCart(id, nombre, precio);
    });
  });

  // delegado para remover items
  document.getElementById('cart-items').addEventListener('click', (e) => {
    if (e.target && e.target.classList.contains('remove-item')) {
      const id = e.target.getAttribute('data-id');
      let cart = loadCart();
      cart = cart.filter(i => String(i.id) !== String(id));
      saveCart(cart);
      renderCart();
    }
  });

  // clear
  document.getElementById('clear-cart').addEventListener('click', (e) => {
    clearCart();
  });

  // checkout - por ahora solo limpiar y mostrar resumen
  document.getElementById('checkout-btn').addEventListener('click', (e) => {
    const cart = loadCart();
    if (cart.length === 0) { alert('Carrito vacío'); return; }
    // mostrar modal con desglose
    populateCartModal(cart);
    document.getElementById('cartModal').style.display = 'flex';
  });

  // cart modal close / confirm
  document.getElementById('cart-modal-close').addEventListener('click', () => {
    document.getElementById('cartModal').style.display = 'none';
  });
  document.getElementById('cancel-sale').addEventListener('click', () => {
    document.getElementById('cartModal').style.display = 'none';
  });
  document.getElementById('monto-pagado').addEventListener('input', () => {
    updateChange();
  });
  document.getElementById('confirm-sale').addEventListener('click', () => {
    // Enviar carrito al endpoint de checkout
    (async function(){
      const cart = loadCart();
      if (cart.length === 0) { alert('Carrito vacío'); return; }
      const monto = Number(document.getElementById('monto-pagado').value || 0);
      const payload = {
        canal_venta: 'presencial',
        monto_pagado: monto || null,
        items: cart.map(i => ({ producto_id: i.id, cantidad: i.qty, precio_unitario: i.precio, descuento_pct: i.descuento_pct || 0 }))
      };

      try {
        const csrftoken = getCookie('csrftoken');
        const r = await fetch('/pos/checkout/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
          },
          body: JSON.stringify(payload)
        });
        const data = await r.json();
        if (!r.ok) {
          const msg = data.detail || 'Error en el checkout';
          alert('Error: ' + msg);
          return;
        }
        // éxito
        alert(`Venta registrada. Folio: ${data.folio} - Total: ${formatCLP(data.total_con_iva)}${data.vuelto ? ' - Vuelto: ' + formatCLP(data.vuelto) : ''}`);
        clearCart();
        document.getElementById('cartModal').style.display = 'none';
      } catch (err) {
        console.error(err);
        alert('Error comunicándose con el servidor');
      }
    })();
  });

  // modal: view-detail buttons
  document.querySelectorAll('.view-detail').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const id = btn.getAttribute('data-id');
      // intentar obtener datos desde API REST
      try {
        const r = await fetch(`/pos/productos/${id}/`);
        if (!r.ok) throw new Error('no data');
        const data = await r.json();
        document.getElementById('modal-nombre').textContent = data.nombre || '';
        document.getElementById('modal-descripcion').textContent = data.descripcion || '';
        document.getElementById('modal-precio').textContent = data.precio || 0;
        document.getElementById('modal-stock').textContent = data.stock_total || 0;
      } catch (err) {
        document.getElementById('modal-nombre').textContent = 'Detalle no disponible';
        document.getElementById('modal-descripcion').textContent = '';
        document.getElementById('modal-precio').textContent = '0';
        document.getElementById('modal-stock').textContent = '0';
      }
      document.getElementById('productModal').style.display = 'flex';
    });
  });

  document.getElementById('modal-close').addEventListener('click', () => {
    document.getElementById('productModal').style.display = 'none';
  });
});

// Helpers: formato CLP y modal population
function formatCLP(value) {
  try {
    const n = Math.round(Number(value) || 0);
    // usar localString para miles y separador de miles '.' en es-CL
    return '$' + n.toLocaleString('es-CL');
  } catch (e) {
    return '$0';
  }
}

// CSRF helper (obtener cookie)
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function populateCartModal(cart) {
  const container = document.getElementById('cart-modal-items');
  container.innerHTML = '';
  let subtotal = 0;
  cart.forEach(i => {
    const div = document.createElement('div');
    div.textContent = `${i.nombre} x${i.qty} — ${formatCLP(i.precio * i.qty)}`;
    container.appendChild(div);
    subtotal += i.precio * i.qty;
  });
  const iva = Math.round((subtotal * 0.19));
  const total = Math.round(subtotal + iva);
  document.getElementById('cart-subtotal').textContent = formatCLP(subtotal);
  document.getElementById('cart-iva').textContent = formatCLP(iva);
  document.getElementById('cart-total-modal').textContent = formatCLP(total);
  document.getElementById('monto-pagado').value = '';
  document.getElementById('cart-change').textContent = formatCLP(0);
  // store totals for updateChange
  document.getElementById('cartModal').dataset.subtotal = subtotal;
  document.getElementById('cartModal').dataset.total = total;
}

function updateChange() {
  const paid = Number(document.getElementById('monto-pagado').value || 0);
  const total = Number(document.getElementById('cartModal').dataset.total || 0);
  const change = Math.max(0, Math.round(paid) - Math.round(total));
  document.getElementById('cart-change').textContent = formatCLP(change);
}
