"""
Conexion a MongoDB.

Una sola conexion para toda la aplicacion. PyMongo ya maneja internamente un
pool de conexiones, asi que NO hay que crear un MongoClient por cada peticion:
eso es el error de rendimiento mas comun al partir.
"""

from flask import current_app, g
from pymongo import MongoClient, ASCENDING, TEXT
from pymongo.errors import ServerSelectionTimeoutError

# El cliente se guarda a nivel de modulo porque debe sobrevivir entre peticiones.
_cliente = None


def obtener_cliente():
    """Devuelve el MongoClient, creandolo la primera vez."""
    global _cliente
    if _cliente is None:
        _cliente = MongoClient(
            current_app.config["MONGO_URI"],
            # Si Atlas no responde en 5 segundos, falla rapido en vez de colgarse.
            serverSelectionTimeoutMS=5000,
            tz_aware=True,
        )
    return _cliente


def obtener_db():
    """Devuelve la base de datos de esta peticion."""
    if "db" not in g:
        g.db = obtener_cliente()[current_app.config["MONGO_DB"]]
    return g.db


def probar_conexion():
    """
    Hace ping al servidor. Sirve para que el error de conexion aparezca al
    arrancar y no en la primera peticion de un alumno confundido.
    """
    try:
        obtener_cliente().admin.command("ping")
        return True, "conexion correcta"
    except ServerSelectionTimeoutError as e:
        return False, str(e)


def crear_indices():
    """
    Los indices se declaran una vez al arrancar. create_index es idempotente:
    si el indice ya existe, no hace nada.
    """
    db = obtener_db()

    # Busquedas y filtros por categoria: el indice que decide si la app sirve.
    db.productos.create_index([("categoria", ASCENDING)], name="idx_categoria")
    db.productos.create_index([("precio", ASCENDING)], name="idx_precio")

    # Indice de texto para buscar por nombre o descripcion.
    db.productos.create_index(
        [("nombre", TEXT), ("descripcion", TEXT)], name="idx_texto"
    )

    # unique=True delega en la base de datos la regla "no hay dos categorias
    # con el mismo nombre". Es mas confiable que comprobarlo en Python.
    db.categorias.create_index([("nombre", ASCENDING)], name="idx_nombre", unique=True)
