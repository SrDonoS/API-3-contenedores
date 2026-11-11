"""
CRUD de categorias.

Sirve para mostrar dos cosas que productos no muestra:

  * el indice unique de Mongo rechazando un duplicado (409)
  * una agregacion sencilla: contar productos por categoria
"""

from flask import Blueprint, jsonify

from ..db import obtener_db
from ..respuestas import cuerpo_json, fallar
from ..serializacion import a_json, a_object_id, ahora, lista_a_json
from ..validacion import validar_categoria

bp = Blueprint("categorias", __name__, url_prefix="/api/categorias")


def _buscar_o_404(coleccion, id_texto):
    oid = a_object_id(id_texto)
    if oid is None:
        fallar(400, f"El identificador '{id_texto}' no tiene un formato valido.")
    documento = coleccion.find_one({"_id": oid})
    if documento is None:
        fallar(404, "No existe una categoria con ese identificador.")
    return oid, documento


@bp.get("")
def listar():
    db = obtener_db()
    cursor = db.categorias.find().sort("nombre", 1)
    return jsonify({"datos": lista_a_json(cursor)}), 200


@bp.get("/<id_categoria>")
def obtener(id_categoria):
    db = obtener_db()
    _, documento = _buscar_o_404(db.categorias, id_categoria)
    return jsonify(a_json(documento)), 200


@bp.post("")
def crear():
    db = obtener_db()
    limpio, errores = validar_categoria(cuerpo_json())
    if errores:
        fallar(400, "Hay errores en los datos enviados.", errores)

    # No se comprueba el duplicado con un find previo: entre el find y el
    # insert otro cliente podria insertar el mismo nombre. Se deja que el
    # indice unique lo rechace, y el manejador de DuplicateKeyError responde 409.
    limpio["creado_en"] = ahora()
    resultado = db.categorias.insert_one(limpio)
    creada = db.categorias.find_one({"_id": resultado.inserted_id})

    respuesta = jsonify(a_json(creada))
    respuesta.status_code = 201
    respuesta.headers["Location"] = f"/api/categorias/{resultado.inserted_id}"
    return respuesta


@bp.delete("/<id_categoria>")
def eliminar(id_categoria):
    db = obtener_db()
    oid, categoria = _buscar_o_404(db.categorias, id_categoria)

    # Mongo no tiene claves foraneas: la integridad referencial es suya.
    # Si no se comprueba, quedan productos apuntando a una categoria borrada.
    en_uso = db.productos.count_documents({"categoria": categoria["nombre"]})
    if en_uso:
        fallar(409, f"No se puede eliminar: hay {en_uso} producto(s) en "
                    f"la categoria '{categoria['nombre']}'.")

    db.categorias.delete_one({"_id": oid})
    return "", 204


@bp.get("/resumen")
def resumen():
    """
    Agregacion: cuantos productos y que precio promedio tiene cada categoria.

    Esto en SQL seria GROUP BY. En Mongo es un pipeline: una lista de etapas
    donde la salida de una es la entrada de la siguiente.
    """
    db = obtener_db()
    pipeline = [
        {"$match": {"activo": True}},
        {"$group": {
            "_id": "$categoria",
            "productos": {"$sum": 1},
            "precio_promedio": {"$avg": "$precio"},
            "stock_total": {"$sum": "$stock"},
        }},
        {"$sort": {"productos": -1}},
    ]
    filas = [
        {
            "categoria": f["_id"] or "(sin categoria)",
            "productos": f["productos"],
            "precio_promedio": round(f["precio_promedio"], 2),
            "stock_total": f["stock_total"],
        }
        for f in db.productos.aggregate(pipeline)
    ]
    return jsonify({"datos": filas}), 200
