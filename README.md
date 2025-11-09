# Forneria

Proyecto inicial en **Django**.

## Instalación

```bash
git clone https://github.com/BlackYcee/Forneria.git
cd Forneria
python -m venv env
source env/bin/activate   # Linux/Mac
env\Scripts\activate      # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver ```

## Template para los json
```json
{
  "categoria": {
    "nombre": "Alimentos",
    "descripcion": "Productos comestibles como pan, leche y frutas"
  },
  "producto": {
    "nombre": "Pan Integral",
    "descripcion": "Pan integral artesanal con semillas",
    "marca": "Forneria",
    "precio": 2500.00,
    "caducidad": "2025-12-31",
    "elaboracion": "2025-11-01",
    "tipo": "Alimento",
    "stock_actual": 50,
    "stock_minimo": 10,
    "stock_maximo": 100,
    "presentacion": "Bolsa de 500g",
    "formato": "Unidad",
    "creado": "2025-11-09T02:35:00",
    "modificado": null,
    "eliminado": null,
    "categoria": 1
  },
  "nutricional": {
    "calorias": 250.50,
    "proteinas": 12.30,
    "grasas": 5.40,
    "carbohidratos": 40.00,
    "azucares": 8.50,
    "sodio": 0.75,
    "producto": 1
  },
  "alerta": {
    "tipo_alerta": "roja",
    "mensaje": "Stock crítico, quedan menos de 5 unidades",
    "fecha_generada": "2025-11-09T15:00:00",
    "estado": "pendiente",
    "producto": 1
  },
  "cliente": {
    "rut": "12345678-5",
    "nombre": "Juan Pérez",
    "correo": "juan.perez@example.com"
  },
  "venta": {
    "fecha": "2025-11-09T14:30:00",
    "total_sin_iva": 10000.00,
    "total_iva": 1900.00,
    "descuento": 500.00,
    "total_con_iva": 11400.00,
    "canal_venta": "presencial",
    "folio": "F0001",
    "monto_pagado": 12000.00,
    "vuelto": 600.00,
    "cliente": 1
  },
  "detalle_venta": {
    "cantidad": 2,
    "precio_unitario": 2500.00,
    "descuento_pct": 10.00,
    "venta": 1,
    "producto": 1
  },
  "movimiento_inventario": {
    "tipo_movimiento": "entrada",
    "cantidad": 20,
    "fecha": "2025-11-09T15:00:00",
    "producto": 1
  },
  "empleado": {
    "nombres": "Carlos",
    "apellido_paterno": "González",
    "run": "98765432-1",
    "correo": "carlos.gonzalez@example.com",
    "fono": 987654321,
    "clave": "claveSegura123",
    "direccion": "Av. Libertad 456, La Serena",
    "cargo": "Cajero"
  },
  "turno": {
    "empleado": 1,
    "fecha": "2025-11-10",
    "hora_entrada": "09:00:00",
    "hora_salida": "17:00:00"
  }
}
