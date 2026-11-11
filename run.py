"""
Punto de entrada.

    python run.py

Antes de la primera ejecucion:
    1. pip install -r requirements.txt
    2. copie .env.ejemplo como .env y ponga su cadena de Atlas
"""

import os

from app import crear_app
from app.db import crear_indices, probar_conexion
from app.db_mysql import probar_mysql

app = crear_app()

if __name__ == "__main__":
    with app.app_context():
        ok, detalle = probar_conexion()
        if ok:
            crear_indices()
            print(f"  Base de datos: {app.config['MONGO_DB']}  [conectada]")
        else:
            print("  AVISO: no se pudo conectar a MongoDB.")
            print(f"  {detalle[:160]}")
            print("  Revise MONGO_URI en .env y la lista de IP en Atlas "
                  "(Network Access).")

        mysql = probar_mysql()
        if mysql is not None:
            if mysql["estado"] == "ok":
                print(f"  MySQL: {mysql['productos']} productos  [conectada]")
            else:
                print(f"  AVISO: no se pudo conectar a MySQL. {mysql['detalle']}")

    # En su computador escucha solo en 127.0.0.1. Dentro de Docker hay que
    # escuchar en 0.0.0.0, o el puerto publicado no llega a la aplicacion
    # (docker-compose.yml define HOST=0.0.0.0 y FLASK_DEBUG=0).
    host = os.getenv("HOST", "127.0.0.1")
    puerto = int(os.getenv("PORT", "5000"))
    depurar = os.getenv("FLASK_DEBUG", "1") == "1"

    print(f"  API      http://127.0.0.1:{puerto}/api/productos")
    print(f"  Cliente  http://127.0.0.1:{puerto}/")
    app.run(host=host, port=puerto, debug=depurar)
