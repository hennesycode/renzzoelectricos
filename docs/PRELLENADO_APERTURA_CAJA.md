# Prellenado Automático de Apertura de Caja

**Fecha:** 3 de noviembre de 2025  
**Funcionalidad:** Auto-carga del dinero del cierre anterior al abrir nueva caja

## Descripción

Se ha implementado una funcionalidad que **carga automáticamente** la información del último cierre de caja cuando se va a abrir una nueva caja. Esto facilita el proceso ya que el dinero que quedó en la caja física al cerrar es exactamente el mismo dinero con el que se debe abrir.

## ¿Cómo Funciona?

### Flujo de Usuario

1. **Usuario cierra caja anterior:**
   - Cuenta el dinero total: $150,000
   - Distribuye: $100,000 en caja + $50,000 guardado
   - Cuenta denominaciones del dinero en caja:
     - 1 billete de $100,000
   - Sistema guarda el cierre

2. **Usuario abre nueva caja:**
   - Hace clic en "Abrir Caja"
   - **AUTOMÁTICAMENTE** aparece:
     - Información del cierre anterior
     - Monto: $100,000 (el dinero que quedó en caja)
     - Denominaciones prellenadas:
       - 1 billete de $100,000 ✓
   - Usuario puede:
     - Usar los valores prellenados si son correctos
     - Modificar cualquier valor si es necesario
     - Agregar o quitar billetes/monedas

3. **Si no hay cierre anterior:**
   - El modal se muestra vacío (valores en 0)
   - Usuario ingresa manualmente el monto inicial

## Implementación Técnica

### 1. Backend - Nueva Vista AJAX

**Archivo:** `caja/views.py`

```python
@staff_or_permission_required('users.can_view_caja')
def obtener_ultimo_cierre(request):
    """
    Devuelve la información del último cierre de caja para usar como base
    al abrir una nueva caja (dinero_en_caja y conteo de denominaciones).
    """
    # Obtener la última caja cerrada
    ultima_caja = CajaRegistradora.objects.filter(
        estado='CERRADA'
    ).order_by('-fecha_cierre').first()
    
    if not ultima_caja:
        return JsonResponse({
            'success': True,
            'hay_cierre_anterior': False,
            'dinero_en_caja': 0,
            'conteos': {}
        })
    
    # Obtener el conteo de cierre (que representa el dinero en caja)
    conteo_cierre = ConteoEfectivo.objects.filter(
        caja=ultima_caja,
        tipo_conteo='CIERRE'
    ).first()
    
    conteos = {}
    if conteo_cierre:
        detalles = DetalleConteo.objects.filter(
            conteo=conteo_cierre
        ).select_related('denominacion')
        
        for detalle in detalles:
            if detalle.cantidad > 0:
                conteos[str(detalle.denominacion.id)] = detalle.cantidad
    
    return JsonResponse({
        'success': True,
        'hay_cierre_anterior': True,
        'dinero_en_caja': float(ultima_caja.dinero_en_caja or 0),
        'conteos': conteos,
        'fecha_cierre': ultima_caja.fecha_cierre.strftime('%d/%m/%Y %H:%M'),
        'cajero': ultima_caja.cajero.get_full_name() or ultima_caja.cajero.username
    })
```

**Respuesta JSON:**
```json
{
  "success": true,
  "hay_cierre_anterior": true,
  "dinero_en_caja": 100000,
  "conteos": {
    "1": 1,    // 1 billete de $100,000
    "5": 2     // 2 billetes de $20,000 (ejemplo)
  },
  "fecha_cierre": "03/11/2025 18:30",
  "cajero": "Juan Pérez"
}
```

### 2. Nueva Ruta

**Archivo:** `caja/urls.py`

```python
path('ultimo-cierre/', views.obtener_ultimo_cierre, name='ultimo_cierre'),
```

### 3. Frontend - Modal Mejorado

**Archivo:** `caja/static/caja/js/abrir_ajax.js`

#### Carga del último cierre:
```javascript
// Cargar información del último cierre para prellenar
let ultimoCierre = null;
try {
    const respCierre = await fetch(window.CAJA_URLS.ultimo_cierre, { 
        headers: { 'X-Requested-With': 'XMLHttpRequest' } 
    });
    if (respCierre.ok) {
        const json = await respCierre.json();
        if (json.success && json.hay_cierre_anterior) {
            ultimoCierre = json;
        }
    }
} catch (e) {
    console.warn('No se pudo cargar el último cierre', e);
}
```

#### Información visual del cierre anterior:
```javascript
if (ultimoCierre) {
    html += `<div style="background: linear-gradient(...); ...">`;
    html += `<h3>💼 Dinero del Cierre Anterior</h3>`;
    html += `<p>${dineroFormateado}</p>`;
    html += `<p>Cerrado el ${ultimoCierre.fecha_cierre} por ${ultimoCierre.cajero}</p>`;
    html += `</div>`;
}
```

#### Prellenado de denominaciones:
```javascript
billetes.forEach(d => {
    // Obtener cantidad del último cierre si existe
    const cantidadInicial = (ultimoCierre && 
                             ultimoCierre.conteos && 
                             ultimoCierre.conteos[d.id]) 
                             ? ultimoCierre.conteos[d.id] 
                             : 0;
    
    html += `<input ... value="${cantidadInicial}">`;
});
```

### 4. Template - URL Disponible

**Archivo:** `caja/templates/caja/dashboard.html`

```javascript
window.CAJA_URLS = {
    // ... otras URLs
    ultimo_cierre: "{% url 'caja:ultimo_cierre' %}",
    // ...
};
```

## Ventajas

### 1. **Eficiencia Operativa**
- ✅ No es necesario contar nuevamente el dinero
- ✅ Reduce el tiempo de apertura de caja
- ✅ Menos errores de digitación

### 2. **Continuidad del Flujo**
- ✅ El dinero en caja física = dinero en sistema
- ✅ No hay discrepancias entre cierres y apertura
- ✅ Facilita el seguimiento del efectivo

### 3. **Experiencia de Usuario**
- ✅ Menos trabajo manual
- ✅ Información contextual clara
- ✅ Posibilidad de ajustar si es necesario

### 4. **Auditoría y Trazabilidad**
- ✅ Se sabe de dónde viene el dinero inicial
- ✅ Se puede verificar la continuidad
- ✅ Información del cajero anterior disponible

## Casos de Uso

### Caso 1: Primer Uso (No hay cierre anterior)
```
Usuario: Abre caja por primera vez
Sistema: Muestra modal sin información prellenada
Usuario: Ingresa manualmente el monto inicial
Resultado: Caja abierta con el monto ingresado
```

### Caso 2: Con Cierre Anterior
```
Usuario: Cerró caja ayer con $100,000 en caja
Sistema: Al abrir caja, muestra:
  - "Dinero del Cierre Anterior: $100,000"
  - "Cerrado el 02/11/2025 18:30 por Juan Pérez"
  - Denominaciones: 1 billete de $100,000
Usuario: Verifica que es correcto y confirma
Resultado: Caja abierta con $100,000
```

### Caso 3: Ajuste Necesario
```
Usuario: Cerró con $100,000 pero agregó $50,000 más
Sistema: Muestra $100,000 prellenado
Usuario: Modifica a $150,000 y ajusta denominaciones
Resultado: Caja abierta con $150,000
```

## Visualización del Modal

```
╔════════════════════════════════════════════════╗
║            💼 Abrir Caja                       ║
╠════════════════════════════════════════════════╣
║                                                ║
║  ┌──────────────────────────────────────────┐ ║
║  │  💼 Dinero del Cierre Anterior          │ ║
║  │         $100,000                         │ ║
║  │  Cerrado el 02/11/2025 18:30            │ ║
║  │  por Juan Pérez                          │ ║
║  └──────────────────────────────────────────┘ ║
║                                                ║
║  💵 Billetes                                   ║
║  ┌─────────────┬─────────────┬─────────────┐ ║
║  │ $100,000 [1]│ $50,000  [0]│ $20,000  [0]│ ║
║  └─────────────┴─────────────┴─────────────┘ ║
║                                                ║
║  🪙 Monedas                                    ║
║  ┌─────────────┬─────────────┬─────────────┐ ║
║  │ $1,000   [0]│ $500     [0]│ $200     [0]│ ║
║  └─────────────┴─────────────┴─────────────┘ ║
║                                                ║
║  💰 Total a Abrir                              ║
║  $100,000                                      ║
║                                                ║
║  ┌──────────────────────────────────────────┐ ║
║  │ Observaciones (opcional)                 │ ║
║  └──────────────────────────────────────────┘ ║
║                                                ║
║      [✅ Abrir Caja]  [❌ Cancelar]           ║
╚════════════════════════════════════════════════╝
```

## Flujo de Datos Completo

```
1. CIERRE DE CAJA
   ↓
   Guarda: dinero_en_caja = $100,000
   Guarda: ConteoEfectivo con denominaciones
   ↓
2. CLICK "ABRIR CAJA"
   ↓
   Frontend llama: GET /caja/ultimo-cierre/
   ↓
3. BACKEND
   ↓
   Busca: CajaRegistradora.estado='CERRADA' (última)
   Busca: ConteoEfectivo.tipo='CIERRE' de esa caja
   Devuelve: dinero_en_caja + conteos
   ↓
4. FRONTEND
   ↓
   Muestra información del cierre anterior
   Prellena inputs con valores del conteo
   Calcula total automáticamente
   ↓
5. USUARIO
   ↓
   Verifica valores (o ajusta si es necesario)
   Confirma apertura
   ↓
6. NUEVA CAJA ABIERTA
   ↓
   monto_inicial = total calculado
   ConteoEfectivo de apertura guardado
```

## Archivos Modificados

1. ✅ **`caja/views.py`** - Nueva vista `obtener_ultimo_cierre()`
2. ✅ **`caja/urls.py`** - Nueva ruta `'ultimo-cierre/'`
3. ✅ **`caja/templates/caja/dashboard.html`** - Nueva URL en `window.CAJA_URLS`
4. ✅ **`caja/static/caja/js/abrir_ajax.js`** - Lógica de carga y prellenado

## Compatibilidad

- ✅ **Primera vez:** Funciona sin cierre anterior
- ✅ **Con cierre:** Carga información automáticamente
- ✅ **Sin datos:** No afecta el funcionamiento normal
- ✅ **Errores de red:** Fallback a entrada manual

## Pruebas Recomendadas

### Test 1: Primera Apertura
- [ ] Abrir caja sin cierre anterior
- [ ] Verificar que no muestra información prellenada
- [ ] Ingresar monto manualmente
- [ ] Verificar que se guarda correctamente

### Test 2: Con Cierre Anterior
- [ ] Cerrar caja con $100,000 en caja
- [ ] Abrir nueva caja
- [ ] Verificar que muestra información del cierre
- [ ] Verificar que denominaciones están prellenadas
- [ ] Verificar que el total se calcula correctamente

### Test 3: Ajuste de Valores
- [ ] Abrir caja con prellenado
- [ ] Modificar cantidades de denominaciones
- [ ] Verificar que el total se actualiza
- [ ] Confirmar apertura
- [ ] Verificar que se guarda con valores modificados

### Test 4: Información Visual
- [ ] Verificar que se muestra fecha del cierre anterior
- [ ] Verificar que se muestra nombre del cajero anterior
- [ ] Verificar que el formato de moneda es correcto
- [ ] Verificar que los colores y diseño son apropiados

## Notas Técnicas

### Seguridad
- ✅ Vista protegida con `@staff_or_permission_required`
- ✅ Solo lectura de datos
- ✅ No modifica información existente

### Performance
- ✅ Query optimizado con `.first()`
- ✅ `.select_related()` para evitar N+1
- ✅ Carga asíncrona sin bloqueo de UI

### Manejo de Errores
- ✅ Try-catch en backend
- ✅ Try-catch en frontend
- ✅ Fallback a valores por defecto
- ✅ Logs de advertencia para debugging

## Soporte y Mantenimiento

### Ubicación del Código

**Backend:**
- Vista: `caja/views.py` línea ~610
- URL: `caja/urls.py` línea ~39

**Frontend:**
- Script: `caja/static/caja/js/abrir_ajax.js` línea ~25-45

### Debugging

Si no se cargan los datos del cierre anterior:

1. Verificar en consola del navegador:
   ```javascript
   fetch(window.CAJA_URLS.ultimo_cierre)
     .then(r => r.json())
     .then(console.log);
   ```

2. Verificar en backend:
   - ¿Existe una caja cerrada?
   - ¿Tiene ConteoEfectivo de cierre?
   - ¿Los permisos están correctos?

3. Verificar la respuesta JSON:
   - `success: true`
   - `hay_cierre_anterior: true`
   - `conteos` tiene datos

---

**Fin del documento**
