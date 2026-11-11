# API CRUD con Flask y MongoDB Atlas

La misma API de catálogo que construimos sobre SQL, ahora guardando en una
base de datos de documentos. **El contrato HTTP no cambió**: las mismas rutas,
los mismos códigos de estado, el mismo JSON. Lo único que cambió es dónde y
cómo se guardan los datos.

Ese es el punto de la clase: el cliente no se entera de qué motor hay detrás.

---

## 1. Qué necesita antes de empezar

* Python 3.10 o superior
* Una cuenta gratuita en <https://www.mongodb.com/cloud/atlas/register>

No hace falta instalar MongoDB en su computador: el clúster vive en la nube.

---

## 2. Crear el clúster en Atlas

Cinco pasos. Los dos que más fallan son el 3 y el 4, así que no los salte.

| # | Paso | Detalle |
|---|------|---------|
| 1 | Cree una cuenta y un proyecto | Cualquier nombre sirve |
| 2 | **Create** → nivel **M0 (Free)** | Elija la región más cercana (São Paulo) |
| 3 | **Database Access** → *Add New Database User* | Anote usuario y contraseña: la contraseña **no se puede volver a ver** |
| 4 | **Network Access** → *Add IP Address* | Para el laboratorio: *Allow access from anywhere* (`0.0.0.0/0`) |
| 5 | **Connect** → *Drivers* → Python | Copie la cadena de conexión |

> **Sobre el paso 4:** `0.0.0.0/0` significa "desde cualquier IP del mundo".
> Es aceptable para un clúster de práctica con datos de juguete, y es
> inaceptable en producción. En un sistema real se autorizan solo las IP de
> los servidores que deben conectarse.

### El nivel gratuito M0, con sus números reales

| Límite | Valor |
|---|---|
| Almacenamiento | 512 MB |
| Conexiones simultáneas | 500 |
| Bases de datos / colecciones | 100 / 500 |
| Operaciones | 100 por segundo |
| Transferencia | 10 GB de entrada y 10 GB de salida cada 7 días |
| Respaldos | No incluidos |
| Versión de MongoDB | 8.0 |
| Inactividad | Se pausa solo tras 30 días sin conexiones |

Gratis para siempre, sin tarjeta de crédito.

---

## 3. Configurar el proyecto

```powershell
# Windows / PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.ejemplo .env
notepad .env          # pegue aquí su cadena de conexión
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.ejemplo .env
nano .env
```

El archivo `.env` queda así:

```
MONGO_URI=mongodb+srv://chalalo:MiClave123@cluster0.ab1cd.mongodb.net/?retryWrites=true&w=majority
MONGO_DB=catalogo
```

> **`.env` nunca se sube al repositorio.** Lleva usuario y contraseña. Ya está
> en el `.gitignore`. Lo que sí se sube es `.env.ejemplo`, con los nombres de
> las variables y sin los valores.

> **Si su contraseña tiene `@`, `/`, `:` o `#`**, hay que codificarla, o la
> cadena de conexión se parte en el lugar equivocado:
> ```python
> from urllib.parse import quote_plus
> print(quote_plus("mi@clave/rara"))     # mi%40clave%2Frara
> ```

---

## 4. Cargar datos y levantar

```powershell
python semilla.py      # 12 productos y 4 categorías de ejemplo
python run.py
```

* API → <http://127.0.0.1:5000/api/productos>
* Cliente web → <http://127.0.0.1:5000/>
* Estado → <http://127.0.0.1:5000/api/salud>

---

## 5. Los endpoints

| Método | Ruta | Qué hace | Éxito |
|---|---|---|---|
| GET | `/api/salud` | Comprueba que la base responde | 200 |
| GET | `/api/productos` | Lista con filtros y paginación | 200 |
| GET | `/api/productos/<id>` | Un producto | 200 |
| POST | `/api/productos` | Crea | 201 |
| PUT | `/api/productos/<id>` | Actualiza (parcial) | 200 |
| DELETE | `/api/productos/<id>` | Elimina | 204 |
| GET | `/api/categorias` | Lista categorías | 200 |
| POST | `/api/categorias` | Crea categoría (nombre único) | 201 |
| DELETE | `/api/categorias/<id>` | Elimina si no está en uso | 204 |
| GET | `/api/categorias/resumen` | Agregación: conteo y promedio por categoría | 200 |

### Filtros de `GET /api/productos`

```
?categoria=Audio
?buscar=mochila                  busca en nombre y descripción, sin distinguir mayúsculas
?precio_min=10000&precio_max=50000
?activo=true
?orden=precio&dir=desc           orden: nombre | precio | stock | creado_en
?pagina=2&tam=5                  tam máximo 100
```

### Respuestas de error

Todas tienen la misma forma:

```json
{
  "error": "Hay errores en los datos enviados.",
  "detalle": { "precio": "El precio no puede ser negativo." }
}
```

| Código | Cuándo |
|---|---|
| 400 | Datos inválidos, o el id no tiene forma de ObjectId |
| 404 | El id tiene forma válida pero no existe ese documento |
| 405 | Método no permitido en esa ruta |
| 409 | Nombre de categoría duplicado, o categoría con productos |
| 415 | El cuerpo no venía como `application/json` |
| 503 | No se pudo conectar a Atlas |

---

## 6. Probar

```powershell
.\probar_api.ps1      # Windows
bash probar_api.sh    # macOS / Linux / WSL
```

Y sin Atlas ni internet, con una base de datos en memoria:

```bash
pip install mongomock
python pruebas_locales.py
```

---

## 7. Los seis errores de la primera vez

| Lo que ve | Qué pasa | Qué hacer |
|---|---|---|
| `Object of type ObjectId is not JSON serializable` | Devolvió el documento tal cual | Páselo por `a_json()`, que convierte `_id` a texto |
| `ServerSelectionTimeoutError` tras 30 s | Su IP no está autorizada | Atlas → Network Access → agregue su IP |
| `Authentication failed` | Usuario o contraseña mal | Database Access → *Edit* → cambie la contraseña |
| La cadena se corta rara | La contraseña tiene `@` o `/` | Codifíquela con `quote_plus()` |
| `InvalidId: ... is not a valid ObjectId` | Le pasó un id que no es de Mongo | Ya está resuelto: devuelve 400, no 500 |
| Guardó un producto con precio 0 | En JavaScript `Number('')` es `0`, no `NaN` | No envíe el campo si viene vacío (vea `cliente/index.html`) |

---

## 8. Estructura

```
api_mongo/
  run.py                  arranque: ping, índices, servidor
  config.py               lee .env
  semilla.py              datos de ejemplo
  pruebas_locales.py      39 pruebas sin necesidad de Atlas
  probar_api.ps1 / .sh    pruebas contra el servidor corriendo
  .env.ejemplo            plantilla (el .env real no se sube)
  app/
    __init__.py           fábrica crear_app()
    db.py                 cliente, base de datos, ping, índices
    serializacion.py      ObjectId <-> JSON
    validacion.py         reglas de los datos
    respuestas.py         fallar() y cuerpo_json()
    errores.py            manejadores en español
    rutas/
      productos.py        el CRUD
      categorias.py       índice único y agregación
  cliente/
    index.html            cliente web sin dependencias
```

---

## 9. Lo que vale la pena mirar en el código

1. **`serializacion.py`** — existe solo porque `_id` es un `ObjectId` y
   `jsonify()` no sabe convertirlo. Es el primer tropiezo de todos.
2. **`validacion.py`** — Mongo acepta cualquier documento. La coherencia de los
   datos pasa a ser responsabilidad suya, no del motor.
3. **`categorias.py`, `crear()`** — no se comprueba el duplicado con un `find`
   previo: se deja que el índice `unique` lo rechace. Entre el `find` y el
   `insert` otro cliente podría insertar el mismo nombre.
4. **`categorias.py`, `eliminar()`** — MongoDB no tiene claves foráneas. La
   integridad referencial se programa a mano o no existe.
5. **`db.py`** — un solo `MongoClient` para toda la aplicación. Crear uno por
   petición es el error de rendimiento más común.

---

## 10. Con Docker: API, MongoDB y MySQL

Tres contenedores definidos en `docker-compose.yml`:

| Contenedor | Imagen | Puerto en su computador |
|---|---|---|
| `catalogo-api` | se construye con el `Dockerfile` | 5000 |
| `catalogo-mongo` | `mongo:8.0` (oficial) | 27017 |
| `catalogo-mysql` | `mysql:8.4` (oficial) | 3307 (usuario `catalogo` / `catalogo123`) |

La API guarda sus datos en MongoDB. MySQL arranca con las mismas tablas del
catalogo y 12 productos (`mysql/init.sql`), y `GET /api/salud` muestra que la
API se conecta a las dos bases.

```powershell
docker compose up -d --build                 # construye la imagen y levanta todo
docker compose ps                            # los tres deben decir "healthy" o "Up"
docker compose exec api python semilla.py    # datos de ejemplo en Mongo
```

* Estado → <http://localhost:5000/api/salud>
* Cliente web → <http://localhost:5000/>

```powershell
docker compose logs api       # ver errores de la API
docker compose down           # apagar (los datos se conservan)
docker compose down -v        # apagar y borrar los datos (init.sql se vuelve a ejecutar)
```
