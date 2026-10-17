"""Real macOS installer → published CLI → Factory → startup-plan cancellation.

Run with Python 3 on macOS with Git, mise and yq installed. Public
runtime/template downloads are real; only GitHub identity/auth is substituted.
No account, cloud resource or remote repository is created.
"""

import errno
import json
import os
import pty
import re
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.platform != 'darwin':
        raise SystemExit('This E2E check requires macOS.')
    missing = [tool for tool in ('git', 'mise', 'yq') if not shutil.which(tool)]
    if missing:
        raise SystemExit('Install E2E prerequisites: ' + ', '.join(missing))
    with tempfile.TemporaryDirectory(prefix='installer-factory-e2e-') as temporary:
        root = Path(temporary)
        home, binaries, factory = root / 'home', root / 'bin', root / 'my factory'
        (home / '.codex').mkdir(parents=True)
        binaries.mkdir()
        gh = binaries / 'gh'
        gh.write_text("""#!/bin/sh
case "$*" in
  *--version*) echo 'gh identity boundary' ;;
  'auth status'*) echo "- Token scopes: 'repo', 'workflow', 'read:packages'" ;;
  'auth setup-git'*) exit 0 ;;
  *api*user*) echo example-owner ;;
  *) echo 'Unexpected GitHub mutation' >&2; exit 99 ;;
esac
""")
        gh.chmod(0o755)
        environment = {
            **os.environ, 'HOME': str(home), 'SHELL': '/bin/zsh',
            'PATH': str(binaries) + os.pathsep + os.environ['PATH'],
            'MISE_DATA_DIR': os.environ.get('MISE_DATA_DIR', str(Path.home() / '.local/share/mise')),
            'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_AUTHOR_NAME': 'Factory E2E',
            'GIT_AUTHOR_EMAIL': 'test@example.invalid', 'NO_COLOR': '1',
            'GH_TOKEN': '', 'GITHUB_TOKEN': '', 'npm_config_cache': str(root / 'npm-cache'),
        }
        for key in ('CI', 'npm_config_yes', 'NPM_CONFIG_YES'):
            environment.pop(key, None)
        # GIVEN an isolated home and the actual candidate installer.
        pid, terminal = pty.fork()
        if pid == 0:
            os.execve('/bin/bash', ['bash', str(ROOT / 'frontend/public/install.sh'), '--onboard'], environment)
        output = bytearray()
        steps = [
            (b'Factory folder', str(factory).encode() + b'\n'),
            (b'Project name (for example, my-startup)', b'example-app\n'),
            (b'Which stack would you like to start with?', b'3\n'),
            (b'Domain (for example, example.com)', b'app.example.com\n'),
            (b'Create the repository under example-owner/example-app?', b'y\n'),
            (b'Create this project and start setup?', b'n\n'),
        ]
        status = None
        try:
            deadline = time.monotonic() + 360
            # WHEN downloads/setup finish, answer each real terminal prompt and cancel launch.
            while time.monotonic() < deadline:
                if select.select([terminal], [], [], 0.2)[0]:
                    try:
                        chunk = os.read(terminal, 8192)
                    except OSError as exc:
                        if exc.errno == errno.EIO:
                            break
                        raise
                    if not chunk:
                        break
                    output.extend(chunk)
                    if steps and steps[0][0] in output:
                        _, answer = steps.pop(0)
                        os.write(terminal, answer)
            else:
                raise AssertionError('Installer onboarding timed out')
            _, status = os.waitpid(pid, 0)
        finally:
            if status is None:
                os.kill(pid, signal.SIGTERM)
                os.waitpid(pid, 0)
            os.close(terminal)
            print(output.decode())
        text = output.decode()
        # THEN the released CLI, neutral workspace, tooling and skills are present.
        assert os.waitstatus_to_exitcode(status) == 0 and not steps
        assert 'Cancelled. No resources were created.' in text
        assert 'Teach your coding agent' not in text
        launcher = home / '.local/bin/startup'
        result = subprocess.run([str(launcher), 'factory', '--help'], env=environment, text=True, capture_output=True, check=True)
        assert 'onboard' in result.stdout
        registry = json.loads(subprocess.check_output(['yq', '-o=json', '.', str(factory / 'projects.yaml')], text=True))
        assert registry['projects'] == []
        for entry in registry['tooling']:
            assert (factory / 'projects/tooling' / entry['name'] / '.git').is_dir()
        answers = json.loads(subprocess.check_output(['yq', '-o=json', '.', str(factory / '.copier-answers.yml')], text=True))
        assert answers['_src_path'] == 'https://github.com/Deploy-your-Startup/startup-factory-template.git'
        # The released CLI pins its tested Factory template; expect that release.
        factory_help = subprocess.run([str(launcher), 'factory', 'init', '--help'], env=environment, text=True, capture_output=True, check=True)
        pinned = re.search(r'--version TEXT\s+\[default: (v\d+\.\d+\.\d+)\]', factory_help.stdout)
        assert pinned, factory_help.stdout
        assert answers['_commit'] == pinned.group(1)
        assert (home / '.agents/skills/deploy-your-startup/SKILL.md').is_file()
        assert 'sprowi-task — installing... ' in text
        assert 'failed' not in text.lower()
        assert not (factory / 'projects/startups/example-app').exists()
        print('Real installer-to-Factory E2E passed; no cloud resources were created.')


if __name__ == '__main__':
    main()
