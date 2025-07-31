$projectDir = "C:\Nutiri-View"
$backendScript = "$projectDir\backend\apppy.py"
$serviceName = "Nutiri-View-Backend"

Set-Location $projectDir

# Attempt to pull changes
git pull
if ($LASTEXITCODE -ne 0) {
    # If merge conflicts occur, reset the local branch to match the remote branch
    Write-Host "Merge conflict detected. Resetting local branch to match remote..." -ForegroundColor Yellow
    git fetch origin
    git reset --hard origin/main
}

# Install pip packages in conda env
conda run -n venv pip install --no-cache-dir -r backend/requirements.txt

# Stop existing apppy.py process if running on port 5000
$existingProcess = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object OwningProcess
if ($existingProcess) {
    Stop-Process -Id $existingProcess.OwningProcess -Force
}

# Start the Flask backend detached
Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList "-ExecutionPolicy Bypass -NoProfile -NoLogo -Command conda run -n venv python $projectDir\backend\apppy.py" `
    -NoNewWindow `
    -WorkingDirectory "$projectDir\backend"

# Node.js build process
npm install
npm run prestart
npm run build
