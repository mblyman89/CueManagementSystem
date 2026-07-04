"""
A fake paramiko-like SSH client that runs commands as LOCAL subprocesses.

It faithfully reproduces the parts of paramiko's API the controller uses:
  - exec_command(cmd) -> (stdin, stdout, stderr)
  - stdout.channel.recv_ready()
  - stdout.readline()
  - stdout.read()
  - stdin.write(); stdin.flush()
  - get_transport().is_active()

This lets us run the REAL Pi execute_show.py (with mocked RPi.GPIO) driven by
the REAL controller handshake logic, proving both sides speak the same protocol.

Command translation: the controller issues shell commands like
  "python3 ~/execute_show.py /tmp/show_data.json --handshake 2>/tmp/show_execution.log"
  "python3 ~/execute_show.py --now"
  "test -f /tmp/show_data.json && echo 'exists'"
  "tail -n 20 /tmp/show_execution.log"
We map these to local equivalents.
"""
import os
import sys
import subprocess
import shlex
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "repo")
SCRIPT = os.path.join(REPO, "CueManagementSystem", "raspberry_pi", "execute_show.py")
MOCK = os.path.join(HERE, "mock_RPi")


class FakeChannel:
    def __init__(self, proc):
        self._proc = proc
        self._timeout = None

    def settimeout(self, t):
        # Mirror paramiko Channel.settimeout: applied to the underlying stdout
        # pipe so a blocking readline() respects it.
        self._timeout = t
        try:
            # Python file objects don't support socket-style timeouts directly,
            # so the FakeStdout.readline honors self._timeout via select.
            pass
        except Exception:
            pass

    def recv_ready(self):
        # Data is ready if the process has produced a line we can read without
        # blocking. We approximate by checking if stdout buffer has data using
        # select on the underlying fd.
        import select
        if self._proc.stdout is None:
            return False
        r, _, _ = select.select([self._proc.stdout], [], [], 0)
        return bool(r)

    def exit_status_ready(self):
        return self._proc.poll() is not None

    def recv_exit_status(self):
        return self._proc.wait()


class FakeStdout:
    def __init__(self, proc):
        self._proc = proc
        self.channel = FakeChannel(proc)

    def readline(self):
        # Honor the channel timeout the way paramiko does: if no data is
        # available within the timeout, return "" (an empty tick) rather than
        # blocking forever. If timeout is None, block normally.
        import select
        timeout = self.channel._timeout
        if timeout is not None and self._proc.stdout is not None:
            r, _, _ = select.select([self._proc.stdout], [], [], timeout)
            if not r:
                return ""  # timeout tick
        return self._proc.stdout.readline()

    def read(self):
        return self._proc.stdout.read()


class FakeStdin:
    def __init__(self, proc):
        self._proc = proc

    def write(self, data):
        self._proc.stdin.write(data)

    def flush(self):
        self._proc.stdin.flush()


class FakeStderr:
    def __init__(self, proc):
        self._proc = proc

    def read(self):
        try:
            return self._proc.stderr.read()
        except Exception:
            return b""


class FakeTransport:
    def is_active(self):
        return True


class FakeSSHClient:
    def __init__(self, show_file, log_file):
        self.show_file = show_file
        self.log_file = log_file
        self._env = dict(os.environ)
        self._env["PYTHONPATH"] = MOCK + os.pathsep + self._env.get("PYTHONPATH", "")

    def get_transport(self):
        return FakeTransport()

    def exec_command(self, command, timeout=None):
        # Translate the Pi-style command into a local invocation.
        # 1) file existence check
        if command.startswith("test -f"):
            exists = os.path.exists(self.show_file)
            proc = subprocess.Popen(
                ["bash", "-c", f"echo '{'exists' if exists else ''}'"],
                stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            return FakeStdin(proc), FakeStdout(proc), FakeStderr(proc)

        # 2) tail of log
        if command.startswith("tail "):
            proc = subprocess.Popen(
                ["bash", "-c", f"tail -n 20 {shlex.quote(self.log_file)} 2>/dev/null || true"],
                stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            return FakeStdin(proc), FakeStdout(proc), FakeStderr(proc)

        # 3) clock probe: python3 ~/execute_show.py --now
        if "--now" in command:
            proc = subprocess.Popen(
                [sys.executable, SCRIPT, "--now"],
                stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1, env=self._env,
            )
            return FakeStdin(proc), FakeStdout(proc), FakeStderr(proc)

        # 4) handshake launch: python3 ~/execute_show.py <file> --handshake 2>logfile
        if "--handshake" in command:
            # Run with stderr redirected to the log file, line-buffered stdout.
            logf = open(self.log_file, "w")
            proc = subprocess.Popen(
                [sys.executable, SCRIPT, self.show_file, "--handshake"],
                stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=logf,
                text=True, bufsize=1, env=self._env,
            )
            return FakeStdin(proc), FakeStdout(proc), FakeStderr(proc)

        # Fallback: run through bash
        proc = subprocess.Popen(
            ["bash", "-c", command],
            stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        return FakeStdin(proc), FakeStdout(proc), FakeStderr(proc)

    def close(self):
        pass
