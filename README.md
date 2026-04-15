# Medallero App

Sistema web para carga, revisión y exportación de medallas de competencias deportivas.

## Objetivo

Permitir una carga de medallas más amigable, clara e intuitiva que el sistema actual, manteniendo como resultado final un archivo Excel plano con esta estructura:

- Evento
- Disciplina
- Prueba
- Género
- Categoria
- Adaptado
- Clase
- Provincia
- Medalla

Cada fila representa una medalla obtenida.

## Stack tecnológica

- Python
- Flask
- SQLite
- HTML
- Bootstrap
- JavaScript
- openpyxl

## Funcionalidades del MVP

- Alta de registros de medallas
- Edición de registros
- Eliminación de registros
- Duplicación de registros
- Tabla de visualización
- Filtros y búsqueda
- Exportación a Excel

## Estructura del proyecto

```text
medallero-app/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── database/
├── exports/
├── templates/
├── static/
└── utils/
