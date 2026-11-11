-- ---------------------------------------------------------------------------
-- Base de datos MySQL del catalogo: el mismo modelo que en MongoDB, en tablas.
--
-- Docker ejecuta este archivo SOLO la primera vez que se crea el contenedor
-- (cuando el volumen mysql_datos esta vacio). Para volver a ejecutarlo:
--     docker compose down -v      (borra los datos)
--     docker compose up -d
-- ---------------------------------------------------------------------------

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS catalogo
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE catalogo;

-- Lo que en Mongo hace el indice unique, aqui lo hace la restriccion UNIQUE.
CREATE TABLE IF NOT EXISTS categorias (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(80)  NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    creado_en   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Diferencia clave con Mongo: aqui SI hay clave foranea. El motor impide
-- borrar una categoria que tiene productos (ON DELETE RESTRICT).
CREATE TABLE IF NOT EXISTS productos (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    nombre         VARCHAR(120)  NOT NULL,
    precio         DECIMAL(12,2) NOT NULL CHECK (precio >= 0),
    categoria_id   INT NULL,
    descripcion    VARCHAR(600),
    stock          INT           NOT NULL DEFAULT 0 CHECK (stock >= 0),
    activo         BOOLEAN       NOT NULL DEFAULT TRUE,
    creado_en      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_producto_categoria
        FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        ON DELETE RESTRICT,
    INDEX idx_precio (precio)
);

INSERT INTO categorias (nombre, descripcion) VALUES
    ('Audio',       'Audifonos, parlantes y microfonos'),
    ('Computacion', 'Perifericos y accesorios'),
    ('Bolsos',      'Mochilas y bolsos para notebook'),
    ('Hogar',       'Articulos para la casa');

INSERT INTO productos (nombre, precio, categoria_id, stock, descripcion, activo)
SELECT p.nombre, p.precio, c.id, p.stock, p.descripcion, p.stock > 0
FROM (
              SELECT 'Audifonos Bluetooth' AS nombre, 29990 AS precio, 'Audio' AS cat, 25 AS stock, 'Inalambricos, estuche de carga' AS descripcion
    UNION ALL SELECT 'Parlante portatil',       19990, 'Audio',       14, 'Resistente al agua, 10 h de bateria'
    UNION ALL SELECT 'Microfono de escritorio', 45990, 'Audio',        6, 'Condensador USB para streaming'
    UNION ALL SELECT 'Teclado mecanico',        59990, 'Computacion', 11, 'Switches rojos, retroiluminado'
    UNION ALL SELECT 'Mouse inalambrico',       14990, 'Computacion', 40, 'Silencioso, 1600 DPI'
    UNION ALL SELECT 'Hub USB-C 7 en 1',        34990, 'Computacion',  9, 'HDMI, lector SD y 3 puertos USB'
    UNION ALL SELECT 'Soporte para notebook',   22990, 'Computacion', 17, 'Aluminio, altura regulable'
    UNION ALL SELECT 'Mochila urbana',          45990, 'Bolsos',       8, 'Compartimento para notebook de 15'
    UNION ALL SELECT 'Bolso mensajero',         32990, 'Bolsos',       5, 'Lona encerada, correa ajustable'
    UNION ALL SELECT 'Lampara de escritorio',   24990, 'Hogar',       12, 'LED regulable, tres temperaturas'
    UNION ALL SELECT 'Termo de acero',          18990, 'Hogar',       30, 'Mantiene la temperatura 12 h'
    UNION ALL SELECT 'Organizador de cables',    6990, 'Hogar',        0, 'Agotado: sirve para probar el filtro de stock'
) AS p
JOIN categorias c ON c.nombre = p.cat;
