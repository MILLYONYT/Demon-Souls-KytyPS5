param(
    [ValidateSet('Recorded','Full')][string]$Mode = 'Recorded',
    [string]$Game = '',
    [switch]$CheckOnly,
    [switch]$NoPause
)
$ErrorActionPreference = 'Stop'
$result = 0
try {
    if (!$Game -and (Test-Path "$PSScriptRoot/game-path.txt")) {
        $Game = (Get-Content "$PSScriptRoot/game-path.txt" -Raw).Trim()
    }
    if (!$Game -and !$CheckOnly) {
        Add-Type -AssemblyName System.Windows.Forms
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = 'Choose your game folder containing eboot.bin and sce_sys'
        try { if ($dialog.ShowDialog() -eq 'OK') { $Game = $dialog.SelectedPath } }
        finally { $dialog.Dispose() }
    }
    if (!(Test-Path "$Game/eboot.bin") -or !(Test-Path "$Game/sce_sys/param.json")) {
        throw 'Choose a game folder containing eboot.bin and sce_sys/param.json.'
    }
    $param = Get-Content "$Game/sce_sys/param.json" -Raw -Encoding UTF8 | ConvertFrom-Json
    $title = [string]$param.titleId
    $version = [string]$param.contentVersion
    if ($title -notmatch '^PPSA\d+$' -or $version -notmatch '^\d+\.\d+\.\d+$') {
        throw 'The game metadata does not contain a valid title ID and version.'
    }
    # Use the exact overrides that launch this build; preserve its legacy shader/cache mode.
    $run = Get-Content "$PSScriptRoot/run.cmd" -Raw
    $match = [regex]::Match($run, ' -Set ([^\s]+)')
    if (!$match.Success) { throw 'Could not resolve the build performance settings from run.cmd.' }
    $pairs = @($match.Groups[1].Value -split ',(?=[A-Za-z_][A-Za-z0-9_]*=)')
    # Recorded precompile must finish the recording, rather than stop after launch's time budget.
    $pairs = @($pairs | Where-Object { $_ -notmatch '^KYTY_SHADER_WARMUP_SECONDS=' })
    foreach ($required in @('KYTY_PORTABLE_SHADERS=0','KYTY_VULKAN_RECORDING=0','KYTY_DEFERRED_SUBMIT=0')) {
        if ($pairs -notcontains $required) { throw "Missing stable build setting: $required" }
    }
    $seedRoot = Join-Path $PSScriptRoot "_PipelineCache/precompile-inputs/$title/$version"
    $seeds = Join-Path $seedRoot 'seeds.seeds'
    $recording = Join-Path $PSScriptRoot '_PipelineCache/warmup-legacy/recording.shaders'
    if ($CheckOnly) {
        Write-Host "PRECOMPILE_PLAN mode=$Mode title=$title version=$version"
        Write-Host ('PRECOMPILE_FLAGS ' + ($pairs -join ','))
        if ($Mode -eq 'Recorded') {
            & "$PSScriptRoot/run-windows.ps1" -Game $Game -Baseline -Precompile -Set ($pairs -join ',') -DryRun
        } else {
            Write-Host "PRECOMPILE_SEEDS $seeds"
            Write-Host 'PRECOMPILE_RECORDED_SEEDS none; generate from selected game files'
        }
        return
    }
    Set-Content "$PSScriptRoot/game-path.txt" $Game -Encoding UTF8
    Write-Host "Precompile $Mode shaders: $title $version"
    Write-Host 'Close the game while preparing its shaders. Results stay in _PipelineCache.'
    if ($Mode -eq 'Recorded') {
        if (!(Test-Path $recording)) { throw 'No recorded shaders yet. Play the game once, then choose Recorded cache again, or choose Full game.' }
        & "$PSScriptRoot/run-windows.ps1" -Game $Game -Baseline -Precompile -Set ($pairs -join ',')
        if ($LASTEXITCODE) { throw "Recorded shader precompile exited with code $LASTEXITCODE; see logs." }
    } else {
        if (!(Get-Command python -ErrorAction SilentlyContinue)) { throw 'Full game precompile requires Python 3 and NumPy. Install Python, then run: python -m pip install numpy' }
        & python -c 'import numpy'
        if ($LASTEXITCODE) { throw 'NumPy is missing. Install it with: python -m pip install numpy' }
        foreach ($pair in $pairs) {
            $key, $value = $pair -split '=', 2
            Set-Item "env:$key" $value
        }
        Remove-Item Env:KYTY_SHADER_WARMUP_ONLY -ErrorAction SilentlyContinue
        & "$PSScriptRoot/precompile-windows.ps1" -Game $Game -Seeds $seeds -Recorded ''
    }
    Write-Host 'Shader preparation finished. Relaunch with run.cmd.'
} catch {
    $result = 1
    Write-Host "Shader preparation failed: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    if (!$NoPause -and !$CheckOnly) { [void](Read-Host 'Press Enter to close') }
}
if ($result) { exit $result }
