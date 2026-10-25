"""Drive the real central application and wait for each tutorial's output."""
from pathlib import Path
import os
import queue
import re
import signal
import subprocess
import sys
import threading
import time

COMMAND_TIMEOUT = 10


class Shell:
    def __init__(self, app, interpreter):
        self.process = subprocess.Popen(
            [str(app), "--shell-port", "0", "--python", str(interpreter)],
            cwd=app.parent,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            bufsize=1,
            start_new_session=os.name != "nt",
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        self.lines = queue.Queue()
        self.pending = ""
        self.transcript = ""
        self.reader = threading.Thread(target=self.read_output, daemon=True)
        self.reader.start()

    def read_output(self):
        for line in self.process.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def wait_for(self, marker):
        deadline = time.monotonic() + COMMAND_TIMEOUT
        while marker not in self.pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssertionError(f"Timeout waiting for {marker}\n{self.transcript}")
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty as error:
                raise AssertionError(f"Missing {marker}\n{self.transcript}") from error
            if line is None:
                raise AssertionError(f"Exited before {marker}\n{self.transcript}")
            self.transcript += line
            self.pending += line
        end = self.pending.index(marker) + len(marker)
        self.pending = self.pending[end:]

    def command(self, command, expected):
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()
        self.wait_for(expected)

    def finish(self):
        self.command("exit", "All module processes exited")
        if self.process.wait(timeout=COMMAND_TIMEOUT) != 0:
            raise AssertionError(self.transcript)

    def cleanup(self):
        if self.process.poll() is not None:
            return
        try:
            self.process.stdin.write("exit\n")
            self.process.stdin.flush()
            self.process.wait(timeout=COMMAND_TIMEOUT)
        except (OSError, subprocess.TimeoutExpired):
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(self.process.pid), "/T", "/F"],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10,
                )
            else:
                os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait(timeout=COMMAND_TIMEOUT)


def hello(shell):
    shell.wait_for("VINC ready")
    shell.command("helloModule", "Started hello")
    shell.command("help", "hello Running")
    shell.finish()
    assert "hello started" in shell.transcript, shell.transcript
    assert "hello stopped" in shell.transcript, shell.transcript


def counter(shell):
    shell.wait_for("VINC ready")
    shell.command("counterSubscriber", "Started receiver")
    shell.command("counterPublisher", "Started sender")
    shell.command("sender invalid", "sender returned 1")
    shell.command("sender send", "received sequence=1 publisher=sender")
    shell.command("receiver status", "received=1")
    shell.command("sender send", "received sequence=2 publisher=sender")
    shell.command("receiver status", "received=2")
    shell.command("receiver reset extra", "receiver returned 1")
    shell.command("receiver status", "received=2")
    shell.command("receiver reset", "counter reset")
    shell.command("receiver status", "received=0")
    shell.command("receiver unknown", "receiver returned 1")
    shell.command("receiver status extra", "receiver returned 1")
    shell.command("receiver status", "received=0")
    shell.command("sender send", "received sequence=3 publisher=sender")
    shell.command("receiver", "received=1")
    shell.command("help", "sender Running")
    receiver_pid = re.search(r"receiver Running MID=\d+ PID=(\d+)", shell.transcript)
    sender_pid = re.search(r"sender Running MID=\d+ PID=(\d+)", shell.transcript)
    assert receiver_pid and sender_pid, shell.transcript
    assert receiver_pid[1] != sender_pid[1], shell.transcript
    shell.finish()
    assert "stopped sender" in shell.transcript, shell.transcript
    assert "stopped receiver" in shell.transcript, shell.transcript


def main():
    app = Path(sys.argv[1]).resolve()
    interpreter = Path(sys.argv[2]).resolve()
    log = Path(sys.argv[3])
    transcripts = []
    try:
        for scenario in (hello, counter):
            shell = Shell(app, interpreter)
            try:
                scenario(shell)
                print(f"PASS {scenario.__name__}")
            finally:
                shell.cleanup()
                transcripts.append(shell.transcript)
    finally:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("\n".join(transcripts), encoding="utf-8")


if __name__ == "__main__":
    main()
