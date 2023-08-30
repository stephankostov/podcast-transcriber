# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/transcribe.ipynb.

# %% auto 0
__all__ = ['batch_size', 'compute_type', 'language', 'device', 'get_tmp_dir', 'whisper_transcribe', 'whisperx_align',
           'diarization_to_df', 'diarize', 'assign_speakers', 'add_missing_field', 'find_first_speaker',
           'add_missing_segment_values', 'add_missing_word_values', 'order_speakers', 'process_transcript',
           'transcribe']

# %% ../nbs/transcribe.ipynb 1
from whisperx import load_model, load_audio, load_align_model, align
from whisperx.diarize import assign_word_speakers
import torch
from pathlib import Path
import json
import pandas as pd
from pyannote.audio import Pipeline

# %% ../nbs/transcribe.ipynb 4
# whisperx config
batch_size = 16
compute_type = "float16"
language = "en"
device = "cuda" if torch.cuda.is_available() else "cpu"

# %% ../nbs/transcribe.ipynb 5
def get_tmp_dir(audio_file): return Path(audio_file).parent

# %% ../nbs/transcribe.ipynb 7
def whisper_transcribe(audio_file, language="en", batch_size=batch_size, compute_type=compute_type, device="cuda", save=True):
    model = load_model("large-v2", device, language=language, compute_type=compute_type)
    audio = load_audio(audio_file)
    transcript = model.transcribe(audio, language=language, batch_size=batch_size)['segments']
    if save: 
        with open(get_tmp_dir(audio_file)/"transcript-whisper.json", "w") as f: 
            json.dump(transcript, f, ensure_ascii=False, indent=2)
    return transcript

# %% ../nbs/transcribe.ipynb 10
def whisperx_align(segments, audio_file, language=language, device="cuda", save=True):
    model, metadata = load_align_model(language_code=language, device=device)
    transcript_aligned = align(segments, model, metadata, audio_file, device=device)
    if save:
        with open(get_tmp_dir(audio_file)/"transcript-whisperx.json", "w") as f: 
            json.dump(transcript_aligned, f, ensure_ascii=False, indent=2)
    return transcript_aligned

# %% ../nbs/transcribe.ipynb 13
def diarization_to_df(diarization):
    df = pd.DataFrame(diarization.itertracks(yield_label=True))
    df['start'] = df[0].apply(lambda x: x.start)
    df['end'] = df[0].apply(lambda x: x.end)
    df.rename(columns={2: "speaker"}, inplace=True)
    return df

def diarize(audio_file, n_speakers, device="cuda", hf_token=None, save=True):
    if hf_token is None: 
        with open(str(Path.home()/".huggingface/token"), "r") as f: hf_token = f.readline()
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization@2.1",
        use_auth_token=hf_token
    ).to(torch.device(device))
    diarization = pipeline(audio_file, num_speakers=n_speakers)
    diarization_df = diarization_to_df(diarization)
    if save: 
        diarization_df.to_csv(get_tmp_dir(audio_file)/"diarization.csv")
    return diarization_df

# %% ../nbs/transcribe.ipynb 16
def assign_speakers(diarization, transcript_whisperx):
    diarized_transcript = assign_word_speakers(
        diarization, transcript_whisperx
    )
    return diarized_transcript

# %% ../nbs/transcribe.ipynb 21
# whisperx has some fields missing, 
# which we added by setting them to their previous value
def add_missing_field(obj, key, prev_value, missing_log=None):
    if not key in obj: 
        obj[key] = prev_value
        if missing_log: missing_log[key].append(obj)
    prev_value = obj[key]
    return obj, prev_value

def find_first_speaker(objects):
    for obj in objects:
        if 'speaker' in obj:
            return obj['speaker']

def add_missing_segment_values(segments):
    prev_speaker = find_first_speaker(segments); prev_start = 0.; prev_end = 0.
    missing_log = { "speaker": [], "start": [], "end": [] }
    for s in segments:
        s, prev_speaker = add_missing_field(s, 'speaker', prev_speaker, missing_log)
        for w in s['words']:
            w, prev_start = add_missing_field(w, 'start', prev_start, missing_log)
            w, prev_end = add_missing_field(w, 'end', prev_end, missing_log)
    return segments, missing_log

def add_missing_word_values(words):
    prev_speaker = find_first_speaker(words); prev_start = 0.; prev_end = 0.
    for w in words:
        w, prev_speaker = add_missing_field(w, 'speaker', prev_speaker)
        w, prev_start = add_missing_field(w, 'start', prev_start)
        w, prev_end = add_missing_field(w, 'end', prev_end)
    return words

# %% ../nbs/transcribe.ipynb 29
def order_speakers(transcript_words):

    # cannot use set as we need to preserve the order of which they appear
    unique_speakers = []
    for speech in transcript_words:
        if speech['speaker'] not in unique_speakers:
            unique_speakers.append(speech['speaker'])
    
    rename_mapping = {speaker:'SPEAKER_0'+str(i) for i, speaker in enumerate(unique_speakers)}

    for word in transcript_words:
        word['speaker'] = rename_mapping[word['speaker']]

    return transcript_words

# %% ../nbs/transcribe.ipynb 31
def process_transcript(transcript):
    return order_speakers(
        add_missing_word_values(
            transcript['word_segments'])
    )

# %% ../nbs/transcribe.ipynb 36
def transcribe(audio_file, n_speakers, device="cuda", save=True):
    transcript_whisper = whisper_transcribe(audio_file=audio_file, device=device)
    transcript_aligned = whisperx_align(transcript_whisper, audio_file, device=device)
    diarization = diarize(audio_file, n_speakers, device)
    transcript_diarized = assign_speakers(diarization, transcript_aligned)
    transcript_processed = process_transcript(transcript_diarized)
    if save:
        with open(get_tmp_dir(audio_file)/'transcript.json', "w") as f:
            json.dump(transcript_processed, f, ensure_ascii=False, indent=2)
    return transcript_processed
