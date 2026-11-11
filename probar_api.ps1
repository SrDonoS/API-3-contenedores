# -----------------------------------------------------------------------
# Pruebas de la API desde PowerShell (Windows)
#
#   .\probar_api.ps1
#
# El servidor debe estar corriendo:  python run.py
# -----------------------------------------------------------------------

$B = "http://127.0.0.1:5000"
$ok = 0; $fallo = 0

function Probar($titulo, $esperado, $metodo, $ruta, $cuerpo) {
    $params = @{ Uri = "$B$ruta"; Method = $metodo; SkipHttpErrorCheck = $true }
    if ($cuerpo) {
        $params.Body        = $cuerpo
        $params.ContentType = "application/json"
    }

    $r = Invoke-WebRequest @params
    $codigo = [int]$r.StatusCode

    if ($codigo -eq $esperado) {
        Write-Host ("  OK    {0,-3} {1}" -f $codigo, $titulo) -ForegroundColor Green
        $script:ok++
    } else {
        Write-Host ("  FALLA {0,-3} {1}  (se esperaba {2})" -f $codigo, $titulo, $esperado) -ForegroundColor Red
        $script:fallo++
    }
    return $r
}

# =======================================================================
Write-Host "`n== Salud ==" -ForegroundColor Cyan
Probar "la API y la base responden"   200 GET "/api/salud"                     | Out-Null

Write-Host "`n== Crear ==" -ForegroundColor Cyan
$r = Probar "crear producto"          201 POST "/api/productos" '{"nombre":"Producto de prueba","precio":12990,"categoria":"Audio","stock":3}'
$id = ($r.Content | ConvertFrom-Json).id
Write-Host "        -> _id que genero MongoDB: $id" -ForegroundColor DarkGray

Write-Host "`n== Validacion ==" -ForegroundColor Cyan
Probar "sin precio"                   400 POST "/api/productos" '{"nombre":"Sin precio"}'                  | Out-Null
Probar "sin nombre"                   400 POST "/api/productos" '{"precio":100}'                           | Out-Null
Probar "precio negativo"              400 POST "/api/productos" '{"nombre":"X","precio":-500}'             | Out-Null
Probar "precio como texto"            400 POST "/api/productos" '{"nombre":"X","precio":"100"}'            | Out-Null
Probar "campo no permitido"           400 POST "/api/productos" '{"nombre":"X","precio":100,"_id":"xxx"}'  | Out-Null

Write-Host "`n== Leer ==" -ForegroundColor Cyan
Probar "listar"                       200 GET "/api/productos"                            | Out-Null
Probar "filtrar por categoria"        200 GET "/api/productos?categoria=Audio"            | Out-Null
Probar "buscar texto"                 200 GET "/api/productos?buscar=mochila"             | Out-Null
Probar "rango de precio"              200 GET "/api/productos?precio_min=10000&precio_max=50000" | Out-Null
Probar "ordenar por precio"           200 GET "/api/productos?orden=precio&dir=desc"      | Out-Null
Probar "paginar"                      200 GET "/api/productos?pagina=1&tam=3"             | Out-Null
Probar "obtener uno"                  200 GET "/api/productos/$id"                        | Out-Null
Probar "id inexistente"               404 GET "/api/productos/507f1f77bcf86cd799439011"   | Out-Null
Probar "id con formato invalido"      400 GET "/api/productos/esto-no-es-un-objectid"     | Out-Null

Write-Host "`n== Actualizar ==" -ForegroundColor Cyan
Probar "actualizar precio"            200 PUT "/api/productos/$id" '{"precio":15990}'                      | Out-Null
Probar "actualizar inexistente"       404 PUT "/api/productos/507f1f77bcf86cd799439011" '{"precio":100}'   | Out-Null
Probar "actualizar sin campos"        400 PUT "/api/productos/$id" '{}'                                    | Out-Null

Write-Host "`n== Categorias ==" -ForegroundColor Cyan
$cat = "Categoria $(Get-Random)"
$r = Probar "crear categoria"         201 POST "/api/categorias" "{`"nombre`":`"$cat`"}"
$cid = ($r.Content | ConvertFrom-Json).id
Probar "categoria duplicada"          409 POST "/api/categorias" "{`"nombre`":`"$cat`"}"   | Out-Null
Probar "resumen por categoria"        200 GET "/api/categorias/resumen"                    | Out-Null
Probar "borrar categoria sin uso"     204 DELETE "/api/categorias/$cid"                    | Out-Null

Write-Host "`n== Eliminar ==" -ForegroundColor Cyan
Probar "eliminar producto"            204 DELETE "/api/productos/$id"  | Out-Null
Probar "eliminar de nuevo"            404 DELETE "/api/productos/$id"  | Out-Null

Write-Host ""
Write-Host "  $ok pruebas correctas, $fallo fallidas" -ForegroundColor $(if ($fallo -eq 0) { "Green" } else { "Red" })
Write-Host ""
