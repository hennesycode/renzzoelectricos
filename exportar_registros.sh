#!/bin/bash
# Script para exportar registros completos de caja y tesorería
# Renzzo Eléctricos - Sistema de Caja

echo "🏪 EXPORTANDO REGISTROS COMPLETOS DE CAJA Y TESORERÍA..."
echo "============================================================"

# Configurar variables
FECHA=$(date +"%Y%m%d_%H%M%S")
ARCHIVO="registros_caja_completos_${FECHA}.txt"

# Ejecutar el comando Django
python manage.py exportar_registros_completos --formato=archivo --archivo="${ARCHIVO}"

echo ""
echo "✅ EXPORTACIÓN COMPLETADA"
echo "📄 Archivo generado: ${ARCHIVO}"
echo ""

# Mostrar información del archivo
if [ -f "${ARCHIVO}" ]; then
    TAMAÑO=$(wc -c < "${ARCHIVO}")
    LINEAS=$(wc -l < "${ARCHIVO}")
    echo "📊 Estadísticas del archivo:"
    echo "   - Tamaño: ${TAMAÑO} bytes"
    echo "   - Líneas: ${LINEAS}"
    echo ""
    
    # Preguntar si quiere ver el contenido
    echo "¿Desea ver el contenido del archivo? (s/n)"
    read -r respuesta
    
    if [[ $respuesta == "s" || $respuesta == "S" ]]; then
        echo ""
        echo "📖 MOSTRANDO CONTENIDO COMPLETO:"
        echo "================================"
        cat "${ARCHIVO}"
    fi
    
    echo ""
    echo "💡 COMANDOS ÚTILES:"
    echo "   - Ver archivo: cat ${ARCHIVO}"
    echo "   - Ver por páginas: less ${ARCHIVO}"
    echo "   - Buscar texto: grep 'texto' ${ARCHIVO}"
    echo "   - Copiar archivo: cp ${ARCHIVO} /ruta/destino/"
else
    echo "❌ Error: No se pudo generar el archivo"
fi

echo ""
echo "🔚 PROCESO COMPLETADO"