"""
Script para crear superusuario automáticamente
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forneria.settings')
django.setup()

from django.contrib.auth.models import User

username = 'admin'
email = 'admin@forneria.cl'
password = 'admin123'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'✅ Superusuario creado: {username}')
    print(f'   Email: {email}')
    print(f'   Password: {password}')
else:
    print(f'⚠️  El superusuario "{username}" ya existe')
