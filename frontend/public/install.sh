#!/bin/bash
# Deploy Your Startup installer. Keep the CLI isolated; reuse compatible uv.
set -euo pipefail

# The only place the CLI version is pinned; scripts/update_cli_release.py
# advances it on stable releases. Each CLI release pins its tested template.
startup_cli_version="v0.1.25"

startup_onboard=false
startup_new_terminal=false
case "${1:-}" in
  --onboard) startup_onboard=true ;;
  "") ;;
  *) echo "Usage: install.sh [--onboard]" >&2; exit 1 ;;
esac
if "$startup_onboard" && ! ( : </dev/tty ) 2>/dev/null; then
  echo "Run onboarding from an interactive terminal." >&2
  exit 1
fi

if [ "$(uname -s)" != Darwin ]; then
  echo "Early access currently supports macOS." >&2
  exit 1
fi
if ! command -v git >/dev/null 2>&1 || ! git --version >/dev/null 2>&1; then
  echo "Install Git first: xcode-select --install. Then run this installer again." >&2
  exit 1
fi

startup_root="$HOME/.local/share/startup"
startup_bin="$HOME/.local/bin"
startup_target="$startup_bin/startup"
if [ -e "$startup_target" ] && ! grep -Eq 'Deploy Your Startup launcher|from cli.startup import cli' "$startup_target"; then
  echo "Another program already owns $startup_target. Move it before installing." >&2
  exit 1
fi

startup_tmp="$(mktemp -d)"
trap 'rm -rf "$startup_tmp"' EXIT
if [ -L "$startup_root" ]; then
  echo "Refusing to install into a symlink: $startup_root" >&2
  exit 1
fi
mkdir -p "$startup_root/runtime/bin" "$startup_bin"

echo "Setting up Startup CLI ${startup_cli_version}…"

# Check capabilities instead of replacing a working user-owned uv installation.
startup_uv_compatible() {
  [ -n "$1" ] || return 1
  "$1" --version >/dev/null 2>&1 || return 1
  startup_uv_help="$("$1" tool install --help 2>/dev/null)" || return 1
  for startup_option in --managed-python --python --quiet; do
    case "$startup_uv_help" in
      *"$startup_option"*) ;;
      *) return 1 ;;
    esac
  done
}
startup_uv="$(command -v uv || true)"
if startup_uv_compatible "$startup_uv"; then
  echo "✓ Using existing uv"
elif startup_uv_compatible "$startup_root/runtime/bin/uv"; then
  startup_uv="$startup_root/runtime/bin/uv"
  echo "✓ Using existing installer-managed uv"
else
  echo "→ Installing a compatible uv for Startup CLI…"
  curl --proto '=https' --tlsv1.2 -fsSL \
    https://astral.sh/uv/0.12.23/install.sh -o "$startup_tmp/uv-install.sh"
  if ! PATH="$startup_root/runtime/bin:$PATH" \
    UV_UNMANAGED_INSTALL="$startup_root/runtime/bin" \
    sh "$startup_tmp/uv-install.sh" >"$startup_tmp/uv.log" 2>&1; then
    cat "$startup_tmp/uv.log" >&2
    exit 1
  fi
  startup_uv="$startup_root/runtime/bin/uv"
  if ! startup_uv_compatible "$startup_uv"; then
    echo "The installed uv could not be verified. Run the installer again." >&2
    exit 1
  fi
fi

# Preserve older installations; new ones share uv's managed Python cache.
if [ -d "$startup_root/python" ]; then
  export UV_PYTHON_INSTALL_DIR="$startup_root/python"
fi
echo "→ Checking Startup CLI installation (first-time downloads may take a few minutes)…"
# The launcher, not this directory, goes on PATH; hide uv's PATH warning about it.
if ! PATH="$startup_root/commands:$PATH" \
  UV_TOOL_DIR="$startup_root/tools" \
  UV_TOOL_BIN_DIR="$startup_root/commands" \
  "$startup_uv" tool install --quiet --managed-python --python 3.14 \
  "git+https://github.com/Deploy-your-Startup/cli@$startup_cli_version" \
  >"$startup_tmp/install.log" 2>&1; then
  echo "Startup CLI installation failed:" >&2
  cat "$startup_tmp/install.log" >&2
  exit 1
fi

printf '%s\n' "${startup_uv%/*}" > "$startup_root/uv-bin"
cat > "$startup_tmp/startup" <<'LAUNCHER'
#!/bin/sh
# Deploy Your Startup launcher
export PATH="$(cat "$HOME/.local/share/startup/uv-bin"):$PATH"
if [ -d "$HOME/.local/share/startup/python" ]; then
  export UV_PYTHON_INSTALL_DIR="$HOME/.local/share/startup/python"
fi
exec "$HOME/.local/share/startup/commands/startup" "$@"
LAUNCHER
chmod +x "$startup_tmp/startup"
# Replace a previous symlink rather than writing through it into its environment.
mv -f "$startup_tmp/startup" "$startup_target"
echo "→ Verifying startup…"
"$startup_target" --help >/dev/null
printf '%s\n' 'Deploy Your Startup managed installation' > "$startup_root/.startup-install"

case ":$PATH:" in
  *":$startup_bin:"*) ;;
  *)
    case "${SHELL:-/bin/zsh}" in
      */bash) startup_profile="$HOME/.bash_profile" ;;
      *) startup_profile="$HOME/.zshrc" ;;
    esac
    if ! grep -Fq 'export PATH="$HOME/.local/bin:$PATH"' "$startup_profile" 2>/dev/null; then
      printf '\n# Deploy Your Startup\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$startup_profile"
    fi
    startup_new_terminal=true
    "$startup_onboard" || echo "Open a new terminal to use startup."
    ;;
esac
# Coding agents learn the CLI from a bundled skill; older CLI releases lack it.
startup_agent_skill=false
if "$startup_target" skills --help >/dev/null 2>&1; then
  for startup_agent_dir in .claude .codex .config/opencode; do
    [ -d "$HOME/$startup_agent_dir" ] && startup_agent_skill=true
  done
fi
if "$startup_onboard"; then
  export PATH="$startup_bin:$PATH"
  # The installer may arrive through a pipe; prompts must read from the terminal.
  startup_github_scopes() {
    local status
    status="$(gh auth status -h github.com --active 2>&1)" || return 1
    case "$status" in *"'workflow'"*) ;; *) return 1 ;; esac
    case "$status" in *"'read:packages'"*|*"'write:packages'"*) return 0 ;; esac
    return 1
  }
  startup_onboarding() {
    printf "\nYour terminal. Let's get started.\n\n"
    echo "You need GitHub and Hetzner Cloud. Bring a domain or register one during setup."
    echo "Servers and your domain are billed by your providers."
    printf "\n[1/3] Connect GitHub\n"
    while ! command -v gh >/dev/null 2>&1; do
      echo "Install GitHub CLI in another terminal: brew install gh"
      echo "Without Homebrew, get it from https://cli.github.com"
      read -r -p "Press Return when ready (Ctrl-C to stop). "
    done
    if ! gh auth status -h github.com >/dev/null 2>&1; then
      gh auth login -h github.com -p https -s repo,workflow,read:packages,write:packages
    fi
    # An existing login may lack scopes the deployment needs; fix it here
    # instead of sending the user to another terminal.
    if ! startup_github_scopes; then
      echo "GitHub needs access to workflows and packages. Approve it in your browser."
      gh auth refresh -h github.com -s repo,workflow,read:packages,write:packages || true
    fi
    gh auth setup-git
    startup_github_account="$(gh api user --jq .login 2>/dev/null || true)"
    [ -z "$startup_github_account" ] || echo "Using GitHub account $startup_github_account."
    printf "\n[2/3] Check this Mac\n"
    until "$startup_target" doctor; do
      echo "Complete the missing setup above in another terminal."
      read -r -p "Press Return to check again (Ctrl-C to stop). "
    done
    printf "\n[3/3] Set up your Factory and first startup\n"
    # Factory onboarding owns its template pin, setup and startup output folder.
    if ! "$startup_target" factory --help >/dev/null 2>&1; then
      echo "This CLI release does not include Factory onboarding. Update the installer and try again." >&2
      return 1
    fi
    "$startup_target" factory onboard
    "$startup_new_terminal" && echo "Open a new terminal to use startup."
    echo "To continue or create another startup: cd ~/Projects/startup-factory && startup bootstrap"
    echo "If you chose another Factory folder, use that folder instead."
  }
  startup_onboarding </dev/tty
else
  echo "✓ Startup CLI is ready. Next: startup doctor"
  if "$startup_agent_skill"; then
    echo "Using a coding agent? Run: startup skills install"
  fi
fi
