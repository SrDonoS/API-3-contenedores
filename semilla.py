"""
Carga datos de ejemplo en la base de datos.

    python semilla.py

Borra lo que haya en las colecciones y deja 12 productos y 4 categorias,
para tener con que probar los filtros, el orden y la paginacion.
"""

from datetime import datetime, timezone

from app import crear_app
from app.db import crear_indices, obtener_db, probar_conexion

CATEGORIAS = [
    {"nombre": "Audio", "descripcion": "Audifonos, parlantes y microfonos"},
    {"nombre": "Computacion", "descripcion": "Perifericos y accesorios"},
    {"nombre": "Bolsos", "descripcion": "Mochilas y bolsos para notebook"},
    {"nombre": "Hogar", "descripcion": "Articulos para la casa"},
]

PRODUCTOS = [
    ("Audifonos Bluetooth",   29990,  "Audio",       25, "Inalambricos, estuche de carga"),
    ("Parlante portatil",     19990,  "Audio",       14, "Resistente al agua, 10 h de bateria"),
    ("Microfono de escritorio", 45990, "Audio",       6, "Condensador USB para streaming"),
    ("Teclado mecanico",      59990,  "Computacion", 11, "Switches rojos, retroiluminado"),
    ("Mouse inalambrico",     14990,  "Computacion", 40, "Silencioso, 1600 DPI"),
    ("Hub USB-C 7 en 1",      34990,  "Computacion",  9, "HDMI, lector SD y 3 puertos USB"),
    ("Soporte para notebook", 22990,  "Computacion", 17, "Aluminio, altura regulable"),
    ("Mochila urbana",        45990,  "Bolsos",       8, "Compartimento para notebook de 15"),
    ("Bolso mensajero",       32990,  "Bolsos",       5, "Lona encerada, correa ajustable"),
    ("Lampara de escritorio", 24990,  "Hogar",       12, "LED regulable, tres temperaturas"),
    ("Termo de acero",         18990, "Hogar",       30, "Mantiene la temperatura 12 h"),
    ("Organizador de cables",   6990, "Hogar",        0, "Agotado: sirve para probar el filtro de stock"),
]


def main():
    app = crear_app()
    with app.app_context():
        ok, detalle = probar_conexion()
        if not ok:
            print("  No se pudo conectar a MongoDB.")
            print(f"  {detalle[:200]}")
            print("\n  Revise:")
            print("   1. que MONGO_URI en .env sea la cadena de su cluster")
            print("   2. que su IP este autorizada en Atlas -> Network Access")
            print("   3. que la clave del usuario no tenga caracteres sin codificar")
            return 1

        db = obtener_db()
        db.productos.delete_many({})
        db.categorias.delete_many({})

        ahora = datetime.now(timezone.utc)

        db.categorias.insert_many([{**c, "creado_en": ahora} for c in CATEGORIAS])
        db.productos.insert_many([
            {
                "nombre": n, "precio": float(p), "categoria": c, "stock": s,
                "descripcion": d, "activo": s > 0,
                "creado_en": ahora, "actualizado_en": ahora,
            }
            for n, p, c, s, d in PRODUCTOS
        ])

        crear_indices()

        print(f"  Base de datos '{app.config['MONGO_DB']}' cargada:")
        print(f"   {db.categorias.count_documents({})} categorias")
        print(f"   {db.productos.count_documents({})} productos")
        print(f"   indices: {', '.join(db.productos.index_information())}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
