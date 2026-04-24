# Deploy FastAPI app to Databricks Apps (requires Databricks CLI auth).
# Usage:
#   cd nyaya-sahayak/databricks/app
#   databricks sync . "/Workspace/Users/<you>/nyaya-sahayak-app"
#   # then click Deploy in Apps UI, or use Apps API.

Write-Host "1) Configure CLI: databricks auth login --host https://<workspace-host>"
Write-Host "2) Sync app folder to workspace path shown in Databricks Apps > Deploy"
Write-Host "3) Set env vars / secrets: DATABRICKS_TOKEN is injected in Apps; add SARVAM_API_KEY via secret scope."
