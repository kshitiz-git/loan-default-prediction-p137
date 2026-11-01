param([string]$Docx, [string]$Pdf)
# docx -> PDF through Word (same route as the reference submission): refresh fields (TOC, PAGE, NUMPAGES), then save as PDF.
$ErrorActionPreference = "Stop"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
  $doc = $word.Documents.Open($Docx, $false, $true)
  $doc.Repaginate()
  foreach ($t in $doc.TablesOfContents) { $t.Update() | Out-Null }
  $doc.Fields.Update() | Out-Null
  foreach ($sec in $doc.Sections) { foreach ($f in $sec.Footers) { $f.Range.Fields.Update() | Out-Null }; foreach ($h in $sec.Headers) { $h.Range.Fields.Update() | Out-Null } }
  $doc.Repaginate()
  foreach ($t in $doc.TablesOfContents) { $t.Update() | Out-Null }
  $pages = $doc.ComputeStatistics(2)
  # ExportAsFixedFormat with CreateBookmarks=1 (headings) so the PDF gets a heading outline like the reference PDFs
  $doc.ExportAsFixedFormat($Pdf, 17, $false, 0, 0, 1, 1, 0, $true, $true, 1, $true, $true, $false)
  Write-Output "PAGES=$pages"
  $doc.Close($false)
} finally {
  $word.Quit()
}
