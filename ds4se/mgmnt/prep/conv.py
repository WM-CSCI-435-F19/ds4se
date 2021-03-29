# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/0.1_mgmnt.prep.conv.ipynb (unless otherwise specified).

__all__ = ['ConventionalPreprocessing', 'open_file', 'get_files', 'get_file_zip', 'loading_artifacts',
           'processing_artifacts']

# Cell
from typing import List, Set, Callable, Tuple, Dict, Optional
import re
from nltk.stem.snowball import SnowballStemmer
import nltk
import pandas as pd
import glob
import os
import pathlib
from string import punctuation
import csv

# Cell
from tensorflow.keras.preprocessing import text
from pathlib import Path
import glob
from datetime import datetime

# Cell
# Imports
import pandas as pd
import sentencepiece as sp
import numpy as np
import json
from pathlib import Path
import sys
import sentencepiece as spm
from tokenizers import ByteLevelBPETokenizer
from tokenizers.processors import BertProcessing

# Cell
import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# Cell
class ConventionalPreprocessing():
    '''NLTK libraries for Conventional Preprocessing'''
    def __init__(self, params, bpe = False):
        self.params = params

        #If BPE provided, then preprocessing with BPE is allowed on CONV
        if bpe:
            self.sp_bpe = spm.SentencePieceProcessor()
            self.sp_bpe.load(params['model_prefix']+'.model')
        else:
            self.sp_bpe = None

        pass

    def bpe_pieces_pipeline(self, doc_list):
        '''Computes BPE preprocessing according to params'''
        encoded_str = ''
        if self.sp_bpe is None:
            logging.info('Provide a BPE Model!')
        else:
            encoded_str = [self.sp_bpe.encode_as_pieces(doc) for doc in doc_list]
        return encoded_str

    #ToDo Transforme it into a For-Comprenhension
    def clean_punctuation(self, token):
        #remove terms !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~0123456789
        return re.sub(r'[^a-zA-Z\s]', ' ', token, re.I|re.A)

    def split_camel_case_token(self, token):
        return re.sub('([a-z])([A-Z])', r'\1 \2', token)

    def remove_terms(self, filtered_tokens):
        remove_terms = punctuation + '0123456789'
        return [token for token in filtered_tokens if token not in remove_terms and len(token)>2 and len(token)<21]

    def stemmer(self, filtered_tokens):
        return [englishStemmer.stem(token) for token in filtered_tokens ]

    def stop_words(self, filtered_tokens):
        stop_words = nltk.corpus.stopwords.words(self.params['language'])
        return [token for token in filtered_tokens if token not in stop_words]

    def basic_pipeline(self, dict_filenames):
        '''@dict_filenames: {filename: code}'''
        pre_process = [( key.replace('.txt', '-pre.txt') , self.clean_punctuation(dict_filenames[key][0])  ) for key in dict_filenames]
        pre_process = [( doc[0] , self.split_camel_case_token(doc[1])  ) for doc in pre_process]
        pre_process = [( doc[0] , doc[1].lower()  ) for doc in pre_process]
        pre_process = [( doc[0] , doc[1].strip()) for doc in pre_process] # Leading whitepsace are removed
        pre_process_tokens = [(doc[0] , nltk.WordPunctTokenizer().tokenize(doc[1])) for doc in pre_process]
        filtered_tokens = [(doc[0], self.stop_words(doc[1]) ) for doc in pre_process_tokens] #Stop Words
        filtered_tokens = [(doc[0], self.stemmer(doc[1]) ) for doc in filtered_tokens] #Filtering Stemmings
        filtered_tokens = [(doc[0], self.remove_terms(doc[1])) for doc in filtered_tokens] #Filtering remove-terms
        pre_process = [(doc[0], ' '.join(doc[1])) for doc in filtered_tokens]
        return pre_process

    def fromdocs_pipeline(self, docs):
        #TODO
        """@tokenized_file: a list of tokens that represents a document/code"""
        pre_process = [ self.clean_punctuation(doc) for doc in docs]
        logging.info('fromtokens_pipeline: clean punctuation')
        pre_process = [ self.split_camel_case_token(doc) for doc in pre_process]
        logging.info('fromtokens_pipeline: camel case')
        pre_process = [ doc.lower() for doc in pre_process]
        logging.info('fromtokens_pipeline: lowe case')
        pre_process = [ doc.strip() for doc in pre_process] # Leading whitepsace are removed
        logging.info('fromtokens_pipeline: white space removed')
        pre_process_tokens = [ nltk.WordPunctTokenizer().tokenize(doc) for doc in pre_process]
        logging.info('fromtokens_pipeline: WordPunctTokenizer')
        filtered_tokens = [ self.stop_words(doc) for doc in pre_process_tokens] #Stop Words
        logging.info('fromtokens_pipeline: Stop words')
        filtered_tokens = [ self.stemmer(doc) for doc in filtered_tokens] #Filtering Stemmings
        logging.info('fromtokens_pipeline: Stemmings')
        filtered_tokens = [ self.remove_terms(doc) for doc in filtered_tokens] #Filtering remove-terms
        logging.info('fromtokens_pipeline: Removed Special Terns')
        pre_process = [ ' '.join(doc) for doc in filtered_tokens]
        logging.info('fromtokens_pipeline END')
        return pre_process

    def frombatch_pipeline(self, batch):
        #TODO
        """@batch: a TensorFlow Dataset Batch"""
        pre_process = [ self.clean_punctuation( doc.decode("utf-8") ) for doc in batch]
        logging.info('frombatch_pipeline: clean punctuation')
        pre_process = [ self.split_camel_case_token(doc) for doc in pre_process]
        logging.info('frombatch_pipeline: camel case')
        pre_process = [ doc.lower() for doc in pre_process]
        logging.info('frombatch_pipeline: lowe case')
        pre_process = [ doc.strip() for doc in pre_process] # Leading whitepsace are removed
        logging.info('frombatch_pipeline: white space removed')
        pre_process_tokens = [ nltk.WordPunctTokenizer().tokenize(doc) for doc in pre_process]
        logging.info('frombatch_pipeline: WordPunctTokenizer')
        filtered_tokens = [ self.stop_words(doc) for doc in pre_process_tokens] #Stop Words
        logging.info('frombatch_pipeline: Stop words')
        filtered_tokens = [ self.stemmer(doc) for doc in filtered_tokens] #Filtering Stemmings
        logging.info('frombatch_pipeline: Stemmings')
        filtered_tokens = [ self.remove_terms(doc) for doc in filtered_tokens] #Filtering remove-terms
        logging.info('frombatch_pipeline: Removed Special Terns')
        #pre_process = [ ' '.join(doc) for doc in filtered_tokens]
        logging.info('frombatch_pipeline [END]')
        return filtered_tokens

    def fromtensor_pipeline(self, ts_x):
        """@ts_x: es un elemento del tensor"""
        #TODO
        pre_process = self.clean_punctuation(ts_x)
        pre_process = self.split_camel_case_token(pre_process)
        pre_process = pre_process.lower()
        pre_process = pre_process.strip()
        pre_process = nltk.WordPunctTokenizer().tokenize(pre_process)
        filtered_tokens = self.stop_words(pre_process)
        filtered_tokens = self.stemmer(filtered_tokens)
        filtered_tokens = self.remove_terms(filtered_tokens)
        pre_process = ' '.join(filtered_tokens)
        logging.info('fromtokens_pipeline END')
        return pre_process

    def SaveCorpus(self, df, language='js', sep=',', mode='a'):
        timestamp = datetime.timestamp(datetime.now())
        path_to_link = self.params['saving_path'] + '['+ self.params['system']  + '-' + language + '-{}].csv'.format(timestamp)

        df.to_csv(path_to_link, header=True, index=True, sep=sep, mode=mode)
        logging.info('Saving in...' + path_to_link)
        pass

    def LoadCorpus(self, timestamp, language='js', sep=',', mode='a'):
        path_to_link = self.params['saving_path'] + '['+ self.params['system']  + '-' + language + '-{}].csv'.format(timestamp)
        return pd.read_csv(path_to_link, header=0, index_col=0, sep=sep)


# Cell
def open_file(f, encoding='utf-8'):
    try:
        #return open(filename, 'r', encoding="ISO-8859-1").read()
        return open(f, 'r', encoding = encoding).read()
    except:
        print("Exception: ", sys.exc_info()[0])

# Cell
def get_files(system, ends):
    path = Path("cisco/CSB-CICDPipelineEdition-master/")
    names = [entry for entry in path.glob('**/*' +ends)]
    filenames = [(filename, os.path.basename(filename), open_file(filename) ) for filename in names]
    return pd.DataFrame( filenames ,columns = ['names','filenames','content'])

# Cell
def get_file_zip(params, ends):
    archive = ZipFile( params['path_zip'], 'r')
    names = [name for name in archive.namelist() if name.endswith(ends)]
    filenames = [(filename, os.path.basename(filename), archive.read(filename) ) for filename in names]
    return pd.DataFrame( filenames ,columns = ['names','filenames','content'])

# Cell
import tensorflow_datasets as tfds

# Cell
def loading_artifacts( params ):
    #Creating the mappings

    df_sys_g = pd.DataFrame( [] ,columns = ['ids','filenames','text']) #global dataframe

    for art in parameters['dataset'].keys():
        sys_names = [[entry for entry in parameters['dataset'][art].glob('**/*' + ex )] for ex in parameters['ends']]
        sys_names = functools.reduce(lambda a,b : a+b,sys_names) #Flatting
        logging.info("artifacts: "  +  str( len(sys_names) ) )
        sys_filenames = [(filename, os.path.basename(filename), open_file(filename, encoding=params['encoding']) ) for filename in sys_names]
        df_sys_l = pd.DataFrame( sys_filenames ,columns = ['ids','filenames','text']) #local dataframe
        df_sys_l['type'] = art
        df_sys_g = pd.concat([df_sys_g, df_sys_l ], ignore_index=True, sort=False)

    return df_sys_g

# Cell
def processing_artifacts( model_prefix, df_sys_all, funct_params ):
    df_sys_all = df_sys_all.copy()
    for bpe in model_prefix.keys(): #BPE Preprocessing
        prep = ConventionalPreprocessing( funct_params( model_prefix[bpe] ) , bpe = True) #Creating the Preprocessing Object
        df_sys_all[ bpe ] = prep.bpe_pieces_pipeline( df_sys_all['text'].values )

    df_sys_all['conv'] = prep.fromdocs_pipeline( df_sys_all['text'].values ) #Conventional Preprocessing
    return df_sys_all, prep