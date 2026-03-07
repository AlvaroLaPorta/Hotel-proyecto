/**
 * Clientes page — CRUD with DNI, room assignment, history, filters, pagination
 */

let currentPage = 1;
let availableRooms = [];

document.addEventListener('DOMContentLoaded', () => {
    loadClientes();
    loadAvailableRooms();
});


async function loadClientes(page = 1) {
    currentPage = page;
    const nombre = document.getElementById('filterNombre').value;
    const dni = document.getElementById('filterDni').value;
    const empresa = document.getElementById('filterEmpresa').value;
    const telefono = document.getElementById('filterTelefono').value;

    const params = new URLSearchParams({ page, per_page: 10 });
    if (nombre) params.set('nombre', nombre);
    if (dni) params.set('dni', dni);
    if (empresa) params.set('empresa', empresa);
    if (telefono) params.set('telefono', telefono);

    try {
        const res = await fetch(`/api/clientes?${params}`);
        const data = await res.json();
        renderClientes(data.clientes);
        renderPagination(data.page, data.pages, data.total);
    } catch (e) {
        console.error('Error loading clients:', e);
    }
}


async function loadAvailableRooms() {
    try {
        const res = await fetch('/api/habitaciones/disponibles');
        availableRooms = await res.json();
    } catch (e) {
        availableRooms = [];
    }
}


function renderClientes(clientes) {
    const tbody = document.getElementById('clientesBody');

    if (clientes.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;color:var(--text-dim);padding:40px;">
            No se encontraron clientes</td></tr>`;
        return;
    }

    tbody.innerHTML = clientes.map(c => `
        <tr>
            <td>${esc(c.dni) || '<span style="color:var(--text-dim)">—</span>'}</td>
            <td><strong>${esc(c.nombre)} ${esc(c.apellido)}</strong></td>
            <td>${esc(c.telefono)}</td>
            <td>${esc(c.empresa)}</td>
            <td>${c.habitacion_numero ? `<span class="badge badge-orange">Hab ${c.habitacion_numero}</span>` : '<span style="color:var(--text-dim)">—</span>'}</td>
            <td>${formatDate(c.hospedaje_desde)}</td>
            <td>${formatDate(c.hospedaje_hasta)}</td>
            <td>${c.activo ? '<span class="badge badge-green">Activo</span>' : '<span class="badge badge-purple">Inactivo</span>'}</td>
            <td style="white-space:nowrap;">
                <button class="btn btn-outline btn-sm" onclick="editClient(${c.id})" title="Editar">✏️</button>
                <button class="btn btn-outline btn-sm" onclick="showHistory(${c.id})" title="Historial" style="border-color:var(--purple);color:var(--purple);">📋</button>
                <button class="btn btn-danger btn-sm" onclick="deleteClient(${c.id})" title="Eliminar">🗑️</button>
            </td>
        </tr>
    `).join('');
}


function renderPagination(page, pages, total) {
    const div = document.getElementById('pagination');
    if (pages <= 1) { div.innerHTML = ''; return; }

    div.innerHTML = `
        <button ${page <= 1 ? 'disabled' : ''} onclick="loadClientes(${page - 1})">← Anterior</button>
        <span class="page-info">Página ${page} de ${pages} (${total} clientes)</span>
        <button ${page >= pages ? 'disabled' : ''} onclick="loadClientes(${page + 1})">Siguiente →</button>
    `;
}


function clearFilters() {
    document.getElementById('filterNombre').value = '';
    document.getElementById('filterDni').value = '';
    document.getElementById('filterEmpresa').value = '';
    document.getElementById('filterTelefono').value = '';
    loadClientes();
}


// ── Modal: Create/Edit ────────────────────────────────────

async function openNewClientModal() {
    await loadAvailableRooms();
    document.getElementById('modalTitle').textContent = 'Nuevo Cliente';
    document.getElementById('clientId').value = '';
    document.getElementById('clientForm').reset();
    populateRoomSelect('');
    document.getElementById('clientModal').classList.add('active');
}


async function editClient(id) {
    await loadAvailableRooms();
    try {
        const res = await fetch(`/api/clientes?per_page=1000`);
        const data = await res.json();
        const client = data.clientes.find(c => c.id === id);
        if (!client) return;

        document.getElementById('modalTitle').textContent = 'Editar Cliente';
        document.getElementById('clientId').value = client.id;
        document.getElementById('clientDni').value = client.dni;
        document.getElementById('clientNombre').value = client.nombre;
        document.getElementById('clientApellido').value = client.apellido;
        document.getElementById('clientTelefono').value = client.telefono;
        document.getElementById('clientEmpresa').value = client.empresa;
        document.getElementById('clientDireccion').value = client.direccion;
        document.getElementById('clientDesde').value = client.hospedaje_desde;
        document.getElementById('clientHasta').value = client.hospedaje_hasta;

        populateRoomSelect(client.habitacion_id, client.habitacion_numero);

        document.getElementById('clientModal').classList.add('active');
    } catch (e) {
        showToast('Error al cargar cliente', 'error');
    }
}


function populateRoomSelect(currentHabId, currentHabNumero) {
    const select = document.getElementById('clientHabitacion');
    select.innerHTML = '<option value="">— Sin asignar —</option>';

    if (currentHabId && currentHabNumero) {
        select.innerHTML += `<option value="${currentHabId}" selected>Hab ${currentHabNumero} (actual)</option>`;
    }

    availableRooms.forEach(r => {
        if (r.id != currentHabId) {
            select.innerHTML += `<option value="${r.id}">Hab ${r.numero} — Piso ${r.piso} (${r.tipo})</option>`;
        }
    });
}


function closeModal() {
    document.getElementById('clientModal').classList.remove('active');
}


async function saveClient(e) {
    e.preventDefault();
    const saveBtn = document.getElementById('saveBtn');
    if (saveBtn.disabled) return;
    saveBtn.disabled = true;
    saveBtn.textContent = 'Guardando...';

    const id = document.getElementById('clientId').value;
    const habSelect = document.getElementById('clientHabitacion').value;

    const payload = {
        dni: document.getElementById('clientDni').value,
        nombre: document.getElementById('clientNombre').value,
        apellido: document.getElementById('clientApellido').value,
        telefono: document.getElementById('clientTelefono').value,
        empresa: document.getElementById('clientEmpresa').value,
        direccion: document.getElementById('clientDireccion').value,
        hospedaje_desde: document.getElementById('clientDesde').value,
        hospedaje_hasta: document.getElementById('clientHasta').value,
    };

    if (habSelect) {
        payload.habitacion_id = parseInt(habSelect);
    } else {
        payload.habitacion_id = null;
    }

    try {
        const url = id ? `/api/clientes/${id}` : '/api/clientes';
        const method = id ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (res.ok) {
            showToast(id ? 'Cliente actualizado' : 'Cliente creado', 'success');
            closeModal();
            loadClientes(currentPage);
            loadAvailableRooms();
        } else {
            const err = await res.json();
            showToast(err.error || 'Error', 'error');
        }
    } catch (e) {
        showToast('Error de conexión', 'error');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Guardar';
    }
}


let pendingDeleteClientId = null;

function deleteClient(id) {
    pendingDeleteClientId = id;
    document.getElementById('deleteConfirmModal').classList.add('active');
}

function closeDeleteConfirm() {
    document.getElementById('deleteConfirmModal').classList.remove('active');
    pendingDeleteClientId = null;
}

async function confirmDeleteClient() {
    if (!pendingDeleteClientId) return;
    const id = pendingDeleteClientId;
    closeDeleteConfirm();
    try {
        const res = await fetch(`/api/clientes/${id}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('Cliente eliminado', 'success');
            loadClientes(currentPage);
            loadAvailableRooms();
        }
    } catch (e) {
        showToast('Error al eliminar', 'error');
    }
}


// ── Modal: History ────────────────────────────────────────

async function showHistory(clientId) {
    const modal = document.getElementById('historyModal');
    const title = document.getElementById('historyTitle');
    const body = document.getElementById('historyBody');

    body.innerHTML = '<p style="color:var(--text-dim);text-align:center;">Cargando historial...</p>';
    modal.classList.add('active');

    try {
        const res = await fetch(`/api/clientes/${clientId}/historial`);
        const data = await res.json();
        const c = data.cliente;

        title.textContent = `📋 Historial — ${c.nombre} ${c.apellido}`;

        // Client info header
        let html = `
            <div style="background:var(--bg-card);border:1px solid var(--border-color);border-radius:10px;padding:16px;margin-bottom:20px;">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                    <div>
                        <strong style="font-size:16px;">${esc(c.nombre)} ${esc(c.apellido)}</strong>
                        ${c.dni ? `<span style="color:var(--text-secondary);margin-left:8px;">DNI: ${esc(c.dni)}</span>` : ''}
                    </div>
                    <div>
                        <span class="badge badge-purple" style="font-size:13px;">
                            ${data.total_estadias} estadía${data.total_estadias !== 1 ? 's' : ''} registrada${data.total_estadias !== 1 ? 's' : ''}
                        </span>
                    </div>
                </div>
                <div style="margin-top:8px;color:var(--text-secondary);font-size:13px;">
                    📞 ${esc(c.telefono) || '—'} · 🏢 ${esc(c.empresa) || '—'} · 📍 ${esc(c.direccion) || '—'}
                </div>
                ${c.activo ? `<div style="margin-top:6px;"><span class="badge badge-green">Actualmente hospedado — Hab ${c.habitacion_numero || '?'}</span></div>` : ''}
            </div>
        `;

        if (data.estadias.length === 0) {
            html += `<p style="color:var(--text-dim);text-align:center;padding:20px;">
                No hay estadías anteriores registradas.
                ${c.activo ? '<br>La estadía actual se registrará al hacer check-out.' : ''}
            </p>`;
        } else {
            html += `
                <div class="table-wrapper" style="margin:0;">
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Habitación</th>
                                <th>Desde</th>
                                <th>Hasta</th>
                                <th>Duración</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            data.estadias.forEach((e, i) => {
                const dias = calcDays(e.desde, e.hasta);
                html += `
                    <tr>
                        <td>${data.estadias.length - i}</td>
                        <td><span class="badge badge-orange">Hab ${e.habitacion_numero || '?'}</span></td>
                        <td>${formatDate(e.desde)}</td>
                        <td>${formatDate(e.hasta)}</td>
                        <td>${dias !== null ? `${dias} día${dias !== 1 ? 's' : ''}` : '—'}</td>
                    </tr>
                `;
            });

            html += `
                        </tbody>
                    </table>
                </div>
            `;
        }

        html += `
            <div class="modal-footer" style="margin-top:16px;">
                <button class="btn btn-outline" onclick="closeHistoryModal()">Cerrar</button>
            </div>
        `;

        body.innerHTML = html;

    } catch (e) {
        body.innerHTML = '<p style="color:var(--red);text-align:center;">Error al cargar historial</p>';
    }
}


function closeHistoryModal() {
    document.getElementById('historyModal').classList.remove('active');
}


function calcDays(desde, hasta) {
    if (!desde || !hasta) return null;
    const d1 = new Date(desde);
    const d2 = new Date(hasta);
    const diff = Math.round((d2 - d1) / (1000 * 60 * 60 * 24));
    return diff >= 0 ? diff : null;
}


// ── Helpers ───────────────────────────────────────────────

function esc(s) {
    if (!s) return '';
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}

function formatDate(d) {
    if (!d) return '—';
    const parts = d.split('-');
    if (parts.length !== 3) return d;
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
}
