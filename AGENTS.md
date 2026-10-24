# Open-VINC Examples

Read README.md and the pinned framework's relevant component contracts first.
Discuss changes before implementation; wait for the owner's explicit 開工 or 動工.
Keep each example focused and explain its ownership, lifecycle and failure behavior.
Use readable C++23 with braces and one statement per line. Check recoverable Results;
do not add framework exceptions or rely on expected::value() throwing.
Do not edit framework/open-vinc or its upstream libraries for an example workaround.
Keep the framework pinned to its reviewed release. Changes require matching documentation.
Validate Debug and Release where available. Tests must bound waits and clean up children.
Document platform evidence precisely; do not claim unexecuted Linux/macOS verification.
Record unresolved findings in README.md. Do not push without the owner's instruction.
