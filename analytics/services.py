"""
Servicios de métricas para Analytics
Utiliza Django ORM puro para cálculos eficientes
"""
from django.db.models import Sum, Count, Avg, F, Q, DecimalField, Case, When, Max, Min
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek, TruncHour, ExtractHour, ExtractWeekDay, Coalesce
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import calendar

from pos.models import Venta, DetalleVenta, Producto, Categoria, Cliente


class FinanzasMetrics:
    """Métricas financieras avanzadas para dashboard de ventas"""

    @staticmethod
    def resumen_periodo(fecha_inicio=None, fecha_fin=None):
        """
        Resumen general de ventas en un periodo
        Retorna: total_ventas, cantidad_transacciones, ticket_promedio, descuentos_totales
        """
        if not fecha_inicio:
            fecha_inicio = timezone.now().date() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = timezone.now().date()

        resultado = Venta.objects.filter(
            fecha__date__range=[fecha_inicio, fecha_fin]
        ).aggregate(
            total_ventas=Coalesce(Sum('total_con_iva'), Decimal('0')),
            cantidad_transacciones=Count('id'),
            ticket_promedio=Coalesce(Avg('total_con_iva'), Decimal('0')),
            total_sin_iva=Coalesce(Sum('total_sin_iva'), Decimal('0')),
            total_iva=Coalesce(Sum('total_iva'), Decimal('0')),
            total_descuentos=Coalesce(Sum('descuento'), Decimal('0'))
        )

        return {
            'total_ventas': float(resultado['total_ventas']),
            'cantidad_transacciones': resultado['cantidad_transacciones'],
            'ticket_promedio': float(resultado['ticket_promedio']),
            'total_sin_iva': float(resultado['total_sin_iva']),
            'total_iva': float(resultado['total_iva']),
            'total_descuentos': float(resultado['total_descuentos']),
            'fecha_inicio': fecha_inicio.isoformat(),
            'fecha_fin': fecha_fin.isoformat()
        }

    @staticmethod
    def ventas_diarias(fecha_inicio=None, fecha_fin=None):
        """
        Ventas agrupadas por día para gráfico de líneas
        Formato optimizado para Chart.js
        """
        if not fecha_inicio:
            fecha_inicio = timezone.now().date() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = timezone.now().date()

        ventas = Venta.objects.filter(
            fecha__date__range=[fecha_inicio, fecha_fin]
        ).annotate(
            dia=TruncDate('fecha')
        ).values('dia').annotate(
            total=Sum('total_con_iva'),
            cantidad=Count('id')
        ).order_by('dia')

        return {
            'labels': [v['dia'].isoformat() for v in ventas],
            'totales': [float(v['total']) for v in ventas],
            'cantidades': [v['cantidad'] for v in ventas]
        }

    @staticmethod
    def ventas_por_hora():
        """
        Distribución de ventas por hora del día (últimos 7 días)
        """
        fecha_inicio = timezone.now() - timedelta(days=7)

        ventas = Venta.objects.filter(
            fecha__gte=fecha_inicio
        ).annotate(
            hora=ExtractHour('fecha')
        ).values('hora').annotate(
            total=Sum('total_con_iva'),
            cantidad=Count('id')
        ).order_by('hora')

        # Llenar horas faltantes con 0
        horas_completas = {h: {'total': 0, 'cantidad': 0} for h in range(24)}
        for v in ventas:
            horas_completas[v['hora']] = {
                'total': float(v['total']),
                'cantidad': v['cantidad']
            }

        return {
            'labels': [f"{h:02d}:00" for h in range(24)],
            'totales': [horas_completas[h]['total'] for h in range(24)],
            'cantidades': [horas_completas[h]['cantidad'] for h in range(24)]
        }

    @staticmethod
    def productos_top(limite=10, fecha_inicio=None, fecha_fin=None):
        """
        Top productos más vendidos por cantidad y por ingresos
        """
        filtros = Q()
        if fecha_inicio and fecha_fin:
            filtros = Q(venta__fecha__date__range=[fecha_inicio, fecha_fin])

        productos = DetalleVenta.objects.filter(filtros).values(
            'producto__id',
            'producto__nombre',
            'producto__categoria__nombre'
        ).annotate(
            cantidad_vendida=Sum('cantidad'),
            ingresos_totales=Sum(
                F('cantidad') * F('precio_unitario'),
                output_field=DecimalField()
            ),
            num_transacciones=Count('venta', distinct=True)
        ).order_by('-ingresos_totales')[:limite]

        return [{
            'producto_id': p['producto__id'],
            'nombre': p['producto__nombre'],
            'categoria': p['producto__categoria__nombre'],
            'cantidad_vendida': p['cantidad_vendida'],
            'ingresos': float(p['ingresos_totales']),
            'transacciones': p['num_transacciones']
        } for p in productos]

    @staticmethod
    def ventas_por_categoria(fecha_inicio=None, fecha_fin=None):
        """
        Distribución de ventas por categoría de producto
        Para gráfico de dona/pie
        """
        filtros = Q()
        if fecha_inicio and fecha_fin:
            filtros = Q(venta__fecha__date__range=[fecha_inicio, fecha_fin])

        categorias = DetalleVenta.objects.filter(filtros).values(
            'producto__categoria__nombre'
        ).annotate(
            total=Sum(
                F('cantidad') * F('precio_unitario'),
                output_field=DecimalField()
            ),
            cantidad_productos=Sum('cantidad')
        ).order_by('-total')

        return {
            'labels': [c['producto__categoria__nombre'] or 'Sin categoría' for c in categorias],
            'totales': [float(c['total']) for c in categorias],
            'cantidades': [c['cantidad_productos'] for c in categorias]
        }

    @staticmethod
    def ventas_por_canal(fecha_inicio=None, fecha_fin=None):
        """
        Comparativa de ventas por canal (presencial vs delivery)
        """
        if not fecha_inicio:
            fecha_inicio = timezone.now().date() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = timezone.now().date()

        canales = Venta.objects.filter(
            fecha__date__range=[fecha_inicio, fecha_fin]
        ).values('canal_venta').annotate(
            total=Sum('total_con_iva'),
            cantidad=Count('id'),
            ticket_promedio=Avg('total_con_iva')
        )

        return [{
            'canal': c['canal_venta'],
            'total': float(c['total']),
            'cantidad': c['cantidad'],
            'ticket_promedio': float(c['ticket_promedio'])
        } for c in canales]

    @staticmethod
    def comparativa_mensual(meses=6):
        """
        Comparativa de ventas de los últimos N meses
        """
        fecha_inicio = timezone.now().date() - timedelta(days=meses*30)

        ventas_mensuales = Venta.objects.filter(
            fecha__date__gte=fecha_inicio
        ).annotate(
            mes=TruncMonth('fecha')
        ).values('mes').annotate(
            total=Sum('total_con_iva'),
            cantidad=Count('id')
        ).order_by('mes')

        return {
            'labels': [v['mes'].strftime('%B %Y') for v in ventas_mensuales],
            'totales': [float(v['total']) for v in ventas_mensuales],
            'cantidades': [v['cantidad'] for v in ventas_mensuales]
        }

    @staticmethod
    def clientes_top(limite=10, fecha_inicio=None, fecha_fin=None):
        """
        Top clientes por volumen de compras
        """
        filtros = Q(cliente__isnull=False)
        if fecha_inicio and fecha_fin:
            filtros &= Q(fecha__date__range=[fecha_inicio, fecha_fin])

        clientes = Venta.objects.filter(filtros).values(
            'cliente__id',
            'cliente__nombre',
            'cliente__rut'
        ).annotate(
            total_compras=Sum('total_con_iva'),
            num_compras=Count('id'),
            ticket_promedio=Avg('total_con_iva')
        ).order_by('-total_compras')[:limite]

        return [{
            'cliente_id': c['cliente__id'],
            'nombre': c['cliente__nombre'] or c['cliente__rut'],
            'rut': c['cliente__rut'],
            'total_compras': float(c['total_compras']),
            'num_compras': c['num_compras'],
            'ticket_promedio': float(c['ticket_promedio'])
        } for c in clientes]

    @staticmethod
    def kpis_hoy():
        """
        KPIs del día actual para cards del dashboard
        """
        hoy = timezone.now().date()
        ayer = hoy - timedelta(days=1)

        # Ventas de hoy
        hoy_stats = Venta.objects.filter(
            fecha__date=hoy
        ).aggregate(
            total=Coalesce(Sum('total_con_iva'), Decimal('0')),
            cantidad=Count('id')
        )

        # Ventas de ayer para comparación
        ayer_stats = Venta.objects.filter(
            fecha__date=ayer
        ).aggregate(
            total=Coalesce(Sum('total_con_iva'), Decimal('0')),
            cantidad=Count('id')
        )

        # Calcular variación porcentual
        variacion_pct = 0
        if ayer_stats['total'] > 0:
            variacion_pct = ((hoy_stats['total'] - ayer_stats['total']) / ayer_stats['total']) * 100

        return {
            'hoy': {
                'total': float(hoy_stats['total']),
                'cantidad': hoy_stats['cantidad']
            },
            'ayer': {
                'total': float(ayer_stats['total']),
                'cantidad': ayer_stats['cantidad']
            },
            'variacion_pct': float(variacion_pct)
        }

    @staticmethod
    def metricas_avanzadas(fecha_inicio=None, fecha_fin=None):
        """
        Métricas financieras avanzadas del periodo
        Incluye: ventas netas, margen de descuento, tasa de descuento promedio
        """
        if not fecha_inicio:
            fecha_inicio = timezone.now().date() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = timezone.now().date()

        resultado = Venta.objects.filter(
            fecha__date__range=[fecha_inicio, fecha_fin]
        ).aggregate(
            total_bruto=Coalesce(Sum(F('total_sin_iva') + F('descuento')), Decimal('0')),
            total_neto=Coalesce(Sum('total_sin_iva'), Decimal('0')),
            total_descuentos=Coalesce(Sum('descuento'), Decimal('0')),
            total_iva=Coalesce(Sum('total_iva'), Decimal('0')),
            cantidad_ventas=Count('id')
        )

        # Cálculos derivados
        total_bruto = float(resultado['total_bruto'])
        total_neto = float(resultado['total_neto'])
        total_descuentos = float(resultado['total_descuentos'])
        total_iva = float(resultado['total_iva'])
        cantidad_ventas = resultado['cantidad_ventas']

        margen_descuento = (total_descuentos / total_bruto * 100) if total_bruto > 0 else 0
        tasa_descuento_promedio = (total_descuentos / cantidad_ventas) if cantidad_ventas > 0 else 0

        return {
            'ventas_brutas': total_bruto,
            'ventas_netas': total_neto,
            'total_descuentos': total_descuentos,
            'total_iva': total_iva,
            'margen_descuento_pct': margen_descuento,
            'descuento_promedio_transaccion': tasa_descuento_promedio,
            'cantidad_ventas': cantidad_ventas,
            'fecha_inicio': fecha_inicio.isoformat(),
            'fecha_fin': fecha_fin.isoformat()
        }

    @staticmethod
    def ticket_promedio_segmentado(fecha_inicio=None, fecha_fin=None):
        """
        Ticket promedio segmentado por canal y por día de semana
        """
        if not fecha_inicio:
            fecha_inicio = timezone.now().date() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = timezone.now().date()

        # Por canal
        por_canal = Venta.objects.filter(
            fecha__date__range=[fecha_inicio, fecha_fin]
        ).values('canal_venta').annotate(
            ticket_promedio=Avg('total_con_iva'),
            cantidad=Count('id')
        )

        # Por día de semana (1=Domingo, 7=Sábado en ExtractWeekDay)
        por_dia_semana = Venta.objects.filter(
            fecha__date__range=[fecha_inicio, fecha_fin]
        ).annotate(
            dia_semana=ExtractWeekDay('fecha')
        ).values('dia_semana').annotate(
            ticket_promedio=Avg('total_con_iva'),
            total=Sum('total_con_iva'),
            cantidad=Count('id')
        ).order_by('dia_semana')

        dias_semana_nombres = {
            1: 'Domingo', 2: 'Lunes', 3: 'Martes', 4: 'Miércoles',
            5: 'Jueves', 6: 'Viernes', 7: 'Sábado'
        }

        return {
            'por_canal': [{
                'canal': c['canal_venta'],
                'ticket_promedio': float(c['ticket_promedio']),
                'cantidad': c['cantidad']
            } for c in por_canal],
            'por_dia_semana': [{
                'dia': dias_semana_nombres.get(d['dia_semana'], 'Desconocido'),
                'dia_numero': d['dia_semana'],
                'ticket_promedio': float(d['ticket_promedio']),
                'total': float(d['total']),
                'cantidad': d['cantidad']
            } for d in por_dia_semana]
        }

    @staticmethod
    def ventas_por_dia_semana(fecha_inicio=None, fecha_fin=None):
        """
        Distribución de ventas por día de la semana
        """
        if not fecha_inicio:
            fecha_inicio = timezone.now().date() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = timezone.now().date()

        ventas = Venta.objects.filter(
            fecha__date__range=[fecha_inicio, fecha_fin]
        ).annotate(
            dia_semana=ExtractWeekDay('fecha')
        ).values('dia_semana').annotate(
            total=Sum('total_con_iva'),
            cantidad=Count('id')
        ).order_by('dia_semana')

        dias_semana_nombres = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']

        # Inicializar todos los días con 0
        resultado = {i+1: {'total': 0, 'cantidad': 0} for i in range(7)}

        for v in ventas:
            resultado[v['dia_semana']] = {
                'total': float(v['total']),
                'cantidad': v['cantidad']
            }

        return {
            'labels': dias_semana_nombres,
            'totales': [resultado[i+1]['total'] for i in range(7)],
            'cantidades': [resultado[i+1]['cantidad'] for i in range(7)]
        }

    @staticmethod
    def clientes_nuevos_vs_recurrentes(fecha_inicio=None, fecha_fin=None):
        """
        Análisis de clientes nuevos vs recurrentes en el periodo
        """
        if not fecha_inicio:
            fecha_inicio = timezone.now().date() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = timezone.now().date()

        # Ventas del periodo con cliente
        ventas_periodo = Venta.objects.filter(
            fecha__date__range=[fecha_inicio, fecha_fin],
            cliente__isnull=False
        )

        # Agrupar por cliente
        clientes_stats = ventas_periodo.values('cliente').annotate(
            num_compras=Count('id'),
            total_gastado=Sum('total_con_iva'),
            primera_compra=Min('fecha')
        )

        nuevos = 0
        recurrentes = 0
        total_nuevos = Decimal('0')
        total_recurrentes = Decimal('0')

        for c in clientes_stats:
            # Si la primera compra fue en este periodo y solo tiene 1 compra, es nuevo
            if c['primera_compra'].date() >= fecha_inicio and c['num_compras'] == 1:
                nuevos += 1
                total_nuevos += c['total_gastado']
            else:
                recurrentes += 1
                total_recurrentes += c['total_gastado']

        return {
            'nuevos': {
                'cantidad': nuevos,
                'total_ventas': float(total_nuevos),
                'promedio': float(total_nuevos / nuevos) if nuevos > 0 else 0
            },
            'recurrentes': {
                'cantidad': recurrentes,
                'total_ventas': float(total_recurrentes),
                'promedio': float(total_recurrentes / recurrentes) if recurrentes > 0 else 0
            }
        }

    @staticmethod
    def heatmap_ventas_hora_dia(fecha_inicio=None, fecha_fin=None):
        """
        Heatmap de ventas: matriz de horas (0-23) x días de semana (Lun-Dom)
        Para visualizar patrones de venta por hora y día
        """
        if not fecha_inicio:
            fecha_inicio = timezone.now().date() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = timezone.now().date()

        ventas = Venta.objects.filter(
            fecha__date__range=[fecha_inicio, fecha_fin]
        ).annotate(
            hora=ExtractHour('fecha'),
            dia_semana=ExtractWeekDay('fecha')
        ).values('hora', 'dia_semana').annotate(
            total=Sum('total_con_iva'),
            cantidad=Count('id')
        )

        # Crear matriz 24h x 7 días
        heatmap = {}
        for hora in range(24):
            heatmap[hora] = {dia: {'total': 0, 'cantidad': 0} for dia in range(1, 8)}

        for v in ventas:
            heatmap[v['hora']][v['dia_semana']] = {
                'total': float(v['total']),
                'cantidad': v['cantidad']
            }

        # Convertir a formato para Chart.js heatmap
        dias_nombres = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']

        return {
            'horas': [f"{h:02d}:00" for h in range(24)],
            'dias': dias_nombres,
            'data': [
                {
                    'hora': f"{hora:02d}:00",
                    'dia': dias_nombres[dia-1],
                    'total': heatmap[hora][dia]['total'],
                    'cantidad': heatmap[hora][dia]['cantidad']
                }
                for hora in range(24) for dia in range(1, 8)
            ]
        }

    @staticmethod
    def proyeccion_ventas(dias_proyeccion=7):
        """
        Proyección simple de ventas basada en promedio de últimos 30 días
        """
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)

        # Promedio diario de los últimos 30 días
        promedio_diario = Venta.objects.filter(
            fecha__date__range=[fecha_inicio, fecha_fin]
        ).aggregate(
            total=Coalesce(Sum('total_con_iva'), Decimal('0'))
        )

        promedio = float(promedio_diario['total']) / 30

        # Proyectar próximos días
        proyecciones = []
        for i in range(1, dias_proyeccion + 1):
            fecha_proyectada = fecha_fin + timedelta(days=i)
            proyecciones.append({
                'fecha': fecha_proyectada.isoformat(),
                'proyeccion': round(promedio, 2)
            })

        return {
            'promedio_diario': round(promedio, 2),
            'proyecciones': proyecciones
        }

    @staticmethod
    def comparativa_mom(meses=6):
        """
        Comparativa Month-over-Month (MoM)
        Muestra crecimiento/decrecimiento porcentual mes a mes
        """
        fecha_inicio = timezone.now().date() - timedelta(days=meses*30)

        ventas_mensuales = Venta.objects.filter(
            fecha__date__gte=fecha_inicio
        ).annotate(
            mes=TruncMonth('fecha')
        ).values('mes').annotate(
            total=Sum('total_con_iva'),
            cantidad=Count('id')
        ).order_by('mes')

        meses_data = list(ventas_mensuales)

        # Calcular variación MoM
        for i in range(1, len(meses_data)):
            mes_anterior = float(meses_data[i-1]['total'])
            mes_actual = float(meses_data[i]['total'])

            variacion = 0
            if mes_anterior > 0:
                variacion = ((mes_actual - mes_anterior) / mes_anterior) * 100

            meses_data[i]['variacion_mom'] = round(variacion, 2)

        # El primer mes no tiene comparación
        if len(meses_data) > 0:
            meses_data[0]['variacion_mom'] = 0

        return [{
            'mes': m['mes'].strftime('%B %Y'),
            'total': float(m['total']),
            'cantidad': m['cantidad'],
            'variacion_mom': m.get('variacion_mom', 0)
        } for m in meses_data]

    @staticmethod
    def alertas_automaticas(fecha_inicio=None, fecha_fin=None):
        """
        Sistema de alertas automáticas basado en métricas
        Detecta: caída de ventas, bajo rendimiento, productos sin vender, etc.
        """
        if not fecha_inicio:
            fecha_inicio = timezone.now().date() - timedelta(days=7)
        if not fecha_fin:
            fecha_fin = timezone.now().date()

        alertas = []

        # 1. Alerta: Caída de ventas respecto a semana anterior
        semana_anterior_inicio = fecha_inicio - timedelta(days=7)
        semana_anterior_fin = fecha_inicio - timedelta(days=1)

        ventas_actuales = Venta.objects.filter(
            fecha__date__range=[fecha_inicio, fecha_fin]
        ).aggregate(total=Coalesce(Sum('total_con_iva'), Decimal('0')))

        ventas_anteriores = Venta.objects.filter(
            fecha__date__range=[semana_anterior_inicio, semana_anterior_fin]
        ).aggregate(total=Coalesce(Sum('total_con_iva'), Decimal('0')))

        if ventas_anteriores['total'] > 0:
            variacion = ((ventas_actuales['total'] - ventas_anteriores['total']) / ventas_anteriores['total']) * 100

            if variacion < -10:
                alertas.append({
                    'tipo': 'danger',
                    'titulo': 'Caída en ventas',
                    'mensaje': f'Las ventas han caído un {abs(variacion):.1f}% respecto a la semana anterior',
                    'valor': float(variacion)
                })
            elif variacion > 20:
                alertas.append({
                    'tipo': 'success',
                    'titulo': 'Incremento en ventas',
                    'mensaje': f'Las ventas han aumentado un {variacion:.1f}% respecto a la semana anterior',
                    'valor': float(variacion)
                })

        # 2. Alerta: Productos sin vender en el periodo
        productos_vendidos = DetalleVenta.objects.filter(
            venta__fecha__date__range=[fecha_inicio, fecha_fin]
        ).values_list('producto_id', flat=True).distinct()

        total_productos = Producto.objects.count()
        productos_sin_venta = total_productos - len(productos_vendidos)

        if productos_sin_venta > 0:
            alertas.append({
                'tipo': 'warning',
                'titulo': 'Productos sin ventas',
                'mensaje': f'{productos_sin_venta} productos no se han vendido en los últimos 7 días',
                'valor': productos_sin_venta
            })

        # 3. Alerta: Días sin ventas
        dias_sin_ventas = 0
        for i in range((fecha_fin - fecha_inicio).days + 1):
            dia = fecha_inicio + timedelta(days=i)
            ventas_dia = Venta.objects.filter(fecha__date=dia).count()
            if ventas_dia == 0:
                dias_sin_ventas += 1

        if dias_sin_ventas > 0:
            alertas.append({
                'tipo': 'warning',
                'titulo': 'Días sin ventas',
                'mensaje': f'Hubo {dias_sin_ventas} días sin ventas en los últimos 7 días',
                'valor': dias_sin_ventas
            })

        # 4. Alerta: Ticket promedio bajo
        ticket_actual = Venta.objects.filter(
            fecha__date__range=[fecha_inicio, fecha_fin]
        ).aggregate(promedio=Avg('total_con_iva'))

        ticket_historico = Venta.objects.filter(
            fecha__date__lt=fecha_inicio
        ).aggregate(promedio=Avg('total_con_iva'))

        if ticket_actual['promedio'] and ticket_historico['promedio']:
            # Convertir a float para evitar errores de tipo Decimal
            ticket_actual_val = float(ticket_actual['promedio'])
            ticket_historico_val = float(ticket_historico['promedio'])

            if ticket_actual_val < ticket_historico_val * 0.8:
                alertas.append({
                    'tipo': 'warning',
                    'titulo': 'Ticket promedio bajo',
                    'mensaje': f'El ticket promedio actual (${ticket_actual_val:.0f}) es significativamente menor al histórico (${ticket_historico_val:.0f})',
                    'valor': ticket_actual_val
                })

        return alertas
