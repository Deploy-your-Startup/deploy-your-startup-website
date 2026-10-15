#!/bin/bash
# Deploy Your Startup installer. Runtime tools stay in our own directory.
set -euo pipefail

# The only place the CLI version is pinned; scripts/update_cli_release.py
# advances it on stable releases. Each CLI release pins its tested template.
startup_cli_version="v0.1.16"

startup_onboard=false
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

echo "Installing Startup CLI $startup_cli_version with Python 3.14…"
curl --proto '=https' --tlsv1.2 -fsSL \
  https://astral.sh/uv/0.12.23/install.sh -o "$startup_tmp/uv-install.sh"
# Match the launcher PATH so other uv installations do not trigger shadow warnings.
PATH="$startup_root/runtime/bin:$PATH" \
UV_UNMANAGED_INSTALL="$startup_root/runtime/bin" sh "$startup_tmp/uv-install.sh"

echo "Installing Python 3.14 and Startup CLI $startup_cli_version. Downloads may take a few minutes…"
UV_PYTHON_INSTALL_DIR="$startup_root/python" \
UV_TOOL_DIR="$startup_root/tools" \
UV_TOOL_BIN_DIR="$startup_root/commands" \
  "$startup_root/runtime/bin/uv" tool install --reinstall --managed-python --python 3.14 \
  "git+https://github.com/Deploy-your-Startup/cli@$startup_cli_version"

cat > "$startup_tmp/startup" <<'LAUNCHER'
#!/bin/sh
# Deploy Your Startup launcher
export PATH="$HOME/.local/share/startup/runtime/bin:$PATH"
export UV_PYTHON_INSTALL_DIR="$HOME/.local/share/startup/python"
exec "$HOME/.local/share/startup/commands/startup" "$@"
LAUNCHER
chmod +x "$startup_tmp/startup"
# Replace a previous symlink rather than writing through it into its environment.
mv -f "$startup_tmp/startup" "$startup_target"
echo "Verifying Startup CLI…"
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
    echo "Open a new terminal to use startup."
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
    gh auth setup-git
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
    echo "To continue or create another startup: cd ~/Projects/startup-factory && startup bootstrap"
    echo "If you chose another Factory folder, use that folder instead."
  }
  startup_onboarding </dev/tty
else
  echo "Installed. Next: startup doctor"
  if "$startup_agent_skill"; then
    echo "Using a coding agent? Run: startup skills install"
  fi
fi
