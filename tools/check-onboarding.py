#!/usr/bin/env python3
"""Run the website's first proxy tutorial with a supplied selected-release binary."""
import argparse
import re
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def request(url):
    with urllib.request.urlopen(url, timeout=2) as response:
        return response.status, response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    runtime = parser.add_mutually_exclusive_group(required=True)
    runtime.add_argument('--binary', type=Path)
    runtime.add_argument('--image', help='Selected official container image')
    args = parser.parse_args()
    binary = str(args.binary.resolve()) if args.binary else None
    version_command = [binary] if binary else ['docker', 'run', '--rm', args.image]
    version = subprocess.check_output(version_command + ['--version'], text=True).strip()
    assert version.startswith('praxis 0.7.2'), f'Expected selected v0.7.2, got {version}'
    tutorial = (ROOT / 'content/guides/first-proxy.md').read_text()
    config = re.search(r'```yaml\n(.*?)\n```', tutorial, re.S).group(1) + '\n'
    with tempfile.TemporaryDirectory(prefix='praxis-tutorial-') as directory:
        work = Path(directory)
        (work / 'index.html').write_text('hello from backend\n')
        config_path = work / 'praxis.yaml'
        config_path.write_text(config)
        def command(path):
            if binary:
                return [binary, '--config', str(path)]
            return ['docker', 'run', '--rm', '--name', work.name, '--network', 'host',
                    '--mount', f'type=bind,source={path},target=/etc/praxis/config.yaml,readonly', args.image]
        subprocess.run(command(config_path) + ['--validate'], check=True)
        denied = work / 'private-endpoints-disabled.yaml'
        denied.write_text(config.replace('allow_private_endpoints: true', 'allow_private_endpoints: false'))
        rejection = subprocess.run(command(denied) + ['--validate'], capture_output=True)
        assert rejection.returncode != 0, 'Loopback upstream should need the tutorial opt-in'
        processes = []
        try:
            with (work / 'servers.log').open('w+') as log:
                processes.append(subprocess.Popen([
                    'python3', '-m', 'http.server', '3000', '--bind', '127.0.0.1',
                    '--directory', directory,
                ], stdout=log, stderr=log))
                processes.append(subprocess.Popen(command(config_path), stdout=log, stderr=log))
                for _ in range(50):
                    if any(p.poll() is not None for p in processes):
                        log.flush()
                        raise AssertionError('Tutorial server exited: ' + (work / 'servers.log').read_text())
                    try:
                        status, body = request('http://127.0.0.1:8080/')
                        break
                    except OSError:
                        time.sleep(0.1)
                else:
                    raise AssertionError('Proxy did not become ready')
                assert status == 200 and body == b'hello from backend\n', (status, body)
                assert request('http://127.0.0.1:3000/') == (200, body)
                print(f'Onboarding passed: {version}; validation, forwarded HTTP 200/body, and private-endpoint guard')
        finally:
            if args.image:
                subprocess.run(['docker', 'stop', '--time', '1', work.name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for process in processes:
                process.terminate()
            for process in processes:
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == '__main__':
    main()
