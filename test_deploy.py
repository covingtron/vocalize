"""Integration tests for the pyinfra deployment script."""

from os import environ
from pathlib import Path
from subprocess import STDOUT, check_output


def test_deploy_dry_run():
    """Ensure the pyinfra script parses correctly and plans the expected operations."""
    pyinfra_cmd = '.venv/bin/pyinfra' if Path('.venv/bin/pyinfra').exists() else 'pyinfra'

    output = check_output(
        [pyinfra_cmd, '@local', 'deploy.py', '--dry'], stderr=STDOUT, env=environ.copy(), text=True
    )

    expected_tasks = [
        'Install ffmpeg',
        'Install docker-ce',
        'Ensure directory /home/ubuntu/.voicemode/models/whisper',
        'Ensure directory /home/ubuntu/.voicemode/models/vad',
        'Download Whisper base model',
        'Download Silero VAD model',
        'Ensure systemd user directory exists',
        'Write user systemd unit file',
        'Reload systemd user daemon',
    ]

    for task in expected_tasks:
        assert task in output
