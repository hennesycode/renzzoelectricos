# 🔧 Guía Rápida: Scripts de Denominaciones

**Fecha:** 2 de Noviembre de 2025  
**Para:** Renzzo Eléctricos - Producción

---

## 📋 Scripts Disponibles

Tienes 3 scripts Python simples para gestionar las denominaciones:

1. **`validar_denominaciones.py`** - Ver qué hay en la base de datos
2. **`eliminar_todas_denominaciones.py`** - Limpiar todo
3. **`crear_denominaciones_correctas.py`** - Crear denominaciones correctas

---

## 🚀 Pasos para Solucionar Error 500

### 1️⃣ SSH al Servidor

```bash
ssh hennesy@ubuntu-server-hennesy
# Contraseña: Comandos555123*
```

### 2️⃣ Ubicar el Proyecto

```bash
cd /ruta/a/tu/proyecto/renzzoelectricos
git pull origin main
```

### 3️⃣ Acceder al Contenedor Docker

```bash
# Buscar el contenedor
sudo docker ps

# Acceder al contenedor (reemplaza con tu ID)
sudo docker exec -it web-gg0wswocg8c4soc80kk88g8g-150356494831 bash
```

### 4️⃣ Validar Estado Actual

```bash
python validar_denominaciones.py
```

**Salida esperada:**
```
🔍 VALIDACIÓN DE DENOMINACIONES
📊 Total de registros: X
📋 LISTADO COMPLETO
   [muestra todas las denominaciones]
🔍 VERIFICACIÓN DE DUPLICADOS
   ⚠️  ENCONTRADOS duplicados... (si hay)
```

### 5️⃣ Eliminar Todas las Denominaciones

```bash
python eliminar_todas_denominaciones.py
```

**Confirmación requerida:** Debes escribir `SI` para confirmar.

**Salida esperada:**
```
🗑️  ELIMINAR TODAS LAS DENOMINACIONES
⚠️  Se encontraron X registros
¿Está SEGURO? (escriba 'SI' para confirmar): SI
✅ Eliminados X registros correctamente
```

### 6️⃣ Crear Denominaciones Correctas

```bash
python crear_denominaciones_correctas.py
```

**Confirmación requerida:** Debes escribir `SI` para confirmar.

**Salida esperada:**
```
💵 CREAR DENOMINACIONES CORRECTAS
📋 Se crearán:
🪙 MONEDAS (4):
   • $    50
   • $   100
   • $   500
   • $ 1,000
💵 BILLETES (7):
   • $  1,000
   • $  2,000
   • $  5,000
   • $ 10,000
   • $ 20,000
   • $ 50,000
   • $100,000
¿Desea continuar? (escriba 'SI' para confirmar): SI
✅ PERFECTO! Todas las denominaciones están creadas
```

### 7️⃣ Recolectar Archivos Estáticos

```bash
# Dentro del contenedor
python manage.py collectstatic --noinput
```

### 8️⃣ Salir y Reiniciar Contenedor

```bash
# Salir del contenedor
exit

# Reiniciar contenedor (fuera del contenedor)
sudo docker restart web-gg0wswocg8c4soc80kk88g8g-150356494831

# Ver logs
sudo docker logs -f --tail=50 web-gg0wswocg8c4soc80kk88g8g-150356494831
```

### 9️⃣ Verificar en el Navegador

1. Limpiar caché del navegador: `Ctrl + Shift + Delete`
2. O usar modo incógnito: `Ctrl + Shift + N`
3. Acceder a: `https://renzzoelectricos.com/admin/caja/denominacionmoneda/`
4. **Debe cargar SIN error 500**
5. Deberías ver **11 denominaciones**: 4 monedas + 7 billetes

---

## 📝 Comandos Completos (Copiar y Pegar)

```bash
# 1. SSH al servidor
ssh hennesy@ubuntu-server-hennesy
# Password: Comandos555123*

# 2. Navegar al proyecto y actualizar código
cd /ruta/a/renzzoelectricos
git pull origin main

# 3. Acceder al contenedor
sudo docker exec -it web-gg0wswocg8c4soc80kk88g8g-150356494831 bash

# 4. Dentro del contenedor - Validar
python validar_denominaciones.py

# 5. Dentro del contenedor - Eliminar todas
python eliminar_todas_denominaciones.py
# Escribe: SI

# 6. Dentro del contenedor - Crear correctas
python crear_denominaciones_correctas.py
# Escribe: SI

# 7. Dentro del contenedor - Recolectar estáticos
python manage.py collectstatic --noinput

# 8. Salir del contenedor
exit

# 9. Reiniciar contenedor
sudo docker restart web-gg0wswocg8c4soc80kk88g8g-150356494831

# 10. Ver logs (Ctrl+C para salir)
sudo docker logs -f --tail=50 web-gg0wswocg8c4soc80kk88g8g-150356494831
```

---

## 🔍 Solución de Problemas

### ❌ Error: "No such file or directory"

**Problema:** Los scripts no están en el contenedor.

**Solución:**
```bash
# Desde FUERA del contenedor (en el servidor)
cd /ruta/a/renzzoelectricos
git pull origin main

# Copiar scripts al contenedor manualmente
sudo docker cp validar_denominaciones.py web-xxx:/app/
sudo docker cp eliminar_todas_denominaciones.py web-xxx:/app/
sudo docker cp crear_denominaciones_correctas.py web-xxx:/app/

# Entrar al contenedor
sudo docker exec -it web-xxx bash
cd /app
python validar_denominaciones.py
```

### ❌ Error 500 persiste después de crear denominaciones

**Posibles causas:**

1. **Caché del navegador no limpiado**
   - Solución: `Ctrl + Shift + Delete` o modo incógnito

2. **Archivos estáticos no recolectados**
   - Solución: `python manage.py collectstatic --noinput`

3. **Contenedor no reiniciado**
   - Solución: `sudo docker restart web-xxx`

4. **Todavía hay duplicados**
   - Solución: Ejecutar `python validar_denominaciones.py` para verificar

### ❌ Error: "ImproperlyConfigured"

**Problema:** Variable de entorno no configurada.

**Solución:**
```bash
# Dentro del contenedor
export DJANGO_SETTINGS_MODULE=config.settings
python validar_denominaciones.py
```

---

## ✅ Resultado Final Esperado

Después de ejecutar todos los pasos:

1. **Base de Datos:**
   - 4 monedas: $50, $100, $500, $1,000
   - 7 billetes: $1,000, $2,000, $5,000, $10,000, $20,000, $50,000, $100,000
   - Total: **11 denominaciones activas**
   - **Sin duplicados**

2. **Admin de Django:**
   - URL: `https://renzzoelectricos.com/admin/caja/denominacionmoneda/`
   - **Debe cargar correctamente (sin error 500)**
   - Lista visible con las 11 denominaciones

3. **Modal Abrir Caja:**
   - URL: `https://renzzoelectricos.com/caja/`
   - Click en "Abrir Caja"
   - **Modal debe mostrar grid de denominaciones**
   - 💵 BILLETES: 7 campos con valores
   - 🪙 MONEDAS: 4 campos con valores

---

## 📞 Soporte

Si después de seguir estos pasos el error persiste:

1. Ejecuta `python validar_denominaciones.py` y copia la salida
2. Verifica los logs: `sudo docker logs web-xxx | grep -i error`
3. Confirma que la migración se aplicó: `python manage.py showmigrations caja`

---

**Última actualización:** 2 de Noviembre de 2025  
**Autor:** GitHub Copilot  
**Proyecto:** Renzzo Eléctricos
