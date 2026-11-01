# Rebuilds the whole submission (9 files in submission\final\UPLOAD) from identity.json.
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File submission\build\build_all.ps1
# Needs: the project .venv (pandas) and a Python with python-docx + matplotlib ($DocPy), plus Microsoft Word for PDF export.
param([string]$DocPy = "S:\retailmax-crm\.venv\Scripts\python.exe")
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
$Build = "$Root\submission\build"
$Final = "$Root\submission\final"
$Upload = "$Final\UPLOAD"
Set-Location $Root

function Step($name, [scriptblock]$cmd) {
  Write-Output "== $name"
  & $cmd
  if ($LASTEXITCODE -ne 0) { throw "$name failed (exit $LASTEXITCODE)" }
}

# Old outputs carry the previous identity in their file names, so clear generated files first.
New-Item -ItemType Directory -Force $Upload | Out-Null
Get-ChildItem $Final -Filter *.docx | Remove-Item -Force
Get-ChildItem $Upload -File | Remove-Item -Force

Step "data files"     { & "$Root\.venv\Scripts\python.exe" -m submission.build.build_data_files }
Step "diagrams"       { & $DocPy -I "$Build\make_diagrams.py" }
Step "declaration"    { & $DocPy -I "$Build\build_declaration.py" }
Step "synopsis"       { & $DocPy -I "$Build\fill_synopsis.py" }
Step "EDA notebook"   { & $DocPy -I "$Build\build_eda_doc.py" }
Step "screens+source" { & $DocPy -I "$Build\build_extras.py" all }
Step "SRS"            { & $DocPy -I "$Build\build_srs.py" }
Step "report"         { & $DocPy -I "$Build\build_report_docx.py" }

Copy-Item "$Final\dataset.csv", "$Final\data_dictionary.csv" $Upload
Write-Output "== UPLOAD folder"
Get-ChildItem $Upload | Select-Object Name, Length | Format-Table -AutoSize
