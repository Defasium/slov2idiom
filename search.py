import pickle
import os
import re
from annoy import AnnoyIndex
import numpy as np
from numpy import diag, sqrt, array
import sentencepiece as spm
from string import punctuation
import joblib


def tokenize_sentence_sp(sentence: str):
    tokens = re.findall(r"\w+(?:'\w+)?|[^\w\s]", sentence.lower())
    tokens = [i for i in tokens
              if i not in punctuation]
    tokens = ' '.join(tokens)
    return SP.id_to_piece(SP.tokenize(tokens))


def svdmap(prompt):
    ts = tokenize_sentence_sp(prompt.lower().strip())
    t_idx = [VOCAB.get(t, NON_REC) for t in ts]
    t_idf = IDF[t_idx].copy()
    t_idf /= sqrt(t_idf.dot(t_idf.T)) # l2 norm
    return ((t_idf.dot(U_RANK[t_idx])).dot(diag(S_RANK)).dot(VH_RANK) + BIAS).dot(INVERSE)


def search_idiom(prompt, num=10):
    idx, dist = UU.get_nns_by_vector(svdmap(prompt), num, include_distances=True)
    return DB[idx]


######################################################################
################# SOME GLOBAL VARIABLES ##############################
######################################################################
SP = spm.SentencePieceProcessor(model_file='data/m.model')
UU = AnnoyIndex(125, 'angular')
UU.load('data/LaBse_CUT_1k.ann') # super fast, will just mmap the file

MODEL = joblib.load('data/svd.gz')
VOCAB = MODEL['map']
IDF = MODEL['idf']
NON_REC = VOCAB['<unk>']
U_RANK = MODEL['u_rank']
S_RANK = MODEL['s_rank']
VH_RANK = MODEL['vh_rank']
BIAS = MODEL['bias']
INVERSE = MODEL['inverse']

DB = []
with open('data/db.txt', 'r', encoding='utf-8') as f:
    for line in f:
       DB.append(line.split('\t'))
DB = array(DB)
