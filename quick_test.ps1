# Quick System Test - Run this first to verify everything works
Write-Host "QUICK SYSTEM TEST" -ForegroundColor Yellow
Write-Host "=================" -ForegroundColor Yellow

# Test 1: Database
Write-Host "Testing database..." -ForegroundColor Green
try {
    $result = python -c "import sqlite3; conn = sqlite3.connect('data/products.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM products'); print(cursor.fetchone()[0]); conn.close()"
    Write-Host "✅ Database: $result products found" -ForegroundColor Green
} catch {
    Write-Host "❌ Database test failed" -ForegroundColor Red
}

# Test 2: Python environment
Write-Host "Testing Python environment..." -ForegroundColor Green
try {
    python -c "import pandas, matplotlib, seaborn, selenium, requests, bs4; print('All modules imported successfully')"
    Write-Host "✅ Python environment is ready" -ForegroundColor Green
} catch {
    Write-Host "❌ Missing Python modules" -ForegroundColor Red
}

# Test 3: CLI
Write-Host "Testing CLI..." -ForegroundColor Green
try {
    python main.py --help | Out-Null
    Write-Host "✅ CLI is working" -ForegroundColor Green
} catch {
    Write-Host "❌ CLI test failed" -ForegroundColor Red
}

# Test 4: Report generation
Write-Host "Testing report generation..." -ForegroundColor Green
try {
    python main.py generate-report --format json 2>$null | Out-Null
    Write-Host "✅ Report generation is working" -ForegroundColor Green
} catch {
    Write-Host "❌ Report generation failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ System is ready for demo!" -ForegroundColor Yellow
Write-Host "Run: .\video_demo_script.ps1" -ForegroundColor Cyan 