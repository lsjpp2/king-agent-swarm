# init.ps1 — Windows Setup Script

# Usage:
#   .\init.ps1 -KingName "YourName" -ClusterRoot "D:\my-agent-cluster"
#   .\init.ps1 -ListAgents   # show detected agents

param(
    [string]$KingName,
    [string]$ClusterRoot,
    [string]$DefaultPM,
    [switch]$ListAgents
)

$ErrorActionPreference = "Stop"

function Log-Info($msg)  { Write-Host "[INFO] $msg" -ForegroundColor Green }
function Log-Warn($msg)  { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Log-Error($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# Detect installed agents
function Detect-Agents {
    Log-Info "Detecting installed agents..."
    $agents = @()

    # Claude Code
    if (Test-Path "$env:USERPROFILE\.claude") {
        $agents += @{ Id="claude"; Name="Claude Code"; Path="$env:USERPROFILE\.claude" }
        Log-Info "  Detected: Claude Code"
    }

    # Cursor
    if (Test-Path "$env:USERPROFILE\.cursor") {
        $agents += @{ Id="cursor"; Name="Cursor"; Path="$env:USERPROFILE\.cursor" }
        Log-Info "  Detected: Cursor"
    }
    elseif (Test-Path "C:\Users\$env:USERNAME\.cursor") {
        $agents += @{ Id="cursor"; Name="Cursor"; Path="C:\Users\$env:USERNAME\.cursor" }
        Log-Info "  Detected: Cursor"
    }

    # OpenCode
    if (Test-Path "$env:USERPROFILE\.config\opencode") {
        $agents += @{ Id="opencode"; Name="OpenCode"; Path="$env:USERPROFILE\.config\opencode" }
        Log-Info "  Detected: OpenCode"
    }

    # Codex
    if (Test-Path "D:\Software\Codex-app\app\Codex.exe") {
        $agents += @{ Id="codex"; Name="Codex"; Path="D:\Software\Codex-app" }
        Log-Info "  Detected: Codex"
    }

    # Kimi
    if (Test-Path "$env:LOCALAPPDATA\Programs\kimi-desktop\Kimi.exe") {
        $agents += @{ Id="kimi"; Name="Kimi"; Path="$env:LOCALAPPDATA\Programs\kimi-desktop" }
        Log-Info "  Detected: Kimi"
    }

    return $agents
}

# Generate coordinator.json
function Gen-Coordinator($agents, $defaultPM) {
    $registry = @{}
    foreach ($a in $agents) {
        $registry[$a.Id] = @{
            platform       = $a.Name
            role           = "Agent (can be PM)"
            can_be_pm      = $true
            identity_file  = "$ClusterRoot\agent-identities\$($a.Id)-identity.md"
            private_memory = $a.Path
        }
    }

    $coordinator = @{
        _schema              = "king-agent-swarm-v1"
        _desc                = "Constitution-level file. Every agent reads this on startup."
        _king                = $KingName
        current_coordinator  = $defaultPM
        since                = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        previous_coordinator = $null
        rotation_policy      = @{
            trigger = "King's command"
            desc    = "King says 'X is Prime Minister from now on' → immediate rotation."
        }
        rotation_history     = @()
        handover_state       = @{
            active_projects    = @()
            pending_decisions  = @()
            last_handover_dump = $null
        }
        agent_registry       = $registry
        cluster_root         = $ClusterRoot
    }

    $coordinator | ConvertTo-Json -Depth 10 | Out-File "$ClusterRoot\coordinator.json" -Encoding UTF8
    Log-Info "Generated coordinator.json"
}

# Generate constitution.md
function Gen-Constitution {
    $template = Get-Content "$PSScriptRoot\templates\constitution.md" -Raw
    $content = $template `
        -replace '\$\{KING_NAME\}', $KingName `
        -replace '\$\{CLUSTER_ROOT\}', $ClusterRoot `
        -replace '\$\{DATE\}', (Get-Date -Format "yyyy-MM-dd")
    $content | Out-File "$ClusterRoot\constitution.md" -Encoding UTF8
    Log-Info "Generated constitution.md"
}

# Generate agent identity cards
function Gen-Identities($agents) {
    New-Item "$ClusterRoot\agent-identities" -ItemType Directory -Force | Out-Null
    foreach ($a in $agents) {
        $content = @"
# $($a.Name) Identity Card

## Core Identity
You are **$($a.Name)**, an AI agent in the King Agent Swarm cluster.

## King Model Rules
- **King**: $KingName (sole sovereign, absolute veto power)
- **Current PM**: [read from \`$ClusterRoot\coordinator.json\` → \`current_coordinator\`]
- You **can** take over as Prime Minister.

## Memory Isolation
- **Private memory**: \`$($a.Path)\`
- **MUST NOT** read other agents' private memory.
- **Shared layer**: \`$ClusterRoot\` (read/write access)

## Startup Self-Check
1. Read \`$ClusterRoot\coordinator.json\` — confirm King and current PM.
2. Read this identity file — confirm your role.
3. Read \`$ClusterRoot\progress\\` — get today's context.
4. Begin duty.
"@
        $content | Out-File "$ClusterRoot\agent-identities\$($a.Id)-identity.md" -Encoding UTF8
        Log-Info "Generated identity: $($a.Id)-identity.md"
    }
}

# ---- Main ----
if ($ListAgents) {
    $agents = Detect-Agents
    Log-Info "Detected $($agents.Count) agent(s)."
    exit 0
}

if (-not $KingName -or -not $ClusterRoot) {
    Write-Host "Usage: .\init.ps1 -KingName \"YourName\" -ClusterRoot \"D:\my-agent-cluster\" [-DefaultPM \"AgentName\"]"
    exit 1
}

Log-Info "Setting up King Agent Swarm..."
Log-Info "  King: $KingName"
Log-Info "  Cluster Root: $ClusterRoot"

New-Item $ClusterRoot -ItemType Directory -Force | Out-Null
$agents = Detect-Agents

if (-not $DefaultPM -and $agents.Count -gt 0) {
    $DefaultPM = $agents[0].Id
    Log-Info "Default PM (first detected): $DefaultPM"
}

Gen-Coordinator $agents $DefaultPM
Gen-Constitution
Gen-Identities $agents

Copy-Item "$PSScriptRoot\templates\handover-protocol.md" "$ClusterRoot\"
New-Item "$ClusterRoot\progress" -ItemType Directory -Force | Out-Null
Log-Info "Generated handover-protocol.md"

Log-Info "Done! Next steps:"
Log-Info "  1. Review $ClusterRoot\coordinator.json"
Log-Info "  2. Inject identity cards into each agent (see docs/quick-start.md)"
Log-Info "  3. Start your agents and verify with the check questions"
