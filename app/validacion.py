"""
Validacion de la entrada.

MongoDB acepta practicamente cualquier documento. Esa libertad es util, pero
significa que la responsabilidad de que los datos sean coherentes pasa a ser
suya: si usted no valida, la coleccion termina con precios en texto, nombres
vacios y campos escritos de tres maneras distintas.
"""

CAMPOS_PRODUCTO = {"nombre", "precio", "categoria", "descripcion", "stock", "activo"}
CAMPOS_CATEGORIA = {"nombre", "descripcion"}


def _texto(valor):
    return valor.strip() if isinstance(valor, str) else None


def validar_producto(datos, parcial=False):
    """
    Devuelve (documento_limpio, errores).

    parcial=True se usa en PUT: solo valida los campos que vinieron, porque en
    una actualizacion no es obligatorio reenviar el objeto completo.
    """
    errores = {}

    if not isinstance(datos, dict):
        return None, {"_": "El cuerpo debe ser un objeto JSON."}

    sobrantes = set(datos) - CAMPOS_PRODUCTO
    if sobrantes:
        errores["_"] = f"Campos no permitidos: {', '.join(sorted(sobrantes))}."

    limpio = {}

    # --- nombre ---
    if "nombre" in datos:
        nombre = _texto(datos["nombre"])
        if not nombre:
            errores["nombre"] = "El nombre es obligatorio y no puede ir vacio."
        elif len(nombre) > 120:
            errores["nombre"] = "El nombre no puede superar los 120 caracteres."
        else:
            limpio["nombre"] = nombre
    elif not parcial:
        errores["nombre"] = "El nombre es obligatorio."

    # --- precio ---
    if "precio" in datos:
        precio = datos["precio"]
        # bool es subclase de int en Python: True pasaria como numero valido.
        if isinstance(precio, bool) or not isinstance(precio, (int, float)):
            errores["precio"] = "El precio debe ser un numero."
        elif precio < 0:
            errores["precio"] = "El precio no puede ser negativo."
        else:
            limpio["precio"] = float(precio)
    elif not parcial:
        errores["precio"] = "El precio es obligatorio."

    # --- categoria (opcional) ---
    if "categoria" in datos:
        if datos["categoria"] is None:
            limpio["categoria"] = None
        else:
            categoria = _texto(datos["categoria"])
            if not categoria:
                errores["categoria"] = "La categoria no puede ir vacia."
            else:
                limpio["categoria"] = categoria

    # --- descripcion (opcional) ---
    if "descripcion" in datos:
        if datos["descripcion"] is None:
            limpio["descripcion"] = None
        else:
            descripcion = _texto(datos["descripcion"])
            if descripcion and len(descripcion) > 600:
                errores["descripcion"] = "La descripcion no puede superar los 600 caracteres."
            else:
                limpio["descripcion"] = descripcion

    # --- stock (opcional, por defecto 0) ---
    if "stock" in datos:
        stock = datos["stock"]
        if isinstance(stock, bool) or not isinstance(stock, int):
            errores["stock"] = "El stock debe ser un numero entero."
        elif stock < 0:
            errores["stock"] = "El stock no puede ser negativo."
        else:
            limpio["stock"] = stock
    elif not parcial:
        limpio["stock"] = 0

    # --- activo (opcional, por defecto True) ---
    if "activo" in datos:
        if not isinstance(datos["activo"], bool):
            errores["activo"] = "El campo activo debe ser true o false."
        else:
            limpio["activo"] = datos["activo"]
    elif not parcial:
        limpio["activo"] = True

    if parcial and not limpio and not errores:
        errores["_"] = "No se envio ningun campo para actualizar."

    return (None, errores) if errores else (limpio, None)


def validar_categoria(datos, parcial=False):
    errores = {}

    if not isinstance(datos, dict):
        return None, {"_": "El cuerpo debe ser un objeto JSON."}

    sobrantes = set(datos) - CAMPOS_CATEGORIA
    if sobrantes:
        errores["_"] = f"Campos no permitidos: {', '.join(sorted(sobrantes))}."

    limpio = {}

    if "nombre" in datos:
        nombre = _texto(datos["nombre"])
        if not nombre:
            errores["nombre"] = "El nombre es obligatorio y no puede ir vacio."
        elif len(nombre) > 80:
            errores["nombre"] = "El nombre no puede superar los 80 caracteres."
        else:
            limpio["nombre"] = nombre
    elif not parcial:
        errores["nombre"] = "El nombre es obligatorio."

    if "descripcion" in datos:
        limpio["descripcion"] = _texto(datos["descripcion"]) or None

    if parcial and not limpio and not errores:
        errores["_"] = "No se envio ningun campo para actualizar."

    return (None, errores) if errores else (limpio, None)
