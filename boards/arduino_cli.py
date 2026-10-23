"""Optional local Arduino Library Manager; source builds retain service policy.

No arbitrary CLI arguments, platform installation, upload or CLI build endpoint.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from pathlib import Path

_LOCK = threading.Lock()
DEFAULT_STATE = Path(__file__).resolve().parents[1] / '.state/arduino-cli'
OUTPUT_LIMIT = 1_000_000


def executable():
    """Executable selection is administrator configuration, never request input."""
    candidate = os.environ.get('ARDUINO_CLI_BIN') or shutil.which('arduino-cli')
    if not candidate:
        return None
    path = Path(candidate).expanduser().resolve()
    return str(path) if path.is_file() and os.access(path, os.X_OK) else None


def _run(arguments, state_root=None, timeout=30):
    binary = executable()
    if not binary:
        return {'available': False, 'ok': False, 'diagnostic': 'Arduino CLI is not installed. Set ARDUINO_CLI_BIN to a trusted executable.'}
    root = Path(state_root or os.environ.get('MINA_ARDUINO_CLI_STATE', DEFAULT_STATE)).resolve()
    with _LOCK:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        for name in ('data', 'downloads', 'user', 'tasks'):
            (root / name).mkdir(exist_ok=True, mode=0o700)
        with tempfile.TemporaryDirectory(prefix='cli-', dir=root / 'tasks') as task:
            config = Path(task) / 'arduino-cli.yaml'
            config.write_text(json.dumps({'directories': {key: str(root / key) for key in ('data', 'downloads', 'user')}, 'library': {'enable_unsafe_install': False}, 'board_manager': {'additional_urls': [], 'enable_unsafe_install': False}}))
            # ARDUINO_* variables override config; do not inherit them or tokens.
            env = {key: value for key, value in os.environ.items() if key in {'PATH', 'SystemRoot', 'WINDIR', 'TMP', 'TEMP', 'LANG', 'LC_ALL', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'}}
            env['HOME'] = task
            env['XDG_CACHE_HOME'] = task
            output = [bytearray(), bytearray()]
            limited = threading.Event()
            deadline = time.monotonic() + timeout
            try:
                proc = subprocess.Popen([binary, '--config-file', str(config), '--json', '--no-color', *arguments], cwd=task, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, start_new_session=os.name == 'posix', bufsize=0)
            except OSError as exc:
                return {'available': True, 'ok': False, 'diagnostic': f'Unable to start Arduino CLI: {exc}'}
            def terminate():
                # Descendants may retain pipes even after the CLI parent exits.
                try:
                    if os.name == 'posix':
                        os.killpg(proc.pid, signal.SIGKILL)
                    else:
                        proc.kill()
                except (ProcessLookupError, OSError):
                    pass

            def drain(stream, target):
                while True:
                    chunk = stream.read(8192)
                    if not chunk:
                        break
                    remaining = OUTPUT_LIMIT - len(target)
                    target.extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        limited.set()
                        terminate()
                        break
                stream.close()
            readers = [threading.Thread(target=drain, args=(stream, target), daemon=True) for stream, target in zip((proc.stdout, proc.stderr), output)]
            for reader in readers:
                reader.start()
            timed_out = False
            try:
                proc.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                timed_out = True
                terminate()
            # Drain within the same operation deadline, including when a parent
            # exits successfully but a child continues holding stdout/stderr.
            for reader in readers:
                reader.join(timeout=max(0, deadline - time.monotonic()))
            if any(reader.is_alive() for reader in readers):
                timed_out = True
                terminate()
            # POSIX group kill closes inherited pipe writers. On Windows there
            # is no portable process-tree kill: never block on daemon readers.
            cleanup_deadline = time.monotonic() + .2
            try:
                proc.wait(timeout=max(0, cleanup_deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                timed_out = True
            for reader in readers:
                reader.join(timeout=max(0, cleanup_deadline - time.monotonic()))
            incomplete_cleanup = any(reader.is_alive() for reader in readers)
            stdout, stderr = (value.decode('utf-8', errors='replace') for value in output)
            result = {'available': True, 'ok': proc.returncode == 0 and not limited.is_set() and not timed_out, 'exitCode': proc.returncode, 'stderr': stderr}
            try:
                result['data'] = json.loads(stdout)
                if isinstance(result['data'], dict) and result['data'].get('warnings'):
                    result['warnings'] = result['data']['warnings']
                    result['diagnostic'] = 'Arduino CLI reported warnings; inspect warnings before treating this operation as ready.'
                    if any(str(warning).startswith('Error') for warning in result['warnings']):
                        result['ok'] = False
            except ValueError:
                result['output'] = stdout
            if timed_out:
                result['diagnostic'] = 'Arduino CLI exceeded the operation timeout.'
                if incomplete_cleanup:
                    result['diagnostic'] += ' Descendant pipe cleanup remains incomplete; process-tree termination is unavailable or the descendant escaped its process group.'
            elif limited.is_set():
                result['diagnostic'] = 'Arduino CLI exceeded the output limit.'
            elif proc.returncode:
                result['diagnostic'] = 'Arduino CLI failed; inspect the returned diagnostics. Indexes may need updating in the isolated state.'
            return result


def status(state_root=None):
    return _run(['version'], state_root)


def list_cores(state_root=None):
    return _run(['core', 'list'], state_root)


def list_libraries(state_root=None):
    return _run(['lib', 'list'], state_root)


def search_libraries(query, state_root=None):
    if not isinstance(query, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 _.+-]{0,99}', query):
        raise ValueError('Search must contain 1–100 plain library search characters.')
    return _run(['lib', 'search', query], state_root)


def install_library(name, version, state_root=None):
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 _.-]{0,99}', name) or name != name.strip():
        raise ValueError('An exact Library Manager name is required; URLs, paths and options are unsupported.')
    if not isinstance(version, str) or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?', version):
        raise ValueError('An explicit version such as 1.2.3 is required.')
    # Dependencies each require their own explicit selection; never overwrite.
    return _run(['lib', 'install', '--no-deps', '--no-overwrite', f'{name}@{version}'], state_root, timeout=90)


def compile_sketch(source, board='arduino-uno'):
    """Use the existing dependency/assembly policy, never CLI recipe execution."""
    if board not in {'arduino-uno', 'arduino-nano'}:
        raise ValueError('Source compilation supports only Uno and classic Nano.')
    from .service import compile_sketch as compile_with_policy
    return compile_with_policy(source, board=board)
