# Makefile for Tauri and Electron builds

.PHONY: all prestart build run python clean

# Default target
all: prestart python

# Prestart script
prestart:
	@echo "Running prestart script..."
	npm run prestart
	@echo "Installing dependencies..."
	npm install

pipreq:
	@echo "Freezing Python dependencies..."
	@powershell -Command "conda activate venv; pip freeze | ForEach-Object { ($$_ -split '==|@')[0] } | Set-Content backend/requirements.txt; conda deactivate"

python:
	@echo "Building Python backend..."
	@call pyinstaller backend/apppy.py -y --distpath backend/ --specpath backend/ --workpath backend/build --name apppy \
	--add-data "$(USERPROFILE)/miniconda3/envs/venv/Library/share/proj;Library/share/proj" \
	--hidden-import=pyogrio._geometry --hidden-import=pyogrio._io --collect-data=numpy

# Build Electron or Tauri based on argument
build:
ifeq ($(ARG), tauri)
	@echo "Building Tauri app..."
	del /F /Q "$(USERPROFILE)\OneDrive - McMaster University\Co-op 2nd Work Term - CWA\CWA-Viewer\release\CWA-Viewer_*.msi"
	del /F /Q "$(USERPROFILE)\OneDrive - McMaster University\Co-op 2nd Work Term - CWA\CWA-Viewer\release\CWA-Viewer_*.exe"
	if exist "src-tauri\target\release\CWA-Viewer_*.exe" del /F /Q "src-tauri\target\release\CWA-Viewer_*.exe"
	if exist "src-tauri\target\release\CWA-Viewer_*.msi" del /F /Q "src-tauri\target\release\CWA-Viewer_*.msi"
	npm run tauri:build
	xcopy "src-tauri\target\release\CWA-Viewer_*.exe" "$(USERPROFILE)\OneDrive - McMaster University\Co-op 2nd Work Term - CWA\CWA-Viewer\release" /Y /I /D
	xcopy "src-tauri\target\release\CWA-Viewer_*.msi" "$(USERPROFILE)\OneDrive - McMaster University\Co-op 2nd Work Term - CWA\CWA-Viewer\release" /Y /I /D
else ifeq ($(ARG), electron)
	@echo "Building Electron app..."
	npm run electron:build
	xcopy dist "$(USERPROFILE)\OneDrive - McMaster University\Co-op 2nd Work Term - CWA\CWA-Viewer\dist" /Y /E /I /D
else
	@echo "Please specify a valid BUILD option (tauri or electron)."
	@exit 1
endif

# Run Electron or Tauri in development mode
run:
ifeq ($(ARG), tauri)
	@echo "Running Tauri app in development mode..."
	npm run tauri dev
else ifeq ($(ARG), electron)
	@echo "Running Electron app in development mode..."
	npm run electron
else
	@echo "Please specify a valid RUN option (tauri or electron)."
	@exit 1
endif

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf dist/ node_modules/ src-tauri/target/ backend/apppy/ backend/build/