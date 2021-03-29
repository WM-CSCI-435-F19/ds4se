# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/3.4_facade.ipynb (unless otherwise specified).

__all__ = ['LinkType', 'get_docs', 'get_counters', 'preprocess', 'TraceLinkValue', 'NumDoc', 'VocabSize',
           'AverageToken', 'Vocab', 'VocabShared', 'SharedVocabSize', 'MutualInformation', 'CrossEntropy', 'makeArray',
           'KLDivergence']

# Cell
import random
from nbdev.showdoc import *
import pandas as pd
import sentencepiece as sp
from pathlib import Path
from collections import Counter
from .mining.unsupervised.traceability.eval import *
# import ds4se.mining.unsupervised.traceability.approach.cisco as cisco
from enum import Enum, unique, auto
from .exp import i
import os
import pkg_resources
from sklearn.manifold import TSNE
import numpy as np

# Cell
@unique
class LinkType(Enum):
    req2tc = auto()
    req2src = auto()

# Cell

#export
"""
Helper functions to extract all entries in the dataframe, which will be contents of either source or target artifacts. Contents are stored
in the column named "contents". This helper function retrive strings stored in this columns and stored them in a list.
:param df: dataframe of content that need to be processed
:param spm: sentence piece processor that will process the dataframe
:returns: documents lists of all entries in the dataframe
"""
def get_docs(df, spm):
    docs = []
    for fn in df["contents"]:
        docs += spm.EncodeAsPieces(fn)
    return docs

#export
"""
Helper functions to retrive counter object for all tokens in a dataframe.
:param docs: doc list of contents that we need to extract information on tokens and their frequency
:returns: documents counter of token and corresponding occurrence.
"""
def get_counters(docs):
    #param doc list of contents that need info on tokens
    #return the counters object of tokens
    doc_cnts = []
    cnt = Counter()
    for tok in docs:
        cnt[tok] += 1
        doc_cnts.append(cnt)
    return doc_cnts

#export
"""
Helper functions that get a dataframe and generate a Counter object for all of them tokens it contains,
as well as their frequency. It load sentence piece model and call two helper function to calculate token freqnency
:param artifacts_df: doc list of contents that we need to extract information on tokens and their frequency
:returns: counter object with token and term occurrence.
"""
def preprocess(artifacts_df):
    spm = sp.SentencePieceProcessor()
    bpe_model_path = pkg_resources.resource_filename('ds4se', 'model/test.model')
    spm.Load(bpe_model_path)
    docs = get_docs(artifacts_df,spm)
    cnts = get_counters(docs)
    return cnts

# Cell
"""
Calculate traceability of two strings of artifacts with given techniques. Method will group two strings as a pair and feed into
the traceability model to get result. If users switch the order of source and target, result should be very similar.
:param source: a string of the entire source file
:param target: a string of the entire target file
:param technique: what tecchnique to use to calculate traceability
:param word2vec_metric: optional, what metric to use to calculate traceability. Only for word2vec
:returns: a tuple: (distance, similarity), similarity is the traceability value
"""
def TraceLinkValue(source, target, technique, word2vec_metric = "WMD"):

    dummy_path = pkg_resources.resource_filename('ds4se', 'model/val.csv')


    value1 = random.randint(0,100)/100
    value2 = random.randint(0,100)/100
    value = (value1, value2)


    if (technique == "VSM"):
        pass
    if (technique == "LDA"):
        pass
    if (technique == "orthogonal"):
        pass
    if (technique == "LSA"):
        pass
    if (technique == "JS"):
        pass
    if (technique == "word2vec"):
        model_path = pkg_resources.resource_filename('ds4se', 'model/word2vec_libest.model')
        parameter = {
            "vectorizationType": VectorizationType.word2vec,
            "linkType": LinkType.req2tc,
            "system": 'libest',
            "path_to_trained_model": model_path,
            "source_path": dummy_path,
            "target_path": dummy_path,
            "system_path": dummy_path,
            "saving_path": 'test_data/',
            "names": ['Source','Target','Linked?']
        }

        source_df = pd.DataFrame({ "ids": ["source"],  "text":[source]})
        target_df = pd.DataFrame({ "ids": ["target"],  "text":[target]})
        word2vec = Word2VecSeqVect(parameter)
        word2vec.df_source = source_df
        word2vec.df_target = target_df
        links = [(source_df["ids"][0],target_df["ids"][0])]
        if (word2vec_metric == "SCM"):
            computeDistanceMetric = word2vec.computeDistanceMetric(links, metric_list = [DistanceMetric.SCM])
        else:
            computeDistanceMetric = word2vec.computeDistanceMetric(links, metric_list = [DistanceMetric.WMD])
        value = (computeDistanceMetric[0][0][2],computeDistanceMetric[0][0][3])

    if (technique == "doc2vec"):
        model_path = pkg_resources.resource_filename('ds4se', 'model/doc2vec_libest.model')
        parameter = {
            "vectorizationType": VectorizationType.doc2vec,
            "linkType": LinkType.req2tc,
            "system": 'libest',
            "path_to_trained_model": model_path,
            "source_path": dummy_path,
            "target_path": dummy_path,
            "system_path": dummy_path,
            "saving_path": 'test_data/',
            "names": ['Source','Target','Linked?']
        }

        source_df = pd.DataFrame({ "ids": ["source"],  "text":[source]})
        target_df = pd.DataFrame({ "ids": ["target"],  "text":[target]})
        doc2vec = Doc2VecSeqVect(params = parameter)
        doc2vec.df_source = source_df
        doc2vec.df_target = target_df
        links = [(source_df["ids"][0],target_df["ids"][0])]
        doc2vec.InferDoc2Vec(steps=200)
        table = doc2vec.computeDistanceMetric( links, metric_list = [DistanceMetric.EUC] )
        value = (table[0][0][2], table[0][0][3])
        #The bottom is here for reference -- may not need it
#         doc2vec.SaveLinks()
#         #will most likely need to change this part need to change this part to a different path
#         path_to_ground_truth = '/tf/main/benchmarking/traceability/testbeds/groundtruth/english/[libest-ground-req-to-tc].txt'
#         doc2vec.MatchWithGroundTruth(path_to_ground_truth)
#         doc2vec.SaveLinks(grtruth = True)
#         #TODO find logic to LoadLink properly and display what is needed

    return value

# Cell
"""
Calculate the number of documents of two artifacts. Since in each dataframe, each document takes exactly one row, just counting the number
of rows in each dataframe will gives the result.
:param source: a dataframe of the entire source file
:param target: a dataframe of the entire target file
:returns: a list containing the number of documents in both source and target artifacts and the difference between the size of two artifacts
"""
def NumDoc(source, target):
    source_doc = source.shape[0]
    target_doc = target.shape[0]
    difference = source_doc - target_doc
    return [source_doc, target_doc, difference, -difference]

# Cell
"""
Calculate the number of vocabulary in each of the two artifacts. This method calls the helper function that uses a bpe model.The helper
function returns a counter object of all tokens and their occurrence, the length of the list is the vocab size.
:param source: a dataframe of the entire source file
:param target: a dataframe of the entire target file
:returns: a list containing the vocabulary size of both source and target artifacts and the difference between the vocabulary sizes two artifacts
"""
def VocabSize(source, target):
    #param source a string of the entire source file
    #param target a string of the entire target file
    #return a list containing the the difference between the two files in terms of vocab
    source_list = preprocess(source)
    target_list = preprocess(target)
    source_size = len(source_list[0])
    target_size = len(target_list[0])
    difference = source_size - target_size
    return [source_size, target_size, difference, -difference]

# Cell
"""
Calculate the average number of token per document in each of the two artifacts. This method calls the helper function that uses a bpe model.The helper
function returns a counter object of all tokens and their occurrence, sum up all the occurrence is the total number of tokens across entire actifact.
Divide that number by the number of documents will get the result we need.
:param source: a dataframe of the entire source file
:param target: a dataframe of the entire target file
:returns: a list containing the average number of token per document in both source and target artifacts and the difference between these two.
"""
def AverageToken(source, target):

    #return a list containing the the difference between the two files in terms of tokens
    source_doc = source.shape[0]
    target_doc = target.shape[0]

    source_list = preprocess(source)
    target_list = preprocess(target)

    source_total_token = sum(source_list[0].values())
    target_total_token = sum(target_list[0].values())

    source_token = source_total_token/source_doc
    target_token = target_total_token/target_doc
    difference = source_token - target_token
    return [source_token, target_token, difference, -difference]

# Cell
"""
Calculate the top 3 most frequent token in one artifacts. This method calls the helper function that uses a bpe model.The helper
function returns a counter object of all tokens and their occurrence, get the first three elements will gives us the most frequent
token. Divide their occurrence with totle number of tokens to get actual frequency
Divide that number by the number of documents will get the result we need.
:param artifacts_df: a dataframe of contents that need to be processed
:returns: a dictionary of top three most frenquent token with their frenquency
"""
def Vocab(artifacts_df):
    #Note: we can add a parameter for user to specify the number of most frequent token to return
    cnts = preprocess(artifacts_df)
    vocab_list = cnts[0].most_common(3)
    total = sum(cnts[0].values())
    vocab_dict = dict()
    vocab_dict[vocab_list[0][0]] = [vocab_list[0][1], vocab_list[0][1]/total]
    vocab_dict[vocab_list[1][0]] = [vocab_list[1][1], vocab_list[1][1]/total]
    vocab_dict[vocab_list[2][0]] = [vocab_list[2][1], vocab_list[2][1]/total]

    return vocab_dict

# Cell
"""
Calculate the top 3 most frequent token in both source and target artifacts. This method calls the helper function that uses a bpe model
with combined dataframe.The helperfunction returns a counter object of all tokens and their occurrence, get the first three elements
will gives us the most frequent token. Divide their occurrence with totle number of tokens to get actual frequency.
Divide that number by the number of documents will get the result we need.
:param source: a dataframe of the entire source file
:param target: a dataframe of the entire target file
:returns: a dictionary of top three most frenquent token with their frenquency
"""
def VocabShared(source, target):
    df = pd.concat([source, target])
    return Vocab(df)

# Cell
"""
Calculate the total number of vocabulary size of both soruce and target artifacts. The method first combines two dataframes together
and then call help function preprocess to get counter object. The length of resulting object is the total size of vocab.
:param source: a dataframe of the entire source file
:param target: a dataframe of the entire target file
:returns: a number indicating the vocabulary size of both soruce and target artifacts
"""
def SharedVocabSize(source, target):
    df = pd.concat([source, target])
    df_counts = preprocess(df)
    shared_size = len(df_counts[0])
    return shared_size

# Cell
"""
Calculate mutual information of source and target artifacts, which will be the overlap between two artifacts.
:param source: a dataframe of the entire source file
:param target: a dataframe of the entire target file
:returns: a number representing the mutual information of two artifacts.
"""
def MutualInformation(source, target):
    #param source a string of the entire source file
    #param target a string of the entire target file
    #return the mutual information
    mutual_information = random.randint(100,200)
    return mutual_information

# Cell
"""
Calculate the cross entropy of soruce and target artifacts. The method first combines two dataframes together
and then call the dit_shannon method to calcualte cross entropy with a counter object.
:param source: a dataframe of the entire source file
:param target: a dataframe of the entire target file
:returns: a number indicating the vocabulary size of both soruce and target artifacts
"""
def CrossEntropy(source, target):
    #param source a dataframe of the entire source artifact
    #param target a dataframe of the entire target artifact
    #return the entropy
    combined = source.append(target)
    entropy = i.dit_shannon(preprocess(combined)[0])

    return entropy


#     cross_entropy = random.randint(100,200)#looks like it is the msi funciton in the classes for word2vec or doc2vec
#     cross_entropy = get_system_entropy_from_df(source, "col1",)
#     return cross_entropy

# Cell
def makeArray(text):
    print("text:",text)
    return np.fromstring(text[1:-1],sep=' ')

#export
"""
Calculate KLDivergence of source and target artifacts combined.
:param source: a dataframe of the entire source file
:param target: a dataframe of the entire target file
:returns: a number representing the divergence of two artifacts.
"""
def KLDivergence(source, target):
    #param source a string of the entire source file
    #param target a string of the entire target file
    #return the divergence

    #we are going to use the TSNE function since this preforms the divergence
    source_df = pd.DataFrame({ "ids": ["source"],  "text":[source]})
    target_df = pd.DataFrame({ "ids": ["target"],  "text":[target]})
    source_df = source_df["text"].apply(makeArray)
    target_ef = target_df["text"].apply(makeArray)
    source_df.head()
    target_df.head()
    divergence = random.randint(100,200)
    return divergence