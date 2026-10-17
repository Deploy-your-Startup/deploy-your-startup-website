"""Propose installer pins as pull requests with real Git and a local GitHub stand-in."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/cli_release_pr.sh'

# GitHub is the only boundary replaced: calls are logged and open PRs are fixtures.
GH = '''#!/bin/sh
echo "$*" >> "$GH_CALLS"
case "$*" in
  "pr list --head "*) cat "$GH_OPEN_FOR_HEAD" ;;
  "pr list --state open"*) cat "$GH_OTHER_RELEASE_PRS" ;;
esac
'''


def git(cwd, *args):
    return subprocess.run(['git', *args], cwd=cwd, text=True, capture_output=True, check=True).stdout


class CliReleasePullRequestTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        # GIVEN a website checkout of main with a pushed remote.
        remote, self.checkout = self.root / 'remote.git', self.root / 'site'
        git(self.root, 'init', '-q', '--bare', '-b', 'main', str(remote))
        (self.checkout / 'frontend/public').mkdir(parents=True)
        git(self.checkout, 'init', '-q', '-b', 'main')
        for key, value in [('user.name', 'Website tests'), ('user.email', 'test@example.invalid'), ('commit.gpgsign', 'false')]:
            git(self.checkout, 'config', key, value)
        self.installer = self.checkout / 'frontend/public/install.sh'
        self.installer.write_text('startup_cli_version="v0.1.18"\n')
        git(self.checkout, 'add', '-A')
        git(self.checkout, 'commit', '-qm', 'site')
        git(self.checkout, 'remote', 'add', 'origin', str(remote))
        git(self.checkout, 'push', '-q', 'origin', 'main')
        self.remote = remote
        tools = self.root / 'tools'
        tools.mkdir()
        (tools / 'gh').write_text(GH)
        (tools / 'gh').chmod(0o755)
        self.calls = self.root / 'gh-calls'
        self.open_for_head = self.root / 'open-for-head'
        self.other_release_prs = self.root / 'other-release-prs'
        self.open_for_head.write_text('0\n')
        self.other_release_prs.write_text('')
        self.env = {**os.environ, 'PATH': f'{tools}:{os.environ["PATH"]}', 'GH_CALLS': str(self.calls),
                    'GH_OPEN_FOR_HEAD': str(self.open_for_head), 'GH_OTHER_RELEASE_PRS': str(self.other_release_prs)}

    def run_script(self, *args):
        return subprocess.run([str(SCRIPT), *args], cwd=self.checkout, env=self.env,
                              text=True, capture_output=True, check=False)

    def gh_calls(self):
        return self.calls.read_text().splitlines() if self.calls.exists() else []

    def test_new_pin_is_proposed_on_a_branch_and_checked_without_touching_main(self):
        # GIVEN the updater changed the pin; WHEN the proposal is opened.
        self.installer.write_text('startup_cli_version="v0.1.19"\n')
        result = self.run_script('open', 'v0.1.19')
        # THEN the pin lives on its release branch, main is unchanged, and checks run there.
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git(self.remote, 'show', 'main:frontend/public/install.sh'), 'startup_cli_version="v0.1.18"\n')
        self.assertEqual(git(self.remote, 'show', 'release/cli-v0.1.19:frontend/public/install.sh'), 'startup_cli_version="v0.1.19"\n')
        self.assertEqual(git(self.remote, 'log', '-1', '--format=%s', 'release/cli-v0.1.19').strip(), 'chore: update installer to CLI v0.1.19')
        calls = self.gh_calls()
        self.assertTrue(any(call.startswith('pr create --base main --head release/cli-v0.1.19 ') for call in calls), calls)
        self.assertEqual(calls[-1], 'workflow run deploy.yml --ref release/cli-v0.1.19')

    def test_an_open_proposal_is_not_repeated(self):
        # GIVEN a PR for this release is already open; WHEN the schedule checks again.
        self.open_for_head.write_text('1\n')
        result = self.run_script('pending', 'v0.1.19')
        # THEN the run reports it as pending; with none open it is not pending.
        self.assertEqual(result.stdout.strip(), 'pending=true')
        self.open_for_head.write_text('0\n')
        self.assertEqual(self.run_script('pending', 'v0.1.19').stdout.strip(), 'pending=false')

    def test_a_newer_release_supersedes_older_proposals(self):
        # GIVEN an older pin proposal is still open; WHEN a newer release is proposed.
        self.other_release_prs.write_text('28\n')
        self.installer.write_text('startup_cli_version="v0.1.20"\n')
        result = self.run_script('open', 'v0.1.20')
        # THEN the older proposal is closed with a pointer to the new release.
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('pr close 28 --comment Superseded by v0.1.20. --delete-branch', self.gh_calls())

    def test_invalid_tags_stop_before_git_or_github(self):
        for args in [('open', 'main'), ('open', 'v0.1.19-rc1'), ('merge', 'v0.1.19')]:
            with self.subTest(args=args):
                result = self.run_script(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Usage:', result.stderr)
        self.assertEqual(self.gh_calls(), [])
        self.assertEqual(git(self.checkout, 'branch', '--show-current').strip(), 'main')


class DeployWorkflowTests(unittest.TestCase):
    def test_scheduled_pin_updates_never_push_to_main_or_deploy_branches(self):
        # GIVEN the protected main branch, WHEN reading the deploy workflow,
        # THEN pins go through the proposal script and only main releases.
        # Plain text, so CI needs no YAML library beyond the standard runner.
        workflow = (ROOT / '.github/workflows/deploy.yml').read_text()
        self.assertNotIn('HEAD:main', workflow)
        self.assertIn("if: github.event_name != 'pull_request' && github.ref == 'refs/heads/main'", workflow)
        self.assertIn('scripts/cli_release_pr.sh open', workflow)
        # A dispatch on a release branch runs the required PR checks.
        self.assertEqual(workflow.count("github.ref != 'refs/heads/main'"), 3)


if __name__ == '__main__':
    unittest.main()
