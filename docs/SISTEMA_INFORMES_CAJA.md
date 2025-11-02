# 📊 Sistema de Informes de Caja - Renzzo Eléctricos

## 🎯 Resumen del Sistema

Se ha implementado un sistema completo de informes y estadísticas de caja con diseño moderno, funcionalidad AJAX y análisis detallado de movimientos financieros.

## ✅ Características Implementadas

### 1. 📊 Balance General
- **Total Dinero Guardado**: Suma de todo el dinero guardado fuera de caja
- **Total Dinero en Caja**: Suma del dinero que quedó en las cajas
- **Total Ingresos**: Suma de todas las entradas de efectivo (sin incluir aperturas)
- **Total Egresos**: Suma de todas las salidas de efectivo
- **Flujo Neto**: Resultado del periodo (Ingresos - Egresos)
- **Estadísticas**: Número de cajas cerradas y promedio de diferencias

### 2. 📋 Historial de Arqueos de Caja
Cada registro muestra:
- **Saldo Inicial**: Dinero con el que se abrió la caja
- **Total Entradas**: Suma de ventas, abonos, etc.
- **Total Salidas**: Retiros, pagos a proveedores, etc.
- **Saldo Teórico**: (Inicial + Entradas) - Salidas
- **Saldo Real**: Dinero contado físicamente al cerrar
- **Diferencia (Descuadre)**: Saldo Real - Saldo Teórico
  - ✅ Verde: Sobrante
  - ❌ Rojo: Faltante
  - ⚪ Gris: Cuadre perfecto
- **Distribución**: Dinero en caja vs dinero guardado

**Paginación**: 5 cajas por página con navegación

### 3. 💰 Flujo de Efectivo Detallado
- **Ingresos por Tipo**: Desglose de entradas (Ventas, Cambios, Ingresos, etc.)
- **Egresos por Tipo**: Desglose de salidas (Gastos, Pagos, Retiros, etc.)
- **Cantidad de Movimientos**: Contador por cada tipo
- **Resultado del Periodo**: 
  - 🟢 Verde: Ganancia (flujo positivo)
  - 🔴 Rojo: Pérdida (flujo negativo)

## 🎨 Diseño y UX

### Tema Visual
- **Colores**: Verde oscuro profesional (#1b4332, #2d6a4f, #40916c)
- **Gradientes**: Modernos y suaves
- **Animaciones**: Transiciones fluidas
- **Iconos**: Bootstrap Icons
- **Responsive**: Se adapta a móviles, tablets y desktop

### Interactividad
- **Sin Recargar Página**: Todo funciona con AJAX
- **Filtros Dinámicos**: Cambio instantáneo de datos
- **Hover Effects**: Cards interactivas
- **Loading States**: Indicadores de carga

## 🔧 Filtros de Fecha

### Filtros Rápidos (Un Click)
1. **Hoy**: Solo movimientos del día actual
2. **Ayer**: Movimientos del día anterior
3. **Última Semana**: Últimos 7 días
4. **Últimos 30 Días**: Último mes
5. **Últimos 2 Meses**: 60 días
6. **Últimos 3 Meses**: 90 días

### Rango Personalizado
- Selector de fecha "Desde"
- Selector de fecha "Hasta"
- Botón "Aplicar Rango" para buscar

## 📱 Acceso al Sistema

### URLs
| Función | URL Local | URL Producción |
|---------|-----------|----------------|
| Informes | http://127.0.0.1:8000/caja/informes/ | https://renzzoelectricos.com/caja/informes/ |
| Dashboard Caja | http://127.0.0.1:8000/caja/ | https://renzzoelectricos.com/caja/ |
| Historial | http://127.0.0.1:8000/caja/historial/ | https://renzzoelectricos.com/caja/historial/ |

### Menú de Navegación
```
Dashboard Oscar → Caja → Informes
```

## 🔐 Permisos

El sistema respeta los permisos de usuario:
- ✅ **Superusuarios**: Acceso completo
- ✅ **Staff**: Acceso completo
- ✅ **Con permiso `can_view_caja`**: Puede ver informes
- ❌ **Sin permisos**: No puede acceder

## 📊 Datos de Prueba

Se crearon 4 cajas de ejemplo con `crear_cajas_ejemplo.py`:

### Caja 1 (hace 2 días)
- Inicial: $50,000
- Final: $245,000
- ✅ Cuadre perfecto (diferencia: $0)
- Distribución: $200,000 en caja + $45,000 guardado

### Caja 2 (hace 1 día)
- Inicial: $100,000
- Final: $330,000
- 💰 Sobrante de $5,000
- Distribución: $280,000 en caja + $50,000 guardado

### Caja 3 (hace 5 horas)
- Inicial: $75,000
- Final: $180,000
- ⚠️ Faltante de $7,000
- Distribución: $150,000 en caja + $30,000 guardado

### Caja 4 (actual)
- 🟢 **ABIERTA**
- Inicial: $120,000
- 3 movimientos registrados

## 🛠️ Tecnologías Utilizadas

### Backend
- **Django 5.1.4**: Framework principal
- **Django Oscar**: Sistema de e-commerce y dashboard
- **Python 3.11**: Lenguaje de programación

### Frontend
- **HTML5**: Estructura semántica
- **CSS3**: Estilos modernos con variables CSS
- **JavaScript ES6+**: Lógica interactiva
- **AJAX/Fetch API**: Comunicación asíncrona
- **Bootstrap Icons**: Iconografía

### Base de Datos
- **PostgreSQL**: Consultas con agregaciones (Sum, Count, Avg)
- **Django ORM**: Abstracción de base de datos

## 📁 Estructura de Archivos

```
caja/
├── views.py                          # ✅ 4 nuevas funciones
│   ├── informes_caja()              # Vista principal
│   ├── balance_general_ajax()       # Balance con filtros
│   ├── historial_arqueos_ajax()     # Lista de cajas (paginado)
│   └── flujo_efectivo_ajax()        # Flujo detallado
│
├── urls.py                           # ✅ 4 nuevas rutas
│   ├── /informes/                   # Página principal
│   ├── /informes/balance-general/   # Endpoint balance
│   ├── /informes/historial-arqueos/ # Endpoint historial
│   └── /informes/flujo-efectivo/    # Endpoint flujo
│
├── templates/caja/
│   └── informes.html                # ✅ Template completo
│
└── static/caja/
    ├── css/
    │   └── informes.css             # ✅ Estilos tema verde
    └── js/
        └── informes.js              # ✅ Lógica AJAX

config/
└── settings.py                       # ✅ Submenú agregado
```

## 🚀 Comandos de Despliegue

### Local (Ya funcionando)
```bash
# El servidor ya está corriendo en:
http://127.0.0.1:8000/

# Para ver informes:
http://127.0.0.1:8000/caja/informes/
```

### Producción (Cuando se suba)
```bash
# 1. Conectar al servidor
ssh usuario@renzzoelectricos.com

# 2. Pull de cambios
cd /ruta/del/proyecto
git pull origin main

# 3. Recolectar estáticos
python manage.py collectstatic --noinput

# 4. Reiniciar servicios
docker-compose restart web
# O si usa systemd:
sudo systemctl restart renzzo

# 5. Verificar
# Ir a: https://renzzoelectricos.com/caja/informes/
```

## 📊 Ejemplos de Uso

### Caso 1: Ver Balance de la Semana
1. Ir a **Dashboard → Caja → Informes**
2. Click en **"Última Semana"** (ya seleccionado por defecto)
3. Ver tarjetas con totales
4. Ver gráfico de flujo neto

### Caso 2: Revisar Cajas del Mes Pasado
1. Ir a **Dashboard → Caja → Informes**
2. Click en **"Últimos 30 Días"**
3. Scroll a **"Historial de Arqueos"**
4. Ver tabla con todas las cajas
5. Click en **"Ver"** para detalles

### Caso 3: Analizar un Día Específico
1. Ir a **Dashboard → Caja → Informes**
2. Seleccionar **fecha desde** y **fecha hasta** (el mismo día)
3. Click en **"Aplicar Rango"**
4. Ver estadísticas del día

### Caso 4: Detectar Descuadres
1. Ir a **"Historial de Arqueos"**
2. Buscar filas con diferencia ≠ 0
3. 🟢 Verde = Sobrante
4. 🔴 Rojo = Faltante
5. Click en **"Ver"** para investigar

## 🎯 Ventajas del Sistema

### Para Gerencia
- ✅ Visión completa del negocio
- ✅ Detectar descuadres rápidamente
- ✅ Análisis de periodos personalizados
- ✅ Estadísticas consolidadas
- ✅ Seguimiento de dinero guardado

### Para Cajeros
- ✅ Ver historial de sus cajas
- ✅ Comparar saldo teórico vs real
- ✅ Transparencia en movimientos
- ✅ Fácil navegación

### Para el Negocio
- ✅ Control financiero preciso
- ✅ Trazabilidad completa
- ✅ Reportes exportables (futuro)
- ✅ Auditoría facilitada

## 🔄 Flujo de Trabajo Completo

```
1. Abrir Caja
   ↓
2. Registrar Movimientos (Ingresos/Egresos)
   ↓
3. Cerrar Caja (con conteo)
   ↓
4. Ver en Informes:
   - Balance general actualizado
   - Nueva caja en historial
   - Flujo de efectivo consolidado
```

## 📈 Métricas y KPIs Disponibles

### Operacionales
- Número de cajas cerradas por periodo
- Promedio de diferencias (calidad del conteo)
- Total de movimientos registrados

### Financieras
- Total de dinero en circulación
- Total de dinero guardado (seguridad)
- Flujo neto (rentabilidad)
- Ingresos y egresos por categoría

## 🐛 Solución de Problemas

### "No veo el menú Informes"
- Verificar que estás autenticado
- Verificar permisos de usuario
- Recargar página (Ctrl + F5)

### "Los datos no cargan"
- Abrir consola del navegador (F12)
- Verificar errores en red
- Verificar que hay cajas cerradas

### "Fechas no funcionan"
- Verificar formato de fecha
- Fecha "Desde" debe ser menor que "Hasta"
- Seleccionar ambas fechas antes de aplicar

## ✅ Próximas Mejoras (Opcional)

- [ ] Exportar reportes a PDF
- [ ] Gráficos con Chart.js
- [ ] Comparación entre periodos
- [ ] Alertas de descuadres
- [ ] Dashboard widgets

---

## 🎉 Sistema Completo y Funcional

✅ **Funcionando en Local**: http://127.0.0.1:8000/caja/informes/  
✅ **Listo para Producción**: Hacer git push  
✅ **Diseño Profesional**: Tema verde oscuro moderno  
✅ **100% AJAX**: Sin recargas de página  
✅ **Responsive**: Mobile, tablet y desktop  
✅ **Integrado con Oscar**: Menú nativo del dashboard  

**Credenciales de Prueba**:
- Usuario: `adminhennesy`
- Password: `admin123`

---

**Desarrollado con ❤️ para Renzzo Eléctricos**  
**Villavicencio, Meta - Colombia** 🇨🇴
