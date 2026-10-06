"""Exercise installer failure paths without installing software or changing accounts."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

INSTALLER = Path(__file__).resolve().parents[1] / 'frontend/public/install.sh'


class InstallerIntegrationTests(unittest.TestCase):
    def run_installer(self, *args, tools=None):
        with tempfile.TemporaryDirectory() as directory:
            for name, script in (tools or {}).items():
                executable = Path(directory, name)
                executable.write_text('#!/bin/sh\n' + script + '\n')
                executable.chmod(0o755)
            return subprocess.run(
                ['/bin/bash', str(INSTALLER), *args], text=True,
                capture_output=True, check=False, start_new_session=True,
                env={**os.environ, 'PATH': directory + ':' + os.environ['PATH']},
            )

    def test_unknown_option_fails_before_installation(self):
        # GIVEN an unsupported option, WHEN running the actual installer,
        # THEN show usage and stop before downloading or installing anything.
        result = self.run_installer('--unknown')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Usage: install.sh [--onboard]', result.stderr)
        self.assertNotIn('Installing', result.stdout)

    def test_onboarding_requires_interactive_terminal(self):
        # GIVEN no controlling terminal, WHEN starting guided onboarding,
        # THEN fail clearly instead of consuming the piped installer as answers.
        result = self.run_installer('--onboard')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Run onboarding from an interactive terminal.', result.stderr)
        self.assertNotIn('Installing', result.stdout)

    def test_unsupported_platform_stops_early(self):
        # GIVEN a Linux host boundary, WHEN installing,
        # THEN explain the supported platform without touching the installation.
        result = self.run_installer(tools={'uname': 'echo Linux'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('supports macOS', result.stderr)

    def test_missing_git_has_an_actionable_next_step(self):
        # GIVEN missing developer tools, WHEN installing on macOS,
        # THEN show the precise prerequisite command before making changes.
        result = self.run_installer(tools={'uname': 'echo Darwin', 'git': 'exit 1'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('xcode-select --install', result.stderr)
        self.assertNotIn('Installing', result.stdout)


if __name__ == '__main__':
    unittest.main()
