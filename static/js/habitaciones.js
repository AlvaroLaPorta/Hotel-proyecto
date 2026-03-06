/**
 * Habitaciones page — Interactive floor plan with 2 floors, multi-guest, special rooms, DNI lookup
 * Rooms 2 & 4 are special (Almacén / Termotanque) — informative only, no check-in.
 */

const SPECIAL_ROOMS = [2, 4];
const SPECIAL_LABELS = { 2: 'Almacén', 4: 'Sala de Termotanque' };

let roomsData = [];
let currentFloor = 1;

document.addEventListener('DOMContentLoaded', () => loadRooms());


function switchFloor(piso) {
    currentFloor = piso;
    document.querySelectorAll('.floor-tab').forEach(tab => {
        tab.classList.toggle('active', parseInt(tab.dataset.piso) === piso);
    });
    renderFloorPlan();
}


async function loadRooms() {
    try {
        const res = await fetch('/api/habitaciones');
        roomsData = await res.json();
        renderFloorPlan();
    } catch (e) {
        console.error('Error loading rooms:', e);
    }
}


function renderFloorPlan() {
    const topRow = document.getElementById('topRow');
    const bottomRow = document.getElementById('bottomRow');
    topRow.innerHTML = '';
    bottomRow.innerHTML = '';

    const floorRooms = roomsData.filter(r => r.piso === currentFloor);

    floorRooms.forEach((room, i) => {
        const el = createRoomElement(room);
        if (i < 5) topRow.appendChild(el);
        else bottomRow.appendChild(el);
    });
}


function isSpecial(room) {
    return SPECIAL_ROOMS.includes(room.numero);
}


function createRoomElement(room) {
    const el = document.createElement('div');
    const special = isSpecial(room);

    let statusClass, dotClass, borderClass, statusText;

    if (special) {
        statusClass = 'special';
        dotClass = 'red';
        borderClass = 'red-border';
        statusText = SPECIAL_LABELS[room.numero] || 'Especial';
    } else if (room.en_mantenimiento) {
        statusClass = 'maintenance';
        dotClass = 'red';
        borderClass = 'red-border';
        statusText = 'Mantenimiento';
    } else if (room.cantidad_huespedes > 0) {
        statusClass = 'occupied';
        dotClass = 'orange';
        borderClass = 'orange-border';
        statusText = 'Ocupada';
    } else {
        statusClass = 'available';
        dotClass = 'green';
        borderClass = 'green-border';
        statusText = 'Disponible';
    }

    el.className = `room ${statusClass}`;
    el.onclick = special ? () => openSpecialModal(room) : () => openRoomModal(room);

    let clientHTML = '';
    if (!special && room.clientes_activos && room.clientes_activos.length > 0) {
        const names = room.clientes_activos.map(c => `${c.nombre} ${c.apellido}`).join(', ');
        const empresa = room.clientes_activos[0].empresa;
        clientHTML = `
            <div class="card-client">${esc(names)}</div>
            ${empresa ? `<div class="card-empresa">${esc(empresa)}</div>` : ''}
        `;
    }

    const tipoLabel = special ? SPECIAL_LABELS[room.numero] : (room.tipo === 'grande' ? 'Grande' : 'Normal');
    const capLabel = !special ? ` · Cap: ${room.capacidad || 2}` : '';
    const guestsLabel = (!special && room.cantidad_huespedes > 0)
        ? `👤 ${room.cantidad_huespedes}/${room.capacidad || 2}`
        : '';

    el.innerHTML = `
        <div class="room-card ${borderClass}">
            <div class="card-header">
                <span class="card-name">Habitación ${String(room.numero).padStart(2, '0')}</span>
                <span class="card-dot ${dotClass}"></span>
            </div>
            <div class="card-type">${statusText}${!special ? ' · ' + tipoLabel + capLabel : ''}</div>
            ${guestsLabel ? `<div class="card-guests">${guestsLabel}</div>` : ''}
            ${clientHTML}
        </div>
    `;

    return el;
}


// ── Special Room Modal ────────────────────────────────────

function openSpecialModal(room) {
    const title = document.getElementById('roomModalTitle');
    const body = document.getElementById('roomModalBody');
    const label = SPECIAL_LABELS[room.numero] || 'Especial';

    title.textContent = `Habitación ${String(room.numero).padStart(2, '0')} — ${label}`;
    body.innerHTML = `
        <p style="color:var(--text-secondary);margin-bottom:16px;">
            Esta habitación es de <strong>${label}</strong> y no está disponible para hospedaje.
            <br>Piso: <strong>${room.piso}</strong>
        </p>
        <div class="modal-footer">
            <button class="btn btn-outline" onclick="closeRoomModal()">Cerrar</button>
        </div>
    `;
    document.getElementById('roomModal').classList.add('active');
}


// ── Room Modal ────────────────────────────────────────────

function openRoomModal(room) {
    const title = document.getElementById('roomModalTitle');
    const body = document.getElementById('roomModalBody');
    const tipoLabel = room.tipo === 'grande' ? 'Grande' : 'Normal';
    title.textContent = `Habitación ${String(room.numero).padStart(2, '0')} — ${tipoLabel}`;

    if (room.en_mantenimiento) {
        body.innerHTML = `
            <p style="color:var(--text-secondary);margin-bottom:16px;">
                Esta habitación está en <strong style="color:var(--red);">mantenimiento</strong>.
                <br>Tipo: <strong>${tipoLabel}</strong> · Piso: <strong>${room.piso}</strong>
            </p>
            <div class="modal-footer">
                <button class="btn btn-outline" onclick="closeRoomModal()">Cerrar</button>
                <button class="btn btn-success" onclick="toggleMaintenance(${room.id}, false)">✅ Quitar Mantenimiento</button>
            </div>
        `;
    } else if (room.clientes_activos && room.clientes_activos.length > 0) {
        const guestListHTML = room.clientes_activos.map(c => `
            <div class="guest-item">
                <div class="guest-info">
                    <div class="guest-name">${esc(c.nombre)} ${esc(c.apellido)} ${c.dni ? `<span style="color:var(--text-dim);font-size:11px;">(DNI: ${esc(c.dni)})</span>` : ''}</div>
                    <div class="guest-detail">📞 ${esc(c.telefono)} · 🏢 ${esc(c.empresa)}</div>
                    <div class="guest-detail">📅 ${formatDate(c.hospedaje_desde)} → ${formatDate(c.hospedaje_hasta)}</div>
                </div>
                <div style="display:flex;gap:6px;">
                    <button class="btn btn-outline btn-sm" onclick="editGuestModal(${c.id})" title="Editar">✏️</button>
                    <button class="btn btn-warning btn-sm" onclick="removeGuest(${c.id})" title="Check-out">🚪</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteGuest(${c.id})" title="Eliminar">🗑️</button>
                </div>
            </div>
        `).join('');

        body.innerHTML = `
            <p style="color:var(--text-secondary);margin-bottom:12px;">
                Tipo: <strong>${tipoLabel}</strong> · Piso: <strong>${room.piso}</strong> ·
                <strong>${room.cantidad_huespedes}/${room.capacidad || 2}</strong> huéspedes
            </p>
            <h3 style="font-size:14px;margin-bottom:10px;">Huéspedes:</h3>
            ${guestListHTML}
            <div class="modal-footer" style="flex-wrap:wrap;">
                <button class="btn btn-success btn-sm" onclick="addGuestForm(${room.id})">+ Agregar Huésped</button>
                <button class="btn btn-danger" onclick="doCheckoutAll(${room.id})">🚪 Check-out Total</button>
                <button class="btn btn-warning btn-sm" onclick="toggleMaintenance(${room.id}, true)">🔧 Mantenimiento</button>
                <button class="btn btn-outline" onclick="closeRoomModal()">Cerrar</button>
            </div>
        `;
    } else {
        // Available — check-in form with DNI lookup
        body.innerHTML = buildCheckinForm(room.id);
    }

    document.getElementById('roomModal').classList.add('active');
}

function buildCheckinForm(habId) {
    return `
        <form onsubmit="doCheckin(event, ${habId})">
            <div class="form-group">
                <label>DNI (buscar cliente existente)</label>
                <div style="display:flex;gap:8px;">
                    <input type="text" class="form-control" id="ciDni" placeholder="Ingrese DNI..." oninput="dniLookupDebounce()">
                    <button type="button" class="btn btn-outline btn-sm" onclick="dniLookup()">🔍</button>
                </div>
                <small id="dniStatus" style="color:var(--text-dim);font-size:11px;"></small>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Nombre *</label>
                    <input type="text" class="form-control" id="ciNombre" required>
                </div>
                <div class="form-group">
                    <label>Apellido *</label>
                    <input type="text" class="form-control" id="ciApellido" required>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Teléfono</label>
                    <input type="text" class="form-control" id="ciTelefono">
                </div>
                <div class="form-group">
                    <label>Empresa</label>
                    <input type="text" class="form-control" id="ciEmpresa">
                </div>
            </div>
            <div class="form-group">
                <label>Dirección</label>
                <input type="text" class="form-control" id="ciDireccion">
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Desde</label>
                    <input type="date" class="form-control" id="ciDesde" value="${todayISO()}">
                </div>
                <div class="form-group">
                    <label>Hasta</label>
                    <input type="date" class="form-control" id="ciHasta">
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-warning" onclick="toggleMaintenance(${habId}, true)">🔧</button>
                <button type="button" class="btn btn-outline" onclick="closeRoomModal()">Cancelar</button>
                <button type="submit" class="btn btn-success">✅ Check-in</button>
            </div>
        </form>
    `;
}


function closeRoomModal() {
    document.getElementById('roomModal').classList.remove('active');
}


// ── DNI Lookup ────────────────────────────────────────────

let dniTimer = null;
function dniLookupDebounce() {
    clearTimeout(dniTimer);
    dniTimer = setTimeout(dniLookup, 500);
}

async function dniLookup() {
    const dni = document.getElementById('ciDni').value.trim();
    const status = document.getElementById('dniStatus');
    if (!dni || dni.length < 3) { status.textContent = ''; return; }

    try {
        const res = await fetch(`/api/clientes/buscar-dni/${dni}`);
        const data = await res.json();
        if (data.found) {
            const c = data.cliente;
            document.getElementById('ciNombre').value = c.nombre;
            document.getElementById('ciApellido').value = c.apellido;
            document.getElementById('ciTelefono').value = c.telefono;
            document.getElementById('ciEmpresa').value = c.empresa;
            document.getElementById('ciDireccion').value = c.direccion || '';
            status.textContent = `✅ Cliente encontrado: ${c.nombre} ${c.apellido}`;
            status.style.color = 'var(--green)';
        } else {
            status.textContent = 'ℹ️ DNI no registrado — se creará nuevo cliente';
            status.style.color = 'var(--text-dim)';
        }
    } catch (e) {
        status.textContent = '';
    }
}


// ── Add Guest form ────────────────────────────────────────

function addGuestForm(habId) {
    const body = document.getElementById('roomModalBody');
    body.innerHTML = `
        <p style="color:var(--text-secondary);margin-bottom:16px;">Agregar huésped adicional:</p>
        ${buildCheckinForm(habId)}
    `;
}


// ── Edit Guest modal ──────────────────────────────────────

async function editGuestModal(clientId) {
    let client = null;
    for (const room of roomsData) {
        if (room.clientes_activos) {
            const found = room.clientes_activos.find(c => c.id === clientId);
            if (found) { client = found; break; }
        }
    }
    if (!client) { showToast('Cliente no encontrado', 'error'); return; }

    const body = document.getElementById('roomModalBody');
    body.innerHTML = `
        <p style="color:var(--text-secondary);margin-bottom:16px;">Editar datos del huésped:</p>
        <form onsubmit="updateGuest(event, ${client.id})">
            <div class="form-group">
                <label>DNI</label>
                <input type="text" class="form-control" id="rDni" value="${esc(client.dni)}">
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Nombre</label>
                    <input type="text" class="form-control" id="rNombre" value="${esc(client.nombre)}" required>
                </div>
                <div class="form-group">
                    <label>Apellido</label>
                    <input type="text" class="form-control" id="rApellido" value="${esc(client.apellido)}" required>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Teléfono</label>
                    <input type="text" class="form-control" id="rTelefono" value="${esc(client.telefono)}">
                </div>
                <div class="form-group">
                    <label>Empresa</label>
                    <input type="text" class="form-control" id="rEmpresa" value="${esc(client.empresa)}">
                </div>
            </div>
            <div class="form-group">
                <label>Dirección</label>
                <input type="text" class="form-control" id="rDireccion" value="${esc(client.direccion)}">
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Desde</label>
                    <input type="date" class="form-control" id="rDesde" value="${client.hospedaje_desde}">
                </div>
                <div class="form-group">
                    <label>Hasta</label>
                    <input type="date" class="form-control" id="rHasta" value="${client.hospedaje_hasta}">
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-outline" onclick="closeRoomModal()">Cancelar</button>
                <button type="submit" class="btn btn-primary">💾 Guardar</button>
            </div>
        </form>
    `;
}


async function updateGuest(e, clientId) {
    e.preventDefault();

    // Frontend date validation
    const desdeVal = document.getElementById('rDesde').value;
    const hastaVal = document.getElementById('rHasta').value;
    if (desdeVal && hastaVal && hastaVal < desdeVal) {
        showToast('La fecha "hasta" no puede ser menor a "desde"', 'error');
        return;
    }

    const payload = {
        dni: document.getElementById('rDni').value,
        nombre: document.getElementById('rNombre').value,
        apellido: document.getElementById('rApellido').value,
        telefono: document.getElementById('rTelefono').value,
        empresa: document.getElementById('rEmpresa').value,
        direccion: document.getElementById('rDireccion').value,
        hospedaje_desde: desdeVal,
        hospedaje_hasta: hastaVal,
    };

    try {
        const res = await fetch(`/api/clientes/${clientId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (res.ok) {
            showToast('Datos actualizados', 'success');
            closeRoomModal();
            loadRooms();
        } else {
            const err = await res.json();
            showToast(err.error || 'Error', 'error');
        }
    } catch (e) {
        showToast('Error al actualizar', 'error');
    }
}


// ── Actions ───────────────────────────────────────────────

async function doCheckin(e, habId) {
    e.preventDefault();

    // Frontend date validation
    const desdeVal = document.getElementById('ciDesde').value;
    const hastaVal = document.getElementById('ciHasta').value;
    if (desdeVal && hastaVal && hastaVal < desdeVal) {
        showToast('La fecha "hasta" no puede ser menor a "desde"', 'error');
        return;
    }

    const payload = {
        habitacion_id: habId,
        dni: document.getElementById('ciDni').value,
        nombre: document.getElementById('ciNombre').value,
        apellido: document.getElementById('ciApellido').value,
        telefono: document.getElementById('ciTelefono').value,
        empresa: document.getElementById('ciEmpresa').value,
        direccion: document.getElementById('ciDireccion').value,
        hospedaje_desde: desdeVal,
        hospedaje_hasta: hastaVal,
    };

    try {
        const res = await fetch('/api/checkin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (res.ok) {
            showToast('Check-in realizado', 'success');
            closeRoomModal();
            loadRooms();
        } else {
            const err = await res.json();
            showToast(err.error || 'Error', 'error');
        }
    } catch (e) {
        showToast('Error de conexión', 'error');
    }
}


async function doCheckoutAll(habId) {
    if (!confirm('¿Confirmar check-out de TODOS los huéspedes?')) return;
    try {
        const res = await fetch(`/api/checkout/${habId}`, { method: 'POST' });
        if (res.ok) {
            showToast('Check-out total realizado', 'success');
            closeRoomModal();
            loadRooms();
        }
    } catch (e) {
        showToast('Error al hacer check-out', 'error');
    }
}


async function removeGuest(clientId) {
    if (!confirm('¿Check-out de este huésped?')) return;
    try {
        const res = await fetch(`/api/checkout-guest/${clientId}`, { method: 'POST' });
        if (res.ok) {
            showToast('Huésped removido', 'success');
            closeRoomModal();
            loadRooms();
        }
    } catch (e) {
        showToast('Error', 'error');
    }
}


async function deleteGuest(clientId) {
    if (!confirm('⚠️ ¿Eliminar este cliente permanentemente de la base de datos?')) return;
    try {
        const res = await fetch(`/api/clientes/${clientId}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('Cliente eliminado', 'success');
            closeRoomModal();
            loadRooms();
        }
    } catch (e) {
        showToast('Error al eliminar', 'error');
    }
}


async function resetAllRooms() {
    if (!confirm('⚠️ ¿Reiniciar TODAS las habitaciones?\nSe hará check-out de todos los huéspedes.')) return;
    try {
        const res = await fetch('/api/reset-all', { method: 'POST' });
        if (res.ok) {
            showToast('Todas las habitaciones liberadas', 'success');
            loadRooms();
        }
    } catch (e) {
        showToast('Error al reiniciar', 'error');
    }
}


async function toggleMaintenance(habId, value) {
    try {
        const res = await fetch(`/api/habitaciones/${habId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ en_mantenimiento: value }),
        });
        if (res.ok) {
            showToast(value ? 'Habitación en mantenimiento' : 'Mantenimiento desactivado', 'info');
            closeRoomModal();
            loadRooms();
        }
    } catch (e) {
        showToast('Error', 'error');
    }
}


// ── Helpers ───────────────────────────────────────────────

function esc(s) {
    if (!s) return '';
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}

function todayISO() {
    return new Date().toISOString().split('T')[0];
}

function formatDate(d) {
    if (!d) return '—';
    const parts = d.split('-');
    if (parts.length !== 3) return d;
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
}


// ── Room Editor ───────────────────────────────────────────

async function openRoomEditor() {
    const modal = document.getElementById('roomEditorModal');
    const body = document.getElementById('roomEditorBody');
    body.innerHTML = '<p style="text-align:center;color:var(--text-dim);">Cargando...</p>';
    modal.classList.add('active');

    try {
        const res = await fetch('/api/habitaciones');
        const rooms = await res.json();

        let html = `
            <div class="table-wrapper" style="margin:0;">
                <table>
                    <thead>
                        <tr>
                            <th>Hab #</th>
                            <th>Piso</th>
                            <th>Tipo</th>
                            <th>Capacidad</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        rooms.forEach(r => {
            const special = SPECIAL_ROOMS.includes(r.numero);
            const estado = r.en_mantenimiento
                ? '<span class="badge badge-red">Mantenim.</span>'
                : (r.disponible
                    ? '<span class="badge badge-green">Disponible</span>'
                    : '<span class="badge badge-orange">Ocupada</span>');

            html += `
                <tr id="roomRow_${r.id}">
                    <td>
                        <input type="number" class="form-control" id="reNum_${r.id}" value="${r.numero}" 
                            style="width:70px;" min="1" ${special ? 'disabled' : ''}>
                    </td>
                    <td>${r.piso}</td>
                    <td>
                        <select class="form-control" id="reTipo_${r.id}" style="width:110px;" ${special ? 'disabled' : ''}>
                            <option value="normal" ${r.tipo === 'normal' ? 'selected' : ''}>Normal</option>
                            <option value="grande" ${r.tipo === 'grande' ? 'selected' : ''}>Grande</option>
                        </select>
                    </td>
                    <td>
                        <input type="number" class="form-control" id="reCap_${r.id}" value="${r.capacidad || 2}" 
                            style="width:70px;" min="1" max="10" ${special ? 'disabled' : ''}>
                    </td>
                    <td>${estado}</td>
                    <td>
                        ${special
                    ? '<span style="color:var(--text-dim);font-size:12px;">Especial</span>'
                    : `<button class="btn btn-primary btn-sm" onclick="saveRoom(${r.id})">💾</button>`
                }
                    </td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
            <div class="modal-footer" style="margin-top:16px;">
                <button class="btn btn-outline" onclick="closeRoomEditor()">Cerrar</button>
            </div>
        `;

        body.innerHTML = html;
    } catch (e) {
        body.innerHTML = '<p style="color:var(--red);text-align:center;">Error al cargar habitaciones</p>';
    }
}


function closeRoomEditor() {
    document.getElementById('roomEditorModal').classList.remove('active');
}


async function saveRoom(roomId) {
    const numero = document.getElementById(`reNum_${roomId}`).value;
    const tipo = document.getElementById(`reTipo_${roomId}`).value;
    const capacidad = document.getElementById(`reCap_${roomId}`).value;

    try {
        const res = await fetch(`/api/habitaciones/${roomId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                numero: parseInt(numero),
                tipo,
                capacidad: parseInt(capacidad),
            }),
        });

        if (res.ok) {
            showToast(`Habitación ${numero} actualizada`, 'success');
            loadRooms();
            openRoomEditor(); // Refresh the editor table
        } else {
            const err = await res.json();
            showToast(err.error || 'Error', 'error');
        }
    } catch (e) {
        showToast('Error al guardar', 'error');
    }
}
