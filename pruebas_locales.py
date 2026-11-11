"""
Prueba la API completa SIN necesidad de Atlas ni de un MongoDB instalado,
reemplazando el cliente real por uno en memoria (mongomock).

    pip install mongomock
    python pruebas_locales.py

Esto NO reemplaza probar contra Atlas: sirve para verificar que la logica de
las rutas, la validacion y los codigos de estado son correctos.
"""

import sys

import mongomock

import app.db as db_modulo
from app import crear_app

# --- reemplaza el cliente real por uno en memoria -----------------------
_falso = mongomock.MongoClient()
db_modulo.obtener_cliente = lambda: _falso

aplicacion = crear_app({"MONGO_DB": "catalogo_prueba"})

ok = fallo = 0


def probar(titulo, esperado, metodo, ruta, cuerpo=None):
    global ok, fallo
    with aplicacion.test_client() as c:
        r = getattr(c, metodo.lower())(ruta, json=cuerpo) if cuerpo is not None \
            else getattr(c, metodo.lower())(ruta)
    if r.status_code == esperado:
        print(f"  OK    {r.status_code:<3} {titulo}")
        ok += 1
    else:
        detalle = r.get_json(silent=True)
        print(f"  FALLA {r.status_code:<3} {titulo}  (se esperaba {esperado})")
        print(f"        -> {detalle}")
        fallo += 1
    return r


with aplicacion.app_context():
    db_modulo.crear_indices()

print("\n== Crear ==")
r = probar("crear producto", 201, "POST", "/api/productos",
           {"nombre": "Audifonos BT", "precio": 29990, "categoria": "Audio",
            "stock": 12, "descripcion": "Inalambricos con estuche"})
creado = r.get_json()
pid = creado["id"]
print(f"        -> id generado por Mongo: {pid}")
assert "_id" not in creado, "el _id no debe salir en la respuesta"
assert r.headers.get("Location") == f"/api/productos/{pid}", "falta Location"

probar("crear segundo producto", 201, "POST", "/api/productos",
       {"nombre": "Mochila urbana", "precio": 45990, "categoria": "Bolsos", "stock": 5})
probar("crear tercero", 201, "POST", "/api/productos",
       {"nombre": "Parlante portatil", "precio": 19990, "categoria": "Audio", "stock": 0})

print("\n== Validacion ==")
probar("sin precio", 400, "POST", "/api/productos", {"nombre": "Sin precio"})
probar("sin nombre", 400, "POST", "/api/productos", {"precio": 100})
probar("nombre vacio", 400, "POST", "/api/productos", {"nombre": "   ", "precio": 100})
probar("precio negativo", 400, "POST", "/api/productos", {"nombre": "X", "precio": -5})
probar("precio como texto", 400, "POST", "/api/productos", {"nombre": "X", "precio": "100"})
probar("precio booleano", 400, "POST", "/api/productos", {"nombre": "X", "precio": True})
probar("stock negativo", 400, "POST", "/api/productos",
       {"nombre": "X", "precio": 100, "stock": -1})
probar("campo no permitido", 400, "POST", "/api/productos",
       {"nombre": "X", "precio": 100, "_id": "hackeado"})

print("\n== Leer ==")
probar("listar", 200, "GET", "/api/productos")
probar("filtrar por categoria", 200, "GET", "/api/productos?categoria=Audio")
probar("buscar texto", 200, "GET", "/api/productos?buscar=mochila")
probar("rango de precio", 200, "GET", "/api/productos?precio_min=20000&precio_max=50000")
probar("ordenar por precio desc", 200, "GET", "/api/productos?orden=precio&dir=desc")
probar("paginar", 200, "GET", "/api/productos?pagina=1&tam=2")
probar("obtener uno", 200, "GET", f"/api/productos/{pid}")
probar("id inexistente", 404, "GET", "/api/productos/507f1f77bcf86cd799439011")
probar("id con formato invalido", 400, "GET", "/api/productos/no-es-un-objectid")
probar("ordenar por campo invalido", 400, "GET", "/api/productos?orden=ninguno")
probar("pagina no numerica", 400, "GET", "/api/productos?pagina=abc")

# --- comprobaciones de contenido, no solo de codigo ---
with aplicacion.test_client() as c:
    cuerpo = c.get("/api/productos?categoria=Audio").get_json()
    assert cuerpo["paginacion"]["total"] == 2, cuerpo["paginacion"]
    assert all(p["categoria"] == "Audio" for p in cuerpo["datos"])

    cuerpo = c.get("/api/productos?buscar=MOCHILA").get_json()
    assert cuerpo["paginacion"]["total"] == 1, "la busqueda debe ignorar mayusculas"

    cuerpo = c.get("/api/productos?orden=precio&dir=desc").get_json()
    precios = [p["precio"] for p in cuerpo["datos"]]
    assert precios == sorted(precios, reverse=True), precios

    cuerpo = c.get("/api/productos?pagina=1&tam=2").get_json()
    assert len(cuerpo["datos"]) == 2 and cuerpo["paginacion"]["paginas"] == 2, cuerpo
print("  OK    comprobaciones de contenido (filtro, busqueda, orden, paginas)")
ok += 1

print("\n== Actualizar ==")
r = probar("actualizar precio", 200, "PUT", f"/api/productos/{pid}", {"precio": 24990})
assert r.get_json()["precio"] == 24990
assert r.get_json()["nombre"] == "Audifonos BT", "PUT parcial no debe borrar el resto"
probar("actualizar inexistente", 404, "PUT",
       "/api/productos/507f1f77bcf86cd799439011", {"precio": 1})
probar("actualizar sin campos", 400, "PUT", f"/api/productos/{pid}", {})
probar("actualizar con precio invalido", 400, "PUT", f"/api/productos/{pid}",
       {"precio": "caro"})

print("\n== Categorias ==")
r = probar("crear categoria", 201, "POST", "/api/categorias", {"nombre": "Audio"})
cid = r.get_json()["id"]
probar("categoria duplicada", 409, "POST", "/api/categorias", {"nombre": "Audio"})
probar("listar categorias", 200, "GET", "/api/categorias")
probar("resumen por categoria", 200, "GET", "/api/categorias/resumen")
probar("borrar categoria en uso", 409, "DELETE", f"/api/categorias/{cid}")

with aplicacion.test_client() as c:
    filas = c.get("/api/categorias/resumen").get_json()["datos"]
    audio = next(f for f in filas if f["categoria"] == "Audio")
    assert audio["productos"] == 2, filas
    assert audio["stock_total"] == 12, filas
print("  OK    la agregacion suma y agrupa correctamente")
ok += 1

print("\n== Eliminar ==")
probar("eliminar producto", 204, "DELETE", f"/api/productos/{pid}")
probar("eliminar de nuevo", 404, "DELETE", f"/api/productos/{pid}")
probar("ya no aparece", 404, "GET", f"/api/productos/{pid}")

print("\n== Varios ==")
probar("metodo no permitido", 405, "PATCH", f"/api/productos/{pid}")
probar("ruta inexistente", 404, "GET", "/api/noexiste")

with aplicacion.test_client() as c:
    r = c.post("/api/productos", data="esto no es json",
               content_type="text/plain")
    print(f"  {'OK   ' if r.status_code == 415 else 'FALLA'} {r.status_code:<3} "
          f"cuerpo que no es JSON")
    ok += 1 if r.status_code == 415 else 0
    fallo += 0 if r.status_code == 415 else 1

print(f"\n  {ok} pruebas correctas, {fallo} fallidas\n")
sys.exit(1 if fallo else 0)
