# AUTOGENERATED! DO NOT EDIT! File to edit: dev/4.0_infoxplainer.ir.ipynb (unless otherwise specified).

__all__ = ['VectorizationType', 'DistanceMetric', 'SimilarityMetric', 'EntropyMetric', 'SoftwareArtifacts',
           'Preprocessing', 'LinkType', 'BasicSequenceVectorization', 'Word2VecSeqVect', 'LoadLinks', 'Doc2VecSeqVect']

# Cell
import numpy as np
import gensim
import pandas as pd
from itertools import product
from random import sample
import functools
import os

# Cell
from gensim.models import WordEmbeddingSimilarityIndex
from gensim.similarities import SparseTermSimilarityMatrix
from gensim import corpora
from datetime import datetime
from enum import Enum, unique, auto
from ..mgmnt.prep import *

# Cell
#export
from scipy.spatial import distance
from scipy.stats import pearsonr

# Cell
import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.ERROR)

# Cell
#@unique
class VectorizationType(Enum):
    word2vec = auto()
    doc2vec = auto()
    vsm2vec = auto()

# Cell
#@unique
class DistanceMetric(Enum):
    WMD = auto()
    COS = auto()
    SCM = auto()
    EUC = auto()
    MAN = auto()

# Cell
#@unique
class SimilarityMetric(Enum):
    WMD_sim = auto()
    COS_sim = auto()
    SCM_sim = auto()
    EUC_sim = auto()
    MAN_sim = auto()
    Pearson = auto()

# Cell
class EntropyMetric(Enum):
    MSI_I = auto() #Minimum shared information Entropy
    MSI_X = auto() #Minimum shared information Extropy
    MI = auto() #Mutual information
    JI = auto() #Joint information
    Loss = auto() #Conditioned Entropy given the output I(x|y)
    Noise = auto() #Conditioned Entropy given the input I(y|x)
    Entropy_src = auto() #Self  Information src artifacts
    Entropy_tgt = auto() #Self Information target artifacts

# Cell
class SoftwareArtifacts(Enum):
    REQ = 'req'
    TC = 'tc'
    SRC = 'src'
    PY = 'py'
    PR = 'pr'
    UC = 'uc'

# Cell
#@unique
class Preprocessing(Enum):
    conv = auto()
    bpe = auto()

# Cell
#@unique
class LinkType(Enum):
    req2tc = auto()
    req2src = auto()
    issue2src = auto()
    pr2src = auto()
    uc2src = auto()
    uc2tc = auto()

# Cell
class BasicSequenceVectorization():
    '''Implementation of the class sequence-vanilla-vectorization other classes can inheritance this one'''
    def __init__(self, params, logging):

        self.params = params
        self.logging = logging
        self.df_nonground_link = None
        self.df_ground_link = None
        bpe = Preprocessing.bpe == self.params['system_path_config']['prep']
        self.prep = ConventionalPreprocessing(self.params, bpe = bpe)

        self.df_all_system = pd.read_csv(
            self.params['system_path_config']['system_path'],
            #names = params['system_path_config']['names'], #include the names into the files!!!
            header = 0,
            index_col = 0,
            sep = self.params['system_path_config']['sep']
        )

        #self.df_source = pd.read_csv(params['source_path'], names=['ids', 'text'], header=None, sep=' ')
        #self.df_target = pd.read_csv(params['target_path'], names=['ids', 'text'], header=None, sep=' ')
        self.df_source = self.df_all_system.loc[self.df_all_system['type'] == self.params['source_type']][self.params['system_path_config']['names']]
        self.df_target = self.df_all_system.loc[self.df_all_system['type'] == self.params['target_type']][self.params['system_path_config']['names']]

        #NA verification
        tag = self.params['system_path_config']['names'][1]
        self.df_source[tag] = self.df_source[tag].fillna("")
        self.df_target[tag] = self.df_target[tag].fillna("")

        ## self.document and self.dictionary is the vocabulary of the traceability corpus
        ## Do not confuse it with the dictionary of the general vectorization model
        if self.params['system_path_config']['prep'] == Preprocessing.conv: #if conventional preprocessing
            self.documents = [doc.split() for doc in self.df_all_system[self.df_all_system[tag].notnull()][tag].values] #Preparing Corpus
            self.dictionary = corpora.Dictionary( self.documents ) #Preparing Dictionary
            self.vocab = dict.fromkeys( self.dictionary.token2id.keys(),0 )
            self.logging.info("conventional preprocessing documents, dictionary, and vocab for the test corpus")

        elif self.params['system_path_config']['prep'] == Preprocessing.bpe:
            self.documents = [eval(doc) for doc in self.df_all_system[tag].values] #Preparing Corpus
            self.dictionary = corpora.Dictionary( self.documents ) #Preparing Dictionary
            self.computing_bpe_vocab(tag=tag)
            self.logging.info("bpe preprocessing documents, dictionary, and vocab for the test corpus")


        #This can be extended for future metrics <---------------------
        self.dict_labels = {
            DistanceMetric.COS:[DistanceMetric.COS, SimilarityMetric.COS_sim],
            SimilarityMetric.Pearson:[SimilarityMetric.Pearson],
            DistanceMetric.EUC:[DistanceMetric.EUC, SimilarityMetric.EUC_sim],
            DistanceMetric.WMD:[DistanceMetric.WMD, SimilarityMetric.WMD_sim],
            DistanceMetric.SCM:[DistanceMetric.SCM, SimilarityMetric.SCM_sim],
            DistanceMetric.MAN:[DistanceMetric.MAN, SimilarityMetric.MAN_sim],
            EntropyMetric.MSI_I:[EntropyMetric.MSI_I, EntropyMetric.MSI_X],
            EntropyMetric.MI:[EntropyMetric.Entropy_src, EntropyMetric.Entropy_tgt,
                              EntropyMetric.JI, EntropyMetric.MI,
                              EntropyMetric.Loss, EntropyMetric.Noise
                             ]
        }

    def computing_bpe_vocab(self,tag):
        ####INFO science params
        abstracted_vocab = [ set( eval(doc) ) for doc in self.df_all_system[ tag ].values] #creation of sets
        abstracted_vocab = functools.reduce( lambda a,b : a.union(b), abstracted_vocab ) #union of sets
        self.vocab = {self.prep.sp_bpe.id_to_piece(id): 0 for id in range(self.prep.sp_bpe.get_piece_size())}
        dict_abs_vocab = { elem : 0 for elem in abstracted_vocab - set(self.vocab.keys()) } #Ignored vocab by BPE
        self.logging.info('Ignored vocab by BPE' + str(abstracted_vocab - set(self.vocab.keys())) )
        self.vocab.update(dict_abs_vocab) #Updating

    def ground_truth_processing(self, path_to_ground_truth = '', from_mappings = False):
        'Optional class when corpus has ground truth. This function create tuples of links'

        if from_mappings:
            df_mapping = pd.read_csv(self.params['path_mappings'], header = 0, sep = ',')
            ground_links = list(zip(df_mapping['id_pr'].astype(str), df_mapping['doc_id']))
            self.logging.info('ground truth from mappings')
        else:
            self.logging.info('generating ground truth')
            ground_truth = open(path_to_ground_truth,'r')
            #Organizing The Ground Truth under the given format
            ground_links = [ [(line.strip().split()[0], elem) for elem in line.strip().split()[1:]] for line in ground_truth]
            ground_links = functools.reduce(lambda a,b : a+b,ground_links) #reducing into one list
            #assert len(ground_links) ==  len(set(ground_links))
            #To Verify Redundancies in the file
            if len(ground_links) !=  len(set(ground_links)):
                ground_links = list(set(ground_links))
                self.logging.warning("-----WARNING!-------- Redundacy in the ground truth file")
        return ground_links

    def samplingLinks(self, sampling = False, samples = 10, basename = False):

        if basename:
            source = [os.path.basename(elem) for elem in self.df_source['ids'].values ]
            target = [os.path.basename(elem) for elem in self.df_target['ids'].values ]
        else:
            source = self.df_source['ids'].values
            target = self.df_target['ids'].values

        if sampling:
            links = sample( list( product( source , target ) ), samples)
        else:
            links = list( product( source , target ))

        return links

    def cos_scipy(self, vector_v, vector_w):
        cos =  distance.cosine( vector_v, vector_w )
        return [cos, 1.-cos]

    def euclidean_scipy(self, vector_v, vector_w):
        dst = distance.euclidean(vector_v,vector_w)
        return [dst, 1./(1.+dst)] #Computing the inverse for similarity

    def manhattan_scipy(self, vector_v, vector_w):
        dst = distance.cityblock(vector_v,vector_w)
        n = len(vector_v)
        return [dst, 1./(1.+dst)] #Computing the inverse for similarity

    def pearson_abs_scipy(self, vector_v, vector_w):
        '''We are not sure that pearson correlation works well on doc2vec inference vectors'''
        #vector_v =  np.asarray(vector_v, dtype=np.float32)
        #vector_w =  np.asarray(vector_w, dtype=np.float32)
        #logging.info("pearson_abs_scipy"  + 'len: ' + str(len(vector_v)) + 'type: ' + str(type(vector_v)) )
        #logging.info("pearson_abs_scipy"  + 'len: ' + str(len(vector_w)) + 'type: ' + str(type(vector_w)) )
        corr, _ = pearsonr(vector_v, vector_w)
        return [abs(corr)] #Absolute value of the correlation


    def computeDistanceMetric(self, links, metric_list):
        '''Metric List Iteration'''

        metric_labels = [ self.dict_labels[metric] for metric in metric_list] #tracking of the labels
        distSim = [[link[0], link[1], self.distance( metric_list, link )] for link in links] #Return the link with metrics
        distSim = [[elem[0], elem[1]] + elem[2] for elem in distSim] #Return the link with metrics

        return distSim, functools.reduce(lambda a,b : a+b, metric_labels)

    def ComputeDistanceArtifacts(self, metric_list, sampling = False , samples = 10, basename = False):
        '''Activates Distance and Similarity Computations
        @metric_list if [] then Computes All metrics
        @sampling is False by the default
        @samples is the number of samples (or links) to be generated'''
        links_ = self.samplingLinks( sampling, samples, basename )

        docs, metric_labels = self.computeDistanceMetric( metric_list=metric_list, links=links_) #checkpoints
        self.df_nonground_link = pd.DataFrame(docs, columns =[self.params['names'][0], self.params['names'][1]]+ metric_labels) #Transforming into a Pandas
        self.logging.info("Non-groundtruth links computed")
        pass


    def SaveLinks(self, grtruth=False, sep=' ', mode='a'):
        timestamp = datetime.timestamp(datetime.now())
        path_to_link = self.params['saving_path'] + '['+ self.params['system'] + '-' + str(self.params['vectorizationType']) + '-' + str(self.params['linkType']) + '-' + str(grtruth) + '-{}].csv'.format(timestamp)

        if grtruth:
            self.df_ground_link.to_csv(path_to_link, header=True, index=True, sep=sep, mode=mode)
        else:
            self.df_nonground_link.to_csv(path_to_link, header=True, index=True, sep=sep, mode=mode)

        self.logging.info('Saving in...' + path_to_link)
        pass

    def findDistInDF(self, g_tuple, from_mappings=False, semeru_format=False):
        '''Return the index values of the matched mappings
        .eq is used for Source since it must match the exact code to avoid number substrings
        for the target, the substring might works fine
        '/' is aggregated before the tuple to avoid matching more then one substring
        '''

        if from_mappings: #SACP Format
            self.logging.info('processing from mappings SACP')
            dist = self.df_ground_link.loc[(self.df_ground_link["Source"].eq(g_tuple[0]) ) &
                 (self.df_ground_link["Target"].str.contains(g_tuple[1], regex=False))]
        elif semeru_format: #LibEST Format
            self.logging.info('processing from semeru_format LibEST')
            dist = self.df_ground_link.loc[(self.df_ground_link["Source"].str.contains('/' + g_tuple[0], regex=False) ) &
                 (self.df_ground_link["Target"].str.contains('/' + g_tuple[1], regex=False))]
        else: #By Default use Semeru Format
            self.logging.info('processing by Default')
            dist = self.df_ground_link[self.df_ground_link[self.params['names'][0]].str.contains( g_tuple[0][:g_tuple[0].find('.')] + '-' )
                     & self.df_ground_link[self.params['names'][1]].str.contains(g_tuple[1][:g_tuple[1].find('.')]) ]
        return dist.index.values


    def MatchWithGroundTruth(self, path_to_ground_truth='', from_mappings=False, semeru_format=False ):
        self.df_ground_link = self.df_nonground_link.copy()
        self.df_ground_link[self.params['names'][2]] = 0

        matchGT = [ self.findDistInDF( g , from_mappings=from_mappings, semeru_format=semeru_format ) for g in self.ground_truth_processing(path_to_ground_truth,from_mappings)]
        matchGT = functools.reduce(lambda a,b : np.concatenate([a,b]), matchGT) #Concatenate indexes
        new_column = pd.Series(np.full([len(matchGT)], 1 ), name=self.params['names'][2], index = matchGT)

        self.df_ground_link.update(new_column)
        self.logging.info("Groundtruth links computed")
        pass

# Cell
from collections import Counter
import dit
import math

# Cell
class Word2VecSeqVect(BasicSequenceVectorization):

    def __init__(self, params, logging):
        super().__init__(params, logging)
        self.new_model = gensim.models.Word2Vec.load( params['path_to_trained_model'] )
        self.new_model.init_sims(replace=True)  # Normalizes the vectors in the word2vec class.
        #Computes cosine similarities between word embeddings and retrieves the closest
        #word embeddings by cosine similarity for a given word embedding.
        self.similarity_index = WordEmbeddingSimilarityIndex(self.new_model.wv)
        #Build a term similarity matrix and compute the Soft Cosine Measure.
        self.similarity_matrix = SparseTermSimilarityMatrix(self.similarity_index, self.dictionary)

        self.dict_distance_dispatcher = {
            DistanceMetric.COS: self.cos_scipy,
            SimilarityMetric.Pearson: self.pearson_abs_scipy,
            DistanceMetric.WMD: self.wmd_gensim,
            DistanceMetric.SCM: self.scm_gensim,
            EntropyMetric.MSI_I: self.msi,
            EntropyMetric.MI: self.mutual_info
        }

    def wmd_gensim(self, sentence_a, sentence_b ):
        wmd = self.new_model.wv.wmdistance(sentence_a, sentence_b)
        return [wmd, self.wmd_similarity(wmd)]

    def wmd_similarity(self, dist):
        return 1./( 1.+float( dist ) ) #Associated Similarity

    def scm_gensim(self, sentence_a, sentence_b ):
        '''Compute SoftCosine Similarity of Gensim'''
        #Convert the sentences into bag-of-words vectors.
        sentence_1 = self.dictionary.doc2bow(sentence_a)
        sentence_2 = self.dictionary.doc2bow(sentence_b)

        #Return the inner product(s) between real vectors / corpora vec1 and vec2 expressed in a non-orthogonal normalized basis,
        #where the dot product between the basis vectors is given by the sparse term similarity matrix.
        scm_similarity = self.similarity_matrix.inner_product(sentence_1, sentence_2, normalized=True)
        return [1-scm_similarity, scm_similarity]

    def msi(self, sentence_a, sentence_b):
        '''@danaderp
        Minimum Shared Information'''
        vocab = self.vocab.copy()
        token_counts_1 = self.__get_cnts(sentence_a, vocab)
        token_counts_2 = self.__get_cnts(sentence_b, vocab)
        self.logging.info('token count processed')
        #Minimum Shared Tokens
        token_counts = { token: min(token_counts_1[token],token_counts_2[token]) for token in vocab }

        alphabet = list(set(token_counts.keys())) #[ list(set(cnt.keys())) for cnt in token_counts ]
        frequencies = self.__get_freqs(token_counts) #[ get_freqs(cnt) for cnt in token_counts ]
        self.logging.info('frequencies processed')

        if not frequencies:
            #"List is empty"
            "nan Means that src and target do not share information at all"
            entropies = float('nan')
            extropies = float('nan')
            self.logging.info('FREQUENCIES NOT COMPUTED!!!<--------------')
        else:
            scalar_distribution = dit.ScalarDistribution(alphabet, frequencies) #[dit.ScalarDistribution(alphabet[id], frequencies[id]) for id in range( len(token_counts) )]
            self.logging.info('scalar_distribution processed')

            entropies = dit.shannon.entropy( scalar_distribution ) #[ dit.shannon.entropy( dist ) for dist in scalar_distribution ]
            self.logging.info('entropies processed')

            extropies = dit.other.extropy( scalar_distribution )# [ dit.other.extropy( dist ) for dist in scalar_distribution ]
            self.logging.info('extropies processed')
        return [entropies,extropies]

    def mutual_info(self, sentence_a, sentence_b):
        """ Computing the manifold of metric of information
        Mutual information
        Joint Information
        Conditioned Information Loss
        Conditioned Information Noise
        Self-Information
        """
        vocab = self.vocab.copy()
        token_counts_1 = self.__get_cnts(sentence_a, vocab)
        token_counts_2 = self.__get_cnts(sentence_b, vocab)
        self.logging.info('token count processed')

        self.logging.info('vocab #'+ str(len(self.vocab.keys())))

        alphabet_source = list(set(token_counts_1.keys()))
        self.logging.info('alphabet_source #'+ str(len(alphabet_source)) )

        alphabet_target = list(set(token_counts_2.keys()))
        self.logging.info('alphabet_target #'+ str(len(alphabet_target)) )


        self.logging.info('diff src2tgt #'+ str(set(token_counts_1.keys()) - set(token_counts_2.keys())))
        self.logging.info('diff tgt2src #'+ str(set(token_counts_2.keys()) - set(token_counts_1.keys())))

        assert( len(alphabet_source) ==  len(alphabet_target) )

        #Computing Self-Information (or Entropy)
        scalar_distribution_source = dit.ScalarDistribution(alphabet_source, self.__get_freqs( token_counts_1 ) )
        entropy_source = dit.shannon.entropy( scalar_distribution_source )

        scalar_distribution_target = dit.ScalarDistribution(alphabet_target, self.__get_freqs( token_counts_2 ) )
        entropy_target = dit.shannon.entropy( scalar_distribution_target )

        #Computing Joint-information
        token_counts = { token: (token_counts_1[token] + token_counts_2[token]) for token in vocab }
        alphabet = list(set(token_counts.keys()))
        self.logging.info('alphabet #'+ str(len(alphabet)))
        frequencies = self.__get_freqs(token_counts)
        ##WARNING! if a document is empty frequencies might create an issue!
        scalar_distribution = dit.ScalarDistribution(alphabet, frequencies)
        joint_entropy = dit.shannon.entropy( scalar_distribution )

        #Computing Mutual-Information
        mutual_information = entropy_source + entropy_target - joint_entropy

        #Computing Noise
        noise = joint_entropy - entropy_target

        #Computing Loss
        loss = joint_entropy - entropy_source

        return [entropy_source, entropy_target, joint_entropy,
                mutual_information, loss, noise]

    def distance(self, metric_list,link):
        '''Iterate on the metrics'''
        #Computation of sentences can be moved directly to wmd_gensim method if we cannot generalize it for
        #the remaining metrics
        ids = self.params['system_path_config']['names'][0]
        txt = self.params['system_path_config']['names'][1]

        if self.params['system_path_config']['prep'] == Preprocessing.conv: #if conventional preprocessing
            sentence_a = self.df_source[self.df_source[ids].str.contains(link[0])][txt].values[0].split()
            sentence_b = self.df_target[self.df_target[ids].str.contains(link[1])][txt].values[0].split()
        elif self.params['system_path_config']['prep'] == Preprocessing.bpe:
            sentence_a = eval(self.df_source[self.df_source[ids].str.contains(link[0])][txt].values[0])
            sentence_b = eval(self.df_target[self.df_target[ids].str.contains(link[1])][txt].values[0])

        dist = [ self.dict_distance_dispatcher[metric](sentence_a,sentence_b) for metric in metric_list]
        self.logging.info("Computed distances or similarities "+ str(link) + str(dist))
        return functools.reduce(lambda a,b : a+b, dist) #Always return a list

    #################################3TODO substitute this block in the future by importing information science module
    def __get_cnts(self, toks, vocab):
        '''@danaderp
        Counts tokens within ONE document'''
        #logging.info("encoding_size:" len
        cnt = Counter(vocab)
        for tok in toks:
            cnt[tok] += 1
        return cnt

    def __get_freqs(self, dict_token_counts):

        num_tokens = sum( dict_token_counts.values() ) #number of subwords inside the document
        if num_tokens == 0.0:
            frequencies = []
            self.logging.info('---------------> NO SHARED INFORMATION <-------------------------')
        else:
            frequencies = [ (dict_token_counts[token])/num_tokens for token in dict_token_counts ]
        return frequencies
    #################################3


# Cell
def LoadLinks(timestamp, params, logging, grtruth=False, sep=' ' ):
    '''Returns a pandas from a saved link computation at a give timestamp
    @timestamp is the version of the model for a given system'''

    path= params['saving_path'] + '['+ params['system'] + '-' + str(params['vectorizationType']) + '-' + str(params['linkType']) + '-' + str(grtruth) + '-{}].csv'.format(timestamp)

    logging.info("Loading computed links from... "+ path)


    df_load = pd.read_csv(path, header=0, index_col=0, sep=sep)
    df_load["Source"] = df_load.Source.astype(str)
    logging.info("df_x.dtypes" + str(df_load.dtypes))
    return df_load

# Cell
class Doc2VecSeqVect(BasicSequenceVectorization):

    def __init__(self, params, logging):
        super().__init__(params, logging)
        self.new_model = gensim.models.Doc2Vec.load( params['path_to_trained_model'] )
        self.new_model.init_sims(replace=True)  # Normalizes the vectors in the word2vec class.
        self.df_inferred_src = None
        self.df_inferred_trg = None

        self.dict_distance_dispatcher = {
            DistanceMetric.COS: self.cos_scipy,
            SimilarityMetric.Pearson: self.pearson_abs_scipy,
            DistanceMetric.EUC: self.euclidean_scipy,
            DistanceMetric.MAN: self.manhattan_scipy
        }
        self.logging.info("d2v loaded")

    def distance(self, metric_list, link):
        '''Iterate on the metrics'''
        ν_inferredSource = self.df_inferred_src[self.df_inferred_src['ids'].str.contains(link[0])]['inf-doc2vec'].values[0]
        w_inferredTarget = self.df_inferred_trg[self.df_inferred_trg['ids'].str.contains(link[1])]['inf-doc2vec'].values[0]

        dist = [ self.dict_distance_dispatcher[metric](ν_inferredSource,w_inferredTarget) for metric in metric_list]
        self.logging.info("Computed distances or similarities "+ str(link) + str(dist))
        return functools.reduce(lambda a,b : a+b, dist) #Always return a list

    """
    def computeDistanceMetric(self, links, metric_list):
        '''It is computed the cosine similarity'''

        metric_labels = [ self.dict_labels[metric] for metric in metric_list] #tracking of the labels
        distSim = [[link[0], link[1], self.distance( metric_list, link )] for link in links] #Return the link with metrics
        distSim = [[elem[0], elem[1]] + elem[2] for elem in distSim] #Return the link with metrics

        return distSim, functools.reduce(lambda a,b : a+b, metric_labels)
    """

    def InferDoc2Vec(self, steps=200):
        '''Activate Inference on Target and Source Corpus'''
        self.df_inferred_src = self.df_source.copy()
        self.df_inferred_trg = self.df_target.copy()

        text = self.params['system_path_config']['names'][1]
        self.df_inferred_src['inf-doc2vec'] =  [self.new_model.infer_vector(artifact.split(),steps=steps) for artifact in self.df_inferred_src[text].values]
        self.df_inferred_trg['inf-doc2vec'] =  [self.new_model.infer_vector(artifact.split(),steps=steps) for artifact in self.df_inferred_trg[text].values]

        self.logging.info("Infer Doc2Vec on Source and Target Complete")