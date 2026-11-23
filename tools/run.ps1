# Build a model (and optionally render it) without opening Blender's window.
#
# Examples:
#   .\tools\run.ps1 pendulum                        # build + save output\pendulum\pendulum.blend
#   .\tools\run.ps1 pendulum -mode preview -still   # quick image
#   .\tools\run.ps1 pendulum -mode preview          # quick video (~0.1 s/frame)
#   .\tools\run.ps1 pendulum -mode final            # realistic video (~2-3 s/frame at 720p)
#   .\tools\run.ps1 collision_pi -mode preview -reel -resolution 1920   # vertical 1080x1920 reel
#   .\tools\run.ps1 pendulum -open                  # build, then open it in Blender
param(
    [Parameter(Mandatory = $true)][string]$model,
    [ValidateSet("none", "preview", "final")][string]$mode = "none",
    [switch]$still,
    [switch]$reel,
    [int]$resolution = 720,
    [switch]$open
)

$repo = Split-Path -Parent $PSScriptRoot
$blender = $env:BLENDER_EXE
if (-not $blender) { $blender = "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" }
$script = Join-Path $repo "models\$model\build.py"
if (-not (Test-Path $script)) { Write-Error "No model script at $script"; exit 1 }

$extra = @("--mode", $mode, "--resolution", $resolution)
if ($still) { $extra += "--still" }
if ($reel) { $extra += "--reel" }

& $blender --background --factory-startup --python-exit-code 1 --python $script -- @extra
if ($LASTEXITCODE -ne 0) { Write-Error "Blender failed (exit $LASTEXITCODE)"; exit $LASTEXITCODE }

if ($open) {
    Start-Process $blender (Join-Path $repo "output\$model\$model.blend")
}
