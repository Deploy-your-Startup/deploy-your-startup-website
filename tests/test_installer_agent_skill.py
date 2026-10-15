"""Run the real installer end to end with local stand-ins for downloads."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

INSTALLER = Path(__file__).resolve().parents[1] / 'frontend/public/install.sh'

# The downloaded uv installer drops a uv that "installs" the CLI stand-in below.
CURL = '''
while [ "$#" -gt 0 ]; do [ "$1" = -o ] && out="$2"; shift; done
cat > "$out" <<'UVINSTALL'
echo "downloading uv 0.12.23 aarch64-apple-darwin"
echo "everything's installed!"
mkdir -p "$UV_UNMANAGED_INSTALL"
cat > "$UV_UNMANAGED_INSTALL/uv" <<'UV'
#!/bin/sh
case "$*" in
  --version) echo "uv 0.12.23"; exit 0 ;;
  "tool install --help") echo "--managed-python --python --quiet"; exit 0 ;;
esac
for arg in "$@"; do
  [ "$arg" = --quiet ] && quiet=true
done
if [ "${quiet:-false}" = false ]; then
  echo "Downloading Python and CLI dependencies" >&2
fi
echo 'Resolved 52 packages' >&2
echo 'Installed 52 packages' >&2
echo 'warning: commands is not on your PATH; run uv tool update-shell' >&2
mkdir -p "$UV_TOOL_BIN_DIR"
cp "$FAKE_STARTUP" "$UV_TOOL_BIN_DIR/startup"
UV
chmod +x "$UV_UNMANAGED_INSTALL/uv"
cp "$UV_UNMANAGED_INSTALL/uv" "$UV_UNMANAGED_INSTALL/uvx"
for tool in uv uvx; do
  if [ "$(command -v "$tool")" != "$UV_UNMANAGED_INSTALL/$tool" ]; then
    echo "WARN: shadowed $tool" >&2
  fi
done
UVINSTALL
'''

# A CLI release with (or without) the `skills` command group.
STARTUP = '''#!/bin/sh
case "$1 $2" in
  "skills --help") [ "$FAKE_SKILLS" = 1 ] ;;
  "skills install") echo "Installed for claude"; mkdir -p "$HOME/.claude/skills/deploy-your-startup" ;;
  "doctor "*) exit 0 ;;
  "factory --help") [ "${FAKE_FACTORY:-1}" = 1 ] ;;
  "factory onboard") echo "FACTORY ONBOARDING STARTED"; exit "${FAKE_FACTORY_FAILURE:-0}" ;;
  "bootstrap "*) echo "UNEXPECTED DIRECT BOOTSTRAP"; exit 99 ;;
  *) exit 0 ;;
esac
'''


class InstallerAgentSkillTests(unittest.TestCase):
    def install(self, *args, skills=True, agents=('.claude',), answers='', factory=True, factory_failure=False, gh='exit 0', existing_uv=False, install_failure=False, private_uv=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools, home = root / 'tools', root / 'home'
            tools.mkdir()
            home.mkdir()
            for agent in agents:
                (home / agent).mkdir(parents=True)
            for name, script in {
                'curl': CURL, 'uname': 'echo Darwin',
                'gh': gh,
                'uv': ('''case "$*" in
  --version) echo 'uv 0.12.3'; exit 0 ;;
  "tool install --help") echo '--managed-python --python --quiet'; exit 0 ;;
esac
if [ "$FAIL_INSTALL" = 1 ]; then echo 'Download unavailable' >&2; exit 1; fi
echo 'Resolved 52 packages' >&2
echo 'Installed 52 packages' >&2
echo 'warning: commands is not on your PATH; run uv tool update-shell' >&2
mkdir -p "$UV_TOOL_BIN_DIR"
cp "$FAKE_STARTUP" "$UV_TOOL_BIN_DIR/startup"
''' if existing_uv else 'echo WRONG UV >&2; exit 99'),
                'uvx': 'echo WRONG UVX >&2; exit 99',
            }.items():
                (tools / name).write_text('#!/bin/sh\n' + script)
                (tools / name).chmod(0o755)
            if private_uv:
                private = home / '.local/share/startup/runtime/bin'
                private.mkdir(parents=True)
                downloaded = root / 'uv-install.sh'
                # GIVEN the runtime from an earlier installation.
                subprocess.run([str(tools / 'curl'), '-o', str(downloaded)], check=True)
                subprocess.run(['/bin/sh', str(downloaded)], check=True, capture_output=True,
                               env={**os.environ, 'UV_UNMANAGED_INSTALL': str(private)})
            fake = root / 'startup'
            fake.write_text(STARTUP)
            fake.chmod(0o755)
            command = ['/bin/bash', str(INSTALLER), *args]
            if args:
                # Onboarding reads from the terminal; give it a real pseudo-terminal.
                # Keep its input open until the installer is done: an early EOF
                # reaches the terminal as Ctrl-D and would end the prompt.
                # BSD (macOS) and util-linux (CI) spell `script` differently.
                if sys.platform == 'darwin':
                    pty = 'script -q /dev/null "$@"'
                else:
                    pty = 'script -qec "$(printf "%q " "$@")" /dev/null'
                command = ['/bin/bash', '-c', f'(printf "%s" "$ANSWERS"; sleep 5) | {pty}', 'bash', *command]
            result = subprocess.run(
                command, text=True, capture_output=True,
                check=False, start_new_session=True, timeout=60,
                env={**os.environ, 'HOME': str(home), 'SHELL': '/bin/bash',
                     'PATH': f'{tools}:{os.environ["PATH"]}',
                     'FAIL_INSTALL': '1' if install_failure else '0', 'ANSWERS': answers, 'FAKE_STARTUP': str(fake), 'FAKE_SKILLS': '1' if skills else '0', 'FAKE_FACTORY': '1' if factory else '0', 'FAKE_FACTORY_FAILURE': '1' if factory_failure else '0'},
            )
            installed = (home / '.claude/skills/deploy-your-startup').is_dir()
            return result, installed

    def test_install_replaces_unusable_uv_with_private_fallback(self):
        # GIVEN uv and uvx already on PATH,
        # WHEN the real installer runs with local download boundaries,
        # THEN it uses a private fallback and shows concise installation progress.
        result, _ = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('shadowed', result.stderr)
        self.assertNotIn('WRONG UV', result.stderr)
        self.assertNotIn('Downloading Python and CLI dependencies', result.stderr)
        self.assertIn('Installing a compatible uv', result.stdout)
        self.assertIn('Verifying startup', result.stdout)
        self.assertEqual(result.stderr, '')
        for noise in ('downloading uv', "everything's installed!", 'Resolved 52 packages',
                      'Installed 52 packages', 'not on your PATH', 'uv tool update-shell'):
            self.assertNotIn(noise, result.stdout)


    def test_reuses_compatible_uv_without_downloading_another_copy(self):
        # GIVEN a compatible uv, WHEN installing, THEN reuse it without a uv download.
        result, _ = self.install(existing_uv=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Using existing uv', result.stdout)
        self.assertNotIn('Installing a compatible uv', result.stdout)
        self.assertIn('Startup CLI is ready', result.stdout)
        self.assertEqual(result.stderr, '')

    def test_reuses_previous_private_uv(self):
        # GIVEN an earlier private uv, WHEN installing, THEN do not download it again.
        result, _ = self.install(private_uv=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Using existing installer-managed uv', result.stdout)
        self.assertNotIn('Installing a compatible uv', result.stdout)

    def test_failed_install_preserves_diagnostics_and_never_claims_success(self):
        # GIVEN a failed download, WHEN installing, THEN show the underlying error.
        result, _ = self.install(existing_uv=True, install_failure=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Download unavailable', result.stderr)
        self.assertIn('installation failed', result.stderr)
        self.assertNotIn('Startup CLI is ready', result.stdout)

    def test_install_points_agent_users_to_the_skill(self):
        # GIVEN a Mac with Claude Code and a CLI release that ships the skill,
        # WHEN installing without onboarding,
        # THEN the next steps mention the skill without installing it unasked.
        result, installed = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Startup CLI is ready. Next: startup doctor', result.stdout)
        self.assertIn('Using a coding agent? Run: startup skills install', result.stdout)
        self.assertFalse(installed)

    def test_no_hint_for_older_cli_or_without_agents(self):
        # GIVEN an older CLI without the skill, or no coding agent on the Mac,
        # WHEN installing, THEN the installer does not suggest a missing command.
        for options in ({'skills': False}, {'agents': ()}):
            result, _ = self.install(**options)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('startup skills install', result.stdout)

    def test_factory_owns_agent_skill_setup(self):
        # GIVEN a configured coding agent, WHEN onboarding creates the Factory,
        # THEN setup is delegated once without a second skill-install prompt.
        result, installed = self.install('--onboard')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn('Teach your coding agent', result.stdout)
        self.assertFalse(installed)
        self.assertIn('FACTORY ONBOARDING STARTED', result.stdout)

    def test_onboarding_repairs_missing_github_scopes_in_place(self):
        # GIVEN a GitHub login without the workflow scope (a GitHub boundary),
        # WHEN onboarding connects GitHub,
        # THEN the installer requests the scopes itself and names the account.
        calls = Path(tempfile.mkdtemp()) / 'gh-calls'
        gh = f'''echo "$*" >> {calls}
case "$*" in
  "auth status -h github.com --active") echo "  - Token scopes: 'gist', 'repo', 'write:packages'" ;;
  "api user --jq .login") echo example-owner ;;
esac'''
        result, _ = self.install('--onboard', answers='\n', gh=gh)
        self.assertEqual(result.returncode, 0, result.stdout)
        requested = calls.read_text().splitlines()
        self.assertIn('auth refresh -h github.com -s repo,workflow,read:packages,write:packages', requested)
        self.assertIn('Using GitHub account example-owner.', result.stdout)
        self.assertLess(result.stdout.index('Using GitHub account'), result.stdout.index('[2/3] Check this Mac'))
        # The new-terminal hint waits until onboarding no longer needs this one.
        self.assertEqual(result.stdout.count('Open a new terminal to use startup.'), 1)
        self.assertLess(result.stdout.index('FACTORY ONBOARDING STARTED'), result.stdout.index('Open a new terminal'))

    def test_onboarding_keeps_a_complete_github_login(self):
        # GIVEN a GitHub login that already has every required scope,
        # WHEN onboarding connects GitHub, THEN no browser refresh is requested.
        calls = Path(tempfile.mkdtemp()) / 'gh-calls'
        gh = f'''echo "$*" >> {calls}
case "$*" in
  "auth status -h github.com --active") echo "  - Token scopes: 'repo', 'workflow', 'write:packages'" ;;
esac'''
        result, _ = self.install('--onboard', answers='\n', gh=gh)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn('auth refresh', calls.read_text())

    def test_onboarding_lets_the_cli_ask_about_the_domain(self):
        # GIVEN guided onboarding for someone who may not own a domain yet,
        # WHEN project setup starts,
        # THEN the installer does not claim ownership, so the CLI can offer registration.
        result, _ = self.install('--onboard', answers='\n')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('FACTORY ONBOARDING STARTED', result.stdout)
        self.assertNotIn('UNEXPECTED DIRECT BOOTSTRAP', result.stdout)
        self.assertNotIn('--domain-owned', result.stdout)
        self.assertIn('register one during setup', result.stdout)

    def test_factory_capability_is_required_before_handoff(self):
        # GIVEN an older installed CLI, WHEN onboarding reaches the Factory,
        # THEN it stops clearly instead of starting a standalone startup.
        result, _ = self.install('--onboard', answers='\n', factory=False)
        self.assertIn('does not include Factory onboarding', result.stdout)
        self.assertNotIn('FACTORY ONBOARDING STARTED', result.stdout)
        self.assertNotIn('UNEXPECTED DIRECT BOOTSTRAP', result.stdout)

    def test_factory_setup_failure_does_not_claim_completion(self):
        # GIVEN failed workspace setup, WHEN the actual installer hands off,
        # THEN the resume/success message is not printed.
        result, _ = self.install('--onboard', answers='\n', factory_failure=True)
        self.assertIn('FACTORY ONBOARDING STARTED', result.stdout)
        self.assertNotIn('To continue or create another startup:', result.stdout)


if __name__ == '__main__':
    unittest.main()
