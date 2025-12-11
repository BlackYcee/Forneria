import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from .models import Cliente
from .services import procesar_venta


@require_http_methods(["POST"])
def procesar_venta_json(request):
    """
    Endpoint para procesar una venta completa desde el frontend React.
    
    JSON esperado:
    {
        "cliente_id": 123,  # null para "Consumidor Final"
        "canal": "pos",
        "items": [
            {
                "producto_id": 38,
                "cantidad": 1,
                "precio_unitario": "8000"
            }
        ],
        "pagos": [
            {
                "metodo": "EFE",
                "monto": "8000",
                "monto_recibido": "10000"
            }
        ]
    }
    """
    try:
        data = json.loads(request.body)
        
        # ✅ Usar 'cliente_id' en lugar de 'usuario'
        cliente_id = data.get('cliente_id')
        canal = data.get('canal', 'pos')
        items = data.get('items', [])
        pagos = data.get('pagos', [])
        
        # Si cliente_id es null, crear venta para "Consumidor Final"
        cliente = None
        if cliente_id:
            try:
                cliente = Cliente.objects.get(id=cliente_id)
            except Cliente.DoesNotExist:
                return JsonResponse({
                    'error': f'Cliente con ID {cliente_id} no encontrado'
                }, status=400)
        
        # Preparar metodo_pago_info del primer pago
        if not pagos:
            return JsonResponse({
                'error': 'Debe proporcionar al menos un método de pago'
            }, status=400)
        
        metodo_pago_info = {
            'metodo': pagos[0]['metodo'],
            'monto': float(pagos[0]['monto']),
            'referencia': pagos[0].get('monto_recibido', pagos[0]['monto'])
        }
        
        # Llamar al servicio procesar_venta
        venta_creada = procesar_venta(
            cliente=cliente,
            items_data=items,
            metodo_pago_info=metodo_pago_info,
            canal=canal,
            direccion=None
        )
        
        return JsonResponse({
            'success': True,
            'venta_id': venta_creada.id,
            'mensaje': 'Venta registrada exitosamente',
            'total': str(venta_creada.total)
        }, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido'
        }, status=400)
    except ValidationError as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno: {str(e)}'
        }, status=500)
