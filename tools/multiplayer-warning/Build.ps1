param(
    [Parameter(Mandatory)][string] $Libraries,
    [Parameter(Mandatory)][string] $WorkDirectory
)

$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot src
$paths = @(
    'net/minecraft/client/1.20.1-20230612.114412/client-1.20.1-20230612.114412-srg.jar',
    'net/minecraftforge/javafmllanguage/1.20.1-47.4.0/javafmllanguage-1.20.1-47.4.0.jar',
    'org/spongepowered/mixin/0.8.5/mixin-0.8.5.jar',
    'org/ow2/asm/asm/9.7.1/asm-9.7.1.jar'
)
$classpath = ($paths | ForEach-Object { (Resolve-Path -LiteralPath (Join-Path $Libraries $_)).Path }) -join [IO.Path]::PathSeparator
$classes = New-Item -ItemType Directory -Path (Join-Path $WorkDirectory 'classes')
$sources = (Get-ChildItem -LiteralPath "$source/java" -Recurse -Filter '*.java').FullName
javac --release 17 -encoding UTF-8 -proc:none -classpath $classpath -d $classes.FullName @sources
if ($LASTEXITCODE) { throw 'Forge helper compilation failed' }
$output = Join-Path $PSScriptRoot '../../mods/reclamation-multiplayer-1.0.0.jar'
jar --create --file $output --manifest "$source/resources/META-INF/MANIFEST.MF" --date 1980-01-01T00:00:02Z `
    -C $classes.FullName lanmc -C "$source/resources" META-INF/mods.toml -C "$source/resources" reclamation.multiplayer.mixins.json
if ($LASTEXITCODE) { throw 'Forge helper packaging failed' }
Get-FileHash -LiteralPath $output
