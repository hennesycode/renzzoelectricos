"""
Comando para generar documentación completa del sistema de caja y tesorería.
Explica cómo funcionan las conexiones entre todos los módulos.
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count
from decimal import Decimal
from caja.models import (
    CajaRegistradora, MovimientoCaja, TipoMovimiento,
    Cuenta, TransaccionGeneral, DenominacionMoneda, ConteoEfectivo
)


class Command(BaseCommand):
    help = 'Genera documentación completa del sistema de caja y tesorería'

    def add_arguments(self, parser):
        parser.add_argument(
            '--formato',
            type=str,
            choices=['consola', 'archivo'],
            default='consola',
            help='Formato de salida (consola o archivo)'
        )

    def handle(self, *args, **options):
        formato = options['formato']
        
        doc = self.generar_documentacion()
        
        if formato == 'archivo':
            with open('documentacion_sistema_caja.md', 'w', encoding='utf-8') as f:
                f.write(doc)
            self.stdout.write(self.style.SUCCESS("📄 Documentación guardada en: documentacion_sistema_caja.md"))
        else:
            self.stdout.write(doc)

    def generar_documentacion(self):
        """Genera la documentación completa del sistema"""
        
        # Obtener estadísticas actuales
        stats = self.obtener_estadisticas()
        
        doc = f"""
# 📊 DOCUMENTACIÓN COMPLETA DEL SISTEMA DE CAJA Y TESORERÍA
## Renzzo Eléctricos - Villavicencio, Meta

---

## 🎯 RESUMEN EJECUTIVO

Este sistema maneja tres tipos de dinero de forma independiente pero conectada:

1. **💵 DINERO EN CAJA**: Efectivo disponible para ventas diarias
2. **🏦 BANCO PRINCIPAL**: Dinero en cuenta bancaria para pagos y transferencias
3. **💰 DINERO GUARDADO**: Efectivo físico guardado fuera de la caja registradora

**Estado actual del sistema:**
- Cajas registradas: {stats['total_cajas']} (abiertas: {stats['cajas_abiertas']}, cerradas: {stats['cajas_cerradas']})
- Transacciones de tesorería: {stats['transacciones_tesoreria']}
- Tipos de movimiento: {stats['tipos_movimiento']}
- Cuentas activas: {stats['cuentas_activas']}

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### MODELOS PRINCIPALES

#### 1. CajaRegistradora
**Propósito**: Representa una sesión de trabajo diaria de caja
```python
# Campos principales:
- cajero: Usuario que maneja la caja
- fecha_apertura/cierre: Horarios de operación
- estado: ABIERTA/CERRADA
- monto_inicial: Dinero base para iniciar ventas
- monto_final_declarado: Dinero contado al cerrar
- monto_final_sistema: Dinero calculado por el sistema
- dinero_en_caja: Dinero que queda en caja al cerrar
- dinero_guardado: Dinero guardado físicamente (DEPRECADO)
```

**Método clave**: `calcular_monto_sistema()`
- Suma: monto_inicial + ingresos_efectivo - egresos
- EXCLUYE: entradas al banco (marcadas con [BANCO])

#### 2. MovimientoCaja
**Propósito**: Registra cada transacción individual en la caja
```python
# Campos principales:
- caja: FK a CajaRegistradora
- tipo: INGRESO/EGRESO
- monto: Cantidad de dinero
- descripcion: Detalle del movimiento
- referencia: Número de factura/recibo
- usuario: Quien registró el movimiento
```

**Tipos especiales**:
- Entradas banco: descripción contiene "[BANCO]"
- Apertura: tipo_movimiento.codigo = "APERTURA"

#### 3. Cuenta
**Propósito**: Representa cuentas financieras del negocio
```python
# Tipos de cuenta:
- BANCO: Cuenta bancaria principal
- RESERVA: Para ajustes de dinero guardado (técnico)

# Campo importante:
- saldo_actual: Solo se usa para BANCO, RESERVA es calculado
```

#### 4. TransaccionGeneral
**Propósito**: Registra movimientos de tesorería (banco y reserva)
```python
# Campos principales:
- tipo: INGRESO/EGRESO/TRANSFERENCIA
- cuenta: De qué cuenta es la transacción
- monto: Cantidad
- tipo_movimiento: Categoría (gasto, compra, etc.)
```

---

## 🔄 FLUJOS OPERATIVOS

### FLUJO 1: OPERACIÓN DIARIA DE CAJA

```
1. APERTURA
   ├─ Se crea CajaRegistradora (estado=ABIERTA)
   ├─ Se registra MovimientoCaja tipo=APERTURA
   └─ Usuario define monto_inicial

2. VENTAS Y MOVIMIENTOS
   ├─ Cada venta → MovimientoCaja (tipo=INGRESO)
   ├─ Cada gasto → MovimientoCaja (tipo=EGRESO)
   └─ Entradas banco → MovimientoCaja (descripción="[BANCO]")

3. CIERRE
   ├─ Usuario cuenta dinero físico
   ├─ Sistema calcula monto_final_sistema
   ├─ Se calcula diferencia = declarado - sistema
   ├─ Usuario decide cuánto dejar en caja (dinero_en_caja)
   └─ Estado cambia a CERRADA
```

### FLUJO 2: GESTIÓN DE TESORERÍA

```
1. REGISTRO DE GASTOS/COMPRAS
   ├─ Origen: CAJA, BANCO, o RESERVA
   ├─ Si es CAJA → MovimientoCaja
   ├─ Si es BANCO/RESERVA → TransaccionGeneral
   └─ Actualización automática de saldos

2. TRANSFERENCIAS
   ├─ Entre cualquier combinación: Caja ↔ Banco ↔ Reserva
   ├─ Origen CAJA: solo TransaccionGeneral en destino
   ├─ Entre cuentas: TransaccionGeneral en ambas
   └─ Validación de fondos disponibles

3. BALANCE/AJUSTES
   ├─ Usuario ingresa saldos reales
   ├─ Sistema calcula diferencias
   ├─ Se crean TransaccionGeneral de ajuste
   └─ Solo BANCO actualiza saldo_actual directamente
```

---

## 📈 CÁLCULOS DE SALDOS

### DINERO EN CAJA
```python
if caja_abierta:
    # Cálculo dinámico para caja abierta
    saldo = caja.monto_inicial + ingresos_efectivo - egresos
    # ingresos_efectivo = ingresos SIN apertura SIN [BANCO]
else:
    # Usar dinero_en_caja de la última caja cerrada
    saldo = ultima_caja_cerrada.dinero_en_caja
```

### BANCO PRINCIPAL
```python
# Método 1: Directo (recomendado)
saldo = cuenta_banco.saldo_actual

# Método 2: Calculado (para validación)
transacciones = TransaccionGeneral.filter(cuenta=cuenta_banco)
saldo = sum(ingresos) - sum(egresos)
```

### DINERO GUARDADO
```python
# Suma de dinero físico de cajas cerradas
total_cajas = sum(caja.dinero_en_caja for caja in cajas_cerradas)

# Más ajustes manuales en cuenta RESERVA
transacciones_reserva = TransaccionGeneral.filter(cuenta=cuenta_reserva)
ajustes = sum(ingresos) - sum(egresos)

saldo_final = total_cajas + ajustes
```

---

## 🔧 COMANDOS DE GESTIÓN

### Validación y Diagnóstico
```bash
# Verificar saldos actuales
python manage.py ver_saldos

# Validación completa con opción de corrección
python manage.py validar_integridad_sistema --fix

# Sincronizar saldos bancarios
python manage.py sincronizar_saldos --cuenta=BANCO
```

### Operaciones Específicas
```bash
# Corregir saldos de cuentas
python manage.py corregir_saldos_cuentas

# Registrar gastos desde línea de comandos
python manage.py registrar_gasto_banco --monto=50000 --descripcion="Pago proveedores"

# Mover dinero de caja a banco
python manage.py mover_egreso_caja_a_banco --caja=5
```

---

## ⚠️ REGLAS IMPORTANTES

### Consistencia de Datos
1. **Dinero en Caja**: Solo se modifica a través de MovimientoCaja
2. **Banco Principal**: saldo_actual debe coincidir con TransaccionGeneral
3. **Dinero Guardado**: NUNCA modificar saldo_actual de cuenta RESERVA
4. **Transferencias**: Siempre validar fondos disponibles antes

### Restricciones del Sistema
1. Solo puede haber 1 CajaRegistradora ABIERTA a la vez
2. Solo puede haber 1 Cuenta activa de cada tipo (BANCO/RESERVA)
3. Los MovimientoCaja de apertura nunca se incluyen en cálculos de efectivo
4. Las entradas [BANCO] no afectan el dinero disponible en caja

### Validaciones Automáticas
1. Fondos suficientes antes de registrar egresos
2. Coherencia entre saldo_actual y transacciones (solo BANCO)
3. Prevención de transferencias a CAJA desde tesorería
4. Validación de cuentas activas antes de operaciones

---

## 🚀 FUNCIONALIDADES AVANZADAS

### Modal de Balance (Tecla B)
- Permite ajustar saldos de BANCO y RESERVA
- Crea transacciones de balance automáticamente
- Solo corrige saldo_actual del BANCO
- RESERVA mantiene cálculo dinámico

### Dashboard en Tiempo Real
- Actualización automática cada 30 segundos
- Cálculos consistentes entre backend y frontend
- Integración con comandos de validación

### APIs REST
- `/api/tesoreria/saldos/`: Obtener saldos actuales
- `/api/tesoreria/registrar-egreso/`: Registrar gastos/compras
- `/api/tesoreria/transferir/`: Transferir entre cuentas
- `/api/tesoreria/balance/`: Aplicar ajustes de balance

---

## 📋 ESTADÍSTICAS ACTUALES

**Cajas Registradoras:**
- Total: {stats['total_cajas']}
- Abiertas: {stats['cajas_abiertas']}
- Cerradas: {stats['cajas_cerradas']}

**Movimientos de Caja:**
- Total: {stats['movimientos_caja']}
- Ingresos: {stats['movimientos_ingresos']}
- Egresos: {stats['movimientos_egresos']}

**Tesorería:**
- Transacciones: {stats['transacciones_tesoreria']}
- Cuentas activas: {stats['cuentas_activas']}
- Tipos de movimiento: {stats['tipos_movimiento']}

---

## 🔍 TROUBLESHOOTING

### Problemas Comunes

1. **"Dinero Guardado aparece en $0"**
   - Verificar que las cajas cerradas tengan dinero_en_caja > 0
   - Ejecutar: `python manage.py validar_integridad_sistema`

2. **"Saldo banco inconsistente"**
   - Ejecutar: `python manage.py sincronizar_saldos --cuenta=BANCO`

3. **"No puedo registrar gasto"**
   - Verificar que exista cuenta activa del tipo seleccionado
   - Confirmar fondos suficientes

4. **"Balance no funciona"**
   - Verificar que existan cuentas BANCO y RESERVA activas
   - Comprobar permisos del usuario

### Herramientas de Diagnóstico
```bash
# Diagnóstico completo
python manage.py validar_integridad_sistema

# Verificación rápida
python manage.py ver_saldos

# Documentación actualizada
python manage.py documentar_sistema --formato=archivo
```

---

*Documentación generada automáticamente el {self.obtener_fecha_actual()}*
*Sistema operativo: Django {self.obtener_version_django()}*
"""
        return doc

    def obtener_estadisticas(self):
        """Obtiene estadísticas actuales del sistema"""
        return {
            'total_cajas': CajaRegistradora.objects.count(),
            'cajas_abiertas': CajaRegistradora.objects.filter(estado='ABIERTA').count(),
            'cajas_cerradas': CajaRegistradora.objects.filter(estado='CERRADA').count(),
            'movimientos_caja': MovimientoCaja.objects.count(),
            'movimientos_ingresos': MovimientoCaja.objects.filter(tipo='INGRESO').count(),
            'movimientos_egresos': MovimientoCaja.objects.filter(tipo='EGRESO').count(),
            'transacciones_tesoreria': TransaccionGeneral.objects.count(),
            'cuentas_activas': Cuenta.objects.filter(activo=True).count(),
            'tipos_movimiento': TipoMovimiento.objects.filter(activo=True).count(),
        }

    def obtener_fecha_actual(self):
        """Obtiene la fecha actual formateada"""
        from django.utils import timezone
        return timezone.now().strftime('%d/%m/%Y %H:%M:%S')

    def obtener_version_django(self):
        """Obtiene la versión de Django"""
        import django
        return django.get_version()