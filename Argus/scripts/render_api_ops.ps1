param(
    [string]$ServiceName = "argus-backend",
    [string]$BackendUrl = "https://argus-backend-hu5g.onrender.com",
    [switch]$Deploy
)

$ErrorActionPreference = "Stop"

if (-not $env:RENDER_API_KEY) {
    throw "RENDER_API_KEY is not set. Set it only for this shell: `$env:RENDER_API_KEY='your_render_api_key'"
}

$headers = @{
    Authorization = "Bearer $env:RENDER_API_KEY"
    Accept = "application/json"
}

function Invoke-RenderApi {
    param(
        [string]$Path,
        [string]$Method = "GET",
        [object]$Body = $null
    )

    $uri = "https://api.render.com/v1$Path"
    if ($Body -ne $null) {
        return Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers -ContentType "application/json" -Body ($Body | ConvertTo-Json -Depth 10)
    }
    return Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers
}

function As-Array {
    param([object]$Value, [string[]]$CandidateProperties)

    if ($null -eq $Value) {
        return @()
    }
    foreach ($property in $CandidateProperties) {
        if ($Value.PSObject.Properties.Name -contains $property) {
            return @($Value.$property)
        }
    }
    return @($Value)
}

Write-Host "Listing Render services..."
$services = Invoke-RenderApi -Path "/services?limit=100"
$serviceItems = As-Array -Value $services -CandidateProperties @("services")
$service = @($serviceItems | Where-Object { $_.service.name -eq $ServiceName -or $_.name -eq $ServiceName } | Select-Object -First 1)[0]
if (-not $service) {
    throw "Could not find Render service named '$ServiceName'."
}

$serviceId = if ($service.service.id) { $service.service.id } else { $service.id }
$serviceName = if ($service.service.name) { $service.service.name } else { $service.name }
Write-Host "Service: $serviceName ($serviceId)"

Write-Host "`nEnvironment variables:"
try {
    $envVars = Invoke-RenderApi -Path "/services/$serviceId/env-vars"
    $envItems = As-Array -Value $envVars -CandidateProperties @("envVars", "env_vars")
    $envItems | ForEach-Object {
        $key = if ($_.envVar.key) { $_.envVar.key } else { $_.key }
        $value = if ($key -match "SECRET|KEY|TOKEN|PASSWORD|DATABASE_URL") { "[redacted]" } else { if ($_.envVar.value) { $_.envVar.value } else { $_.value } }
        Write-Host "- $key=$value"
    }
} catch {
    Write-Host "Env var inspection failed: $($_.Exception.Message)"
}

Write-Host "`nRecent deploys:"
$deploys = Invoke-RenderApi -Path "/services/$serviceId/deploys?limit=5"
$deployItems = As-Array -Value $deploys -CandidateProperties @("deploys")
$deployItems | ForEach-Object {
    $deployRecord = if ($_.deploy) { $_.deploy } else { $_ }
    $commit = if ($deployRecord.commit.id) { $deployRecord.commit.id } elseif ($deployRecord.commit) { $deployRecord.commit } else { "unknown" }
    Write-Host "- $($deployRecord.id) status=$($deployRecord.status) commit=$commit created=$($deployRecord.createdAt)"
}

if ($Deploy) {
    Write-Host "`nTriggering deploy for latest commit..."
    $created = Invoke-RenderApi -Path "/services/$serviceId/deploys" -Method "POST" -Body @{}
    $newDeploy = if ($created.deploy) { $created.deploy } else { $created }
    Write-Host "Deploy: $($newDeploy.id) status=$($newDeploy.status)"

    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 5
        $current = Invoke-RenderApi -Path "/services/$serviceId/deploys/$($newDeploy.id)"
        $currentDeploy = if ($current.deploy) { $current.deploy } else { $current }
        Write-Host "Deploy status: $($currentDeploy.status)"
        if ($currentDeploy.status -in @("live", "deployed", "succeeded", "failed", "canceled", "cancelled")) {
            break
        }
    }
}

Write-Host "`nHealth check:"
$elapsed = Measure-Command {
    $health = Invoke-RestMethod -Uri "$BackendUrl/api/health" -TimeoutSec 10
}
$health | ConvertTo-Json -Compress | Write-Host
Write-Host "Health response time: $([math]::Round($elapsed.TotalMilliseconds, 2)) ms"
