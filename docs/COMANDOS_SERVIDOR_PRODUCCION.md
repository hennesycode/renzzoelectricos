# 🔧 Comandos para Configurar Servidor de Producción

## 📡 Conexión al Servidor

```bash
# Conectar al servidor Ubuntu
ssh hennesy@ubuntu-server-hennesy
# Contraseña: Comandos555123*
```

## 🐳 Paso 1: Verificar Contenedores Docker

```bash
# Listar todos los contenedores en ejecución
sudo docker ps

# Buscar el contenedor específico
sudo docker ps | grep web-gg0wswocg8c4soc80kk88g8g-150356494831
```

## 📦 Paso 2: Acceder al Contenedor

```bash
# Opción 1: Acceso con el ID completo
sudo docker exec -it web-gg0wswocg8c4soc80kk88g8g-150356494831 bash

# Opción 2: Si el nombre es diferente, usar docker ps para ver el nombre exacto
# y luego usar ese nombre

# Opción 3: Si es un contenedor de docker-compose
cd /ruta/a/renzzoelectricos
sudo docker-compose exec web bash
```

## 👤 Paso 3: Configurar Permisos del Usuario

### Opción A: Desde Dentro del Contenedor (Método Directo)

```bash
# Una vez dentro del contenedor, ejecutar:
python manage.py shell

# Dentro del shell de Django, ejecutar:
from users.models import User

# Buscar todos los usuarios
users = User.objects.all()
for u in users:
    print(f"ID: {u.id}, Username: {u.username}, Email: {u.email}, Staff: {u.is_staff}, Superuser: {u.is_superuser}")

# Seleccionar el usuario que necesitas (reemplazar 'admin' con el username correcto)
user = User.objects.get(username='admin')  # O usar el username que veas

# Dar permisos de staff y superuser
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.save()

# Verificar
print(f"Usuario: {user.username}")
print(f"Staff: {user.is_staff}")
print(f"Superuser: {user.is_superuser}")
print(f"Activo: {user.is_active}")

# Salir del shell
exit()
```

### Opción B: Script Python Automático (Método Rápido)

```bash
# Crear script temporal dentro del contenedor
cat > configurar_permisos.py << 'EOF'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

print("=" * 70)
print("CONFIGURANDO PERMISOS DE USUARIOS")
print("=" * 70)

# Listar todos los usuarios
print("\nUsuarios actuales:")
for u in User.objects.all():
    print(f"  - {u.username} (Staff: {u.is_staff}, Superuser: {u.is_superuser})")

# Buscar usuario admin o el primer usuario
try:
    user = User.objects.get(username='admin')
except User.DoesNotExist:
    print("\nNo se encontró usuario 'admin', usando el primer usuario...")
    user = User.objects.first()

if user:
    print(f"\nConfigurando permisos para: {user.username}")
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.save()
    
    print(f"✅ Usuario actualizado:")
    print(f"   - Username: {user.username}")
    print(f"   - Email: {user.email}")
    print(f"   - Staff: {user.is_staff}")
    print(f"   - Superuser: {user.is_superuser}")
    print(f"   - Activo: {user.is_active}")
else:
    print("❌ No se encontraron usuarios en la base de datos")

print("\n" + "=" * 70)
EOF

# Ejecutar el script
python configurar_permisos.py

# Eliminar el script temporal
rm configurar_permisos.py
```

### Opción C: Comando Directo (Una Línea)

```bash
# Desde dentro del contenedor:
python manage.py shell -c "from users.models import User; user = User.objects.get(username='admin'); user.is_staff = True; user.is_superuser = True; user.save(); print(f'✅ Usuario {user.username} actualizado - Staff: {user.is_staff}, Superuser: {user.is_superuser}')"
```

## 🔄 Paso 4: Actualizar Código y Archivos Estáticos

```bash
# Desde dentro del contenedor (después de configurar permisos):

# 1. Verificar que las denominaciones existen
python crear_denominaciones.py

# 2. IMPORTANTE: Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Salir del contenedor
exit
```

## 🔃 Paso 5: Reiniciar Servicios

```bash
# Desde el servidor (fuera del contenedor):

# Opción 1: Con docker-compose
cd /ruta/a/renzzoelectricos
sudo docker-compose restart web

# Opción 2: Con docker directo
sudo docker restart web-gg0wswocg8c4soc80kk88g8g-150356494831

# Ver logs para verificar
sudo docker logs -f web-gg0wswocg8c4soc80kk88g8g-150356494831
# O con docker-compose:
sudo docker-compose logs -f web
```

## ✅ Paso 6: Verificar Acceso

1. Abrir navegador en **https://renzzoelectricos.com/admin/**
2. Iniciar sesión con las credenciales del usuario
3. Verificar que puedes acceder al admin de Django
4. Ir a **Dashboard → Caja**
5. Hacer clic en **"Abrir Caja"**
6. Verificar que aparecen las denominaciones

## 🐛 Troubleshooting

### Si no puedes acceder al contenedor:

```bash
# Ver todos los contenedores (incluyendo detenidos)
sudo docker ps -a

# Ver contenedores de docker-compose
cd /ruta/a/renzzoelectricos
sudo docker-compose ps

# Reiniciar todos los servicios
sudo docker-compose down
sudo docker-compose up -d
```

### Si el usuario no existe:

```bash
# Crear un nuevo superusuario
sudo docker exec -it NOMBRE_CONTENEDOR python manage.py createsuperuser
# O con docker-compose:
sudo docker-compose exec web python manage.py createsuperuser
```

### Verificar la base de datos:

```bash
# Acceder al contenedor de MySQL
sudo docker exec -it NOMBRE_CONTENEDOR_MYSQL mysql -u root -p

# Ver usuarios
USE nombre_base_datos;
SELECT id, username, email, is_staff, is_superuser, is_active FROM users_user;
```

## 📝 Notas Importantes

1. **Siempre usa `sudo`** para comandos docker en el servidor
2. **Guarda las credenciales** del superusuario en un lugar seguro
3. **Verifica los logs** después de cada cambio: `docker-compose logs -f web`
4. **Limpia caché del navegador** después de los cambios
5. **Ejecuta `collectstatic`** después de pull desde Git

## 🔒 Seguridad

- Cambia la contraseña del servidor después de la primera configuración
- Usa contraseñas fuertes para el superusuario de Django
- No compartas las credenciales en repositorios públicos
- Considera usar variables de entorno para datos sensibles

## 📞 Comandos de Emergencia

```bash
# Ver estado de todos los servicios
sudo docker-compose ps

# Reiniciar todo
sudo docker-compose restart

# Ver logs de errores
sudo docker-compose logs --tail=100 web

# Entrar al contenedor sin importar el nombre
sudo docker exec -it $(sudo docker ps | grep web | awk '{print $1}') bash

# Backup de base de datos
sudo docker-compose exec db mysqldump -u root -p nombre_db > backup_$(date +%Y%m%d).sql
```
