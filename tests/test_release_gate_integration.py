"""Execute the workflow's release selection shell against a real Git checkout."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseGateTests(unittest.TestCase):
    def test_polling_never_deploys_an_unchanged_release(self):
        # GIVEN the actual workflow selection step and a real checkout.
        workflow = (ROOT / ".github/workflows/deploy.yml").read_text()
        step = workflow.split("      - name: Select deployment commit", 1)[1].split("\n  test:", 1)[0]
        script = "\n".join(line[10:] for line in step.split("        run: |\n", 1)[1].splitlines())
        for event in ("schedule", "push", "workflow_dispatch", "pull_request"):
            for updated in ("true", "false"):
                with self.subTest(event=event, updated=updated), tempfile.TemporaryDirectory() as directory:
                    output = Path(directory) / "output"
                    # WHEN GitHub runs the shipped shell for this event and update result.
                    subprocess.run(["bash", "-e", "-c", script], cwd=ROOT, check=True,
                                   env={**os.environ, "GITHUB_EVENT_NAME": event,
                                        "UPDATED": updated, "GITHUB_OUTPUT": str(output)})
                    # THEN only unchanged push/manual runs deploy; an updated pin gets a fresh dispatch.
                    expected = updated == "false" and event in ("push", "workflow_dispatch")
                    self.assertIn("deploy=" + str(expected).lower(), output.read_text())
                    self.assertIn("sha=", output.read_text())


if __name__ == "__main__":
    unittest.main()
