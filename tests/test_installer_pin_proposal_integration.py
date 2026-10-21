"""Execute the workflow's installer pin proposal against real Git repositories."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = "v9.9.9"
BRANCH = f"chore/cli-{TAG}"


def proposal_script():
    workflow = (ROOT / ".github/workflows/deploy.yml").read_text()
    step = workflow.split("      - name: Test and propose a new installer pin", 1)[1].split("      - name: ", 1)[0]
    return "\n".join(line[10:] for line in step.split("        run: |\n", 1)[1].splitlines())


class InstallerPinProposalTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.origin = root / "origin.git"
        self.checkout = root / "checkout"
        self.calls = root / "calls"
        # The owner's Git configuration must not change the outcome.
        self.env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                    "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
        self.git(root, "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.git(root, "clone", "-q", str(self.origin), str(self.checkout))
        installer = self.checkout / "frontend/public/install.sh"
        installer.parent.mkdir(parents=True)
        installer.write_text('startup_cli_version="v0.1.1"\n')
        # make.sh test is covered by its own checks; here it only records the call.
        make = self.checkout / "make.sh"
        make.write_text(f'#!/bin/bash\necho "make.sh $*" >> {self.calls}\n')
        make.chmod(0o755)
        self.git(self.checkout, "add", "-A")
        self.git(self.checkout, "commit", "-q", "-m", "fixture")
        self.git(self.checkout, "push", "-q", "origin", "main")
        # gh is the GitHub API boundary; the stand-in records its arguments.
        bin_dir = root / "bin"
        bin_dir.mkdir()
        gh = bin_dir / "gh"
        gh.write_text(f'#!/bin/bash\necho "gh $*" >> {self.calls}\n')
        gh.chmod(0o755)
        self.env["PATH"] = f"{bin_dir}:{os.environ['PATH']}"

    def tearDown(self):
        self.directory.cleanup()

    def git(self, cwd, *args):
        return subprocess.run(["git", *args], cwd=cwd, env=self.env, check=True,
                              capture_output=True, text=True).stdout

    def propose(self):
        # WHEN GitHub runs the shipped step after the updater changed the pin.
        (self.checkout / "frontend/public/install.sh").write_text(f'startup_cli_version="{TAG}"\n')
        return subprocess.run(["bash", "-e", "-c", proposal_script()], cwd=self.checkout,
                              env={**self.env, "TAG": TAG}, capture_output=True, text=True)

    def calls_made(self):
        return self.calls.read_text() if self.calls.exists() else ""

    def test_new_release_is_proposed_on_a_branch_and_checked(self):
        # GIVEN a protected main with an older pin and no open proposal.
        main_before = self.git(self.origin, "rev-parse", "main")

        result = self.propose()

        # THEN main is untouched, the branch carries only the pin, and its checks are dispatched.
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git(self.origin, "rev-parse", "main"), main_before)
        changed = self.git(self.origin, "diff", "--name-only", "main", BRANCH).split()
        self.assertEqual(changed, ["frontend/public/install.sh"])
        calls = self.calls_made()
        self.assertIn("make.sh test", calls)
        self.assertIn(f"gh pr create --base main --head {BRANCH}", calls)
        self.assertIn(f"gh workflow run deploy.yml --ref {BRANCH}", calls)

    def test_an_open_proposal_is_not_tested_or_proposed_again(self):
        # GIVEN the proposal branch already exists on the remote.
        self.git(self.checkout, "push", "-q", "origin", f"main:{BRANCH}")

        result = self.propose()

        # THEN the step stops before tests, commits and API calls.
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("already proposed", result.stdout)
        self.assertEqual(self.calls_made(), "")


if __name__ == "__main__":
    unittest.main()
