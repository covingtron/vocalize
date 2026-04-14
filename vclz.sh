# shellcheck shell=bash
# Gemini Skill: Vocalize
#
# Description: Call the `vclz` shell function to receive spoken input from the user.
# The user will speak, and the function will transcribe the audio to text.
#
# Instructions for LLM:
# 1. Run `vclz` in your shell to prompt the user for input.
# 2. Wait for the command to finish. The standard output is the text of what the user said.
# 3. If the output is empty or the user asks to try again, you may retry calling `vclz`.

vclz() {
    local input_audio_path="$1"
    local raw_recording_path=''

    if [ -z "$input_audio_path" ]; then
        raw_recording_path="/tmp/vclz_raw_$$.wav"
        echo '🎙️  Recording... Press ENTER to stop.' >&2

        if command -v ffmpeg >/dev/null 2>&1; then
            local capture_format='pulse'
            local capture_device='default'
            if [ "$(uname)" = 'Darwin' ]; then
                capture_format='avfoundation'
                capture_device=':0'
            fi
            ffmpeg -f "$capture_format" -i "$capture_device" -y "$raw_recording_path" >/dev/null 2>&1 &
        elif command -v rec >/dev/null 2>&1; then
            rec "$raw_recording_path" >/dev/null 2>&1 &
        else
            echo 'Error: ffmpeg or sox (rec) is required to record audio.' >&2
            return 1
        fi

        local process_identifier=$!
        read -r
        kill -INT "$process_identifier" 2>/dev/null || kill "$process_identifier" 2>/dev/null
        wait "$process_identifier" 2>/dev/null

        input_audio_path="$raw_recording_path"
    fi

    local transcoded_audio_path="/tmp/vclz_16000hertz_$$.wav"

    if command -v ffmpeg >/dev/null 2>&1; then
        ffmpeg -i "$input_audio_path" -ar 16000 -ac 1 -c:a pcm_s16le -y "$transcoded_audio_path" >/dev/null 2>&1
    elif command -v sox >/dev/null 2>&1; then
        sox "$input_audio_path" -r 16000 -c 1 -b 16 "$transcoded_audio_path" >/dev/null 2>&1
    else
        cp "$input_audio_path" "$transcoded_audio_path"
    fi

    echo '🧠 Transcribing...' >&2

    local whisper_executable="${WHISPER_CLI:-whisper-cli}"
    local whisper_model_path="${WHISPER_MODEL:-models/ggml-base.en.bin}"
    local whisper_arguments=(
        --model "$whisper_model_path"
        --file "$transcoded_audio_path"
        --output-txt
    )

    local vad_model_path="${VAD_MODEL:-models/ggml-silero-v6.2.0.bin}"
    if [ -n "$vad_model_path" ] && [ -f "$vad_model_path" ]; then
        whisper_arguments+=(--vad -vm "$vad_model_path")
    fi

    "$whisper_executable" "${whisper_arguments[@]}" >/dev/null 2>&1

    local text_output_path="${transcoded_audio_path}.txt"
    if [ -f "$text_output_path" ]; then
        cat "$text_output_path"
        rm -f "$text_output_path"
    else
        echo 'Error: Transcription failed or produced no output.' >&2
    fi

    [ -n "$raw_recording_path" ] && rm -f "$raw_recording_path"
    rm -f "$transcoded_audio_path"
}
