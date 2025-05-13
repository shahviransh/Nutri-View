pipreq:
	@echo "Freezing Python dependencies..."
	@powershell -Command "conda activate venv; pip freeze | ForEach-Object { ($$_ -split '==|@')[0] } | Set-Content backend/requirements.txt; conda deactivate"