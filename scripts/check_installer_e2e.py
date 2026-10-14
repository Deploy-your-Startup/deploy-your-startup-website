"""Run on macOS with uv and a real CLI checkout: python3 scripts/check_installer_e2e.py <cli-repo>."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    repo = Path(__file__).resolve().parents[1]
    cli = Path(sys.argv[1]).resolve()
    uv = shutil.which('uv')
    if sys.platform != 'darwin' or not uv:
        raise SystemExit('This E2E check requires macOS and uv.')
    revision = subprocess.check_output(
        ['git', '-C', str(cli), 'rev-parse', 'HEAD'], text=True,
    ).strip()
    python_dir = subprocess.check_output([uv, 'python', 'dir'], text=True).strip()
    cache_dir = subprocess.check_output([uv, 'cache', 'dir'], text=True).strip()

    # GIVEN real uv, the real CLI at a fixed revision and an isolated user home.
    with tempfile.TemporaryDirectory(prefix='startup-installer-e2e-') as directory:
        root = Path(directory)
        home, bins = root / 'home', root / 'bin'
        home.mkdir()
        bins.mkdir()
        wrapper = bins / 'uv'
        # Only replace the GitHub source boundary, never CLI code or uv behavior.
        source = f'git+file://{cli}@{revision}'
        wrapper.write_text(
            f'#!{sys.executable}\nimport os, sys\n'
            f'args = [{source!r} if a.startswith('
            '"git+https://github.com/Deploy-your-Startup/cli@") else a '
            'for a in sys.argv[1:]]\n'
            f'os.execv({uv!r}, [{uv!r}] + args)\n'
        )
        wrapper.chmod(0o755)
        env = {
            **os.environ, 'HOME': str(home), 'SHELL': '/bin/zsh',
            'PATH': f'{bins}:{os.environ["PATH"]}',
            'UV_PYTHON_INSTALL_DIR': python_dir, 'UV_CACHE_DIR': cache_dir,
        }

        def run(*command):
            result = subprocess.run(
                command, env=env, text=True, capture_output=True, timeout=300,
            )
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)
            return result.stdout

        # WHEN installing twice, THEN uv preserves the installed executable.
        executable = home / '.local/share/startup/tools/deploy-your-startup-cli/bin/startup'
        first = run('/bin/bash', str(repo / 'frontend/public/install.sh'))
        assert 'Using existing uv' in first, first
        installed_at = executable.stat().st_mtime_ns
        run('/bin/bash', str(repo / 'frontend/public/install.sh'))
        assert executable.stat().st_mtime_ns == installed_at, 'CLI was reinstalled'
        assert not (home / '.local/share/startup/runtime/bin/uv').exists()
        assert 'bootstrap' in run(str(home / '.local/bin/startup'), '--help')
        assert (home / '.zshrc').read_text().count('# Deploy Your Startup') == 1

        # WHEN uninstalling, THEN only the managed CLI is removed.
        run('/bin/bash', str(repo / 'frontend/public/uninstall.sh'), '--yes')
        assert not (home / '.local/share/startup').exists()
        assert not (home / '.local/bin/startup').exists()
        assert Path(uv).exists()
        assert Path(python_dir).exists()
        assert '# Deploy Your Startup' not in (home / '.zshrc').read_text()
    print('PASS: real uv and CLI install, repeat, launch and uninstall; shared runtime preserved.')


if __name__ == '__main__':
    main()
