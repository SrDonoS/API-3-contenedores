"""
CRUD de productos.

Las cinco operaciones de siempre, ahora contra una coleccion de MongoDB en
lugar de una tabla:

    GET    /api/productos        listar (con filtros y paginacion)
    GET    /api/productos/<id>   obtener uno
    POST   /api/productos        crear
    PUT    /api/productos/<id>   actualizar
    DELETE /api/productos/<id>   eliminar
"""

from flask import Blueprint, jsonify, request
from pymongo import ASCENDING, DESCENDING, ReturnDocument

from ..db import obtener_db
from ..respuestas import cuerpo_json, fallar
from ..serializacion import a_json, a_object_id, ahora, lista_a_json
from ..validacion import validar_producto

bp = Blueprint("productos", __name__, url_prefix="/api/productos")

ORDENES_VALIDOS = {"nombre", "precio", "stock", "creado_en"}


def _buscar_o_404(coleccion, id_texto):
    oid = a_object_id(id_texto)
    if oid is None:
        # El id no tiene forma de ObjectId: es la peticion la que esta mal.
        fallar(400, f"El identificador '{id_texto}' no tiene un formato valido.")
    documento = coleccion.find_one({"_id": oid})
    if documento is None:
        fallar(404, "No existe un producto con ese identificador.")
    return oid, documento


# ---------------------------------------------------------------- LISTAR
@bp.get("")
def listar():
    """
    Filtros por query string:
        ?categoria=Audio      filtra por categoria exacta
        ?buscar=mochila       busca en nombre y descripcion
        ?precio_min=1000&precio_max=50000
        ?activo=true
        ?orden=precio&dir=desc
        ?pagina=1&tam=10
    """
    db = obtener_db()
    filtro = {}

    if categoria := request.args.get("categoria"):
        filtro["categoria"] = categoria

    if buscar := request.args.get("buscar"):
        # Expresion regular sin distinguir mayusculas. Para catalogos grandes
        # conviene $text con el indice de texto; aqui se usa regex porque es
        # mas facil de leer en clase y funciona con busquedas parciales.
        filtro["$or"] = [
            {"nombre": {"$regex": buscar, "$options": "i"}},
            {"descripcion": {"$regex": buscar, "$options": "i"}},
        ]

    rango = {}
    for parametro, operador in (("precio_min", "$gte"), ("precio_max", "$lte")):
        if (valor := request.args.get(parametro)) is not None:
            try:
                rango[operador] = float(valor)
            except ValueError:
                fallar(400, f"El parametro {parametro} debe ser un numero.")
    if rango:
        filtro["precio"] = rango

    if (activo := request.args.get("activo")) is not None:
        filtro["activo"] = activo.lower() in ("true", "1", "si")

    # --- orden ---
    campo = request.args.get("orden", "creado_en")
    if campo not in ORDENES_VALIDOS:
        fallar(400, f"No se puede ordenar por '{campo}'.",
                {"validos": sorted(ORDENES_VALIDOS)})
    direccion = DESCENDING if request.args.get("dir", "asc") == "desc" else ASCENDING

    # --- paginacion ---
    try:
        pagina = max(1, int(request.args.get("pagina", 1)))
        tam = min(100, max(1, int(request.args.get("tam", 10))))
    except ValueError:
        fallar(400, "Los parametros pagina y tam deben ser numeros enteros.")

    total = db.productos.count_documents(filtro)
    cursor = (db.productos.find(filtro)
              .sort(campo, direccion)
              .skip((pagina - 1) * tam)
              .limit(tam))

    return jsonify({
        "datos": lista_a_json(cursor),
        "paginacion": {
            "pagina": pagina,
            "tam": tam,
            "total": total,
            "paginas": (total + tam - 1) // tam,
        },
    }), 200


# ---------------------------------------------------------------- OBTENER
@bp.get("/<id_producto>")
def obtener(id_producto):
    db = obtener_db()
    _, documento = _buscar_o_404(db.productos, id_producto)
    return jsonify(a_json(documento)), 200


# ---------------------------------------------------------------- CREAR
@bp.post("")
def crear():
    db = obtener_db()
    limpio, errores = validar_producto(cuerpo_json())
    if errores:
        fallar(400, "Hay errores en los datos enviados.", errores)

    limpio["creado_en"] = ahora()
    limpio["actualizado_en"] = limpio["creado_en"]

    # insert_one devuelve el _id que Mongo genero. No hay que pedirlo aparte.
    resultado = db.productos.insert_one(limpio)
    creado = db.productos.find_one({"_id": resultado.inserted_id})

    # 201 y la cabecera Location: donde queda el recurso que se acaba de crear.
    respuesta = jsonify(a_json(creado))
    respuesta.status_code = 201
    respuesta.headers["Location"] = f"/api/productos/{resultado.inserted_id}"
    return respuesta


# ---------------------------------------------------------------- ACTUALIZAR
@bp.put("/<id_producto>")
def actualizar(id_producto):
    db = obtener_db()
    oid, _ = _buscar_o_404(db.productos, id_producto)

    limpio, errores = validar_producto(cuerpo_json(), parcial=True)
    if errores:
        fallar(400, "Hay errores en los datos enviados.", errores)

    limpio["actualizado_en"] = ahora()

    # find_one_and_update con return_document=AFTER devuelve el documento ya
    # modificado en una sola ida a la base de datos.
    actualizado = db.productos.find_one_and_update(
        {"_id": oid},
        {"$set": limpio},                       # $set cambia solo esos campos
        return_document=ReturnDocument.AFTER,
    )
    return jsonify(a_json(actualizado)), 200


# ---------------------------------------------------------------- ELIMINAR
@bp.delete("/<id_producto>")
def eliminar(id_producto):
    db = obtener_db()
    oid, _ = _buscar_o_404(db.productos, id_producto)
    db.productos.delete_one({"_id": oid})
    # 204: se borro y no hay nada que devolver.
    return "", 204
