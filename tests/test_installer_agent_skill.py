"""Run the real installer end to end with local stand-ins for downloads."""
import errno
import os
import pty
import select
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

INSTALLER = Path(__file__).resolve().parents[1] / 'frontend/public/install.sh'

# The downloaded uv installer drops a uv that "installs" the CLI stand-in below.
CURL = '''
while [ "$#" -gt 0 ]; do [ "$1" = -o ] && out="$2"; shift; done
cat > "$out" <<'UVINSTALL'
mkdir -p "$UV_UNMANAGED_INSTALL"
cat > "$UV_UNMANAGED_INSTALL/uv" <<'UV'
#!/bin/sh
for arg in "$@"; do
  [ "$arg" = --quiet ] && quiet=true
done
if [ "${quiet:-false}" = false ]; then
  echo "Downloading Python and CLI dependencies" >&2
fi
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
  "doctor --help") [ "$FAKE_NEW_CLI" = 1 ] && echo "--provider"; exit 0 ;;
  "doctor "*) echo "Checking GitHub and Git only"; exit 0 ;;
  "bootstrap "*) echo "BOOTSTRAP STARTED: $*"; exit "$FAKE_BOOTSTRAP_EXIT" ;;
  *) exit 0 ;;
esac
'''


GH = """
printf '%s\\n' "$*" >> "$GH_CALLS"
case "$1 $2" in
  "auth status") [ "$FAKE_GH_STATE" = connected ] || [ -f "$GH_LOGIN_DONE" ] ;;
  "auth login") [ "$FAKE_GH_STATE" != denied ] || exit 1; touch "$GH_LOGIN_DONE" ;;
  "auth setup-git") exit 0 ;;
  *) exit 99 ;;
esac
"""


def terminal_run(command, environment, answers):
    """Run the actual installer with a controlling terminal and bounded reads."""
    pid, descriptor = pty.fork()
    if pid == 0:
        os.execvpe(command[0], command, environment)
    output = bytearray()
    status = None
    try:
        os.write(descriptor, answers.encode())
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if select.select([descriptor], [], [], 0.1)[0]:
                try:
                    chunk = os.read(descriptor, 65536)
                except OSError as error:
                    if error.errno == errno.EIO:
                        break
                    raise
                if not chunk:
                    break
                output.extend(chunk)
            if status is None:
                finished, result = os.waitpid(pid, os.WNOHANG)
                if finished:
                    status = result
                # Continue draining terminal output until EIO.
        else:
            raise TimeoutError(output.decode(errors="replace"))
    finally:
        os.close(descriptor)
        if status is None:
            finished, result = os.waitpid(pid, os.WNOHANG)
            if not finished:
                os.kill(pid, 9)
                _, result = os.waitpid(pid, 0)
            status = result
    return subprocess.CompletedProcess(command, os.waitstatus_to_exitcode(status), output.decode(), "")


class InstallerAgentSkillTests(unittest.TestCase):
    def install(self, *args, skills=True, agents=('.claude',), answers='', github='connected', token=False, new_cli=True, bootstrap_exit=0, missing_gh=False, bad_checksum=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools, home = root / 'tools', root / 'home'
            tools.mkdir()
            home.mkdir()
            for agent in agents:
                (home / agent).mkdir(parents=True)
            for utility in ('cp', 'cat', 'chmod', 'mkdir', 'mktemp', 'rm', 'grep', 'mv', 'sh', 'bash', 'git', 'ln', 'install', 'touch', 'unzip', 'shasum', 'readlink', 'awk'):
                source = shutil.which(utility)
                assert source, utility
                (tools / utility).symlink_to(source)
            downloads = CURL
            if missing_gh:
                # Both GitHub's archive and uv installer are download boundaries.
                downloads = '''
case "$*" in
  *gh_*.zip*)
    while [ "$#" -gt 0 ]; do [ "$1" = -o ] && out="$2"; shift; done
    echo synthetic-archive > "$out"
    exit 0 ;;
esac
''' + CURL
                (tools / 'unzip').unlink()
                (tools / 'unzip').write_text('#!/bin/sh\nmkdir -p "$4/gh_2.102.0_macOS_amd64/bin"\ncat > "$4/gh_2.102.0_macOS_amd64/bin/gh" <<\'GH\'\n#!/bin/sh\n' + GH + '\nGH\n')
                (tools / 'unzip').chmod(0o755)
                if not bad_checksum:
                    # Checksum verification is exercised separately with the real
                    # shasum in the tampered-download scenario below.
                    (tools / 'shasum').unlink()
                    (tools / 'shasum').write_text('#!/bin/sh\nread -r checksum archive\n[ "$checksum" = b245f24eb2bf5f75b426b4c26da3651a107f8d5b6f4fddfbfccc5679041378b3 ]\n')
                    (tools / 'shasum').chmod(0o755)
            for name, script in {
                'curl': downloads, 'uname': '[ "$1" = -m ] && echo x86_64 || echo Darwin',
                'uv': 'echo WRONG UV >&2; exit 99',
                'uvx': 'echo WRONG UVX >&2; exit 99',
            }.items():
                (tools / name).write_text('#!/bin/sh\n' + script)
                (tools / name).chmod(0o755)
            if not missing_gh:
                (tools / 'gh').write_text('#!/bin/sh\n' + GH)
                (tools / 'gh').chmod(0o755)
            fake = root / 'startup'
            fake.write_text(STARTUP)
            fake.chmod(0o755)
            command = ['/bin/bash', str(INSTALLER), *args]
            environment = {**os.environ, 'HOME': str(home), 'SHELL': '/bin/bash',
                           'PATH': str(tools), 'FAKE_STARTUP': str(fake),
                           'FAKE_SKILLS': '1' if skills else '0',
                           'FAKE_NEW_CLI': '1' if new_cli else '0',
                           'FAKE_GH_STATE': github, 'GH_CALLS': str(root / 'gh-calls'),
                           'GH_LOGIN_DONE': str(root / 'gh-connected'),
                           'FAKE_BOOTSTRAP_EXIT': str(bootstrap_exit)}
            for name in ('GH_TOKEN', 'GITHUB_TOKEN', 'GH_HOST'):
                environment.pop(name, None)
            if token:
                environment['GH_TOKEN'] = 'synthetic-private-token'
            if args:
                result = terminal_run(command, environment, answers)
            else:
                result = subprocess.run(command, text=True, capture_output=True, check=False,
                                        start_new_session=True, timeout=30, env=environment)
            calls = root / 'gh-calls'
            self.gh_calls = calls.read_text() if calls.exists() else ''
            self.cli_installed = (home / '.local/bin/startup').is_file()
            self.gh_installed = (home / '.local/bin/gh').is_file()
            installed = (home / '.claude/skills/deploy-your-startup').is_dir()
            return result, installed

    def test_install_shows_progress_with_existing_uv(self):
        # GIVEN uv and uvx already on PATH,
        # WHEN the real installer runs with local download boundaries,
        # THEN its private runtime takes precedence and installation stays visible.
        result, _ = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('shadowed', result.stderr)
        self.assertNotIn('WRONG UV', result.stderr)
        self.assertIn('Downloading Python and CLI dependencies', result.stderr)
        self.assertIn('Installing Python 3.14 and Startup CLI', result.stdout)
        self.assertIn('Verifying Startup CLI', result.stdout)

    def test_install_points_agent_users_to_the_skill(self):
        # GIVEN a Mac with Claude Code and a CLI release that ships the skill,
        # WHEN installing without onboarding,
        # THEN the next steps mention the skill without installing it unasked.
        result, installed = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Installed. Next: startup doctor', result.stdout)
        self.assertIn('Using a coding agent? Run: startup skills install', result.stdout)
        self.assertFalse(installed)

    def test_no_hint_for_older_cli_or_without_agents(self):
        # GIVEN an older CLI without the skill, or no coding agent on the Mac,
        # WHEN installing, THEN the installer does not suggest a missing command.
        for options in ({'skills': False}, {'agents': ()}):
            result, _ = self.install(**options)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('startup skills install', result.stdout)

    def test_onboarding_installs_skill_when_user_agrees(self):
        # GIVEN guided onboarding on a Mac with Claude Code,
        # WHEN the user answers yes to the agent question,
        # THEN the skill is installed before project setup starts.
        result, installed = self.install('--onboard', answers='y\ny\n')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('Teach your coding agent', result.stdout)
        self.assertTrue(installed)
        self.assertLess(result.stdout.index('Installed for claude'),
                        result.stdout.index('BOOTSTRAP STARTED'))

    def test_onboarding_skips_skill_by_default(self):
        # GIVEN the same onboarding, WHEN the user just presses Return,
        # THEN nothing is installed and project setup continues.
        result, installed = self.install('--onboard', answers='\ny\n')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse(installed)
        self.assertIn('BOOTSTRAP STARTED', result.stdout)

    def test_onboarding_lets_the_cli_ask_about_the_domain(self):
        # GIVEN guided onboarding for someone who may not own a domain yet,
        # WHEN project setup starts,
        # THEN the installer does not claim ownership, so the CLI can offer registration.
        result, _ = self.install('--onboard', answers='\ny\n')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('BOOTSTRAP STARTED: bootstrap', result.stdout)
        self.assertIn('startup name → template → project folder → hosting → GitHub account → review and create', result.stdout)
        self.assertLess(result.stdout.index('Next: startup name'), result.stdout.index('BOOTSTRAP STARTED'))
        self.assertNotIn('--domain-owned', result.stdout)
        self.assertNotIn('--kind', result.stdout)
        self.assertNotIn('--provider', result.stdout)
        self.assertNotIn('Check this Mac', result.stdout)


    def test_later_finishes_setup_without_starting_a_project(self):
        # GIVEN GitHub is already connected but no SSH/server credentials exist.
        # WHEN declining agent installation and project creation.
        result, _ = self.install('--onboard', answers='n\nn\n')
        # THEN installation succeeds with a concrete command for later.
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('✓ Setup complete.', result.stdout)
        self.assertIn('Ready when you are. Create a startup with: startup bootstrap', result.stdout)
        self.assertNotIn('BOOTSTRAP STARTED', result.stdout)
        self.assertNotIn('auth login', self.gh_calls)
        self.assertTrue(self.cli_installed)

    def test_environment_token_reuses_authentication(self):
        # GIVEN a token provided by an automation environment.
        # WHEN completing setup and postponing project creation.
        result, _ = self.install('--onboard', token=True, answers='n\nn\n')
        # THEN no login is requested and no token is printed.
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn('auth login', self.gh_calls)
        self.assertNotIn('synthetic-private-token', result.stdout + result.stderr)

    def test_new_login_uses_github_cli(self):
        # GIVEN no existing GitHub authentication.
        # WHEN the external GitHub CLI completes its login flow.
        result, _ = self.install('--onboard', github='new', answers='n\nn\n')
        # THEN the native login is used and Git HTTPS credentials are configured.
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('auth login -h github.com -p https -s repo,workflow,read:packages,write:packages', self.gh_calls)
        self.assertIn('auth setup-git', self.gh_calls)

    def test_cancelled_login_preserves_cli_without_claiming_completion(self):
        # GIVEN a user who cancels the GitHub login.
        # WHEN guided installation reaches authentication.
        result, _ = self.install('--onboard', github='denied')
        # THEN the CLI remains installed, but setup is explicitly incomplete.
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.cli_installed)
        self.assertIn('CLI installed. GitHub is not connected.', result.stdout)
        self.assertNotIn('✓ Setup complete.', result.stdout)
        self.assertNotIn('BOOTSTRAP STARTED', result.stdout)

    def test_invalid_environment_token_does_not_open_an_ineffective_login(self):
        # GIVEN an invalid environment token that would override stored credentials.
        # WHEN authentication is checked.
        result, _ = self.install('--onboard', github='denied', token=True)
        # THEN the user is told to replace the token, without exposing it.
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Update GH_TOKEN or GITHUB_TOKEN', result.stdout)
        self.assertNotIn('auth login', self.gh_calls)
        self.assertNotIn('synthetic-private-token', result.stdout)

    def test_failed_project_setup_keeps_successful_installation_distinct(self):
        # GIVEN successful CLI/GitHub setup and a subsequent project failure.
        # WHEN creating a startup.
        result, _ = self.install('--onboard', answers='n\ny\n', bootstrap_exit=1)
        # THEN the failure preserves the installation and reports the next step.
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.cli_installed)
        self.assertIn('CLI setup is complete. Project setup did not finish', result.stdout)
        self.assertIn('same project name and folder', result.stdout)

    def test_old_cli_release_cannot_enter_the_incompatible_flow(self):
        # GIVEN an installer pin that has not yet advanced to the companion release.
        # WHEN attempting guided setup.
        result, _ = self.install('--onboard', new_cli=False)
        # THEN the older full-stack doctor and fixed provider flow are not run.
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('does not yet support the new setup flow', result.stdout)
        self.assertNotIn('BOOTSTRAP STARTED', result.stdout)

    def test_missing_github_cli_is_installed_without_homebrew(self):
        # GIVEN a fresh Mac with neither gh nor Homebrew on PATH.
        # WHEN installing with local download boundaries.
        result, _ = self.install('--onboard', missing_gh=True, answers='n\nn\n')
        # THEN a managed gh is installed and setup completes.
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(self.gh_installed)
        self.assertIn('Installing GitHub CLI', result.stdout)
        self.assertIn('✓ Setup complete.', result.stdout)

    def test_tampered_github_download_is_rejected(self):
        # GIVEN a downloaded archive that does not match the pinned SHA-256.
        # WHEN the real checksum tool checks the downloaded file.
        result, _ = self.install('--onboard', missing_gh=True, bad_checksum=True)
        # THEN no gh executable is installed and setup never claims success.
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse(self.gh_installed)
        self.assertNotIn('✓ Setup complete.', result.stdout)


class UninstallerGitHubCliTests(unittest.TestCase):
    def test_removes_only_its_managed_github_link(self):
        # GIVEN either the installer's managed gh or an independent executable.
        for managed in (True, False):
            with self.subTest(managed=managed), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                runtime = home / '.local/share/startup'
                runtime.mkdir(parents=True)
                (runtime / '.startup-install').write_text('Deploy Your Startup managed installation\n')
                binaries = home / '.local/bin'
                binaries.mkdir(parents=True)
                (binaries / 'startup').write_text('# Deploy Your Startup launcher\n')
                gh = binaries / 'gh'
                if managed:
                    gh.symlink_to(runtime / 'runtime/bin/gh')
                else:
                    gh.write_text('independent GitHub CLI')
                # WHEN running the actual uninstaller in an isolated home.
                result = subprocess.run(
                    ['/bin/bash', str(INSTALLER.with_name('uninstall.sh')), '--yes'],
                    env={**os.environ, 'HOME': str(home)}, text=True,
                    capture_output=True, check=False, timeout=30,
                )
                # THEN only the managed link disappears; external software survives.
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse(runtime.exists())
                self.assertFalse((binaries / 'startup').exists())
                if managed:
                    self.assertFalse(gh.is_symlink())
                else:
                    self.assertEqual(gh.read_text(), 'independent GitHub CLI')


if __name__ == '__main__':
    unittest.main()
