# 🧪 Pruebas del Dashboard Financiero

## ✅ Checklist de Implementación Completada

- [x] App `analytics` creada
- [x] Servicio `FinanzasMetrics` con 10 métodos
- [x] 9 endpoints API REST
- [x] Template HTML del dashboard
- [x] Vista Django para renderizar
- [x] URLs configuradas
- [x] Template tags customizados
- [x] Integración con `basepos.html`

---

## 🚀 Cómo Probar

### 1. Instalar Dependencias

```bash
cd "C:\Users\mahon\OneDrive\Documentos\git\Forneria"
pip install -r requirements.txt
```

**Dependencias agregadas:**
- `django-filter==23.5`
- `dj-rest-auth==5.0.2`
- `python-dateutil==2.8.2`

---

### 2. Ejecutar el Servidor

```bash
python manage.py runserver
```

---

### 3. Acceder al Dashboard

Abre tu navegador y visita:

```
http://127.0.0.1:8000/analytics/dashboard/
```

**Deberías ver:**
- ✅ 4 cards con KPIs (Ventas Hoy, Últimos 30 días, Ticket Promedio, Descuentos)
- ✅ Tabla de desglose financiero
- ✅ Tabla de ventas por canal (Presencial/Delivery)
- ✅ Top 10 productos más vendidos
- ✅ Ventas por categoría
- ✅ Top 5 clientes

---

## 🔍 Probar Endpoints API Individuales

### Endpoint 1: Resumen Financiero
```bash
# En el navegador o con curl
http://127.0.0.1:8000/analytics/finanzas/resumen/

# Con filtro de fechas
http://127.0.0.1:8000/analytics/finanzas/resumen/?fecha_inicio=2025-11-01&fecha_fin=2025-11-24
```

**Respuesta esperada:**
```json
{
  "total_ventas": 1250000.50,
  "cantidad_transacciones": 145,
  "ticket_promedio": 8620.69,
  "total_sin_iva": 1050420.17,
  "total_iva": 199580.33,
  "total_descuentos": 45000.00,
  "fecha_inicio": "2025-10-25",
  "fecha_fin": "2025-11-24"
}
```

---

### Endpoint 2: KPIs de Hoy
```bash
http://127.0.0.1:8000/analytics/finanzas/kpis-hoy/
```

**Respuesta esperada:**
```json
{
  "hoy": {
    "total": 125000.00,
    "cantidad": 23
  },
  "ayer": {
    "total": 98000.00,
    "cantidad": 18
  },
  "variacion_pct": 27.55
}
```

---

### Endpoint 3: Ventas Diarias (Chart.js format)
```bash
http://127.0.0.1:8000/analytics/finanzas/ventas-diarias/
```

**Respuesta esperada:**
```json
{
  "labels": ["2025-11-01", "2025-11-02", "2025-11-03"],
  "totales": [45000.50, 52000.00, 48500.75],
  "cantidades": [12, 15, 13]
}
```

---

### Endpoint 4: Top Productos
```bash
http://127.0.0.1:8000/analytics/finanzas/productos-top/

# Con límite personalizado
http://127.0.0.1:8000/analytics/finanzas/productos-top/?limite=5
```

---

### Endpoint 5: Ventas por Categoría
```bash
http://127.0.0.1:8000/analytics/finanzas/ventas-por-categoria/
```

---

### Endpoint 6: Ventas por Canal
```bash
http://127.0.0.1:8000/analytics/finanzas/ventas-por-canal/
```

---

### Endpoint 7: Top Clientes
```bash
http://127.0.0.1:8000/analytics/finanzas/clientes-top/?limite=5
```

---

### Endpoint 8: Ventas por Hora
```bash
http://127.0.0.1:8000/analytics/finanzas/ventas-por-hora/
```

---

### Endpoint 9: Comparativa Mensual
```bash
http://127.0.0.1:8000/analytics/finanzas/comparativa-mensual/?meses=6
```

---

## 📊 Verificar Datos

### Si ves "Sin datos" en el dashboard:

Esto es normal si no tienes ventas en la base de datos. Para verificar:

```bash
python manage.py shell
```

Dentro del shell de Django:

```python
from pos.models import Venta, DetalleVenta, Producto

# Verificar cuántas ventas existen
print(f"Ventas totales: {Venta.objects.count()}")
print(f"Productos: {Producto.objects.count()}")

# Ver las últimas 5 ventas
for v in Venta.objects.all()[:5]:
    print(f"Venta {v.id} - {v.fecha} - ${v.total_con_iva}")
```

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'dj_rest_auth'"
```bash
pip install dj-rest-auth==5.0.2
```

---

### Error: "TemplateDoesNotExist: dashboard_finanzas.html"
Verifica que el archivo existe en:
```
C:\Users\mahon\OneDrive\Documentos\git\Forneria\templates\dashboard_finanzas.html
```

Y que `TEMPLATES_DIR` está configurado en `settings.py`:
```python
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
```

---

### Error: "No module named 'analytics_extras'"
Verifica que existen los archivos:
```
analytics/templatetags/__init__.py
analytics/templatetags/analytics_extras.py
```

Y reinicia el servidor Django.

---

### Error de Base de Datos (MySQL)
Verifica que MySQL está corriendo y la base de datos `forneria` existe:

```bash
mysql -u root -p
```

```sql
SHOW DATABASES;
USE forneria;
SHOW TABLES;
```

---

## ✨ Próximos Pasos

Una vez que verifiques que el dashboard funciona:

1. **Agregar Chart.js** para gráficos visuales
2. **Implementar filtros de fecha** en el dashboard HTML
3. **Agregar métricas de inventario** (InventarioMetrics)
4. **Dashboard de inventario** separado
5. **Exportar a PDF/Excel**

---

## 📝 Notas

- El dashboard muestra datos de los **últimos 30 días** por defecto
- Si no hay datos, se mostrará un mensaje amigable
- Los endpoints API funcionan independientemente del HTML
- Formato de fechas: `YYYY-MM-DD` (ej: `2025-11-24`)

---

## 🎯 URLs Importantes

| URL | Descripción |
|-----|-------------|
| `http://127.0.0.1:8000/analytics/dashboard/` | Dashboard HTML |
| `http://127.0.0.1:8000/analytics/finanzas/resumen/` | API Resumen |
| `http://127.0.0.1:8000/pos/sistema/` | Sistema POS |
| `http://127.0.0.1:8000/admin/` | Admin Django |
| `http://127.0.0.1:8000/api/redoc/` | Documentación API |

---

¡Listo para probar! 🚀
