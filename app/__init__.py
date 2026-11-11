"""
Fabrica de la aplicacion.

crear_app() arma la aplicacion y la devuelve. Este patron permite crear una
aplicacion distinta para las pruebas (con otra base de datos) sin tocar nada.
"""

from flask import Flask, jsonify, send_from_directory

from .errores import registrar_errores


def crear_app(config=None):
    app = Flask(__name__, static_folder=None)

    # Configuracion por defecto, sobreescribible al llamar crear_app(...)
    from config import Config
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    # Para que jsonify no reordene las claves alfabeticamente.
    app.json.sort_keys = False

    registrar_errores(app)

    from .rutas.productos import bp as bp_productos
    from .rutas.categorias import bp as bp_categorias
    app.register_blueprint(bp_productos)
    app.register_blueprint(bp_categorias)

    @app.get("/api/salud")
    def salud():
        """Comprueba que la API responde y que las bases de datos contestan."""
        from .db import probar_conexion
        from .db_mysql import probar_mysql
        ok, detalle = probar_conexion()
        mysql = probar_mysql()          # None si MySQL no esta configurado
        mysql_ok = mysql is None or mysql["estado"] == "ok"
        return jsonify({
            "api": "ok",
            "base_de_datos": "ok" if ok else "sin conexion",
            "detalle": detalle,
            "motor": "MongoDB",
            "mysql": mysql if mysql is not None else "no configurado",
        }), (200 if ok and mysql_ok else 503)

    @app.get("/")
    def cliente():
        """Cliente web minimo para probar la API desde el navegador."""
        import os
        carpeta = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cliente")
        return send_from_directory(carpeta, "index.html")

    return app
