"""
Comando para corregir el dinero guardado de las cajas cerradas.
Permite ajustar manualmente los valores incorrectos.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from caja.models import CajaRegistradora


class Command(BaseCommand):
    help = 'Corrige el dinero guardado en cajas cerradas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--caja',
            type=int,
            required=True,
            help='ID de la caja a corregir'
        )
        parser.add_argument(
            '--dinero-guardado',
            type=float,
            required=True,
            help='Nuevo valor del dinero guardado'
        )
        parser.add_argument(
            '--aplicar',
            action='store_true',
            help='Aplicar realmente el cambio'
        )

    def handle(self, *args, **options):
        caja_id = options['caja']
        nuevo_dinero = Decimal(str(options['dinero_guardado']))
        aplicar = options['aplicar']
        
        self.stdout.write(self.style.SUCCESS("🔧 CORRECCIÓN DE DINERO GUARDADO"))
        self.stdout.write("=" * 50)
        
        try:
            caja = CajaRegistradora.objects.get(id=caja_id)
        except CajaRegistradora.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ No existe caja con ID {caja_id}"))
            return
        
        dinero_actual = caja.dinero_en_caja or Decimal('0.00')
        diferencia = nuevo_dinero - dinero_actual
        
        self.stdout.write(f"📦 CAJA {caja.id}:")
        self.stdout.write(f"   Estado: {caja.get_estado_display()}")
        self.stdout.write(f"   Fecha cierre: {caja.fecha_cierre}")
        self.stdout.write(f"   Dinero actual: ${dinero_actual:,.0f}")
        self.stdout.write(f"   Dinero nuevo: ${nuevo_dinero:,.0f}")
        self.stdout.write(f"   Diferencia: {diferencia:+,.0f}")
        
        if not aplicar:
            self.stdout.write(self.style.WARNING("⚠️  MODO SIMULACIÓN - Para aplicar usa --aplicar"))
        else:
            caja.dinero_en_caja = nuevo_dinero
            caja.save()
            
            if diferencia > 0:
                self.stdout.write(self.style.SUCCESS(f"✅ CORREGIDO: +${diferencia:,.0f}"))
            elif diferencia < 0:
                self.stdout.write(self.style.SUCCESS(f"✅ CORREGIDO: ${diferencia:,.0f}"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ Sin cambios necesarios"))
        
        # Mostrar totales después del cambio
        self.stdout.write("\n💰 TOTALES DESPUÉS DEL CAMBIO:")
        
        if aplicar:
            cajas_cerradas = CajaRegistradora.objects.filter(estado='CERRADA')
        else:
            # Simular el cambio
            cajas_cerradas = CajaRegistradora.objects.filter(estado='CERRADA')
            total_simulado = sum(
                (nuevo_dinero if c.id == caja_id else (c.dinero_en_caja or Decimal('0.00')))
                for c in cajas_cerradas
            )
            self.stdout.write(f"   Total dinero guardado (simulado): ${total_simulado:,.0f}")
            return
        
        total_real = sum(
            c.dinero_en_caja or Decimal('0.00') 
            for c in cajas_cerradas
        )
        self.stdout.write(f"   Total dinero guardado: ${total_real:,.0f}")