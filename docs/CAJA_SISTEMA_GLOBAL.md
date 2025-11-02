# Sistema de Caja Registradora - Caja Única Global

## Resumen de Cambios

El sistema de caja ha sido actualizado para funcionar con **UNA ÚNICA CAJA GLOBAL** compartida por todos los usuarios autorizados del sistema.

## Características Principales

### 1. Caja Única Global
- ✅ Solo puede existir **UNA caja abierta** en todo el sistema a la vez
- ✅ **Todos los usuarios** con permisos `users.can_view_caja` ven la misma caja
- ✅ Cualquier usuario con permisos `users.can_manage_caja` puede:
  - Abrir la caja del sistema
  - Cerrar la caja del sistema
  - Registrar movimientos en la caja abierta

### 2. Conteo de Denominaciones
- ✅ **Apertura**: Se guarda un `ConteoEfectivo` tipo APERTURA con todas las denominaciones
- ✅ **Cierre**: Se guarda un `ConteoEfectivo` tipo CIERRE con todas las denominaciones
- ✅ Denominaciones activas:
  - **Billetes**: $100,000 | $50,000 | $20,000 | $10,000 | $5,000 | $2,000 | $1,000
  - **Monedas**: $1,000 | $500 | $200 | $100 | $50

### 3. Flujo de Trabajo

#### Abrir Caja (Modal AJAX)
1. Usuario autorizado hace clic en "Abrir Caja"
2. Modal muestra denominaciones (billetes y monedas)
3. Usuario ingresa cantidades
4. Sistema calcula total en tiempo real
5. Al confirmar:
   - Crea `CajaRegistradora` con estado ABIERTA
   - Guarda `ConteoEfectivo` tipo APERTURA
   - Guarda detalles por denominación en `DetalleConteo`

#### Registrar Movimientos (Modal AJAX)
1. Mientras la caja está abierta, cualquier usuario puede registrar movimientos
2. Modal permite seleccionar:
   - Tipo (Ingreso/Egreso)
   - Tipo de movimiento (Venta, Gasto, etc.)
   - Monto
   - Descripción
   - Referencia
3. El movimiento queda registrado con el usuario que lo creó

#### Cerrar Caja (Modal AJAX)
1. Usuario autorizado hace clic en "Cerrar Caja"
2. Modal muestra:
   - Monto esperado según sistema
   - Denominaciones para contar efectivo actual
3. Usuario ingresa cantidades contadas
4. Sistema calcula total y diferencia
5. Al confirmar:
   - Guarda `ConteoEfectivo` tipo CIERRE
   - Actualiza caja: estado CERRADA, montos, diferencia
   - Muestra diferencia (sobrante/faltante)

### 4. Cambios en el Modelo de Datos

#### ConteoEfectivo
```python
# ANTES (OneToOne - solo un conteo por caja)
caja = models.OneToOneField(...)

# AHORA (ForeignKey - múltiples conteos por caja)
caja = models.ForeignKey(..., related_name='conteos')
tipo_conteo = models.CharField(...)  # APERTURA o CIERRE
usuario = models.ForeignKey(...)     # Quién hizo el conteo
total = models.DecimalField(...)     # Total contado
```

#### CajaRegistradora
- El campo `cajero` indica quién **abrió** la caja
- Pero la caja es **global** y todos los usuarios autorizados pueden trabajar en ella

### 5. Dashboard

El dashboard muestra:
- **Si hay caja abierta**:
  - Quién la abrió
  - Cuándo se abrió
  - Monto inicial
  - Tiempo transcurrido
- **Estadísticas del día** (global, todos los usuarios):
  - Total ingresos
  - Total egresos
  - Número de movimientos
- **Últimos movimientos** con nombre del usuario que los creó

### 6. Historial

El historial muestra **TODAS las cajas del sistema** (no filtradas por usuario), incluyendo:
- Fecha apertura y cierre
- Usuario que abrió
- Montos iniciales y finales
- Diferencias

## Permisos Necesarios

### Ver Caja (`users.can_view_caja`)
- Ver dashboard
- Ver historial
- Ver detalles de cajas

### Gestionar Caja (`users.can_manage_caja`)
- Abrir caja
- Cerrar caja
- Registrar movimientos

## Migraciones Aplicadas

1. **0001_initial.py**: Modelos iniciales
2. **0002_cambio_conteo_a_fk_y_tipo.py**: 
   - Cambio de OneToOne a ForeignKey en ConteoEfectivo
   - Agregado campo `tipo_conteo`
   - Agregado campo `usuario`
   - Renombrado `total_contado` a `total`

## Comandos Útiles

```bash
# Seed de datos iniciales (tipos de movimiento y denominaciones)
python manage.py setup_caja

# Activar billete de $1,000 (si no está activo)
python manage.py shell -c "from caja.models import DenominacionMoneda; DenominacionMoneda.objects.filter(valor=1000, tipo='BILLETE').update(activo=True)"
```

## Próximos Pasos

- [ ] Agregar constraint en base de datos para asegurar solo una caja abierta
- [ ] Implementar bloqueo optimista para evitar condiciones de carrera
- [ ] Agregar tests unitarios y de integración
- [ ] Mejorar UX de los modales (máscaras de entrada, mejor responsive)
- [ ] Agregar reportes y análisis de caja

## Notas Técnicas

- Todos los endpoints AJAX incluyen fallback a formularios tradicionales
- Los modales usan SweetAlert2 para mejor UX
- Las denominaciones se cargan dinámicamente desde el servidor
- El total se calcula en tiempo real en el cliente
- Los conteos se persisten automáticamente al abrir/cerrar
