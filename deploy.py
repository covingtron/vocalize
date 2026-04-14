# pyrefly: ignore[unexpected-keyword]
"""Pyinfra deployment script for voicemode dependencies on Ubuntu."""
# pyright: reportCallIssue=false

from io import StringIO

from pyinfra.operations import apt, files, server

# Install and configure ffmpeg
apt.packages(
    # pyrefly: ignore[unexpected-keyword]
    name='Install ffmpeg',
    packages=['ffmpeg'],
    update=True,
    _sudo=True,  # pyrefly: ignore[unexpected-keyword]
)

# Install and configure docker-ce on Ubuntu
server.shell(
    # pyrefly: ignore[unexpected-keyword]
    name='Install docker-ce',
    commands=[
        'curl -fsSL https://get.docker.com -o get-docker.sh',
        'sh get-docker.sh',
        'usermod -aG docker ubuntu',
    ],
    _sudo=True,  # pyrefly: ignore[unexpected-keyword]
)

# Download whisper and vad models
models_dir = '/home/ubuntu/.voicemode/models'
whisper_dir = f'{models_dir}/whisper'
vad_dir = f'{models_dir}/vad'

for d in [models_dir, whisper_dir, vad_dir]:
    files.directory(
        # pyrefly: ignore[unexpected-keyword]
        name=f'Ensure directory {d}',
        path=d,
        present=True,
        user='ubuntu',
        group='ubuntu',
        mode='0755',
    )

files.download(
    # pyrefly: ignore[unexpected-keyword]
    name='Download Whisper base model',
    src='https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin',
    dest=f'{whisper_dir}/ggml-base.en.bin',
    user='ubuntu',
    group='ubuntu',
)

files.download(
    # pyrefly: ignore[unexpected-keyword]
    name='Download Silero VAD model',
    src='https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx',
    dest=f'{vad_dir}/silero_vad.onnx',
    user='ubuntu',
    group='ubuntu',
)

# Write user systemd unit file
systemd_dir = '/home/ubuntu/.config/systemd/user'
files.directory(
    # pyrefly: ignore[unexpected-keyword]
    name='Ensure systemd user directory exists',
    path=systemd_dir,
    present=True,
    user='ubuntu',
    group='ubuntu',
    mode='0755',
)

systemd_unit = """[Unit]
Description=VoiceMode Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/env python3 -m voicemode
Restart=on-failure
RestartSec=10
Environment="PATH=%h/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="VOICEMODE_MODELS_DIR=%h/.voicemode/models"

[Install]
WantedBy=default.target
"""

files.put(
    # pyrefly: ignore[unexpected-keyword]
    name='Write user systemd unit file',
    src=StringIO(systemd_unit),
    dest=f'{systemd_dir}/voicemode.service',
    user='ubuntu',
    group='ubuntu',
    mode='0644',
)

server.shell(
    # pyrefly: ignore[unexpected-keyword]
    name='Reload systemd user daemon',
    commands=['systemctl --user daemon-reload'],
    # pyrefly: ignore[unexpected-keyword]
    _su_user='ubuntu',
)
