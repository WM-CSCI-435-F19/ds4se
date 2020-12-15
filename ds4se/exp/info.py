# AUTOGENERATED! DO NOT EDIT! File to edit: dev/1.1_exp.info.ipynb (unless otherwise specified).

__all__ = ['logger', 'get_cnts', 'encode_text', 'get_freqs', 'get_dist', 'get_entropies_from_docs',
           'get_entropy_from_docs', 'get_doc_entropies_from_df', 'get_corpus_entropies_from_df',
           'get_system_entropy_from_df', 'shared_cnts_from_docs', 'shared_entropy_from_docs', 'shared_entropy_from_df',
           'info_content', 'get_shared_probs_from_docs']

# Cell
# Imports
import dit
import math
import os
import logging

import matplotlib.pyplot as plt
import pandas as pd
import sentencepiece as sp

from collections import Counter
from pathlib import Path
from scipy.stats import sem, t
from statistics import mean, median, stdev
from tqdm.notebook import tqdm

# Cell
logger = logging.getLogger(__name__)
logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=logging.INFO,
    )

# Cell
def get_cnts(toks, vocab):
    cnt = Counter(vocab)
    for tok in toks:
        cnt[tok] += 1

    return cnt

# Cell
def encode_text(text, model_prefix):
    '''Encodes text using a pre-trained sp model, returns the occurrences of each token in the text'''
    sp_processor = sp.SentencePieceProcessor()
    sp_processor.Load(f"{model_prefix}.model")
    encoding = sp_processor.encode_as_pieces(text)

    vocab = {sp_processor.id_to_piece(id): 0 for id in range(sp_processor.get_piece_size())}
    token_counts = get_cnts(encoding, vocab)
    return token_counts

# Cell
def get_freqs(token_counts):
    num_tokens = sum(token_counts.values())
    frequencies = []
    for token in token_counts:
        frequencies.append((token_counts[token])/num_tokens)

    return frequencies

# Cell
def get_dist(token_counts):
    '''Takes in a counter object of token occurrences, computes the entropy of the corpus that produced it'''
    alphabet = list(set(token_counts.keys()))
    frequencies = get_freqs(token_counts)
#     for token in token_counts:s
#         frequencies.append((token_counts[token])/num_tokens)
#     logging.info(f'alphabet size {len(alphabet)}, freq size {len(frequencies)} alphabet - {list(token_counts.keys())}')
    return dit.ScalarDistribution(alphabet, frequencies)

# Cell
def get_entropies_from_docs(docs, vocab):
    entropies = []
    for doc in tqdm(docs):
        token_counts = get_cnts(doc, vocab)
        entropies.append(dit.shannon.entropy(get_dist(token_counts)))

    return entropies

# Cell
def get_entropy_from_docs(docs, vocab):
    entropies = []
    token_counts = Counter(vocab)
    for doc in tqdm(docs):
        token_counts += get_cnts(doc, vocab)

    return dit.shannon.entropy(get_dist(token_counts))

# Cell
def get_doc_entropies_from_df(df, col, model_path, data_types):
    '''Returns a list of the entropies of each entry in a dataframe column'''
    all_entropies = []
    for data_type in data_types:
        corpus = df.loc[df['data_type'] == data_type]
        entropies = []
        for data in corpus[col]:
            token_counts= encode_text(data, model_path)
            entropies.append(dit.shannon.entropy(get_dist(token_counts)))

        all_entropies.append(entropies)

    return all_entropies

# Cell
def get_corpus_entropies_from_df(df, col, model_path, data_types):
    entropies = []
    for data_type in data_types:
        corpus = df.loc[df['data_type'] == data_type]
        token_counts = Counter()
        for data in corpus[col]:
            token_counts += encode_text(data, model_path)
        entropies.append(dit.shannon.entropy(get_dist(token_counts)))

    return entropies

# Cell
def get_system_entropy_from_df(df, col, model_path):
    token_counts = Counter()
    for data in df[col]:
        token_counts += encode_text(data, model_path)

    return dit.shannon.entropy(get_dist(token_counts))

# Cell
def shared_cnts_from_docs(sys_docs, vocab):
    cnts = []
    for docs in sys_docs:
        token_counts = Counter(vocab)
        for doc in tqdm(docs):
            token_counts += get_cnts(doc, vocab)
        cnts.append(token_counts)

    return cnts

# Cell
def shared_entropy_from_docs(sys_docs, vocab):
    cnts = shared_cnts_from_docs(sys_docs, vocab)
    overlap = set(cnts[0])
    for i, cnt in enumerate(cnts[1:]):
        overlap &= set(cnt)

    overlap = Counter({k: sum(cnts, Counter(vocab)).get(k, 0) for k in list(overlap)})
    return dit.shannon.entropy(get_dist(overlap))

# Cell
def shared_entropy_from_df(df, col, model_path, data_types):
    cnts = []
    for data_type in data_types:
        corpus = df.loc[df['data_type'] == data_type]
        token_counts = Counter()
        for data in corpus[col]:
            token_counts += encode_text(data, model_path)
        cnts.append(token_counts)

    overlap = set(cnts[0])
    for i, cnt in enumerate(cnts[1:]):
        overlap &= set(cnt)

    overlap = Counter({k: sum(cnts, Counter()).get(k, 0) for k in list(overlap)})
    return dit.shannon.entropy(get_dist(overlap))

# Cell
def info_content(freqs):
    tot = 0
    for freq in freqs:
        tot += math.log(1 / freq, 2)
    return tot

# Cell
def get_shared_probs_from_docs(sys_docs, vocab):
    cnts = shared_cnts_from_docs(sys_docs, vocab)
    overlap = set(cnts[0])
    for i, cnt in enumerate(cnts[1:]):
        overlap &= set(cnt)

    all_cnts = sum(cnts, Counter())
    freqs = []
    for tok, freq in zip(all_cnts, get_freqs(all_cnts)):
        if tok in overlap:
            freqs.append(freq)

    return sum(freqs), info_content(freqs) / len(freqs) if len(freqs) != 0 else 0