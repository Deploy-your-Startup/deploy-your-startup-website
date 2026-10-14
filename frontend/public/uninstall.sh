#!/bin/bash
# Remove only the managed CLI installation. Projects and credentials stay put.
set -euo pipefail

startup_root="$HOME/.local/share/startup"
startup_target="$HOME/.local/bin/startup"
startup_yes=false
case "${1:-}" in
  --yes) startup_yes=true ;;
  '') ;;
  *) echo "Usage: uninstall.sh [--yes]" >&2; exit 1 ;;
esac
if [ "$#" -gt 1 ]; then
  echo "Usage: uninstall.sh [--yes]" >&2
  exit 1
fi

if [ ! -e "$startup_root" ] && [ ! -L "$startup_root" ]; then
  echo "Startup CLI is not installed by this installer."
  exit 0
fi
if [ -L "$startup_root" ] || [ ! -f "$startup_root/.startup-install" ] || \
  ! grep -Fxq 'Deploy Your Startup managed installation' "$startup_root/.startup-install"; then
  echo "Unrecognized installation. Run the current installer first; nothing was removed." >&2
  exit 1
fi
if [ -e "$startup_target" ] || [ -L "$startup_target" ]; then
  if [ -L "$startup_target" ] || ! grep -Fxq '# Deploy Your Startup launcher' "$startup_target"; then
    echo "The startup command has changed. Nothing was removed." >&2
    exit 1
  fi
fi

if [ "$startup_yes" != true ]; then
  echo "Remove Startup CLI and its private runtime? Projects and credentials stay."
  if ! read -r -p 'Type remove to continue: ' startup_answer </dev/tty; then
    echo "Confirmation unavailable. Use --yes for unattended removal." >&2
    exit 1
  fi
  if [ "$startup_answer" != remove ]; then
    echo "Cancelled."
    exit 0
  fi
fi

startup_tmp="$(mktemp -d)"
trap 'rm -rf "$startup_tmp"' EXIT
for startup_profile in "$HOME/.zshrc" "$HOME/.bash_profile"; do
  if [ -L "$startup_profile" ]; then
    echo "Linked shell profile preserved. Remove the installer PATH entry manually: $startup_profile"
    continue
  fi
  if [ -f "$startup_profile" ]; then
    awk '
      $0 == "# Deploy Your Startup" {
        marker = $0
        if (getline > 0) {
          if ($0 == "export PATH=\"$HOME/.local/bin:$PATH\"") next
          print marker
          print
          next
        }
        print marker
        next
      }
      { print }
    ' "$startup_profile" > "$startup_tmp/profile"
    cat "$startup_tmp/profile" > "$startup_profile"
  fi
done
# Remove only our GitHub CLI link, preserving any independently installed gh.
startup_gh_target="$HOME/.local/bin/gh"
if [ -L "$startup_gh_target" ] && [ "$(readlink "$startup_gh_target")" = "$startup_root/runtime/bin/gh" ]; then
  rm -f "$startup_gh_target"
fi
rm -f "$startup_target"
rm -rf "$startup_root"
echo "Startup CLI removed. Projects, Keychain credentials and cloud resources are unchanged."
