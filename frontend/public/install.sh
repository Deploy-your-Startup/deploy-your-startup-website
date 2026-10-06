#!/bin/bash
# Deploy Your Startup installer. Runtime tools stay in our own directory.
set -euo pipefail

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

echo "Installing Startup CLI v0.1.0 with Python 3.14…"
curl --proto '=https' --tlsv1.2 -fsSL \
  https://astral.sh/uv/0.12.23/install.sh -o "$startup_tmp/uv-install.sh"
UV_UNMANAGED_INSTALL="$startup_root/runtime/bin" sh "$startup_tmp/uv-install.sh"

UV_PYTHON_INSTALL_DIR="$startup_root/python" \
UV_TOOL_DIR="$startup_root/tools" \
UV_TOOL_BIN_DIR="$startup_root/commands" \
  "$startup_root/runtime/bin/uv" tool install --reinstall --quiet --managed-python --python 3.14 \
  git+https://github.com/Deploy-your-Startup/cli@v0.1.0

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
echo "Installed. Next: startup doctor"
