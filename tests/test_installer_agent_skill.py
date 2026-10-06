"""Run the real installer end to end with local stand-ins for downloads."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

INSTALLER = Path(__file__).resolve().parents[1] / 'frontend/public/install.sh'

# The downloaded uv installer drops a uv that "installs" the CLI stand-in below.
CURL = '''
while [ "$#" -gt 0 ]; do [ "$1" = -o ] && out="$2"; shift; done
cat > "$out" <<'UVINSTALL'
mkdir -p "$UV_UNMANAGED_INSTALL"
printf '#!/bin/sh\\nmkdir -p "$UV_TOOL_BIN_DIR"\\ncp "$FAKE_STARTUP" "$UV_TOOL_BIN_DIR/startup"\\n' > "$UV_UNMANAGED_INSTALL/uv"
chmod +x "$UV_UNMANAGED_INSTALL/uv"
UVINSTALL
'''

# A CLI release with (or without) the `skills` command group.
STARTUP = '''#!/bin/sh
case "$1 $2" in
  "skills --help") [ "$FAKE_SKILLS" = 1 ] ;;
  "skills install") echo "Installed for claude"; mkdir -p "$HOME/.claude/skills/deploy-your-startup" ;;
  "doctor "*) exit 0 ;;
  "bootstrap "*) echo "BOOTSTRAP STARTED" ;;
  *) exit 0 ;;
esac
'''


class InstallerAgentSkillTests(unittest.TestCase):
    def install(self, *args, skills=True, agents=('.claude',), answers=''):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools, home = root / 'tools', root / 'home'
            tools.mkdir()
            home.mkdir()
            for agent in agents:
                (home / agent).mkdir(parents=True)
            for name, script in {
                'curl': CURL, 'uname': 'echo Darwin',
                'gh': 'exit 0',
            }.items():
                (tools / name).write_text('#!/bin/sh\n' + script)
                (tools / name).chmod(0o755)
            fake = root / 'startup'
            fake.write_text(STARTUP)
            fake.chmod(0o755)
            command = ['/bin/bash', str(INSTALLER), *args]
            if args:
                # Onboarding reads from the terminal; give it a real pseudo-terminal.
                # Keep its input open until the installer is done: an early EOF
                # reaches the terminal as Ctrl-D and would end the prompt.
                command = ['/bin/sh', '-c', '(printf "%s" "$ANSWERS"; sleep 5) | script -q /dev/null "$@"', 'sh', *command]
            result = subprocess.run(
                command, text=True, capture_output=True,
                check=False, start_new_session=True, timeout=60,
                env={**os.environ, 'HOME': str(home), 'SHELL': '/bin/zsh',
                     'PATH': f'{tools}:{os.environ["PATH"]}',
                     'ANSWERS': answers, 'FAKE_STARTUP': str(fake), 'FAKE_SKILLS': '1' if skills else '0'},
            )
            installed = (home / '.claude/skills/deploy-your-startup').is_dir()
            return result, installed

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
        result, installed = self.install('--onboard', answers='y\n')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('Teach your coding agent', result.stdout)
        self.assertTrue(installed)
        self.assertLess(result.stdout.index('Installed for claude'),
                        result.stdout.index('BOOTSTRAP STARTED'))

    def test_onboarding_skips_skill_by_default(self):
        # GIVEN the same onboarding, WHEN the user just presses Return,
        # THEN nothing is installed and project setup continues.
        result, installed = self.install('--onboard', answers='\n')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse(installed)
        self.assertIn('BOOTSTRAP STARTED', result.stdout)


if __name__ == '__main__':
    unittest.main()
