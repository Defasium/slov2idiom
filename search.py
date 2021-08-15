from functools import lru_cache
from hashlib import md5
import os
import re
from annoy import AnnoyIndex
import numpy as np
from numpy import diag, sqrt, array, float64
from numpy.random import randint
import sentencepiece as spm
from string import punctuation
import joblib

######################################################################
################# SOME GLOBAL VARIABLES ##############################
######################################################################
SALT = os.environ.get('SALT', '-')
SP = spm.SentencePieceProcessor(model_file='data/m.model')
UU = AnnoyIndex(125, 'angular')
UU.load('data/LaBse_CUT_1k.ann') # super fast, will just mmap the file

MODEL = joblib.load('data/svd.gz')
VOCAB = MODEL['map']
IDF = float64(MODEL['idf'])
NON_REC = VOCAB['<unk>']
U_RANK = float64(MODEL['u_rank'])
S_RANK = float64(MODEL['s_rank'])
VH_RANK = float64(MODEL['vh_rank'])
BIAS = float64(MODEL['bias'])
INVERSE = float64(MODEL['inverse'])

DB = []
with open('data/db.txt', 'r', encoding='utf-8') as f:
    for line in f:
       DB.append(line.strip().split('\t'))
DB = array(DB)

EMOJITABLE = ('1️⃣','2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟')
######################################################################


def tokenize_sentence_sp(sentence: str):
    tokens = re.findall(r"\w+(?:'\w+)?|[^\w\s]", sentence.lower())
    tokens = [i for i in tokens
              if i not in punctuation]
    tokens = ' '.join(tokens)
    return SP.id_to_piece(SP.tokenize(tokens))


@lru_cache(maxsize=100)
def svdmap(prompt):
    ts = tokenize_sentence_sp(prompt.lower().strip())
    t_idx = [VOCAB.get(t, NON_REC) for t in ts]
    t_idf = IDF[t_idx].copy()
    t_idf /= sqrt(t_idf.dot(t_idf.T)) # l2 norm
    return ((t_idf.dot(U_RANK[t_idx])).dot(diag(S_RANK)).dot(VH_RANK) + BIAS).dot(INVERSE)


@lru_cache(maxsize=100)
def search_idiom(prompt, num=10, return_index=False):
    idx, dist = UU.get_nns_by_vector(svdmap(prompt), num, include_distances=True)
    if return_index:
        return DB[idx], make_hash_with(idx, SALT)
    return DB[idx]


def make_hash_with(indices, salt):
    return [make_one_hash(index, salt) for index in indices]


@lru_cache(maxsize=1000)
def make_one_hash(elem, salt=SALT):
    return md5(''.join((str(elem), salt)).encode('utf-8')).hexdigest()


def make_random_hash():
    return make_one_hash(randint(DB.shape[0]))


@lru_cache(maxsize=100)
def find_nn_by_hash(mdhash, num=6, return_index=False):
    idx, dist = UU.get_nns_by_item(HASHMAP.get(mdhash, 0), num, include_distances=True)
    if return_index:
        return DB[idx], make_hash_with(idx, SALT)
    return DB[idx]


def construct_table(rows):
    result = []
    for i, row in enumerate(rows):
        result.append('%s *%s* — %s\n'%(EMOJITABLE[i], row[0].upper(), row[1]))
    return ''.join(result)


def construct_idiom_info(row):
    return '*%s*\n\t%s'%(row[0].upper(), row[1])


HASHMAP = {make_one_hash(i):i for i in range(DB.shape[0])}
