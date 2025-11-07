# ============================================================================
# Script de Construcción Docker para Renzzo Eléctricos (PowerShell)
# ============================================================================

param(
    [string]$ImageName = "renzzoelectricos",
    [string]$Tag = "latest"
)

$ErrorActionPreference = "Stop"

Write-Host "� Construyendo imagen Docker para Renzzo Eléctricos..." -ForegroundColor Cyan
Write-Host ""

try {
    # Limpiar imagen anterior
    Write-Host "🧹 Limpiando imagen anterior..." -ForegroundColor Yellow
    docker rmi "${ImageName}:${Tag}" 2>$null

    # Construir nueva imagen
    Write-Host "🏗️ Construyendo nueva imagen..." -ForegroundColor Yellow
    docker build -t "${ImageName}:${Tag}" .

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Imagen construida exitosamente: ${ImageName}:${Tag}" -ForegroundColor Green
        Write-Host ""
        Write-Host "� Para ejecutar el contenedor:" -ForegroundColor White
        Write-Host "   docker run -p 5018:8000 ${ImageName}:${Tag}" -ForegroundColor Gray
        Write-Host ""
    } else {
        throw "Error en la construcción de la imagen"
    }
} catch {
    Write-Host ""
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    exit 1
}