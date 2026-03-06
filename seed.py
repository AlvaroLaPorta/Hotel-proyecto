"""
Seed script — Initialize the 20 hotel rooms (2 floors) in the database.
Run once: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from database import db
from models import Habitacion

app = create_app()

with app.app_context():
    # Only seed if no rooms exist
    if Habitacion.query.count() == 0:
        rooms = []
        # Piso 1: Habitaciones 1-10
        for i in range(1, 11):
            tipo = 'grande' if i in [3, 7, 10] else 'normal'
            cap = 4 if tipo == 'grande' else 2
            rooms.append(Habitacion(
                numero=i, piso=1, tipo=tipo, capacidad=cap,
                disponible=True, en_mantenimiento=False
            ))
        # Piso 2: Habitaciones 11-20
        for i in range(11, 21):
            tipo = 'grande' if i in [13, 17, 20] else 'normal'
            cap = 4 if tipo == 'grande' else 2
            rooms.append(Habitacion(
                numero=i, piso=2, tipo=tipo, capacidad=cap,
                disponible=True, en_mantenimiento=False
            ))

        db.session.add_all(rooms)
        db.session.commit()
        print("✅ 20 habitaciones creadas (2 pisos × 10 habitaciones).")
    else:
        count = Habitacion.query.count()
        if count < 20:
            # Add missing rooms for floor 2
            existing = {h.numero for h in Habitacion.query.all()}
            for i in range(11, 21):
                if i not in existing:
                    tipo = 'grande' if i in [13, 17, 20] else 'normal'
                    db.session.add(Habitacion(
                        numero=i, piso=2, tipo=tipo,
                        disponible=True, en_mantenimiento=False
                    ))
            db.session.commit()
            print(f"✅ Habitaciones del piso 2 añadidas. Total: {Habitacion.query.count()}")
        else:
            print(f"ℹ️  Ya existen {count} habitaciones en la base de datos.")
