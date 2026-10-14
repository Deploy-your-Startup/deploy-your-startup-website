#!/bin/bash
# Deploy Your Startup installer. Runtime tools stay in our own directory.
set -euo pipefail

# The only place the CLI version is pinned; scripts/update_cli_release.py
# advances it on stable releases. Each CLI release pins its tested template.
startup_cli_version="v0.1.13"

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
startup_step=""
startup_spinner_pid=""
startup_is_animated=false
startup_accent=""
startup_emphasis=""
startup_muted=""
startup_reset=""
# stdin may be the curl pipe; only the output terminal controls presentation.
if [ -t 1 ] && [ "${TERM:-dumb}" != dumb ] && [ -z "${NO_COLOR:-}" ] && [ -z "${CI:-}" ]; then
  [ -n "${STARTUP_NO_ANIMATION:-}" ] || startup_is_animated=true
  # Match the current landing page's muted blue, with a 256-color approximation.
  # Basic terminals keep their own foreground rather than substitute neon cyan.
  case "${COLORTERM:-}:${TERM:-}" in
    truecolor:*|24bit:*|*:*direct*) startup_accent=$'\033[38;2;156;190;220m' ;;
    *:*256color*) startup_accent=$'\033[38;5;110m' ;;
  esac
  startup_emphasis=$'\033[1m'
  startup_muted=$'\033[2m'
  startup_reset=$'\033[0m'
fi

startup_stop_spinner() {
  if [ -n "$startup_spinner_pid" ]; then
    kill "$startup_spinner_pid" 2>/dev/null || true
    wait "$startup_spinner_pid" 2>/dev/null || true
    startup_spinner_pid=""
    printf '\r\033[2K'
  fi
}

startup_cleanup() {
  local startup_status=$?
  startup_stop_spinner
  if [ "$startup_status" -ne 0 ] && [ -n "$startup_step" ]; then
    printf '\n  ! %s did not finish.\n' "$startup_step" >&2
    printf '  Run the installer again when ready.\n' >&2
  fi
  rm -rf "$startup_tmp"
}
trap 'startup_cleanup' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

startup_show_progress() {
  local startup_message="$1"
  if "$startup_is_animated"; then
    (
      while :; do
        for startup_frame in '·›··' '··›·' '···›' '›···'; do
          sleep 0.25
          printf '\r\033[2K  %s%s%s %s…' "$startup_accent" "$startup_frame" "$startup_reset" "$startup_message"
        done
      done
    ) &
    startup_spinner_pid=$!
    printf '  %s›···%s %s…' "$startup_accent" "$startup_reset" "$startup_message"
  else
    printf '  · %s…\n' "$startup_message"
  fi
}

startup_run_step() {
  startup_step="$1"
  local startup_complete="$2"
  shift 2
  printf '  %s·%s %s…\n' "$startup_accent" "$startup_reset" "$startup_step"
  # Stream the command's output directly; a spinner would overwrite its logs.
  # Keep it in the foreground so failures and Ctrl-C stop installation.
  "$@"
  printf '  %s✓%s %s\n' "$startup_accent" "$startup_reset" "$startup_complete"
  startup_step=""
}

startup_check_github_connection() {
  local startup_status=0
  startup_show_progress "Checking GitHub connection"
  # Only animate the silent check; login prompts keep the terminal to themselves.
  gh auth status -h github.com >/dev/null 2>&1 || startup_status=$?
  startup_stop_spinner
  if [ "$startup_status" -eq 0 ]; then
    printf '  %s✓%s GitHub connected\n' "$startup_accent" "$startup_reset"
  fi
  return "$startup_status"
}

if [ -L "$startup_root" ]; then
  echo "Refusing to install into a symlink: $startup_root" >&2
  exit 1
fi
mkdir -p "$startup_root/runtime/bin" "$startup_bin"

printf '\n  %s>_%s %sdeploy your startup%s\n' "$startup_accent" "$startup_reset" "$startup_emphasis" "$startup_reset"
printf '\n  Ideas in. Startups out.\n'
printf '  %sBuild your idea. Find out what works.%s\n\n' "$startup_muted" "$startup_reset"
printf '  %sGive us a moment. We’re setting up your machine to build your startup.%s\n\n' "$startup_muted" "$startup_reset"

startup_install_runtime() {
  curl --proto '=https' --tlsv1.2 -fsSL \
    https://astral.sh/uv/0.12.23/install.sh -o "$startup_tmp/uv-install.sh"
  # Match the launcher PATH so other uv installations do not trigger shadow warnings.
  PATH="$startup_root/runtime/bin:$PATH" \
  UV_UNMANAGED_INSTALL="$startup_root/runtime/bin" sh "$startup_tmp/uv-install.sh"
}

startup_install_cli() {
  UV_PYTHON_INSTALL_DIR="$startup_root/python" \
  UV_TOOL_DIR="$startup_root/tools" \
  UV_TOOL_BIN_DIR="$startup_root/commands" \
    "$startup_root/runtime/bin/uv" tool install --reinstall --managed-python --python 3.14 \
    "git+https://github.com/Deploy-your-Startup/cli@$startup_cli_version"
}

startup_run_step "Preparing your launchpad" "Launchpad prepared" startup_install_runtime
startup_run_step "Installing Python 3.14 and Startup CLI $startup_cli_version" "Startup CLI $startup_cli_version installed" startup_install_cli

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
startup_verify_cli() {
  "$startup_target" --help >/dev/null
}
startup_run_step "Verifying Startup CLI" "CLI verified" startup_verify_cli
printf '%s\n' 'Deploy Your Startup managed installation' > "$startup_root/.startup-install"

startup_needs_new_terminal=false
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
    startup_needs_new_terminal=true
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
    # Install the official GitHub CLI without requiring Homebrew or sudo.
    # Existing gh installations and their credential stores are reused.
    if ! command -v gh >/dev/null 2>&1; then
      startup_gh_version="2.102.0"
      case "$(uname -m)" in
        arm64) startup_gh_arch=arm64; startup_gh_sha=da922c20d1792e5b2cbf375593d7a658acf034c12c84e007e71c76ef959c337e ;;
        x86_64) startup_gh_arch=amd64; startup_gh_sha=b245f24eb2bf5f75b426b4c26da3651a107f8d5b6f4fddfbfccc5679041378b3 ;;
        *) echo "Unsupported Mac architecture for GitHub CLI." >&2; return 1 ;;
      esac
      startup_gh_target="$startup_bin/gh"
      if [ -e "$startup_gh_target" ] || [ -L "$startup_gh_target" ]; then
        echo "Another file owns $startup_gh_target. Install GitHub CLI from https://cli.github.com and retry." >&2
        return 1
      fi
      startup_install_github_cli() {
        curl --proto '=https' --tlsv1.2 -fsSL \
          "https://github.com/cli/cli/releases/download/v${startup_gh_version}/gh_${startup_gh_version}_macOS_${startup_gh_arch}.zip" \
          -o "$startup_tmp/gh.zip"
        printf '%s  %s\n' "$startup_gh_sha" "$startup_tmp/gh.zip" | shasum -a 256 -c -
        unzip -q "$startup_tmp/gh.zip" -d "$startup_tmp/github-cli"
        install -m 755 "$startup_tmp/github-cli/gh_${startup_gh_version}_macOS_${startup_gh_arch}/bin/gh" "$startup_root/runtime/bin/gh"
        ln -s "$startup_root/runtime/bin/gh" "$startup_gh_target"
      }
      startup_run_step "Installing GitHub CLI" "GitHub CLI ready" startup_install_github_cli
    fi
    if ! startup_check_github_connection; then
      if [ -n "${GH_TOKEN:-}" ] || [ -n "${GITHUB_TOKEN:-}" ]; then
        echo "CLI installed. The supplied GitHub token could not authenticate. Update GH_TOKEN or GITHUB_TOKEN and retry." >&2
        return 1
      fi
      printf '\n  Sign in to connect GitHub.\n\n'
      if ! gh auth login -h github.com -p https -s repo,workflow,read:packages,write:packages; then
        echo "CLI installed. GitHub is not connected. Retry this installer with --onboard when ready." >&2
        return 1
      fi
      if ! startup_check_github_connection; then
        echo "CLI installed. GitHub connection could not be verified. Check your connection and retry with --onboard." >&2
        return 1
      fi
    fi
    gh auth setup-git
    # This doctor profile belongs to the companion CLI release. Never run the
    # older full-stack doctor here: it requires SSH/Chrome before target choice.
    if ! "$startup_target" doctor --help | grep -q -- '--provider'; then
      echo "CLI installed and GitHub connected. This CLI release does not yet support the new setup flow." >&2
      echo "Update after the onboarding CLI release is published. Existing command: startup bootstrap" >&2
      return 1
    fi
    until "$startup_target" doctor; do
      echo "CLI installed. GitHub or Git setup is incomplete; follow the guidance above."
      read -r -p "Press Return to check again (Ctrl-C to stop). "
    done
    echo "✓ Setup complete."
    printf '\n  %sReady for your next idea.%s\n\n' "$startup_emphasis" "$startup_reset"
    if "$startup_agent_skill"; then
      read -r -p "Teach your coding agent (Claude Code, Codex, OpenCode) to use startup? [y/N] " startup_answer
      case "$startup_answer" in
        [yY]*) "$startup_target" skills install || echo "Skipped. Later: startup skills install" ;;
      esac
    fi
    read -r -p "Create a startup now? [y/N] " startup_answer
    case "$startup_answer" in
      [yY]*)
        echo "Next: startup name → template → project folder → hosting → GitHub account → review and create."
        if ! "$startup_target" bootstrap; then
          echo "CLI setup is complete. Project setup did not finish; existing project files are preserved." >&2
          echo "Follow the reported next step, or rerun startup bootstrap with the same project name and folder." >&2
          return 1
        fi
        ;;
      *) echo "Ready when you are. Create a startup with: startup bootstrap" ;;
    esac
  }
  startup_onboarding </dev/tty
else
  printf '\n  %sReady for your next idea.%s\n\n' "$startup_emphasis" "$startup_reset"
  echo "Installed. Next: startup doctor"
  if "$startup_agent_skill"; then
    echo "Using a coding agent? Run: startup skills install"
  fi
fi
if "$startup_needs_new_terminal"; then
  echo "Open a new terminal to use startup."
fi
