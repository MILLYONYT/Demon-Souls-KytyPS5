param(
    [ValidateSet('Recorded','Full')][string]$Mode = 'Recorded',
    [string]$Game = '',
    [switch]$CheckOnly,
    [switch]$NoPause
)
$ErrorActionPreference = 'Stop'
function Test-PythonExecutable([string]$path) {
    # Windows advertises Store launchers as python.exe even when Python is absent.
    if (!$path -or $path -match '[\\/]Microsoft[\\/]WindowsApps[\\/]' -or !(Test-Path $path -PathType Leaf)) { return $false }
    try {
        # Windows PowerShell 5.1 strips embedded double quotes from native arguments.
        # Keep this program quote-free so a valid interpreter is not rejected.
        & $path -c 'import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] < (3,15) and sys.maxsize > 2**32 else 1)' 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } catch { return $false }
}
function Test-PythonImport([string]$path, [string]$module) {
    if ($module -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') { throw 'Invalid Python module name.' }
    try {
        & $path -c ("import " + $module) 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } catch { return $false }
}
function Ensure-ShaderPython {
    $toolRoot = Join-Path $env:LOCALAPPDATA 'KytyPS5/ShaderTools'
    $venvRoot = Join-Path $toolRoot 'venv'
    $python = Join-Path $venvRoot 'Scripts/python.exe'
    if (!(Test-PythonExecutable $python)) {
        $base = Join-Path $toolRoot 'Python314/python.exe'
        if (!(Test-PythonExecutable $base)) {
            $base = $null
            foreach ($candidate in @(Get-Command python,python3 -CommandType Application -All -ErrorAction SilentlyContinue)) {
                if (Test-PythonExecutable $candidate.Source) { $base = $candidate.Source; break }
            }
        }
        if (!$base) {
            Write-Host 'No working Python installation found. Setting up Python for shader preparation...'
            New-Item -ItemType Directory -Force $toolRoot | Out-Null
            $installer = Join-Path $toolRoot 'python-3.14.8-amd64.exe'
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest 'https://www.python.org/ftp/python/3.14.8/python-3.14.8-amd64.exe' -OutFile $installer -UseBasicParsing
            $hash = (Get-FileHash $installer -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($hash -ne '759be887b96e736a3ca886daf8d575f18fcae1a09efab6902f42d59e8999f8ef') {
                throw 'The Python installer checksum does not match the official release. Download cancelled.'
            }
            $signature = Get-AuthenticodeSignature $installer
            if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'CN=Python Software Foundation(?:,|$)') {
                throw 'The Python installer signature could not be verified.'
            }
            $target = Join-Path $toolRoot 'Python314'
            $arguments = '/quiet /norestart InstallAllUsers=0 PrependPath=0 AssociateFiles=0 Include_launcher=0 Include_test=0 Include_doc=0 Include_pip=1 Include_tcltk=0 Shortcuts=0 TargetDir="' + $target + '"'
            $install = Start-Process $installer -ArgumentList $arguments -Wait -PassThru
            if ($install.ExitCode -notin @(0,3010)) { throw "Python setup failed with exit code $($install.ExitCode)." }
            $base = Join-Path $target 'python.exe'
            if (!(Test-PythonExecutable $base)) { throw "Python setup completed but validation failed at $base. Expected a working 64-bit Python 3.11-3.14 interpreter." }
            Remove-Item $installer -ErrorAction SilentlyContinue
        }
        Write-Host 'Creating the shader-preparation Python environment...'
        & $base -m venv $venvRoot | Out-Host
        if ($LASTEXITCODE -or !(Test-PythonExecutable $python)) { throw 'Could not create the shader-preparation Python environment.' }
    }
    if (!(Test-PythonImport $python 'numpy')) {
        Write-Host 'Installing NumPy for shader preparation...'
        & $python -m pip install --disable-pip-version-check --only-binary=:all: numpy | Out-Host
        if ($LASTEXITCODE) { throw 'NumPy download/install failed. Check the Internet connection and rerun Full game precompile.' }
    }
    if (!(Test-PythonImport $python 'numpy')) { throw 'NumPy is installed but could not load in the shader-preparation environment.' }
    return $python
}
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
        if (Test-PythonExecutable (Join-Path $env:LOCALAPPDATA 'Microsoft/WindowsApps/python.exe')) { throw 'Microsoft Store Python alias was incorrectly accepted.' }
        Write-Host 'PYTHON_ALIAS_CHECK passed'
        if ($env:GITHUB_ACTIONS -eq 'true') {
            # Exercise the actual native-command probes under the workflow's powershell.exe.
            $candidates = @((Get-Command python -CommandType Application -ErrorAction SilentlyContinue).Source)
            if ($env:RUNNER_TOOL_CACHE) {
                $candidates += @(Get-ChildItem (Join-Path $env:RUNNER_TOOL_CACHE 'Python/*/x64/python.exe') -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
            }
            $ciPython = $candidates | Where-Object { Test-PythonExecutable $_ } | Select-Object -First 1
            if (!$ciPython) { throw 'CI did not accept an installed supported Python interpreter.' }
            if (!(Test-PythonImport $ciPython 'sys')) { throw 'Python import probe rejected a built-in module.' }
            if (Test-PythonImport $ciPython 'kyty_intentionally_missing_probe_module') { throw 'Python import probe accepted a missing module.' }
            Write-Host 'PYTHON_INTERPRETER_AND_IMPORT_CHECK passed'
        }
        Write-Host "PRECOMPILE_PLAN mode=$Mode title=$title version=$version"
        Write-Host ('PRECOMPILE_FLAGS ' + ($pairs -join ','))
        if ($Mode -eq 'Recorded') {
            & "$PSScriptRoot/run-windows.ps1" -Game $Game -Baseline -Precompile -Set ($pairs -join ',') -DryRun
            if ($LASTEXITCODE) { throw 'Recorded precompile dry-run failed.' }
        } else {
            Write-Host "PRECOMPILE_SEEDS $seeds"
            Write-Host 'PRECOMPILE_RECORDED_SEEDS none; generate from selected game files'
        }
        # A deliberately failing import is part of the CI probe, not this plan's result.
        $global:LASTEXITCODE = 0
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
        $python = Ensure-ShaderPython
        # The scanner launches python by name; resolve it to the verified environment.
        $env:PATH = (Split-Path $python) + ';' + $env:PATH
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
