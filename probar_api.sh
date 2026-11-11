#!/usr/bin/env bash
# -----------------------------------------------------------------------
# Pruebas de la API desde macOS, Linux o WSL
#
#   bash probar_api.sh
#
# El servidor debe estar corriendo:  python run.py
# -----------------------------------------------------------------------
B=http://127.0.0.1:5000
ok=0; fallo=0

probar() {   # probar "titulo" esperado METODO ruta [cuerpo]
  local titulo="$1" esperado="$2" metodo="$3" ruta="$4" cuerpo="$5"
  local codigo args=(-s -o /tmp/_resp.json -w "%{http_code}" -X "$metodo" "$B$ruta")

  [ -n "$cuerpo" ] && args+=(-H "Content-Type: application/json" -d "$cuerpo")

  codigo=$(curl "${args[@]}")

  if [ "$codigo" = "$esperado" ]; then
    printf "  OK    %-3s %s\n" "$codigo" "$titulo"; ok=$((ok+1))
  else
    printf "  FALLA %-3s %s  (se esperaba %s)\n" "$codigo" "$titulo" "$esperado"; fallo=$((fallo+1))
  fi
}

echo; echo "== Salud =="
probar "la API y la base responden"  200 GET "/api/salud"

echo; echo "== Crear =="
probar "crear producto" 201 POST "/api/productos" \
  '{"nombre":"Producto de prueba","precio":12990,"categoria":"Audio","stock":3}'
ID=$(python3 -c "import json;print(json.load(open('/tmp/_resp.json'))['id'])")
echo "        -> _id que genero MongoDB: $ID"

echo; echo "== Validacion =="
probar "sin precio"              400 POST "/api/productos" '{"nombre":"Sin precio"}'
probar "sin nombre"              400 POST "/api/productos" '{"precio":100}'
probar "precio negativo"         400 POST "/api/productos" '{"nombre":"X","precio":-500}'
probar "precio como texto"       400 POST "/api/productos" '{"nombre":"X","precio":"100"}'
probar "campo no permitido"      400 POST "/api/productos" '{"nombre":"X","precio":100,"_id":"xxx"}'

echo; echo "== Leer =="
probar "listar"                  200 GET "/api/productos"
probar "filtrar por categoria"   200 GET "/api/productos?categoria=Audio"
probar "buscar texto"            200 GET "/api/productos?buscar=mochila"
probar "rango de precio"         200 GET "/api/productos?precio_min=10000&precio_max=50000"
probar "ordenar por precio"      200 GET "/api/productos?orden=precio&dir=desc"
probar "paginar"                 200 GET "/api/productos?pagina=1&tam=3"
probar "obtener uno"             200 GET "/api/productos/$ID"
probar "id inexistente"          404 GET "/api/productos/507f1f77bcf86cd799439011"
probar "id con formato invalido" 400 GET "/api/productos/esto-no-es-un-objectid"

echo; echo "== Actualizar =="
probar "actualizar precio"       200 PUT "/api/productos/$ID" '{"precio":15990}'
probar "actualizar inexistente"  404 PUT "/api/productos/507f1f77bcf86cd799439011" '{"precio":100}'
probar "actualizar sin campos"   400 PUT "/api/productos/$ID" '{}'

echo; echo "== Categorias =="
CAT="Categoria $RANDOM"
probar "crear categoria"         201 POST "/api/categorias" "{\"nombre\":\"$CAT\"}"
CID=$(python3 -c "import json;print(json.load(open('/tmp/_resp.json'))['id'])")
probar "categoria duplicada"     409 POST "/api/categorias" "{\"nombre\":\"$CAT\"}"
probar "resumen por categoria"   200 GET "/api/categorias/resumen"
probar "borrar categoria sin uso" 204 DELETE "/api/categorias/$CID"

echo; echo "== Eliminar =="
probar "eliminar producto"       204 DELETE "/api/productos/$ID"
probar "eliminar de nuevo"       404 DELETE "/api/productos/$ID"

echo
echo "  $ok pruebas correctas, $fallo fallidas"
echo
[ "$fallo" -eq 0 ]
