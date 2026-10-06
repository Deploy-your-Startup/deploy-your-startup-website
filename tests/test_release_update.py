"""Drive the updater against real installer files and synthetic release metadata."""

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseUpdateTests(unittest.TestCase):
    def update(self, tag, **metadata):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            installer = root / 'install.sh'
            original = (ROOT / 'frontend/public/install.sh').read_text()
            # GIVEN a published installer with an older fixed CLI pin.
            original = re.sub(r'startup_cli_version="v[\d.]+"', 'startup_cli_version="v0.1.1"', original)
            installer.write_text(original)
            release = root / 'release.json'
            release.write_text(json.dumps({'tag_name': tag, 'draft': False, 'prerelease': False, **metadata}))
            # WHEN the real updater consumes public release metadata.
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/update_cli_release.py'), '--release', str(release), '--installer', str(installer)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout, installer.read_text(), original

    def test_new_stable_release_changes_only_the_cli_pin(self):
        output, updated, original = self.update('v0.1.3')
        self.assertIn('changed=true', output)
        self.assertEqual(updated, original.replace('startup_cli_version="v0.1.1"', 'startup_cli_version="v0.1.3"'))

    def test_prerelease_draft_and_invalid_tags_are_skipped(self):
        for tag, metadata in [('v0.1.2', {'prerelease': True}), ('v0.1.3', {'draft': True}), ('v0.1.3-rc1', {}), ('main', {})]:
            with self.subTest(tag=tag, metadata=metadata):
                output, updated, original = self.update(tag, **metadata)
                self.assertIn('changed=false', output)
                self.assertEqual(updated, original)

    def test_same_or_older_release_never_downgrades_the_installer(self):
        for tag in ['v0.1.1', 'v0.1.0']:
            output, updated, original = self.update(tag)
            self.assertIn('changed=false', output)
            self.assertEqual(updated, original)

    def test_the_whole_installer_follows_the_single_cli_pin(self):
        # GIVEN a new release, WHEN the updater runs,
        # THEN only the pin changes and no other line names a CLI version.
        _, updated, _ = self.update('v0.1.3')
        self.assertEqual(len(re.findall(r'v\d+\.\d+\.\d+', updated)), 1)
        self.assertIn('cli@$startup_cli_version', updated)
        self.assertIn('Startup CLI $startup_cli_version', updated)

    def test_versions_are_compared_numerically(self):
        output, updated, original = self.update('v0.1.10')
        self.assertIn('changed=true', output)
        self.assertEqual(updated, original.replace('startup_cli_version="v0.1.1"', 'startup_cli_version="v0.1.10"'))
