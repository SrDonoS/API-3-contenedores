"""
Conexion a MySQL.

La API guarda sus datos en MongoDB. MySQL corre en su propio contenedor con
las mismas tablas del catalogo (mysql/init.sql), y la API solo comprueba que
puede conectarse y leerlo: el resultado aparece en GET /api/salud.

Si MYSQL_HOST no esta definido (por ejemplo, al usar Atlas sin Docker), MySQL
se considera "no configurado" y no se intenta conectar.
"""

from flask import current_app


def probar_mysql():
    """
    Devuelve None si MySQL no esta configurado, o un diccionario con el estado
    de la conexion y cuantas filas tiene cada tabla.
    """
    cfg = current_app.config
    if not cfg.get("MYSQL_HOST"):
        return None

    try:
        import pymysql      # se importa aqui para no exigirlo si no se usa MySQL

        conexion = pymysql.connect(
            host=cfg["MYSQL_HOST"],
            port=cfg["MYSQL_PORT"],
            user=cfg["MYSQL_USER"],
            password=cfg["MYSQL_PASSWORD"],
            database=cfg["MYSQL_DB"],
            connect_timeout=5,
        )
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM categorias")
                categorias = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM productos")
                productos = cursor.fetchone()[0]
        finally:
            conexion.close()

        return {"estado": "ok", "categorias": categorias, "productos": productos}

    except Exception as e:      # sin conexion, clave incorrecta, tabla inexistente...
        return {"estado": "sin conexion", "detalle": str(e)[:200]}
