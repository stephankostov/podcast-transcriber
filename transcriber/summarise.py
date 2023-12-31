# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/summarise.ipynb.

# %% auto 0
__all__ = ['load_llm_pipeline', 'get_base_prompt', 'get_intro_prompt', 'get_standard_prompt', 'format_speech_text',
           'format_summary', 'parse_summary', 'get_topic_summary_prompt', 'summarise_topics',
           'get_whole_summary_prompt', 'summarise_transcript', 'get_roles_prompt', 'markdown_to_dict', 'parse_roles',
           'identify_speakers', 'summarise', 'get_num_tokens', 'chunk_text', 'get_chunk_summary_prompt',
           'get_chain_title_prompt', 'get_topic_title_chain', 'title_topics']

# %% ../nbs/summarise.ipynb 21
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from .group import group_paragraphs_text
import torch
import pandas as pd
import io

# %% ../nbs/summarise.ipynb 24
def load_llm_pipeline(model="meta-llama/Llama-2-13b-chat-hf", cache_dir=None, **pipeline_args): 
    
    repo_branch = "main"

    tokenizer = AutoTokenizer.from_pretrained(model, revision=repo_branch, cache_dir=cache_dir)
    model = AutoModelForCausalLM.from_pretrained(model, revision=repo_branch, cache_dir=cache_dir, load_in_8bit=True, trust_remote_code=True, device_map='auto')

    pipe = pipeline(
        model=model, tokenizer=tokenizer,
        return_full_text=False,  
        task='text-generation',
        # -- model hyperparameters --
        temperature=0.1,  # 'randomness' of outputs, 0.0 is the min and 1.0 the max
        top_p=0.15,  # select from top tokens whose probability add up to this value
        top_k=0,  # select from top 0 tokens (because zero, relies on top_p)
        max_new_tokens=400, 
        repetition_penalty=1.2,  
        **pipeline_args
    )

    return pipe

# %% ../nbs/summarise.ipynb 29
def get_base_prompt(topic_text):
    return f"""

Your answer should be displayed in the following format:

###SECTION###
SPEAKER_00: example text
SPEAKER_01: example text

###SECTION TITLE###
example concise title

###SECTION SUMMARY###
example concise summary paragraph

Now give real titles and summaries for the below:

###SECTION###
{topic_text}

###SECTION TITLE###
"""

def get_intro_prompt(topic_text):
    return "For the following podcast introduction section, give it a title followed by a summary. Both the title and summary should be separated into their own section under the headers delimited by triple hashtags." + get_base_prompt(topic_text)

def get_standard_prompt(topic_text):
    return "You are an AI text summariser who for legal reasons absolutely cannot mention any personal names of the people in the text.\n\nFor the following podcast section, give it a title followed by a summary. Both the title and summary should be separated into their own section under the headers delimited by triple hashtags (###)." + get_base_prompt(topic_text)

# %% ../nbs/summarise.ipynb 30
def format_speech_text(topic): return '\n'.join([speech['label'] + ": " + speech['text'] for speech in topic['groups']])

# %% ../nbs/summarise.ipynb 31
def format_summary(summary):
    summary = summary.replace("'",'"')
    if summary.startswith('"') and summary.endswith('"') and '"' not in summary[1:-2]:
        summary = summary[1:-2]
    return summary

# %% ../nbs/summarise.ipynb 32
def parse_summary(llm_summary):
    split = llm_summary.split("###")
    if len(split) == 3:
        return {
            'title': format_summary(split[0].strip()),
            'summary': format_summary(split[2].strip()),
            'summary_unparsed': llm_summary
        }
    else:
        return {'title': "", 
                'summary': "", 
                'summary_unparsed': llm_summary
            }

# %% ../nbs/summarise.ipynb 33
def get_topic_summary_prompt(topic):
    speech_text = format_speech_text(topic)
    if topic['label'] == 0:
        prompt = get_intro_prompt(speech_text)
    else:
        prompt = get_standard_prompt(speech_text)
    return prompt

# %% ../nbs/summarise.ipynb 34
def summarise_topics(transcript, llm):
    for i, topic in enumerate(transcript):
        prompt = get_topic_summary_prompt(topic)
        summary = parse_summary(
            llm(prompt)[0]['generated_text']
        )
        topic.update(summary)
        torch.cuda.empty_cache()
    return transcript

# %% ../nbs/summarise.ipynb 38
def get_whole_summary_prompt(summarised_topics):
    summaries = '\n\n'.join([topic['summary'] for topic in summarised_topics])
    prompt = f"""Written below are summaries of every topic of a podcast episode. Please write a detailed summary for the whole podcast episode.
    
###SECTION SUMMARIES###
{summaries}

###WHOLE SUMMARY###
"""
    return prompt

# %% ../nbs/summarise.ipynb 39
def summarise_transcript(transcript, llm):
    prompt = get_whole_summary_prompt(transcript)
    print(len(llm.tokenizer.tokenize(prompt)))
    llm.model.config.max_new_tokens = 2048
    summary = llm(prompt)[0]['generated_text']
    return summary

# %% ../nbs/summarise.ipynb 45
def get_roles_prompt(topic): 
    return f"""Below is a transcript of an introduction section from a podcast episode. For each speaker, please identify their name, and whether their role (host, co-host, guest). Note that usually the first name mentioned is the guest which is being introduced by the host speaking. Make sure that you write the host as the first entry in the table, and don't get mixed up between the naming.

For each speaker write your answer in a table format like the example below.

###PODCAST TRANSCRIPT###
SPEAKER_00: Hello I'm here with my guest William Shakespear. My name is Joe Rogan welcome to the podcast.
SPEAKER_01: Thanks Joe, pleasure to be on.

| SPEAKER NUMBER | NAME | ROLE |
| --- | --- | --- |
| SPEAKER_00 | Joe Rogan | Host |
| SPEAKER_01 | William Shakespear | Guest |

Now do it for the below transcript:

###PODCAST TRANSCRIPT###
{format_speech_text(topic)}

| SPEAKER NUMBER | NAME | ROLE |
| --- | --- | --- |
|"""


# %% ../nbs/summarise.ipynb 48
def markdown_to_dict(markdown_table):
    df = pd.read_table(io.StringIO(markdown_table), sep='|')
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.dropna(how='all')
    df = df.dropna(axis=1, how='all')
    df = df.iloc[1:]
    df.columns = df.columns.str.strip()
    dct_list = df.to_dict('records')
    dct = {d['SPEAKER NUMBER']: {k: v for k, v in d.items() if k != 'SPEAKER NUMBER'} for d in dct_list}
    return dct

# %% ../nbs/summarise.ipynb 49
def parse_roles(roles_output, prompt):
    markdown_table = "\n" + "\n".join(prompt.splitlines()[-3:]) + roles_output + "\n"
    dct = markdown_to_dict(markdown_table)
    dct = {k: {k2.lower(): v2 for k2, v2 in v.items()} for k, v in dct.items()}
    return dct

# %% ../nbs/summarise.ipynb 51
def identify_speakers(transcript, llm):
    prompt = get_roles_prompt(transcript[0])
    llm_output = llm(prompt)[0]['generated_text']
    speaker_ids = parse_roles(llm_output, prompt)
    return speaker_ids

# %% ../nbs/summarise.ipynb 56
def summarise(transcript, id_speakers=True):
    llm = load_llm_pipeline(cache_dir="/home/steph/.cache/huggingface/os_models")
    summarised_topics = summarise_topics(transcript, llm)
    summarised_transcript = summarise_transcript(summarised_topics, llm)
    output = {
        'summary': summarised_transcript, 
        'topics': summarised_topics
    }
    if id_speakers: 
        speaker_ids = identify_speakers(transcript, llm)
        output.update({
            'speaker_ids': speaker_ids
        })
    return output

# %% ../nbs/summarise.ipynb 66
def get_num_tokens(text, tokenizer): return len(tokenizer.tokenize(text))

# %% ../nbs/summarise.ipynb 70
def chunk_text(topic_text, chunk_size=4000):
    paragraphs = split_paragraphs_text(topic_text).split("\n\n")
    split_idxs = [0]
    current_length = 0
    for i, paragraph in enumerate(paragraphs):
        current_length += len(paragraph)
        if current_length > chunk_size:
            split_idxs.append(i+1)
            current_length = 0
    if len(split_idxs) > 1: split_idxs.pop()
    chunks = []
    for i, j in zip(split_idxs, split_idxs[1:]+[None]):
        if i > 0: 
            if j:
                chunks.append('\n\n'.join(paragraphs[i-1:j+1]))
            else:
                chunks.append('\n\n'.join(paragraphs[i-1:j]))
        else:
            if j:
                chunks.append('\n\n'.join(paragraphs[i:j+1]))
            else:
                chunks.append('\n\n'.join(paragraphs[i:j]))
    return chunks 

# %% ../nbs/summarise.ipynb 72
def get_chunk_summary_prompt(chunk_text):
    return f"""Write a concise summary of the following:

\"{chunk_text}\"

CONCISE SUMMARY: """

# %% ../nbs/summarise.ipynb 73
def get_chain_title_prompt(topic_text):
    return f"""The following is a series of summaries of a text chapter. Generate a title from these summaries.

It should be displayed in the below format:

###CHAPTER SUMMARIES###
summary of chapter describing why ai is good

another summary of chapter describing why ai is good

###CHAPTER TITLE###
why ai is good

Now try below:

###CHAPTER SUMMARIES###
{topic_text}

###CHAPTER TITLE###

"""

# %% ../nbs/summarise.ipynb 74
def get_topic_title_chain(text, pipe):
    text_chunks = chunk_text(text)
    chunk_summaries = []
    for text_chunk in text_chunks:
        summary = pipe(get_chunk_summary_prompt(text_chunk))[0]['generated_text'].strip()
        chunk_summaries.append(summary)
    title = pipe(get_chain_title_prompt("\n\n".join(chunk_summaries)))[0]['generated_text']
    return title

# %% ../nbs/summarise.ipynb 77
def title_topics(topics, model, tokenizer):
    pipe = pipeline(
        model=model, tokenizer=tokenizer,
        return_full_text=False,  
        task='text-generation',
        # we pass model parameters here too
        # stopping_criteria=stopping_criteria
        temperature=0.1,  # 'randomness' of outputs, 0.0 is the min and 1.0 the max
        top_p=0.15,  # select from top tokens whose probability add up to 15%
        top_k=0,  # select from top 0 tokens (because zero, relies on top_p)
        max_new_tokens=480,  # max number of tokens to generate in the output
        repetition_penalty=1.2  # without this output begins repeating
    )
    for topic in topics:
        topic_text = topic['text']
        if get_num_tokens(topic_text, tokenizer) < 1900: 
            topic['label'] = get_topic_title(topic_text, pipe)
        else:
            print("Topic is larger than the model's context window, running summary chain", topic['label'])
            topic['label'] = get_topic_title_chain(topic_text, pipe)
    return topics
