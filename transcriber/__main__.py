from transcriber.download import download_episode
from transcriber.transcribe import transcribe
from transcriber.group import group
from transcriber.summarise import summarise
from transcriber.frontend import create_html

import json
from pathlib import Path
import logging
import argparse

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S')

def saveToJSON(o, filename, episode_file, tmp=False):
    save_dir = Path(episode_file).parents[0] if not tmp else Path(episode_file).parents[1]
    with open(save_dir/filename, 'w') as f:
        json.dump(o, f, ensure_ascii=False, indent=2)

def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--url', type=str, required=True, help='url of episode mp3 / youtube video')
    p.add_argument('--name', type=str, required=True, help='episode name')
    p.add_argument('--type', type=str, default='podcast', choices=['podcast','youtube'], help='source type')
    p.add_argument('--n_speakers', type=int, required=False, help='number of speakers in episode (leave blank if at all unsure)')
    p.add_argument('--n_topics', type=int, required=False, help='number of topics in episode')
    args = p.parse_args()
    
    logging.info("STAGE: Downloading & formatting audio")
    audio_wav, audio_mp3 = download_episode(args.url, args.name, args.type)

    logging.info("STAGE: Transcribing audio")
    transcript = transcribe(audio_wav, args.n_speakers)

    logging.info("STAGE: Grouping transcript")
    transcript_split = group(transcript['words'], args.n_topics)
    saveToJSON(transcript_split, 'transcript-split.json', audio_wav, True)

    logging.info("STAGE: Summarising transcript groups")
    transcript_full = summarise(transcript_split)
    saveToJSON(transcript_full, 'transcript.json', audio_wav, False)

    logging.info("STAGE: Creating HTML output")
    create_html(transcript_full, audio_mp3)

    logging.info("DONE")

    return transcript_split

if __name__ == '__main__':
    main()