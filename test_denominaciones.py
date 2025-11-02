"""
Script de prueba para verificar el endpoint de denominaciones
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

# Crear cliente de prueba
client = Client()

# Obtener un usuario superuser
user = User.objects.filter(is_superuser=True).first()

if not user:
    print("❌ No se encontró un usuario superuser. Crea uno primero.")
    exit(1)

print(f"✅ Usuario de prueba: {user.username} (superuser={user.is_superuser}, staff={user.is_staff})")

# Login
client.force_login(user)

# Probar el endpoint de denominaciones
print("\n🔄 Probando endpoint /caja/denominaciones/...")
response = client.get('/caja/denominaciones/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')

print(f"   - Status Code: {response.status_code}")
print(f"   - Content-Type: {response.get('Content-Type', 'N/A')}")

if response.status_code == 200:
    import json
    data = json.loads(response.content)
    print(f"   - Success: {data.get('success', False)}")
    print(f"   - Denominaciones encontradas: {len(data.get('denominaciones', []))}")
    print("\n💰 Denominaciones:")
    for denom in data.get('denominaciones', []):
        print(f"      ID: {denom['id']}, Valor: ${denom['valor']:,.0f}, Tipo: {denom['tipo']}")
    print("\n✅ Endpoint funcionando correctamente!")
else:
    print(f"   - Response: {response.content.decode('utf-8')}")
    print("\n❌ El endpoint no está funcionando correctamente")
