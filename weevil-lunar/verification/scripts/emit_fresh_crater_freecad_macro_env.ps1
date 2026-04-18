param(
    [string]$ReceiptPath = "cad/generated/fresh_crater_freecad_input_receipt_2026-04-18.json"
)

$root = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
$receiptFull = Join-Path $root $ReceiptPath
if (-not (Test-Path $receiptFull)) {
    throw "Missing receipt: $receiptFull"
}

$receipt = Get-Content -Raw -Encoding UTF8 $receiptFull | ConvertFrom-Json
$baseCsv = $receipt.freecad_spreadsheet_csv
$phase2Csv = $receipt.phase2_alias_csv

Write-Output ("`$env:WEEVIL_BASE_CSV = '{0}'" -f $baseCsv)
Write-Output ("`$env:WEEVIL_PHASE2_CSV = '{0}'" -f $phase2Csv)
Write-Output "Run cad/Phase2_Templates.FCMacro inside FreeCAD after setting those environment variables in the launching shell."
