# init.sh — Unix/macOS Setup Script

# Usage:
#   ./init.sh --king "YourName" --cluster-root "/path/to/cluster"
#   ./init.sh --king "YourName" --cluster-root "~/agent-cluster"
#   ./init.sh --list-agents   # show detected agents

set -e

# Defaults
KING_NAME=""
CLUSTER_ROOT=""
DEFAULT_PM=""
DETECTED_AGENTS=()

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Detect installed agents
detect_agents() {
    log_info "Detecting installed agents..."

    # Claude Code
    if command -v claude &>/dev/null || [ -d "$HOME/.claude" ]; then
        DETECTED_AGENTS+=("claude:Claude Code:$HOME/.claude")
        log_info "  Detected: Claude Code"
    fi

    # Cursor
    if [ -d "$HOME/.cursor" ] || [ -d "/Applications/Cursor.app" ] || [ -d "$LOCALAPPDATA/Cursor" ]; then
        DETECTED_AGENTS+=("cursor:Cursor:$HOME/.cursor")
        log_info "  Detected: Cursor"
    fi

    # OpenCode (check common paths)
    if [ -d "$HOME/.config/opencode" ] || [ -d "$LOCALAPPDATA/@opencode-aidesktop" ]; then
        DETECTED_AGENTS+=("opencode:OpenCode:$HOME/.config/opencode")
        log_info "  Detected: OpenCode"
    fi

    if [ ${#DETECTED_AGENTS[@]} -eq 0 ]; then
        log_warn "No agents detected. You will need to add them manually to coordinator.json."
    fi
}

# Generate coordinator.json
gen_coordinator() {
    local agents_json=""
    local first=true

    for agent in "${DETECTED_AGENTS[@]}"; do
        IFS=':' read -r agent_id agent_name agent_path <<< "$agent"
        if [ "$first" = true ]; then first=false; else agents_json="${agents_json},"; fi
        agents_json="${agents_json}
    \"${agent_id}\": {
      \"platform\": \"${agent_name}\",
      \"role\": \"Agent (can be PM)\",
      \"can_be_pm\": true,
      \"identity_file\": \"${CLUSTER_ROOT}/agent-identities/${agent_id}-identity.md\",
      \"private_memory\": \"${agent_path}\"
    }"
    done

    cat > "${CLUSTER_ROOT}/coordinator.json" <<JSON
{
  "_schema": "king-agent-swarm-v1",
  "_desc": "Constitution-level file. Every agent reads this on startup.",
  "_king": "${KING_NAME}",
  "current_coordinator": "${DEFAULT_PM}",
  "since": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "previous_coordinator": null,
  "rotation_policy": {
    "trigger": "King's command",
    "desc": "King says 'X is Prime Minister from now on' → immediate rotation."
  },
  "rotation_history": [],
  "handover_state": {
    "active_projects": [],
    "pending_decisions": [],
    "last_handover_dump": null
  },
  "agent_registry": {${agents_json}
  },
  "cluster_root": "${CLUSTER_ROOT}"
}
JSON
    log_info "Generated coordinator.json"
}

# Generate constitution.md
gen_constitution() {
    cp "$(dirname "$0")/templates/constitution.md" "${CLUSTER_ROOT}/constitution.md"
    # Replace placeholders
    sed -i.bak "s/\${KING_NAME}/${KING_NAME}/g" "${CLUSTER_ROOT}/constitution.md"
    sed -i.bak "s|\${CLUSTER_ROOT}|${CLUSTER_ROOT}|g" "${CLUSTER_ROOT}/constitution.md"
    sed -i.bak "s/\${DATE}/$(date +"%Y-%m-%d")/g" "${CLUSTER_ROOT}/constitution.md"
    rm -f "${CLUSTER_ROOT}/constitution.md.bak"
    log_info "Generated constitution.md"
}

# Generate agent identity cards
gen_identities() {
    mkdir -p "${CLUSTER_ROOT}/agent-identities"
    for agent in "${DETECTED_AGENTS[@]}"; do
        IFS=':' read -r agent_id agent_name agent_path <<< "$agent"
        cat > "${CLUSTER_ROOT}/agent-identities/${agent_id}-identity.md" <<MD
# ${agent_name} Identity Card

## Core Identity
You are **${agent_name}**, an AI agent in the King Agent Swarm cluster.

## King Model Rules
- **King**: ${KING_NAME} (sole sovereign, absolute veto power)
- **Current PM**: [read from \`${CLUSTER_ROOT}/coordinator.json\` → \`current_coordinator\`]
- You **can** take over as Prime Minister.

## Memory Isolation
- **Private memory**: \`${agent_path}\`
- **MUST NOT** read other agents' private memory.
- **Shared layer**: \`${CLUSTER_ROOT}/\` (read/write access)

## Startup Self-Check
1. Read \`${CLUSTER_ROOT}/coordinator.json\` — confirm King and current PM.
2. Read this identity file — confirm your role.
3. Read \`${CLUSTER_ROOT}/progress/\` — get today's context.
4. Begin duty.
MD
        log_info "Generated identity: ${agent_id}-identity.md"
    done
}

# Main
main() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --king) KING_NAME="$2"; shift 2 ;;
            --cluster-root) CLUSTER_ROOT="$2"; shift 2 ;;
            --default-pm) DEFAULT_PM="$2"; shift 2 ;;
            --list-agents) detect_agents; exit 0 ;;
            *) log_error "Unknown option: $1"; exit 1 ;;
        esac
    done

    if [ -z "$KING_NAME" ] || [ -z "$CLUSTER_ROOT" ]; then
        echo "Usage: ./init.sh --king \"YourName\" --cluster-root \"/path/to/cluster\" [--default-pm \"AgentName\"]"
        exit 1
    fi

    # Expand ~ in CLUSTER_ROOT
    CLUSTER_ROOT="${CLUSTER_ROOT/#\~/$HOME}"

    log_info "Setting up King Agent Swarm..."
    log_info "  King: ${KING_NAME}"
    log_info "  Cluster Root: ${CLUSTER_ROOT}"

    mkdir -p "${CLUSTER_ROOT}/agent-identities"
    mkdir -p "${CLUSTER_ROOT}/progress"

    detect_agents

    if [ -z "$DEFAULT_PM" ] && [ ${#DETECTED_AGENTS[@]} -gt 0 ]; then
        DEFAULT_PM=$(echo "${DETECTED_AGENTS[0]}" | cut -d: -f1)
        log_info "Default PM (first detected): ${DEFAULT_PM}"
    fi

    gen_coordinator
    gen_constitution
    gen_identities

    cp "$(dirname "$0")/templates/handover-protocol.md" "${CLUSTER_ROOT}/"
    mkdir -p "${CLUSTER_ROOT}/progress"
    log_info "Generated handover-protocol.md"

    log_info "Done! Next steps:"
    log_info "  1. Review ${CLUSTER_ROOT}/coordinator.json"
    log_info "  2. Inject identity cards into each agent (see docs/quick-start.md)"
    log_info "  3. Start your agents and verify with the check questions"
}

main "$@"
