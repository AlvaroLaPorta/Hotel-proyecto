"""
Hotel Karim — Flask Application
Main app with page routes and REST API endpoints.
"""
import sys
import os
from datetime import datetime, date

from flask import Flask, render_template, request, jsonify

sys.path.insert(0, os.path.dirname(__file__))
from database import db, init_db
from models import Cliente, Habitacion, Estadia


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hotel-karim-secret-key'
    init_db(app)
    return app


app = create_app()


# ── Auto-checkout: runs before every request ───────────────────

@app.before_request
def auto_checkout():
    """Automatically check out guests whose hospedaje_hasta < today."""
    today = date.today()
    expired = Cliente.query.filter(
        Cliente.activo == True,
        Cliente.hospedaje_hasta != None,
        Cliente.hospedaje_hasta <= today
    ).all()

    if expired:
        for c in expired:
            _record_estadia(c)
            hab_id = c.habitacion_id
            c.activo = False
            c.habitacion_id = None

            # Free room if no more active guests
            if hab_id:
                hab = Habitacion.query.get(hab_id)
                if hab:
                    remaining = Cliente.query.filter(
                        Cliente.habitacion_id == hab.id,
                        Cliente.activo == True,
                        Cliente.id != c.id
                    ).count()
                    if remaining == 0:
                        hab.disponible = True

        db.session.commit()


# ── Page Routes ────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/clientes')
def clientes_page():
    return render_template('clientes.html')


@app.route('/habitaciones')
def habitaciones_page():
    return render_template('habitaciones.html')


@app.route('/configuracion')
def configuracion_page():
    return render_template('configuracion.html')


# ── API: Clientes ──────────────────────────────────────────────

@app.route('/api/clientes', methods=['GET'])
def api_get_clientes():
    """Get clients with optional filters and pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    nombre = request.args.get('nombre', '').strip()
    empresa = request.args.get('empresa', '').strip()
    telefono = request.args.get('telefono', '').strip()
    dni = request.args.get('dni', '').strip()

    query = Cliente.query

    if nombre:
        query = query.filter(
            (Cliente.nombre.ilike(f'%{nombre}%')) |
            (Cliente.apellido.ilike(f'%{nombre}%'))
        )
    if empresa:
        query = query.filter(Cliente.empresa.ilike(f'%{empresa}%'))
    if telefono:
        query = query.filter(Cliente.telefono.ilike(f'%{telefono}%'))
    if dni:
        query = query.filter(Cliente.dni.ilike(f'%{dni}%'))

    query = query.order_by(Cliente.created_at.desc())
    total = query.count()
    clientes = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'clientes': [c.to_dict() for c in clientes],
        'total': total,
        'page': page,
        'pages': (total + per_page - 1) // per_page,
    })


@app.route('/api/clientes/buscar-dni/<dni>', methods=['GET'])
def api_buscar_por_dni(dni):
    """Look up a client by DNI. Returns client data if found."""
    cliente = Cliente.query.filter_by(dni=dni.strip()).first()
    if cliente:
        return jsonify({'found': True, 'cliente': cliente.to_dict()})
    return jsonify({'found': False})


@app.route('/api/clientes', methods=['POST'])
def api_create_cliente():
    """Create a new client or reuse by DNI."""
    data = request.get_json()
    if not data or not data.get('nombre') or not data.get('apellido'):
        return jsonify({'error': 'Nombre y apellido son obligatorios'}), 400

    dni = data.get('dni', '').strip() or None
    hab_id = data.get('habitacion_id')

    # Validate room availability if assigning
    if hab_id:
        hab = Habitacion.query.get(hab_id)
        if not hab:
            return jsonify({'error': 'Habitación no encontrada'}), 400
        if hab.en_mantenimiento:
            return jsonify({'error': 'Habitación en mantenimiento'}), 400
        if hab.numero in [2, 4]:
            return jsonify({'error': 'Habitación especial, no disponible'}), 400

    desde = _parse_date(data.get('hospedaje_desde'))
    hasta = _parse_date(data.get('hospedaje_hasta'))

    # Date validation: hasta must be >= desde
    if desde and hasta and hasta < desde:
        return jsonify({'error': 'La fecha "hasta" no puede ser menor a la fecha "desde"'}), 400

    # Default desde to today when assigning a room
    if hab_id and not desde:
        desde = date.today()

    # Check if DNI already exists — reuse client
    if dni:
        existing = Cliente.query.filter_by(dni=dni).first()
        if existing:
            # Record previous stay if was active in another room
            if existing.activo and existing.habitacion_id:
                _record_estadia(existing)

            existing.nombre = data['nombre']
            existing.apellido = data['apellido']
            existing.telefono = data.get('telefono', '')
            existing.empresa = data.get('empresa', '')
            existing.direccion = data.get('direccion', '')
            existing.hospedaje_desde = desde
            existing.hospedaje_hasta = hasta

            # Free old room if changing
            if existing.habitacion_id and existing.habitacion_id != hab_id:
                old_hab = Habitacion.query.get(existing.habitacion_id)
                if old_hab:
                    other = Cliente.query.filter(
                        Cliente.habitacion_id == old_hab.id,
                        Cliente.activo == True,
                        Cliente.id != existing.id
                    ).count()
                    if other == 0:
                        old_hab.disponible = True

            existing.habitacion_id = hab_id
            existing.activo = True if hab_id else existing.activo

            if hab_id:
                hab = Habitacion.query.get(hab_id)
                if hab:
                    hab.disponible = False

            db.session.commit()
            return jsonify(existing.to_dict()), 200

    cliente = Cliente(
        dni=dni,
        nombre=data['nombre'],
        apellido=data['apellido'],
        telefono=data.get('telefono', ''),
        empresa=data.get('empresa', ''),
        direccion=data.get('direccion', ''),
        hospedaje_desde=desde,
        hospedaje_hasta=hasta,
        habitacion_id=hab_id,
        activo=True if hab_id else data.get('activo', True),
    )

    if hab_id:
        hab = Habitacion.query.get(hab_id)
        if hab:
            hab.disponible = False

    db.session.add(cliente)
    db.session.commit()
    return jsonify(cliente.to_dict()), 201


@app.route('/api/clientes/<int:id>', methods=['PUT'])
def api_update_cliente(id):
    """Update a client."""
    cliente = Cliente.query.get_or_404(id)
    data = request.get_json()

    if 'dni' in data:
        cliente.dni = data.get('dni', '').strip() or None
    if 'nombre' in data:
        cliente.nombre = data['nombre']
    if 'apellido' in data:
        cliente.apellido = data['apellido']
    if 'telefono' in data:
        cliente.telefono = data.get('telefono', '')
    if 'empresa' in data:
        cliente.empresa = data.get('empresa', '')
    if 'direccion' in data:
        cliente.direccion = data.get('direccion', '')
    if 'hospedaje_desde' in data:
        cliente.hospedaje_desde = _parse_date(data.get('hospedaje_desde'))
    if 'hospedaje_hasta' in data:
        cliente.hospedaje_hasta = _parse_date(data.get('hospedaje_hasta'))

    # Handle room assignment change
    if 'habitacion_id' in data:
        old_hab_id = cliente.habitacion_id
        new_hab_id = data.get('habitacion_id')

        # Free old room if leaving it
        if old_hab_id and old_hab_id != new_hab_id:
            _record_estadia(cliente)
            old_hab = Habitacion.query.get(old_hab_id)
            if old_hab:
                other = Cliente.query.filter(
                    Cliente.habitacion_id == old_hab.id,
                    Cliente.activo == True,
                    Cliente.id != cliente.id
                ).count()
                if other == 0:
                    old_hab.disponible = True

        # Assign new room
        cliente.habitacion_id = new_hab_id
        if new_hab_id:
            new_hab = Habitacion.query.get(new_hab_id)
            if new_hab:
                new_hab.disponible = False
                cliente.activo = True
                # Default desde to today if not set
                if not cliente.hospedaje_desde:
                    cliente.hospedaje_desde = date.today()
        elif not new_hab_id and old_hab_id:
            # Unassigning from room
            cliente.activo = False

    db.session.commit()
    return jsonify(cliente.to_dict())


@app.route('/api/clientes/<int:id>', methods=['DELETE'])
def api_delete_cliente(id):
    """Delete a client permanently."""
    cliente = Cliente.query.get_or_404(id)

    # Free the room if this was the last active client
    if cliente.habitacion_id and cliente.activo:
        hab = Habitacion.query.get(cliente.habitacion_id)
        if hab:
            other_active = Cliente.query.filter(
                Cliente.habitacion_id == hab.id,
                Cliente.activo == True,
                Cliente.id != cliente.id
            ).count()
            if other_active == 0:
                hab.disponible = True

    db.session.delete(cliente)
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/clientes/<int:id>/historial', methods=['GET'])
def api_historial_cliente(id):
    """Get all stays for a client."""
    cliente = Cliente.query.get_or_404(id)
    estadias = Estadia.query.filter_by(cliente_id=id).order_by(Estadia.desde.desc()).all()
    return jsonify({
        'cliente': cliente.to_dict(),
        'estadias': [e.to_dict() for e in estadias],
        'total_estadias': len(estadias),
    })


# ── API: Habitaciones ──────────────────────────────────────────

@app.route('/api/habitaciones', methods=['GET'])
def api_get_habitaciones():
    """Get all rooms with their current clients."""
    piso = request.args.get('piso', type=int)
    query = Habitacion.query
    if piso:
        query = query.filter_by(piso=piso)
    habitaciones = query.order_by(Habitacion.piso, Habitacion.numero).all()
    return jsonify([h.to_dict() for h in habitaciones])


@app.route('/api/habitaciones/disponibles', methods=['GET'])
def api_get_habitaciones_disponibles():
    """Get available rooms for assignment dropdown."""
    rooms = Habitacion.query.filter_by(disponible=True, en_mantenimiento=False).order_by(
        Habitacion.piso, Habitacion.numero).all()
    # Exclude special rooms (2 and 4)
    result = [{'id': r.id, 'numero': r.numero, 'piso': r.piso, 'tipo': r.tipo}
              for r in rooms if r.numero not in [2, 4]]
    return jsonify(result)


@app.route('/api/habitaciones/<int:id>', methods=['PUT'])
def api_update_habitacion(id):
    """Update a room (maintenance, type, capacity, etc.)."""
    hab = Habitacion.query.get_or_404(id)
    data = request.get_json()

    if 'en_mantenimiento' in data:
        hab.en_mantenimiento = data['en_mantenimiento']
        if data['en_mantenimiento']:
            hab.disponible = False
        else:
            active = Cliente.query.filter_by(habitacion_id=hab.id, activo=True).count()
            if active == 0:
                hab.disponible = True
    if 'tipo' in data:
        hab.tipo = data['tipo']
    if 'capacidad' in data:
        cap = int(data['capacidad'])
        if cap < 1:
            return jsonify({'error': 'La capacidad debe ser al menos 1'}), 400
        hab.capacidad = cap
    if 'numero' in data:
        new_num = int(data['numero'])
        existing = Habitacion.query.filter(Habitacion.numero == new_num, Habitacion.id != hab.id).first()
        if existing:
            return jsonify({'error': f'Ya existe la habitación {new_num}'}), 400
        hab.numero = new_num

    db.session.commit()
    return jsonify(hab.to_dict())


# ── API: Check-in / Check-out ──────────────────────────────────

@app.route('/api/checkin', methods=['POST'])
def api_checkin():
    """Check in a guest. If DNI exists, reuse that client."""
    data = request.get_json()
    hab_id = data.get('habitacion_id')
    hab = Habitacion.query.get_or_404(hab_id)

    if hab.en_mantenimiento:
        return jsonify({'error': 'Habitación en mantenimiento'}), 400

    # Check capacity
    current_guests = Cliente.query.filter_by(habitacion_id=hab.id, activo=True).count()
    if current_guests >= hab.capacidad:
        return jsonify({'error': f'Habitación llena (máx {hab.capacidad} huéspedes)'}), 400

    # Date validation
    desde = _parse_date(data.get('hospedaje_desde'))
    hasta = _parse_date(data.get('hospedaje_hasta'))
    if desde and hasta and hasta < desde:
        return jsonify({'error': 'La fecha "hasta" no puede ser menor a la fecha "desde"'}), 400

    dni = data.get('dni', '').strip() or None

    # If DNI provided and client exists, reuse
    if dni:
        existing = Cliente.query.filter_by(dni=dni).first()
        if existing:
            # Record previous stay if was active
            if existing.activo and existing.habitacion_id:
                _record_estadia(existing)
            existing.nombre = data.get('nombre', existing.nombre)
            existing.apellido = data.get('apellido', existing.apellido)
            existing.telefono = data.get('telefono', existing.telefono)
            existing.empresa = data.get('empresa', existing.empresa)
            existing.direccion = data.get('direccion', existing.direccion)
            existing.hospedaje_desde = _parse_date(data.get('hospedaje_desde'))
            existing.hospedaje_hasta = _parse_date(data.get('hospedaje_hasta'))
            existing.habitacion_id = hab_id
            existing.activo = True
            hab.disponible = False
            db.session.commit()
            return jsonify(hab.to_dict()), 201

    # New client
    cliente = Cliente(
        dni=dni,
        nombre=data['nombre'],
        apellido=data['apellido'],
        telefono=data.get('telefono', ''),
        empresa=data.get('empresa', ''),
        direccion=data.get('direccion', ''),
        hospedaje_desde=_parse_date(data.get('hospedaje_desde')),
        hospedaje_hasta=_parse_date(data.get('hospedaje_hasta')),
        habitacion_id=hab_id,
        activo=True,
    )

    hab.disponible = False
    db.session.add(cliente)
    db.session.commit()
    return jsonify(hab.to_dict()), 201


@app.route('/api/checkout/<int:hab_id>', methods=['POST'])
def api_checkout(hab_id):
    """Free a room — check out ALL guests."""
    hab = Habitacion.query.get_or_404(hab_id)
    active_clients = Cliente.query.filter_by(habitacion_id=hab.id, activo=True).all()

    for c in active_clients:
        _record_estadia(c)
        c.activo = False
        c.habitacion_id = None

    hab.disponible = True
    db.session.commit()
    return jsonify(hab.to_dict())


@app.route('/api/checkout-guest/<int:client_id>', methods=['POST'])
def api_checkout_guest(client_id):
    """Check out a single guest from a room."""
    cliente = Cliente.query.get_or_404(client_id)
    _record_estadia(cliente)
    hab_id = cliente.habitacion_id
    cliente.activo = False
    cliente.habitacion_id = None

    if hab_id:
        hab = Habitacion.query.get(hab_id)
        remaining = Cliente.query.filter_by(habitacion_id=hab.id, activo=True).count()
        if remaining == 0:
            hab.disponible = True
        db.session.commit()
        return jsonify(hab.to_dict())

    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/reset-all', methods=['POST'])
def api_reset_all():
    """Check out ALL guests from ALL rooms at once."""
    active_clients = Cliente.query.filter_by(activo=True).all()
    for c in active_clients:
        _record_estadia(c)
        c.activo = False
        c.habitacion_id = None

    rooms = Habitacion.query.filter_by(en_mantenimiento=False).all()
    for r in rooms:
        r.disponible = True

    db.session.commit()
    return jsonify({'ok': True, 'liberadas': len(rooms)})


# ── Helpers ────────────────────────────────────────────────────

def _record_estadia(cliente):
    """Save a stay record for the given client before checkout."""
    if not cliente.habitacion_id:
        return
    hab = Habitacion.query.get(cliente.habitacion_id)
    estadia = Estadia(
        cliente_id=cliente.id,
        habitacion_id=cliente.habitacion_id,
        habitacion_numero=hab.numero if hab else None,
        desde=cliente.hospedaje_desde,
        hasta=cliente.hospedaje_hasta,
    )
    db.session.add(estadia)


def _parse_date(s):
    """Parse an ISO date string, return None if invalid."""
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


# ── Run ────────────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(debug=not getattr(sys, 'frozen', False), port=port)
