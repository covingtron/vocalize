"""Integration tests for vclz shell function."""

from os import environ
from pathlib import Path
from subprocess import STDOUT, check_output

MOCK_SETUP = """
ffmpeg() {
    while [ $# -gt 0 ]; do
        case "$1" in
            /tmp/vclz_raw_*.wav|/tmp/vclz_16000hertz_*.wav) touch "$1" ;;
        esac
        shift
    done
}
mock_whisper_cli() {
    file=''
    while [ $# -gt 0 ]; do
        if [ "$1" = '--file' ]; then
            file="$2"
        fi
        shift
    done
    echo "${EXPECTED_TRANSCRIPTION:-mocked transcription output}" > "${file}.txt"
}
kill() { true; }
wait() { true; }
export WHISPER_CLI='mock_whisper_cli'
export WHISPER_MODEL='dummy.bin'
export VAD_MODEL=''
"""


def test_vclz_function_loads():
    script = Path('vclz.sh').read_text()
    minimal_environment = {'PATH': environ.get('PATH', '')}
    output = check_output(['sh', '-c', f'{script}\ntype vclz'], env=minimal_environment)

    assert b'vclz is a ' in output or b'function' in output


def test_vclz_with_input_file(tmp_path: Path):
    script = Path('vclz.sh').read_text()
    dummy_input = tmp_path / 'input.wav'
    dummy_input.touch()
    minimal_environment = {'PATH': environ.get('PATH', '')}

    run_script = f"{MOCK_SETUP}\n{script}\nvclz '{dummy_input}'"
    output = check_output(['sh', '-c', run_script], env=minimal_environment, stderr=STDOUT)

    assert b'mocked transcription output\n' in output
    assert b'Transcribing...' in output


def test_vclz_records_when_no_input():
    script = Path('vclz.sh').read_text()
    minimal_environment = {
        'EXPECTED_TRANSCRIPTION': 'spoken words',
        'PATH': environ.get('PATH', ''),
    }

    run_script = f'{MOCK_SETUP}\n{script}\nvclz'
    output = check_output(
        ['sh', '-c', run_script], input=b'\n', env=minimal_environment, stderr=STDOUT
    )

    assert b'Recording... Press ENTER to stop.' in output
    assert b'spoken words\n' in output
    assert b'Transcribing...' in output
