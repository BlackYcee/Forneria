import requests
import json

# Crear empleado
empleado_data = {
    'nombre_completo': 'Ana Perez',
    'username': 'vendedor1',
    'password': 'password123',
    'cargo': 'Vendedor'
}

response = requests.post(
    'http://localhost:8000/pos/api/empleados/',
    json=empleado_data,
    headers={'Content-Type': 'application/json'}
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 201:
    print("\n✅ Empleado creado exitosamente!")
    data = response.json()
    print(f"ID: {data.get('id')}")
    print(f"Nombres: {data.get('nombres')}")
    print(f"Apellido: {data.get('apellido_paterno')}")
    print(f"Cargo: {data.get('cargo')}")
else:
    print("\n❌ Error al crear empleado")
    try:
        errors = response.json()
        print(f"Errores: {json.dumps(errors, indent=2)}")
    except:
        pass
