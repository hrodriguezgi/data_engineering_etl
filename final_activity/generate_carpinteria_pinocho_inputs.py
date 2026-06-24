"""
Generate final-project input files for the Carpinteria Pinocho ETL case.
"""

from pathlib import Path

import duckdb
import sqlite3
import pandas as pd


BASE_DIR = Path(__file__).parent / "data" / "carpinteria_pinocho"
DB_PATH = BASE_DIR / "sucursal_norte.duckdb"
DB2_PATH = BASE_DIR / "sucursal_norte.db"
CSV_PATH = BASE_DIR / "ventas_centro.csv"
XLSX_PATH = BASE_DIR / "sucursal_sur.xlsx"


def build_north_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    clientes = pd.DataFrame(
        [
            {"id_cliente": "C001", "nombre_cliente": "Muebles La 70", "ciudad_cliente": "Medellin"},
            {"id_cliente": "C002", "nombre_cliente": "Hogar Bello", "ciudad_cliente": "Bello"},
            {"id_cliente": "C003", "nombre_cliente": "Disenos Oriente", "ciudad_cliente": "Rionegro"},
            {"id_cliente": "C003", "nombre_cliente": "Disenos Oriente ", "ciudad_cliente": "Rionegro"},
            {"id_cliente": "C004", "nombre_cliente": "Casa Nogal", "ciudad_cliente": "Sabaneta"},
            {"id_cliente": "C005", "nombre_cliente": "Decor Antioquia", "ciudad_cliente": "Envigado"},
            {"id_cliente": "C006", "nombre_cliente": "Almacen Laureles", "ciudad_cliente": "Medellin"},
            {"id_cliente": "C007", "nombre_cliente": "Roble Hogar", "ciudad_cliente": "Itagui"},
            {"id_cliente": "C008", "nombre_cliente": "Espacios Unicos", "ciudad_cliente": "Copacabana"},
            {"id_cliente": "C009", "nombre_cliente": "Veta Studio", "ciudad_cliente": "Medellin"},
            {"id_cliente": "C010", "nombre_cliente": "Madera Viva", "ciudad_cliente": "Bello"},
            {"id_cliente": "C011", "nombre_cliente": "Proyecto Habitat", "ciudad_cliente": "Envigado"},
            {"id_cliente": "C012", "nombre_cliente": "Innova Muebles", "ciudad_cliente": "Rionegro"},
            {"id_cliente": "C013", "nombre_cliente": "Casa Central", "ciudad_cliente": "Medellin"},
            {"id_cliente": "C014", "nombre_cliente": "Nogal Deco", "ciudad_cliente": "Sabaneta"},
        ]
    )

    productos = pd.DataFrame(
        [
            {
                "id_producto": "P001",
                "nombre_producto": "Mesa comedor 4 puestos",
                "categoria": "Mesas",
                "precio_unitario": 450000,
            },
            {"id_producto": "P002", "nombre_producto": "Silla pino", "categoria": "Sillas", "precio_unitario": 120000},
            {
                "id_producto": "P003",
                "nombre_producto": "Biblioteca modular",
                "categoria": "Bibliotecas",
                "precio_unitario": 680000,
            },
            {
                "id_producto": "P004",
                "nombre_producto": "Escritorio ejecutivo",
                "categoria": "Escritorios",
                "precio_unitario": 520000,
            },
            {
                "id_producto": "P005",
                "nombre_producto": "Mesa auxiliar",
                "categoria": "Mesas",
                "precio_unitario": 180000,
            },
            {
                "id_producto": "P006",
                "nombre_producto": "Closet dos puertas",
                "categoria": "Closets",
                "precio_unitario": 760000,
            },
            {
                "id_producto": "P007",
                "nombre_producto": "Sofa madera lino",
                "categoria": "Sofas",
                "precio_unitario": 980000,
            },
            {
                "id_producto": "P008",
                "nombre_producto": "Barra desayunador",
                "categoria": "Barras",
                "precio_unitario": 390000,
            },
            {
                "id_producto": "P009",
                "nombre_producto": "Mesa de noche",
                "categoria": "Dormitorio",
                "precio_unitario": 210000,
            },
            {
                "id_producto": "P010",
                "nombre_producto": "Centro de entretenimiento",
                "categoria": "Salas",
                "precio_unitario": 840000,
            },
            {"id_producto": "P011", "nombre_producto": "silla pino", "categoria": "Sillas", "precio_unitario": 120000},
            {
                "id_producto": "P012",
                "nombre_producto": "Archivador vertical",
                "categoria": "Oficina",
                "precio_unitario": 310000,
            },
        ]
    )

    ventas = pd.DataFrame(
        [
            {
                "id_venta": "VN001",
                "fecha_venta": "2026-05-02",
                "id_cliente": "C001",
                "id_producto": "P001",
                "cantidad": 2,
            },
            {
                "id_venta": "VN002",
                "fecha_venta": "02/05/2026",
                "id_cliente": "C002",
                "id_producto": "P002",
                "cantidad": 4,
            },
            {
                "id_venta": "VN003",
                "fecha_venta": "2026-05-03",
                "id_cliente": "C003",
                "id_producto": "P003",
                "cantidad": 1,
            },
            {
                "id_venta": "VN004",
                "fecha_venta": "2026-05-03",
                "id_cliente": "C004",
                "id_producto": "P005",
                "cantidad": 2,
            },
            {
                "id_venta": "VN005",
                "fecha_venta": "2026/05/04",
                "id_cliente": "C005",
                "id_producto": "P004",
                "cantidad": 1,
            },
            {
                "id_venta": "VN006",
                "fecha_venta": "2026-05-04",
                "id_cliente": "C006",
                "id_producto": "P002",
                "cantidad": 6,
            },
            {
                "id_venta": "VN007",
                "fecha_venta": "05-05-2026",
                "id_cliente": "C007",
                "id_producto": "P006",
                "cantidad": 1,
            },
            {
                "id_venta": "VN008",
                "fecha_venta": "2026-05-05",
                "id_cliente": "C008",
                "id_producto": "P007",
                "cantidad": 1,
            },
            {
                "id_venta": "VN009",
                "fecha_venta": "2026-05-06",
                "id_cliente": "C009",
                "id_producto": "P008",
                "cantidad": 2,
            },
            {
                "id_venta": "VN010",
                "fecha_venta": "2026-05-06",
                "id_cliente": "C010",
                "id_producto": "P009",
                "cantidad": 3,
            },
            {
                "id_venta": "VN011",
                "fecha_venta": "2026-05-07",
                "id_cliente": "C011",
                "id_producto": "P010",
                "cantidad": 1,
            },
            {
                "id_venta": "VN012",
                "fecha_venta": "2026-05-07",
                "id_cliente": "C012",
                "id_producto": "P012",
                "cantidad": 2,
            },
            {
                "id_venta": "VN013",
                "fecha_venta": "2026-05-08",
                "id_cliente": "C013",
                "id_producto": "P005",
                "cantidad": 4,
            },
            {
                "id_venta": "VN014",
                "fecha_venta": "2026-05-08",
                "id_cliente": "C014",
                "id_producto": "P001",
                "cantidad": 1,
            },
            {
                "id_venta": "VN015",
                "fecha_venta": "2026-05-09",
                "id_cliente": "C001",
                "id_producto": "P011",
                "cantidad": 8,
            },
            {
                "id_venta": "VN016",
                "fecha_venta": "2026-05-09",
                "id_cliente": "C002",
                "id_producto": "P003",
                "cantidad": 1,
            },
            {
                "id_venta": "VN017",
                "fecha_venta": "2026-05-10",
                "id_cliente": "C003",
                "id_producto": "P004",
                "cantidad": 2,
            },
            {
                "id_venta": "VN018",
                "fecha_venta": "10/05/2026",
                "id_cliente": "C004",
                "id_producto": "P006",
                "cantidad": 1,
            },
            {
                "id_venta": "VN019",
                "fecha_venta": "2026-05-10",
                "id_cliente": "C005",
                "id_producto": "P010",
                "cantidad": 1,
            },
            {
                "id_venta": "VN020",
                "fecha_venta": "2026-05-11",
                "id_cliente": "C006",
                "id_producto": "P002",
                "cantidad": None,
            },
            {
                "id_venta": "VN021",
                "fecha_venta": "2026-05-11",
                "id_cliente": "C007",
                "id_producto": "P007",
                "cantidad": 2,
            },
            {
                "id_venta": "VN022",
                "fecha_venta": "2026-05-12",
                "id_cliente": "C008",
                "id_producto": "P009",
                "cantidad": 2,
            },
            {
                "id_venta": "VN023",
                "fecha_venta": "2026-05-12",
                "id_cliente": "C009",
                "id_producto": "P008",
                "cantidad": 3,
            },
            {
                "id_venta": "VN024",
                "fecha_venta": "2026-05-13",
                "id_cliente": "C010",
                "id_producto": "P004",
                "cantidad": 1,
            },
            {
                "id_venta": "VN025",
                "fecha_venta": "2026-05-13",
                "id_cliente": "C011",
                "id_producto": "P012",
                "cantidad": 2,
            },
            {
                "id_venta": "VN026",
                "fecha_venta": "2026-05-14",
                "id_cliente": "C012",
                "id_producto": "P001",
                "cantidad": 1,
            },
            {
                "id_venta": "VN027",
                "fecha_venta": "14/05/2026",
                "id_cliente": "C013",
                "id_producto": "P005",
                "cantidad": 2,
            },
            {
                "id_venta": "VN028",
                "fecha_venta": "2026-05-15",
                "id_cliente": "C014",
                "id_producto": "P010",
                "cantidad": 1,
            },
            {
                "id_venta": "VN003",
                "fecha_venta": "2026-05-03",
                "id_cliente": "C003",
                "id_producto": "P003",
                "cantidad": 1,
            },
            {
                "id_venta": "VN019",
                "fecha_venta": "2026-05-10",
                "id_cliente": "C005",
                "id_producto": "P010",
                "cantidad": 1,
            },
        ]
    )

    return clientes, productos, ventas


def build_center_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "venta_id": "VC001",
                "fecha": "2026/05/01",
                "cliente": "Almacen Roble",
                "ciudad": "Medellin",
                "producto": "Mesa comedor 4 puestos",
                "categoria_producto": "Mesas",
                "cantidad": 1,
                "valor_unitario": 450000,
            },
            {
                "venta_id": "VC002",
                "fecha": "01-05-2026",
                "cliente": "Almacen Roble ",
                "ciudad": "Medellin",
                "producto": "Silla pino",
                "categoria_producto": "Sillas",
                "cantidad": 6,
                "valor_unitario": 120000,
            },
            {
                "venta_id": "VC003",
                "fecha": "2026-05-03",
                "cliente": "Casa Viva",
                "ciudad": "Envigado",
                "producto": "Biblioteca modular",
                "categoria_producto": "Biblioteca",
                "cantidad": 1,
                "valor_unitario": 680000,
            },
            {
                "venta_id": "VC003",
                "fecha": "2026-05-03",
                "cliente": "Casa Viva",
                "ciudad": "Envigado",
                "producto": "Biblioteca modular",
                "categoria_producto": "Biblioteca",
                "cantidad": 1,
                "valor_unitario": 680000,
            },
            {
                "venta_id": "VC004",
                "fecha": "2026-05-04",
                "cliente": "Deco Hogar",
                "ciudad": "Bello",
                "producto": "Silla pino",
                "categoria_producto": "Sillas",
                "cantidad": 2,
                "valor_unitario": None,
            },
            {
                "venta_id": "VC005",
                "fecha": "05/05/2026",
                "cliente": "Linea Madera",
                "ciudad": "Itagui",
                "producto": "Escritorio ejecutivo",
                "categoria_producto": "Escritorios",
                "cantidad": 1,
                "valor_unitario": 520000,
            },
            {
                "venta_id": "VC006",
                "fecha": "2026-05-05",
                "cliente": "Linea Madera",
                "ciudad": "Itagui",
                "producto": "mesa auxiliar",
                "categoria_producto": "Mesas",
                "cantidad": 3,
                "valor_unitario": 180000,
            },
            {
                "venta_id": "VC007",
                "fecha": "2026-05-06",
                "cliente": "Punto Nogal",
                "ciudad": "Sabaneta",
                "producto": "Closet dos puertas",
                "categoria_producto": "Closets",
                "cantidad": 1,
                "valor_unitario": 760000,
            },
            {
                "venta_id": "VC008",
                "fecha": "06/05/2026",
                "cliente": "Punto Nogal",
                "ciudad": "Sabaneta",
                "producto": "Sofa madera lino",
                "categoria_producto": "Sofas",
                "cantidad": 1,
                "valor_unitario": 980000,
            },
            {
                "venta_id": "VC009",
                "fecha": "2026/05/07",
                "cliente": "Mobiliario 33",
                "ciudad": "Medellin",
                "producto": "Barra desayunador",
                "categoria_producto": "Barras",
                "cantidad": 2,
                "valor_unitario": 390000,
            },
            {
                "venta_id": "VC010",
                "fecha": "07-05-2026",
                "cliente": "Mobiliario 33",
                "ciudad": "Medellin",
                "producto": "Mesa de noche",
                "categoria_producto": "Dormitorio",
                "cantidad": 4,
                "valor_unitario": 210000,
            },
            {
                "venta_id": "VC011",
                "fecha": "2026-05-07",
                "cliente": "Casa Viva",
                "ciudad": "Envigado",
                "producto": "Centro de entretenimiento",
                "categoria_producto": "Salas",
                "cantidad": 1,
                "valor_unitario": 840000,
            },
            {
                "venta_id": "VC012",
                "fecha": "2026-05-08",
                "cliente": "Casa Viva",
                "ciudad": "Envigado",
                "producto": "Archivador vertical",
                "categoria_producto": "Oficina",
                "cantidad": 2,
                "valor_unitario": 310000,
            },
            {
                "venta_id": "VC013",
                "fecha": "08/05/2026",
                "cliente": "Roble Urbano",
                "ciudad": "Rionegro",
                "producto": "Silla pino",
                "categoria_producto": "sillas",
                "cantidad": 8,
                "valor_unitario": 120000,
            },
            {
                "venta_id": "VC014",
                "fecha": "2026-05-09",
                "cliente": "Roble Urbano",
                "ciudad": "Rionegro",
                "producto": "Biblioteca modular ",
                "categoria_producto": "Bibliotecas",
                "cantidad": 1,
                "valor_unitario": 680000,
            },
            {
                "venta_id": "VC015",
                "fecha": "2026-05-09",
                "cliente": "Nido Interior",
                "ciudad": "La Ceja",
                "producto": "Escritorio ejecutivo",
                "categoria_producto": "Escritorios",
                "cantidad": 2,
                "valor_unitario": 520000,
            },
            {
                "venta_id": "VC016",
                "fecha": "2026/05/10",
                "cliente": "Nido Interior",
                "ciudad": "La Ceja",
                "producto": "Mesa auxiliar",
                "categoria_producto": "Mesas",
                "cantidad": 2,
                "valor_unitario": 180000,
            },
            {
                "venta_id": "VC017",
                "fecha": "10-05-2026",
                "cliente": "Hogar Azul",
                "ciudad": "Bello",
                "producto": "Closet dos puertas",
                "categoria_producto": "Closets",
                "cantidad": 1,
                "valor_unitario": 760000,
            },
            {
                "venta_id": "VC018",
                "fecha": "2026-05-10",
                "cliente": "Hogar Azul",
                "ciudad": "Bello",
                "producto": "Sofa madera lino",
                "categoria_producto": "Sofas",
                "cantidad": 1,
                "valor_unitario": None,
            },
            {
                "venta_id": "VC019",
                "fecha": "2026-05-11",
                "cliente": "Taller Habitat",
                "ciudad": "Copacabana",
                "producto": "Mesa comedor 4 puestos",
                "categoria_producto": "Mesas",
                "cantidad": 1,
                "valor_unitario": 450000,
            },
            {
                "venta_id": "VC020",
                "fecha": "11/05/2026",
                "cliente": "Taller Habitat",
                "ciudad": "Copacabana",
                "producto": "Silla pino",
                "categoria_producto": "Sillas",
                "cantidad": 4,
                "valor_unitario": 120000,
            },
            {
                "venta_id": "VC021",
                "fecha": "2026-05-12",
                "cliente": "Casa Prisma",
                "ciudad": "Medellin",
                "producto": "Centro de entretenimiento",
                "categoria_producto": "Salas",
                "cantidad": 1,
                "valor_unitario": 840000,
            },
            {
                "venta_id": "VC022",
                "fecha": "2026-05-12",
                "cliente": "Casa Prisma",
                "ciudad": "Medellin",
                "producto": "Mesa de noche",
                "categoria_producto": "Dormitorios",
                "cantidad": 2,
                "valor_unitario": 210000,
            },
            {
                "venta_id": "VC023",
                "fecha": "2026/05/13",
                "cliente": "Habitarte",
                "ciudad": "Envigado",
                "producto": "Archivador vertical",
                "categoria_producto": "Oficina",
                "cantidad": 1,
                "valor_unitario": 310000,
            },
            {
                "venta_id": "VC024",
                "fecha": "13-05-2026",
                "cliente": "Habitarte",
                "ciudad": "Envigado",
                "producto": "Barra desayunador",
                "categoria_producto": "Barras",
                "cantidad": 2,
                "valor_unitario": 390000,
            },
            {
                "venta_id": "VC025",
                "fecha": "2026-05-14",
                "cliente": "Nodo Madera",
                "ciudad": "Itagui",
                "producto": "Mesa auxiliar",
                "categoria_producto": "Mesas",
                "cantidad": 2,
                "valor_unitario": 180000,
            },
            {
                "venta_id": "VC026",
                "fecha": "14/05/2026",
                "cliente": "Nodo Madera",
                "ciudad": "Itagui",
                "producto": "Silla pino",
                "categoria_producto": "Sillas",
                "cantidad": 10,
                "valor_unitario": 120000,
            },
            {
                "venta_id": "VC027",
                "fecha": "2026-05-15",
                "cliente": "Rincon Mueble",
                "ciudad": "Sabaneta",
                "producto": "Closet dos puertas",
                "categoria_producto": "Closets",
                "cantidad": 1,
                "valor_unitario": 760000,
            },
            {
                "venta_id": "VC028",
                "fecha": "2026-05-15",
                "cliente": "Rincon Mueble",
                "ciudad": "Sabaneta",
                "producto": "Escritorio ejecutivo",
                "categoria_producto": "Escritorios",
                "cantidad": 1,
                "valor_unitario": 520000,
            },
            {
                "venta_id": "VC029",
                "fecha": "2026-05-16",
                "cliente": "Casa Prisma",
                "ciudad": "Medellin",
                "producto": "Mesa comedor 4 puestos",
                "categoria_producto": "Mesas",
                "cantidad": 1,
                "valor_unitario": 450000,
            },
            {
                "venta_id": "VC030",
                "fecha": "2026-05-16",
                "cliente": "Casa Prisma",
                "ciudad": " Medellin",
                "producto": "Silla pino",
                "categoria_producto": "Sillas",
                "cantidad": 4,
                "valor_unitario": 120000,
            },
        ]
    )


def build_south_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    productos = pd.DataFrame(
        [
            {"cod_producto": "PS001", "producto": "Mesa auxiliar", "categoria": "Mesas", "precio_unitario": 180000},
            {
                "cod_producto": "PS002",
                "producto": "Escritorio ejecutivo",
                "categoria": "Escritorios",
                "precio_unitario": 520000,
            },
            {"cod_producto": "PS003", "producto": "Silla pino", "categoria": "Sillas", "precio_unitario": 118000},
            {"cod_producto": "PS003", "producto": "Silla Pino", "categoria": "Sillas", "precio_unitario": 118000},
            {
                "cod_producto": "PS004",
                "producto": "Biblioteca modular",
                "categoria": "Bibliotecas",
                "precio_unitario": 675000,
            },
            {
                "cod_producto": "PS005",
                "producto": "Closet dos puertas",
                "categoria": "Closets",
                "precio_unitario": 755000,
            },
            {
                "cod_producto": "PS006",
                "producto": "Mesa comedor 4 puestos",
                "categoria": "Mesas",
                "precio_unitario": 448000,
            },
            {
                "cod_producto": "PS007",
                "producto": "Centro de entretenimiento",
                "categoria": "Salas",
                "precio_unitario": 835000,
            },
            {
                "cod_producto": "PS008",
                "producto": "Barra desayunador",
                "categoria": "Barras",
                "precio_unitario": 392000,
            },
            {
                "cod_producto": "PS009",
                "producto": "Mesa de noche",
                "categoria": "Dormitorio",
                "precio_unitario": 212000,
            },
            {
                "cod_producto": "PS010",
                "producto": "Archivador vertical",
                "categoria": "Oficina",
                "precio_unitario": 312000,
            },
            {"cod_producto": "PS011", "producto": "Sofa madera lino", "categoria": "Sofas", "precio_unitario": 975000},
        ]
    )

    ventas = pd.DataFrame(
        [
            {
                "id_venta": "VS001",
                "fecha": "2026-05-02",
                "cliente": "Comercial Madera",
                "ciudad": "Itagui",
                "cod_producto": "PS001",
                "cantidad": 2,
            },
            {
                "id_venta": "VS002",
                "fecha": "03/05/2026",
                "cliente": "Comercial Madera",
                "ciudad": "Itagui",
                "cod_producto": "PS003",
                "cantidad": 4,
            },
            {
                "id_venta": "VS003",
                "fecha": "mayo 4 2026",
                "cliente": "Casa Nogal",
                "ciudad": "Sabaneta",
                "cod_producto": "PS010",
                "cantidad": 1,
            },
            {
                "id_venta": "VS004",
                "fecha": "2026-05-05",
                "cliente": "Hogar Ideal",
                "ciudad": "Envigado",
                "cod_producto": "PS002",
                "cantidad": None,
            },
            {
                "id_venta": "VS005",
                "fecha": "2026/05/05",
                "cliente": "Hogar Ideal",
                "ciudad": "Envigado",
                "cod_producto": "PS004",
                "cantidad": 1,
            },
            {
                "id_venta": "VS006",
                "fecha": "06-05-2026",
                "cliente": "Nodo Sur",
                "ciudad": "La Estrella",
                "cod_producto": "PS005",
                "cantidad": 1,
            },
            {
                "id_venta": "VS007",
                "fecha": "2026-05-06",
                "cliente": "Nodo Sur",
                "ciudad": "La Estrella",
                "cod_producto": "PS006",
                "cantidad": 1,
            },
            {
                "id_venta": "VS008",
                "fecha": "2026-05-07",
                "cliente": "Muebles Avenida",
                "ciudad": "Medellin",
                "cod_producto": "PS007",
                "cantidad": 1,
            },
            {
                "id_venta": "VS009",
                "fecha": "07/05/2026",
                "cliente": "Muebles Avenida",
                "ciudad": "Medellin",
                "cod_producto": "PS008",
                "cantidad": 2,
            },
            {
                "id_venta": "VS010",
                "fecha": "2026-05-08",
                "cliente": "Casa Nativa",
                "ciudad": "Caldas",
                "cod_producto": "PS009",
                "cantidad": 2,
            },
            {
                "id_venta": "VS011",
                "fecha": "2026-05-08",
                "cliente": "Casa Nativa",
                "ciudad": "Caldas",
                "cod_producto": "PS011",
                "cantidad": 1,
            },
            {
                "id_venta": "VS012",
                "fecha": "09/05/2026",
                "cliente": "Deco Sur",
                "ciudad": "Envigado",
                "cod_producto": "PS003",
                "cantidad": 6,
            },
            {
                "id_venta": "VS013",
                "fecha": "2026-05-09",
                "cliente": "Deco Sur",
                "ciudad": "Envigado",
                "cod_producto": "PS001",
                "cantidad": 2,
            },
            {
                "id_venta": "VS014",
                "fecha": "2026-05-10",
                "cliente": "Patio Central",
                "ciudad": "Sabaneta",
                "cod_producto": "PS004",
                "cantidad": 1,
            },
            {
                "id_venta": "VS015",
                "fecha": "10/05/2026",
                "cliente": "Patio Central",
                "ciudad": "Sabaneta",
                "cod_producto": "PS999",
                "cantidad": 1,
            },
            {
                "id_venta": "VS016",
                "fecha": "2026-05-11",
                "cliente": "Interior Lab",
                "ciudad": "Itagui",
                "cod_producto": "PS002",
                "cantidad": 1,
            },
            {
                "id_venta": "VS017",
                "fecha": "2026/05/11",
                "cliente": "Interior Lab ",
                "ciudad": "Itagui",
                "cod_producto": "PS010",
                "cantidad": 2,
            },
            {
                "id_venta": "VS018",
                "fecha": "12-05-2026",
                "cliente": "Madera Casa",
                "ciudad": "Bello",
                "cod_producto": "PS006",
                "cantidad": 1,
            },
            {
                "id_venta": "VS019",
                "fecha": "2026-05-12",
                "cliente": "Madera Casa",
                "ciudad": "Bello",
                "cod_producto": "PS003",
                "cantidad": 4,
            },
            {
                "id_venta": "VS020",
                "fecha": "2026-05-13",
                "cliente": "Sur Deco",
                "ciudad": "Medellin",
                "cod_producto": "PS007",
                "cantidad": 1,
            },
            {
                "id_venta": "VS021",
                "fecha": "13/05/2026",
                "cliente": "Sur Deco",
                "ciudad": "Medellin",
                "cod_producto": "PS008",
                "cantidad": 2,
            },
            {
                "id_venta": "VS022",
                "fecha": "2026-05-14",
                "cliente": "Habita Sur",
                "ciudad": "Caldas",
                "cod_producto": "PS009",
                "cantidad": 2,
            },
            {
                "id_venta": "VS023",
                "fecha": "",
                "cliente": "Habita Sur",
                "ciudad": "Caldas",
                "cod_producto": "PS001",
                "cantidad": 1,
            },
            {
                "id_venta": "VS024",
                "fecha": "2026-05-15",
                "cliente": None,
                "ciudad": "Envigado",
                "cod_producto": "PS011",
                "cantidad": 1,
            },
            {
                "id_venta": "VS025",
                "fecha": "2026-05-15",
                "cliente": "Casa Nogal",
                "ciudad": "Sabaneta",
                "cod_producto": "PS004",
                "cantidad": 1,
            },
        ]
    )

    return productos, ventas


def write_duckdb(clientes: pd.DataFrame, productos: pd.DataFrame, ventas: pd.DataFrame) -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    with duckdb.connect(str(DB_PATH)) as conn:
        conn.register("clientes_df", clientes)
        conn.register("productos_df", productos)
        conn.register("ventas_df", ventas)
        conn.execute("CREATE TABLE clientes AS SELECT * FROM clientes_df")
        conn.execute("CREATE TABLE productos AS SELECT * FROM productos_df")
        conn.execute("CREATE TABLE ventas AS SELECT * FROM ventas_df")


def write_sqlite(clientes: pd.DataFrame, productos: pd.DataFrame, ventas: pd.DataFrame) -> None:
    if DB2_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB2_PATH) as conn:
        clientes.to_sql("clientes", conn, index=False)
        productos.to_sql("productos", conn, index=False)
        ventas.to_sql("ventas", conn, index=False)


def write_csv(df: pd.DataFrame) -> None:
    df.to_csv(CSV_PATH, index=False)


def write_excel(productos: pd.DataFrame, ventas: pd.DataFrame) -> None:
    with pd.ExcelWriter(XLSX_PATH, engine="openpyxl") as writer:
        productos.to_excel(writer, index=False, sheet_name="productos")
        ventas.to_excel(writer, index=False, sheet_name="ventas")


def main() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    north_clientes, north_productos, north_ventas = build_north_data()
    center_ventas = build_center_data()
    south_productos, south_ventas = build_south_data()

    write_duckdb(north_clientes, north_productos, north_ventas)
    write_sqlite(north_clientes, north_productos, north_ventas)
    write_csv(center_ventas)
    write_excel(south_productos, south_ventas)

    print(f"Created {DB_PATH}")
    print(f"Created {DB2_PATH}")
    print(f"Created {CSV_PATH}")
    print(f"Created {XLSX_PATH}")


if __name__ == "__main__":
    main()
