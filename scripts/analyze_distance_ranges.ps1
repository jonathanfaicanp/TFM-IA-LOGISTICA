<#!
Genera estadisticas agregadas de L/100 km por vehiculo y tramo de distancia.
Lee el CSV original sin modificarlo y no escribe registros de trayecto.
#>
param(
    [string]$InputPath = "data/datos_operativa.csv",
    [string]$OutputPath = "data/analisis_distancia_2024_2025.md"
)

function Convert-Number([string]$Value) {
    $text = $Value.Trim().Replace([char]0xA0, "")
    if ($text.Contains(",") -and $text.Contains(".")) { $text = $text.Replace(".", "").Replace(",", ".") }
    elseif ($text.Contains(",")) { $text = $text.Replace(",", ".") }
    return [double]::Parse($text, [Globalization.CultureInfo]::InvariantCulture)
}

function Get-Quantile($Sorted, [double]$Probability) {
    $sorted = @($Sorted)
    $count = $sorted.Count
    if ($count -eq 0) { return $null }
    if ($count -eq 1) { return [double]$sorted[0] }
    $position = ($count - 1) * $Probability
    $lower = [math]::Floor($position)
    $upper = [math]::Ceiling($position)
    return [double]$sorted[$lower] + ($position - $lower) * ([double]$sorted[$upper] - [double]$sorted[$lower])
}

function Get-RangeLabel([double]$DistanceKm) {
    if ($DistanceKm -le 1) { return "<= 1" }
    if ($DistanceKm -le 2) { return "> 1 y <= 2" }
    if ($DistanceKm -le 5) { return "> 2 y <= 5" }
    if ($DistanceKm -le 10) { return "> 5 y <= 10" }
    if ($DistanceKm -le 20) { return "> 10 y <= 20" }
    if ($DistanceKm -le 50) { return "> 20 y <= 50" }
    if ($DistanceKm -le 100) { return "> 50 y <= 100" }
    if ($DistanceKm -le 300) { return "> 100 y <= 300" }
    return "> 300"
}

function Format-Number($Value) { return ([double]$Value).ToString("0.###", [Globalization.CultureInfo]::InvariantCulture) }

$ranges = @("<= 1", "> 1 y <= 2", "> 2 y <= 5", "> 5 y <= 10", "> 10 y <= 20", "> 20 y <= 50", "> 50 y <= 100", "> 100 y <= 300", "> 300")
$rows = Import-Csv -LiteralPath $InputPath -Delimiter ";"

$valid = foreach ($row in $rows) {
    try {
        $date = [datetime]::ParseExact($row.'Fecha de inicio'.Substring(0, 10), 'yyyy-MM-dd', $null)
        $distanciaKm = (Convert-Number $row.Distancia) / 1000
        $consumoLitros = (Convert-Number $row.Consumo) / 1000
        if (($date.Year -in 2024, 2025) -and $distanciaKm -gt 0 -and $consumoLitros -gt 0) {
            [pscustomobject]@{
                Vehiculo = $row.'Codigo Vehiculo'
                Rango = Get-RangeLabel $distanciaKm
                L100 = 100 * $consumoLitros / $distanciaKm
            }
        }
    } catch { }
}

$vehicleCounts = @($valid | Group-Object Vehiculo)
$eligible = @($vehicleCounts | Where-Object Count -ge 100 | ForEach-Object Name)
$analysis = @($valid | Where-Object { $_.Vehiculo -in $eligible })
$groupStats = @{}
foreach ($group in ($analysis | Group-Object Vehiculo, Rango)) {
    $values = @($group.Group.L100 | Sort-Object)
    $groupStats[$group.Name] = [pscustomobject]@{
        Count = $values.Count; Median = Get-Quantile $values 0.5; P75 = Get-Quantile $values 0.75
        P90 = Get-Quantile $values 0.9; P95 = Get-Quantile $values 0.95
    }
}

$lines = @(
    "# L/100 km por rango de distancia (2024-2025)", "",
    "El CSV original solo se ha leido. Este informe contiene exclusivamente resultados agregados.", "",
    "Criterio: ano 2024 o 2025, Consumo > 0 y Distancia > 0; distancia_km = Distancia / 1000, consumo_litros = Consumo / 1000 y consumo_l_100km = consumo_litros / distancia_km * 100.", "",
    "- Registros validos de vehiculos incluidos: $($analysis.Count)",
    "- Vehiculos incluidos (>= 100 registros validos): $($eligible.Count)", "",
    "## Resumen por vehiculo", "",
    "| Codigo Vehiculo | Registros validos | Mediana global L/100km |", "| --- | ---: | ---: |"
)
foreach ($vehicle in ($eligible | Sort-Object {[int]$_})) {
    $values = @($analysis | Where-Object Vehiculo -eq $vehicle | ForEach-Object L100 | Sort-Object)
    $lines += "| $vehicle | $($values.Count) | $(Format-Number (Get-Quantile $values 0.5)) |"
}

$lines += "", "## Estadisticas por vehiculo y rango", "", "| Codigo Vehiculo | Rango distancia (km) | Registros | Mediana L/100km | P75 | P90 | P95 |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"
foreach ($vehicle in ($eligible | Sort-Object {[int]$_})) {
    foreach ($range in $ranges) {
        $stat = $groupStats["$vehicle, $range"]
        if ($null -ne $stat) {
            $lines += "| $vehicle | $range | $($stat.Count) | $(Format-Number $stat.Median) | $(Format-Number $stat.P75) | $(Format-Number $stat.P90) | $(Format-Number $stat.P95) |"
        } else {
            $lines += "| $vehicle | $range | 0 | - | - | - | - |"
        }
    }
}

$lines += "", "## Cobertura agregada por rango", "", "| Rango distancia (km) | Registros |", "| --- | ---: |"
foreach ($range in $ranges) { $lines += "| $range | $(@($analysis | Where-Object Rango -eq $range).Count) |" }

$parent = Split-Path -Parent $OutputPath
if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
[IO.File]::WriteAllLines($OutputPath, $lines, [Text.UTF8Encoding]::new($false))
