from django.core.management.base import BaseCommand
from django.db import connection, transaction
from decimal import Decimal
from caja.models import Cuenta

class Command(BaseCommand):
    help = 'Aplica el saldo correcto del banco'

    def handle(self, *args, **options):
        self.stdout.write("🔧 APLICANDO SALDO CORRECTO")
        self.stdout.write("=" * 40)
        
        saldo_correcto = Decimal('1340865.00')
        
        try:
            with transaction.atomic():
                # SQL directo
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE caja_cuenta SET saldo_actual = %s WHERE tipo = 'BANCO' AND activo = 1",
                        [saldo_correcto]
                    )
                    rows = cursor.rowcount
                
                # Verificar
                cuenta = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
                cuenta.refresh_from_db()
                
                self.stdout.write(f"✅ SALDO APLICADO: ${cuenta.saldo_actual:,.2f}")
                self.stdout.write(f"📊 Filas actualizadas: {rows}")
                
                if cuenta.saldo_actual == saldo_correcto:
                    self.stdout.write(f"🎉 CORRECTO")
                else:
                    self.stdout.write(f"❌ ERROR")
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))