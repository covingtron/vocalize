# Vocalize (`vclz`) Architecture Plan

## Overview
Vocalize (`vclz`) is a minimal command-line interface designed to bridge the gap between Large Language Models (LLMs) executing in a shell environment and the user's local microphone. Instead of relying on MCP (Model Context Protocol) for voice input, LLMs can shell out to the `vclz` command to record and transcribe human speech on-demand.

The tool utilizes `ffmpeg` for recording and transcoding, and `whisper.cpp` for local, offline transcription, avoiding any external APIs or web services.

## Core Components (Working Backwards)

### 1. LLM Prompt / Skill Definition
To enable an LLM (like Gemini or Claude) to use `vclz`, we provide a specific "Skill" or prompt instructions. The LLM needs to know how to invoke the tool and handle the response.

**Prompt Example:**
> **Skill: Vocalize (`vclz`)**
> When you need to ask the user a question and want spoken input instead of typed input, execute the `vclz` command in your shell tool.
> 1. Run `vclz`.
> 2. Wait for the command to exit.
> 3. The standard output (stdout) will contain the exact transcribed text of what the user said.
> 4. If the output is empty or transcription fails, prompt the user visually and retry calling `vclz`.

### 2. Transcription Engine (`whisper.cpp`)
We use the local `whisper-cli` binary.
*   **Models:** We cherry-pick the model handling from `voicemode`, targeting `.bin` ggml models (e.g., `ggml-base.en.bin` or `ggml-tiny.en.bin` for speed).
*   **Execution:** `whisper-cli --model <model_path> --file <transcoded_audio> --output-txt`
*   **Result:** The CLI writes to `<file>.txt`. `vclz` will output this text to stdout and clean up the temporary files.

### 3. Voice Activity Detection (VAD)
To speed up transcription and filter out background noise or silence, `vclz` integrates `whisper.cpp`'s native VAD support.
*   **Model:** Silero VAD (`ggml-silero-v6.2.0.bin`).
*   **Usage:** Passed to whisper-cli via `--vad -vm <path_to_silero_model>`.
*   **Benefit:** Only speech segments are processed by the Whisper model, drastically improving inference time.

### 4. Transcoding (Format Normalization)
`whisper.cpp` strictly requires 16 kHz, 16-bit WAV files.
*   Whether the input is a pre-existing `.opus` / `.wav` file passed as an argument, or a raw recording from the mic, `vclz` normalizes it.
*   **Tooling:** `ffmpeg` is the primary dependency.
*   **Command:** `ffmpeg -i <input> -ar 16000 -ac 1 -c:a pcm_s16le -y <normalized.wav>`
*   **Fallback:** `sox` can be used if `ffmpeg` is unavailable.

### 5. Starting and Stopping Recording
When `vclz` is run without arguments, it defaults to capturing microphone input.
*   **Capture Interface:**
    *   macOS: `ffmpeg -f avfoundation -i ":0"`
    *   Linux: `ffmpeg -f pulse -i default` (or ALSA fallback)
*   **Control Flow:** The script starts the `ffmpeg` recording process in the background, prompts the user visually (`"🎙️ Recording... Press ENTER to stop."`), and waits for a carriage return (`read -r`).
*   **Termination:** Once the user presses ENTER, the script sends `SIGINT` to the background `ffmpeg` process, cleanly finalizing the recording before moving to the transcoding step.

## Non-Goals
*   Text-to-Speech (TTS) response generation. The LLM will respond using standard text/markdown in the chat interface.
*   Cloud/Web API transcription (e.g., OpenAI API). Everything runs locally on-device.
*   Continuous listening. `vclz` is strictly an explicitly invoked, push-to-talk style interaction triggered by the LLM.

## Setup Requirements
1. `ffmpeg` or `sox` installed on the host system.
2. `whisper.cpp` compiled locally (`whisper-cli` accessible in PATH or via ENV var).
3. Downloaded ggml Whisper model and Silero VAD model.
