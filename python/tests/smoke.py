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
EXAMPLE_ROOT = Path(__file__).resolve().parents[2]
STARTUP_SCRIPT = "scripts/rpc-startup.tcl"


class Shell:
    def __init__(self, app, interpreter, startup=None, working_directory=None):
        self.app = app
        self.interpreter = interpreter
        arguments = [str(app), "--shell-port", "0"]
        if interpreter is not None:
            arguments += ["--python", str(interpreter)]
        if startup is not None:
            arguments += ["-S", startup]
        self.process = subprocess.Popen(
            arguments,
            cwd=working_directory or app.parent,
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


def parameters(shell):
    shell.wait_for("VINC ready")
    shell.command("counterSubscriber", "Started receiver")
    shell.command("parameterPublisher", "Started sender")
    shell.command("param set sender.step 1", "Parameter committed (not saved)")
    if "step=1\n" not in shell.transcript:
        shell.wait_for("step=1\n")
    shell.command("help", "sender Running")
    initial_sender = re.search(r"sender Running MID=\d+ PID=(\d+)", shell.transcript)
    assert initial_sender, shell.transcript

    shell.command("param get sender.step", "= 1")
    shell.command("sender send", "received sequence=1 publisher=sender")
    shell.command("param set sender.step 5", "step=5")
    shell.command("param get sender.step", "= 5")
    shell.command("sender send", "received sequence=6 publisher=sender")
    shell.command("sender send", "received sequence=11 publisher=sender")
    shell.command("receiver status", "received=3")

    # Invalid parameter values do not change the live value or stop the Module.
    shell.command("param set sender.step nope", "Invalid Value")
    shell.command("param get sender.step", "= 5")
    shell.command("sender send", "received sequence=16 publisher=sender")
    shell.command("param set sender.step 18446744073709551615", "step=18446744073709551615")
    shell.command("sender send", "sender returned 1")
    assert "sequence limit reached" in shell.transcript, shell.transcript
    shell.command("receiver status", "received=4")
    shell.command("param set sender.step 1", "step=1")
    shell.command("sender send", "received sequence=17 publisher=sender")
    shell.command("receiver status", "received=5")

    shell.command("help", "sender Running")
    sender_pids = re.findall(r"sender Running MID=\d+ PID=(\d+)", shell.transcript)
    assert len(sender_pids) == 2 and sender_pids[0] == sender_pids[1], shell.transcript
    shell.command("param set sender.step 5", "step=5")
    shell.command("param save", "Parameters saved")
    shell.finish()
    assert "stopped sender" in shell.transcript, shell.transcript
    assert "stopped receiver" in shell.transcript, shell.transcript

    # Restart the real central process and both Modules, using the same saved file.
    restarted = Shell(shell.app, shell.interpreter)
    try:
        restarted.wait_for("VINC ready")
        restarted.command("counterSubscriber", "Started receiver")
        restarted.command("parameterPublisher", "Started sender")
        if "step=5\n" not in restarted.transcript:
            restarted.wait_for("step=5\n")
        restarted.command("param get sender.step", "= 5")
        restarted.command("sender send", "received sequence=5 publisher=sender")
        restarted.command("sender send", "received sequence=10 publisher=sender")
        restarted.command("receiver status", "received=2")
        restarted.finish()
        assert "stopped sender" in restarted.transcript, restarted.transcript
        assert "stopped receiver" in restarted.transcript, restarted.transcript
    finally:
        restarted.cleanup()
        shell.transcript += "\nRESTART AFTER PARAM SAVE\n" + restarted.transcript


def rpc(shell):
    shell.wait_for("VINC ready")
    shell.command("rpcPublisher", "Started sender")
    shell.command("help", "sender Running")
    # A missing target is a recoverable RPC failure, not a sender crash.
    shell.command("sender count", "RPC failed:")
    shell.command("rpcSubscriber", "Started receiver")
    shell.command("sender count", "RPC received=0")
    shell.command("sender count extra", "sender returned 1")
    shell.command("sender invalid", "sender returned 1")
    shell.command("sender send", "received sequence=1 publisher=sender")
    shell.command("sender count", "RPC received=1")
    shell.command("sender send", "received sequence=2 publisher=sender")
    shell.command("sender count", "RPC received=2")
    shell.command("sender count", "RPC received=2")
    shell.command("receiver reset", "counter reset")
    shell.command("sender count", "RPC received=0")
    shell.command("sender send", "received sequence=3 publisher=sender")
    shell.command("sender count", "RPC received=1")
    shell.command("help", "sender Running")
    shell.wait_for("receiver Running")

    sender_pids = re.findall(r"sender Running MID=\d+ PID=(\d+)", shell.transcript)
    receiver_pid = re.search(r"receiver Running MID=\d+ PID=(\d+)", shell.transcript)
    assert len(sender_pids) == 2 and sender_pids[0] == sender_pids[1], shell.transcript
    assert receiver_pid and receiver_pid[1] != sender_pids[-1], shell.transcript
    shell.finish()
    assert "stopped sender" in shell.transcript, shell.transcript
    assert "stopped receiver" in shell.transcript, shell.transcript


def startup_scripts(shell):
    # -S must finish before ordinary terminal input is accepted again.
    shell.wait_for("Script completed: " + STARTUP_SCRIPT)
    shell.command("sender count", "RPC received=0")
    shell.command("sender send", "received sequence=1 publisher=sender")
    shell.command("sender count", "RPC received=1")
    shell.command("srun " + STARTUP_SCRIPT, "Script error in " + STARTUP_SCRIPT)
    # The duplicate receiver name stops the script and leaves existing Modules alive.
    shell.command("sender count", "RPC received=1")
    shell.command("help", "sender Running")
    receiver_pid = re.search(r"receiver Running MID=\d+ PID=(\d+)", shell.transcript)
    sender_pid = re.search(r"sender Running MID=\d+ PID=(\d+)", shell.transcript)
    assert receiver_pid and sender_pid and receiver_pid[1] != sender_pid[1], shell.transcript
    shell.finish()
    assert "ready receiver" in shell.transcript, shell.transcript
    assert "ready sender" in shell.transcript, shell.transcript
    assert "stopped receiver" in shell.transcript, shell.transcript
    assert "stopped sender" in shell.transcript, shell.transcript

    # A new central application can launch the same file interactively with srun.
    interactive = Shell(shell.app, shell.interpreter, working_directory=EXAMPLE_ROOT)
    try:
        interactive.wait_for("VINC ready")
        interactive.command("srun " + STARTUP_SCRIPT, "Script completed: " + STARTUP_SCRIPT)
        interactive.command("sender count", "RPC received=0")
        interactive.command("sender send", "received sequence=1 publisher=sender")
        interactive.command("sender count", "RPC received=1")
        interactive.finish()
        assert "stopped receiver" in interactive.transcript, interactive.transcript
        assert "stopped sender" in interactive.transcript, interactive.transcript
    finally:
        interactive.cleanup()
        shell.transcript += "\nINTERACTIVE SRUN\n" + interactive.transcript


def structured_lines(text, level=None, message=None):
    return [
        line for line in text.splitlines()
        if "origin=structured" in line
        and (level is None or f"level={level}" in line)
        and (message is None or message in line)
    ]


def trace_until(shell, enabled):
    deadline = time.monotonic() + COMMAND_TIMEOUT
    while time.monotonic() < deadline:
        shell.command("sender trace", "trace debug_enabled=")
        states = re.findall(r"trace debug_enabled=([01])", shell.transcript)
        if states[-1] == str(enabled):
            return
    raise AssertionError("Log source level did not reach sender\n" + shell.transcript)


def logging(shell):
    shell.wait_for("VINC ready")
    shell.command("log show on", "Log display on")
    shell.command("log show info", "Log display level updated")
    shell.command("logSubscriber", "Started receiver")
    shell.command("logPublisher", "Started sender")
    shell.command("sender count", "RPC count=0")
    assert structured_lines(shell.transcript, "INFO", "sender started"), shell.transcript
    if not structured_lines(shell.transcript, "INFO", "receiver started"):
        shell.wait_for("receiver started")

    begin = len(shell.transcript)
    shell.command("sender trace", "trace debug_enabled=0")
    shell.command("sender count", "RPC count=0")
    assert not structured_lines(shell.transcript[begin:], "DEBUG"), shell.transcript

    # Showing Debug alone cannot recover messages filtered at the Module source.
    shell.command("log show debug", "Log display level updated")
    begin = len(shell.transcript)
    shell.command("sender trace", "trace debug_enabled=0")
    shell.command("sender count", "RPC count=0")
    assert not structured_lines(shell.transcript[begin:], "DEBUG"), shell.transcript

    shell.command("log level sender debug", "Log source level update queued")
    begin = len(shell.transcript)
    trace_until(shell, 1)
    if not structured_lines(shell.transcript[begin:], "DEBUG", "trace detail"):
        shell.wait_for("trace detail")
    shell.command("sender send", "received sequence=1 publisher=sender")
    shell.command("sender count", "RPC count=1")

    # A later Info record from the same source fences earlier hidden Debug records.
    shell.command("log show info", "Log display level updated")
    begin = len(shell.transcript)
    shell.command("sender trace", "trace debug_enabled=1")
    shell.command("sender count", "RPC count=1")
    assert not structured_lines(shell.transcript[begin:], "DEBUG"), shell.transcript

    shell.command("log show warn", "Log display level updated")
    begin = len(shell.transcript)
    shell.command("sender send", "received sequence=2 publisher=sender")
    shell.command("sender count", "RPC received=2")
    shell.command("sender invalid", "unknown sender command")
    assert structured_lines(shell.transcript[begin:], "WARN", "unknown sender command"), shell.transcript
    assert not structured_lines(shell.transcript[begin:], "INFO"), shell.transcript
    shell.command("sender count missingReceiver", "RPC request failed:")
    assert structured_lines(shell.transcript[begin:], "ERROR", "RPC request failed:"), shell.transcript

    shell.command("log level sender warn", "Log source level update queued")
    trace_until(shell, 0)
    shell.command("log show debug", "Log display level updated")
    begin = len(shell.transcript)
    shell.command("sender count", "RPC received=2")
    shell.command("sender invalid", "unknown sender command")
    assert not structured_lines(shell.transcript[begin:], "INFO"), shell.transcript
    assert not structured_lines(shell.transcript[begin:], "DEBUG"), shell.transcript

    shell.command("log show off", "Log display off")
    shell.command("log level sender debug", "Log source level update queued")
    trace_until(shell, 1)
    begin = len(shell.transcript)
    shell.command("sender count", "RPC received=2")
    shell.command("sender send", "received sequence=3 publisher=sender")
    shell.finish()
    assert not structured_lines(shell.transcript[begin:]), shell.transcript
    assert "Log rejected:" not in shell.transcript, shell.transcript
    assert "stopped sender" in shell.transcript and "stopped receiver" in shell.transcript

    created = set(shell.log_directory.glob("*/vinc-*.log")) - shell.log_files_before
    assert created, "No new log file"
    saved = "\n".join(path.read_text(encoding="utf-8") for path in sorted(created))
    for level, message in [
        ("INFO", "sender started"), ("INFO", "counter received sequence=3"),
        ("DEBUG", "trace detail"), ("WARN", "unknown sender command"),
        ("ERROR", "RPC request failed:"), ("INFO", "sender stopped"),
    ]:
        assert structured_lines(saved, level, message), f"Missing saved {level}: {message}\n{saved}"


def main():
    app = Path(sys.argv[1]).resolve()
    interpreter = None if sys.argv[2] == "-" else Path(sys.argv[2]).resolve()
    log = Path(sys.argv[3])
    transcripts = []
    try:
        scenarios = {
            "hello": hello, "counter": counter, "parameters": parameters,
            "rpc": rpc, "startup": startup_scripts,
            "logging": logging,
        }
        selected = sys.argv[4:] or list(scenarios)
        for name in selected:
            scenario = scenarios[name]
            saved_file = None
            saved_contents = None
            log_directory = None
            log_files_before = set()
            if name in ("parameters", "logging"):
                cache = (app.parent / "CMakeCache.txt").read_text(encoding="utf-8")
                identity = re.search(r"^VINC_NAME:STRING=([A-Za-z0-9_-]+)$", cache, re.MULTILINE)
                if identity is None:
                    raise AssertionError("Cannot locate the example's parameter file")
                if name == "parameters":
                    saved_file = app.parent / "vinc_data" / identity[1] / "params.toml"
                    if saved_file.exists():
                        saved_contents = saved_file.read_bytes()
                else:
                    log_directory = app.parent / "vinc_data" / identity[1] / "logs"
                    log_files_before = set(log_directory.glob("*/vinc-*.log"))
            shell = Shell(
                app, interpreter,
                startup=STARTUP_SCRIPT if name == "startup" else None,
                working_directory=EXAMPLE_ROOT if name == "startup" else None,
            )
            if name == "logging":
                shell.log_directory = log_directory
                shell.log_files_before = log_files_before
            try:
                scenario(shell)
                print(f"PASS {scenario.__name__}")
            finally:
                shell.cleanup()
                transcripts.append(shell.transcript)
                # Restore exactly the settings present before this test owned Vinc.
                if saved_file is not None and "VINC ready" in shell.transcript:
                    if saved_contents is None:
                        saved_file.unlink(missing_ok=True)
                    else:
                        saved_file.write_bytes(saved_contents)
    finally:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("\n".join(transcripts), encoding="utf-8")


if __name__ == "__main__":
    main()
