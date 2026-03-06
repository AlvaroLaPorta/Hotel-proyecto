"""
Database configuration — SQLAlchemy + SQLite
"""
import os
import sys
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# When running as a PyInstaller bundle, store DB next to the exe
if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def init_db(app):
    """Initialize the database with the Flask app."""
    db_path = os.path.join(_BASE_DIR, 'hotel.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        from models import Cliente, Habitacion, Estadia  # noqa
        db.create_all()
        # Auto-seed if empty
        if Habitacion.query.count() == 0:
            _seed_rooms()


def _seed_rooms():
    """Create the initial 20 rooms."""
    from models import Habitacion
    rooms = []
    for i in range(1, 11):
        tipo = 'grande' if i in [3, 7, 10] else 'normal'
        cap = 4 if tipo == 'grande' else 2
        rooms.append(Habitacion(numero=i, piso=1, tipo=tipo, capacidad=cap,
                                disponible=True, en_mantenimiento=False))
    for i in range(11, 21):
        tipo = 'grande' if i in [13, 17, 20] else 'normal'
        cap = 4 if tipo == 'grande' else 2
        rooms.append(Habitacion(numero=i, piso=2, tipo=tipo, capacidad=cap,
                                disponible=True, en_mantenimiento=False))
    db.session.add_all(rooms)
    db.session.commit()
