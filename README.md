# Podcast Transcriber

Tool to create written transcripts for podcasts and other interview style audio. 

# Demo

See an example podcast transcript [here.](https://stephankostov.github.io/podcast-transcriber/)

# Introduction

Podcasts are verging on the most popular form of long-form media due to its ease of creation, and consumption by end-users. Originally built to allow for revision and notetaking, now with summarisation features it can also be used to get a quick understanding of a podcast's contents.

# Features

- Audio-to-Text transcription including speaker detection (diarization).
- Automatic topic generation.
- Topic and full-text summarisation.
- Front-end transcript display.
    - Easy to read transcript with summarisation.
    - Episode audio player with word-level seeking.

# How it Works

Use of free publically available AI models that can be run on a local instance.

- Transcription: [`whisperx`](https://github.com/m-bain/whisperX)
    - Open source transcription pipeline combining OpenAI's transcription model [whisper](https://github.com/openai/whisper) with Active Speech Recognition (ASR) to generate accurate word-level timestamps.
- Diarization: [`pyannote`](https://github.com/pyannote/pyannote-audio)
    - Open source model to diarize transcripts.
- Topic Modelling: 
    - Clustering embeddings created by public [sentence embedding model](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) as well as cosine positional embeddings.
- Summarisation: 
    - Use of meta's [`Llama2`](https://ai.meta.com/llama/) LLM to generate titles and summaries for topics.

# Usage

Run the main.py script with the following parameters supplied:
- url
- episode_name
- media_type (podcast/youtube)
- n_speakers (optional)

This will run a pipeline of the mentioned processes, downloading the specified url, and outputting the transcript as an html file that can be viewed through a browser.

# Development

Developed firstly through jupyter notebooks (see each for additional info and design choices). 

These notebooks have each been created as python modules through the [`nbdev`](https://github.com/fastai/nbdev/tree/master) library. This was simply done by tagging the code with required cells with the `#|export` tag.

# Installation

`pip install git+https://github.com/stephankostov/transcriber.git`

Whisper requires ffmpeg and also rust to also be installed. See their installation instructions in their [repo](https://github.com/openai/whisper/blob/main/README.md) for details.

# ToDo

- Pyannote diarization model performs poorly with overlapping speech
    - Look into other diarization models such as nvidia nemo
- Speech segments often wrongly split in between sentences
    - Split speech segments on sentences rather than words
- Topic grouping is rather arbitrary
    - Topics are usually introduced by the interviewer so code a solution that takes this into account in the topic splitting.
