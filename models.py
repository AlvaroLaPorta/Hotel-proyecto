"""
SQLAlchemy Models — Cliente y Habitacion
"""
from datetime import datetime, date
from database import db


class Habitacion(db.Model):
    __tablename__ = 'habitaciones'

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)
    piso = db.Column(db.Integer, nullable=False, default=1)
    tipo = db.Column(db.String(20), nullable=False, default='normal')  # 'normal' o 'grande'
    capacidad = db.Column(db.Integer, nullable=False, default=2)  # Max guests
    disponible = db.Column(db.Boolean, default=True)
    en_mantenimiento = db.Column(db.Boolean, default=False)

    # Relación con clientes
    clientes = db.relationship('Cliente', backref='habitacion', lazy=True)

    def get_active_clients(self):
        """Return list of active (checked-in) clients."""
        return [c for c in self.clientes if c.activo]

    def to_dict(self):
        active = self.get_active_clients()
        return {
            'id': self.id,
            'numero': self.numero,
            'piso': self.piso,
            'tipo': self.tipo,
            'capacidad': self.capacidad,
            'disponible': self.disponible,
            'en_mantenimiento': self.en_mantenimiento,
            'clientes_activos': [c.to_dict() for c in active],
            'cantidad_huespedes': len(active),
        }


class Cliente(db.Model):
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(20), unique=True, nullable=True)  # Identificador único
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(30), nullable=True)
    empresa = db.Column(db.String(150), nullable=True)
    direccion = db.Column(db.String(250), nullable=True)
    hospedaje_desde = db.Column(db.Date, nullable=True)
    hospedaje_hasta = db.Column(db.Date, nullable=True)
    habitacion_id = db.Column(db.Integer, db.ForeignKey('habitaciones.id'), nullable=True)
    activo = db.Column(db.Boolean, default=True)  # Currently checked in
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'dni': self.dni or '',
            'nombre': self.nombre,
            'apellido': self.apellido,
            'telefono': self.telefono or '',
            'empresa': self.empresa or '',
            'direccion': self.direccion or '',
            'hospedaje_desde': self.hospedaje_desde.isoformat() if self.hospedaje_desde else '',
            'hospedaje_hasta': self.hospedaje_hasta.isoformat() if self.hospedaje_hasta else '',
            'habitacion_id': self.habitacion_id,
            'habitacion_numero': self.habitacion.numero if self.habitacion else None,
            'activo': self.activo,
            'created_at': self.created_at.isoformat() if self.created_at else '',
        }


class Estadia(db.Model):
    """Records each completed stay for history tracking."""
    __tablename__ = 'estadias'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    habitacion_id = db.Column(db.Integer, nullable=True)
    habitacion_numero = db.Column(db.Integer, nullable=True)
    desde = db.Column(db.Date, nullable=True)
    hasta = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship('Cliente', backref=db.backref('estadias', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'habitacion_numero': self.habitacion_numero,
            'desde': self.desde.isoformat() if self.desde else '',
            'hasta': self.hasta.isoformat() if self.hasta else '',
            'created_at': self.created_at.isoformat() if self.created_at else '',
        }

