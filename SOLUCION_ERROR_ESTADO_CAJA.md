# SOLUCIÓN: Error 500 en caja/estado-caja/ al cerrar caja

## 🔍 Problema identificado

El error 500 en el endpoint `caja/estado-caja/` ocurre cuando:
1. No hay denominaciones de moneda creadas en la base de datos del servidor
2. Hay algún error en la función `calcular_denominaciones_esperadas()`
3. Las migraciones no están aplicadas correctamente en el servidor

## 📋 Soluciones

### 1. Aplicar migraciones en el servidor

```bash
# En el servidor, dentro del directorio del proyecto:
python manage.py migrate caja
```

### 2. Poblar denominaciones de moneda

**Opción A: Usando el comando de management (RECOMENDADO)**
```bash
python manage.py poblar_denominaciones
```

**Opción B: Usando el script independiente**
```bash
python poblar_denominaciones.py
```

### 3. Verificar que las denominaciones están creadas

```bash
python manage.py shell -c "from caja.models import DenominacionMoneda; print('Total denominaciones:', DenominacionMoneda.objects.count()); print('Activas:', DenominacionMoneda.objects.filter(activo=True).count())"
```

### 4. Probar el endpoint directamente

```bash
# Desde el servidor, verificar que el endpoint funciona:
curl -H "Accept: application/json" http://localhost:8000/dashboard/caja/estado-caja/
```

## 🚀 Pasos para ejecutar en el servidor

1. **Conectarse al servidor** (SSH/Terminal)
2. **Navegar al directorio del proyecto**
3. **Activar el entorno virtual** (si aplica)
4. **Aplicar migraciones:**
   ```bash
   python manage.py migrate caja
   ```
5. **Poblar denominaciones:**
   ```bash
   python manage.py poblar_denominaciones
   ```
6. **Reiniciar el servidor web** (nginx/apache/gunicorn)
7. **Probar la funcionalidad** desde el navegador

## 🔧 Archivos creados para la solución

- `poblar_denominaciones.py` - Script independiente
- `caja/management/commands/poblar_denominaciones.py` - Comando Django
- `SOLUCION_ERROR_ESTADO_CAJA.md` - Este documento

## ⚠️ Notas importantes

- Las denominaciones creadas incluyen billetes y monedas colombianas estándar
- El comando es seguro de ejecutar múltiples veces (no duplica datos)
- Si el problema persiste, revisar los logs del servidor para más detalles
- El error ocurre específicamente al intentar cerrar caja porque requiere calcular denominaciones esperadas

## 📊 Denominaciones que se crean

**Billetes:** $100.000, $50.000, $20.000, $10.000, $5.000, $2.000, $1.000
**Monedas:** $1.000, $500, $200, $100, $50

Total: 12 denominaciones principales de moneda colombiana.