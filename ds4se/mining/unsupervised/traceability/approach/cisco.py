# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/3.2_mining.unsupervised.traceability.approach.cisco.ipynb (unless otherwise specified).

__all__ = ['VectorizationType', 'LinkType', 'DistanceMetric', 'SimilarityMetric', 'Preprocessing',
           'BasicSequenceVectorization', 'Word2VecSeqVect', 'LoadLinks', 'VectorEvaluation',
           'SupervisedVectorEvaluation']

# Cell
# Imports
import numpy as np
import gensim
import pandas as pd
from itertools import product
from random import sample
import functools
import os
from enum import Enum, unique, auto

# Cell
from datetime import datetime
import seaborn as sns

# Cell
import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# Cell
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import plot_precision_recall_curve
from sklearn.metrics import auc
import matplotlib.pyplot as plt
from prg import prg
from pandas.plotting import scatter_matrix
from pandas.plotting import lag_plot
import math as m
import random as r
import collections
from sklearn.metrics.pairwise import cosine_similarity

# Cell
from gensim.models import WordEmbeddingSimilarityIndex
from gensim.similarities import SparseTermSimilarityMatrix
from gensim import corpora

# Cell
#export
from scipy.spatial import distance
from scipy.stats import pearsonr

# Cell
from sklearn.metrics import average_precision_score
from sklearn.metrics import roc_curve
from sklearn.metrics import roc_auc_score
from sklearn.metrics import confusion_matrix

# Cell
#@unique
class VectorizationType(Enum):
    word2vec = auto()
    doc2vec = auto()
    vsm2vec = auto()

# Cell
#@unique
class LinkType(Enum):
    req2tc = auto()
    req2src = auto()
    issue2src = auto()
    pr2src = auto()

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
#@unique
class Preprocessing(Enum):
    conv = auto()
    bpe = auto()

# Cell
class BasicSequenceVectorization():
    '''Implementation of the class sequence-vanilla-vectorization other classes can inheritance this one'''
    def __init__(self, params):

        self.params = params
        self.df_nonground_link = None
        self.df_ground_link = None
        self.prep = ConventionalPreprocessing(params, bpe = True)

        self.df_all_system = pd.read_csv(
            params['system_path_config']['system_path'],
            #names = params['system_path_config']['names'], #include the names into the files!!!
            header = 0,
            index_col = 0,
            sep = params['system_path_config']['sep']
        )

        #self.df_source = pd.read_csv(params['source_path'], names=['ids', 'text'], header=None, sep=' ')
        #self.df_target = pd.read_csv(params['target_path'], names=['ids', 'text'], header=None, sep=' ')
        self.df_source = self.df_all_system.loc[self.df_all_system['type'] == params['source_type']][params['system_path_config']['names']]
        self.df_target = self.df_all_system.loc[self.df_all_system['type'] == params['target_type']][params['system_path_config']['names']]

        #NA verification
        tag = parameters['system_path_config']['names'][1]
        self.df_source[tag] = self.df_source[tag].fillna("")
        self.df_target[tag] = self.df_target[tag].fillna("")

        if params['system_path_config']['prep'] == Preprocessing.conv: #if conventional preprocessing
            self.documents = [doc.split() for doc in self.df_all_system[self.df_all_system[tag].notnull()][tag].values] #Preparing Corpus
            self.dictionary = corpora.Dictionary( self.documents ) #Preparing Dictionary
            logging.info("conventional preprocessing documents and dictionary")
        elif params['system_path_config']['prep'] == Preprocessing.bpe:
            self.documents = [eval(doc) for doc in self.df_all_system[tag].values] #Preparing Corpus
            self.dictionary = corpora.Dictionary( self.documents ) #Preparing Dictionary
            logging.info("bpe preprocessing documents and dictionary")

        ####INFO science params
        abstracted_vocab = [ set(doc) for doc in self.df_all_system[ 'bpe8k' ].values] #creation of sets
        abstracted_vocab = functools.reduce( lambda a,b : a.union(b), abstracted_vocab ) #union of sets
        self.vocab = {self.prep.sp_bpe.id_to_piece(id): 0 for id in range(self.prep.sp_bpe.get_piece_size())}
        dict_abs_vocab = { elem : 0 for elem in abstracted_vocab - set(self.vocab.keys()) } #Ignored vocab by BPE
        self.vocab.update(dict_abs_vocab) #Updating


        #This can be extended for future metrics <---------------------
        self.dict_labels = {
            DistanceMetric.COS:[DistanceMetric.COS, SimilarityMetric.COS_sim],
            SimilarityMetric.Pearson:[SimilarityMetric.Pearson],
            DistanceMetric.EUC:[DistanceMetric.EUC, SimilarityMetric.EUC_sim],
            DistanceMetric.WMD:[DistanceMetric.WMD, SimilarityMetric.WMD_sim],
            DistanceMetric.SCM:[DistanceMetric.SCM, SimilarityMetric.SCM_sim],
            DistanceMetric.MAN:[DistanceMetric.MAN, SimilarityMetric.MAN_sim],
            EntropyMetric.MSI_I:[EntropyMetric.MSI_I, EntropyMetric.MSI_X]
        }


    def ground_truth_processing(self, path_to_ground_truth = '', from_mappings = False):
        'Optional class when corpus has ground truth. This function create tuples of links'

        if from_mappings:
            df_mapping = pd.read_csv(self.params['path_mappings'], header = 0, sep = ',')
            ground_links = list(zip(df_mapping['id_pr'].astype(str), df_mapping['doc_id']))
        else:
            ground_truth = open(path_to_ground_truth,'r')
            #Organizing The Ground Truth under the given format
            ground_links = [ [(line.strip().split()[0], elem) for elem in line.strip().split()[1:]] for line in ground_truth]
            ground_links = functools.reduce(lambda a,b : a+b,ground_links) #reducing into one list
            assert len(ground_links) ==  len(set(ground_links)) #To Verify Redundancies in the file
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
        logging.info("pearson_abs_scipy" + str(vector_v) + "__" + str(vector_w))
        corr, _ = pearsonr(vector_v, vector_w)
        return [abs(corr)] #Absolute value of the correlation


    def computeDistanceMetric(self, links, metric_list):
        '''Metric List Iteration'''

        metric_labels = [ self.dict_labels[metric] for metric in metric_list] #tracking of the labels
        distSim = [[link[0], link[1], self.distance( metric_list, link )] for link in links] #Return the link with metrics
        distSim = [[elem[0], elem[1]] + elem[2] for elem in distSim] #Return the link with metrics

        return distSim, functools.reduce(lambda a,b : a+b, metric_labels)

    def ComputeDistanceArtifacts(self, metric_list, sampling = False , samples = 10, basename = False):
        '''Acticates Distance and Similarity Computations
        @metric_list if [] then Computes All metrics
        @sampling is False by the default
        @samples is the number of samples (or links) to be generated'''
        links_ = self.samplingLinks( sampling, samples, basename )

        docs, metric_labels = self.computeDistanceMetric( metric_list=metric_list, links=links_) #checkpoints
        self.df_nonground_link = pd.DataFrame(docs, columns =[self.params['names'][0], self.params['names'][1]]+ metric_labels) #Transforming into a Pandas
        logging.info("Non-groundtruth links computed")
        pass


    def SaveLinks(self, grtruth=False, sep=' ', mode='a'):
        timestamp = datetime.timestamp(datetime.now())
        path_to_link = self.params['saving_path'] + '['+ self.params['system'] + '-' + str(self.params['vectorizationType']) + '-' + str(self.params['linkType']) + '-' + str(grtruth) + '-{}].csv'.format(timestamp)

        if grtruth:
            self.df_ground_link.to_csv(path_to_link, header=True, index=True, sep=sep, mode=mode)
        else:
            self.df_nonground_link.to_csv(path_to_link, header=True, index=True, sep=sep, mode=mode)

        logging.info('Saving in...' + path_to_link)
        pass

    def findDistInDF(self, g_tuple, from_mappings=False, semeru_format=False):
        '''Return the index values of the matched mappings
        .eq is used for Source since it must match the exact code to avoid number substrings
        for the target, the substring might works fine'''

        if from_mappings:
            dist = self.df_ground_link.loc[(self.df_ground_link["Source"].eq(g_tuple[0]) ) &
                 (self.df_ground_link["Target"].str.contains(g_tuple[1], regex=False))]
            logging.info('findDistInDF: from_mappings')
        elif semeru_format:
            dist = self.df_ground_link.loc[(self.df_ground_link["Source"].str.contains(g_tuple[0], regex=False) ) &
                 (self.df_ground_link["Target"].str.contains(g_tuple[1], regex=False))]
            logging.info('findDistInDF: semeru_format')
        else:
            dist = self.df_ground_link[self.df_ground_link[self.params['names'][0]].str.contains( g_tuple[0][:g_tuple[0].find('.')] + '-' )
                     & self.df_ground_link[self.params['names'][1]].str.contains(g_tuple[1][:g_tuple[1].find('.')]) ]
            logging.info('findDistInDF: default')
        return dist.index.values


    def MatchWithGroundTruth(self, path_to_ground_truth='', from_mappings=False, semeru_format=False ):
        self.df_ground_link = self.df_nonground_link.copy()
        self.df_ground_link[self.params['names'][2]] = 0

        matchGT = [ self.findDistInDF( g , from_mappings=from_mappings, semeru_format=semeru_format ) for g in self.ground_truth_processing(path_to_ground_truth,from_mappings)]
        matchGT = functools.reduce(lambda a,b : np.concatenate([a,b]), matchGT) #Concatenate indexes
        new_column = pd.Series(np.full([len(matchGT)], 1 ), name=self.params['names'][2], index = matchGT)

        self.df_ground_link.update(new_column)
        logging.info("Groundtruth links computed")
        pass

# Cell
class Word2VecSeqVect(BasicSequenceVectorization):

    def __init__(self, params):
        super().__init__(params)
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
            EntropyMetric.MSI_I: self.msi
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
        token_counts_1 = self.get_cnts(sentence_a, self.vocab)
        token_counts_2 = self.get_cnts(sentence_b, self.vocab)
        logging.info('token count processed')

        #Minimum Shared Tokens
        token_counts = { token: min(token_counts_1[token],token_counts_2[token]) for token in self.vocab }

        alphabet = list(set(token_counts.keys())) #[ list(set(cnt.keys())) for cnt in token_counts ]
        frequencies = self.get_freqs(token_counts) #[ get_freqs(cnt) for cnt in token_counts ]
        logging.info('frequencies processed')

        if not frequencies:
            #"List is empty"
            entropies = float('nan')
            extropies = float('nan')
        else:
            scalar_distribution = dit.ScalarDistribution(alphabet, frequencies) #[dit.ScalarDistribution(alphabet[id], frequencies[id]) for id in range( len(token_counts) )]
            logging.info('scalar_distribution processed')

            entropies = dit.shannon.entropy( scalar_distribution ) #[ dit.shannon.entropy( dist ) for dist in scalar_distribution ]
            logging.info('entropies processed')

            extropies = dit.other.extropy( scalar_distribution )# [ dit.other.extropy( dist ) for dist in scalar_distribution ]
            logging.info('extropies processed')
        return [entropies,extropies]


    def distance(self, metric_list,link):
        '''Iterate on the metrics'''
        #Computation of sentences can be moved directly to wmd_gensim method if we cannot generalize it for
        #the remaining metrics
        ids = parameters['system_path_config']['names'][0]
        txt = parameters['system_path_config']['names'][1]

        if self.params['system_path_config']['prep'] == Preprocessing.conv: #if conventional preprocessing
            sentence_a = self.df_source[self.df_source[ids].str.contains(link[0])][txt].values[0].split()
            sentence_b = self.df_target[self.df_target[ids].str.contains(link[1])][txt].values[0].split()
        elif self.params['system_path_config']['prep'] == Preprocessing.bpe:
            sentence_a = eval(self.df_source[self.df_source[ids].str.contains(link[0])][txt].values[0])
            sentence_b = eval(self.df_target[self.df_target[ids].str.contains(link[1])][txt].values[0])

        dist = [ self.dict_distance_dispatcher[metric](sentence_a,sentence_b) for metric in metric_list]
        logging.info("Computed distances or similarities "+ str(link) + str(dist))
        return functools.reduce(lambda a,b : a+b, dist) #Always return a list

    #################################3TODO substitute this block in the future by importing information science module
    def get_cnts(self, toks, vocab):
        '''@danaderp
        Counts tokens within ONE document'''
        #logging.info("encoding_size:" len
        cnt = Counter(vocab)
        for tok in toks:
            cnt[tok] += 1
        return cnt

    def get_freqs(self, dict_token_counts):

        num_tokens = sum( dict_token_counts.values() ) #number of subwords inside the document
        if num_tokens == 0.0:
            frequencies = []
            logging.info('---------------> NO SHARED INFORMATION <-------------------------')
        else:
            frequencies = [ (dict_token_counts[token])/num_tokens for token in dict_token_counts ]
        return frequencies
    #################################3


# Cell
def LoadLinks(timestamp, params, grtruth=False, sep=' ' ):
    '''Returns a pandas from a saved link computation at a give timestamp
    @timestamp is the version of the model for a given system'''

    path= params['saving_path'] + '['+ params['system'] + '-' + str(params['vectorizationType']) + '-' + str(params['linkType']) + '-' + str(grtruth) + '-{}].csv'.format(timestamp)

    logging.info("Loading computed links from... "+ path)

    return pd.read_csv(path, header=0, index_col=0, sep=sep)

# Cell
class VectorEvaluation():
    '''Approaches Common Evaluations and Interpretations (statistical analysis)'''
    def __init__(self, sequenceVectorization):
        self.seqVect = sequenceVectorization

# Cell
class SupervisedVectorEvaluation(VectorEvaluation):
    def __init__(self, sequenceVectorization, sim_list):
        super().__init__(sequenceVectorization)
        self.sim_list = sim_list

        self.df_filtered = sequenceVectorization.df_ground_link
        self.df_filtered = self.df_filtered[~self.df_filtered.isin([np.nan, np.inf, -np.inf]).any(1)]

        #CreateFilters Here

        self.y_test = self.df_filtered['Linked?'].values
        self.y_score = [self.df_filtered[sim].values for sim in sim_list]
        self.title = str(sequenceVectorization.params['vectorizationType'])
        pass

    def Compute_precision_recall_gain(self):
        '''One might choose PRG if there is little interest in identifying false negatives '''
        for count,sim in enumerate(self.sim_list):
            prg_curve = prg.create_prg_curve(self.y_test, self.y_score[count])
            auprg = prg.calc_auprg(prg_curve)
            prg.plot_prg(prg_curve)
            logging.info('auprg:  %.3f' %  auprg)
            logging.info("compute_precision_recall_gain Complete: "+str(sim))
        pass

    def Compute_avg_precision(self):
        '''Generated precision-recall curve'''

        # calculate the no skill line as the proportion of the positive class
        no_skill = len(self.y_test[self.y_test==1]) / len(self.y_test)

        for count,sim in enumerate(self.sim_list):
            plt.plot([0, 1], [no_skill, no_skill], linestyle='--', label='No Skill') #reference curve
            precision, recall, _ = precision_recall_curve(self.y_test, self.y_score[count]) #compute precision-recall curve
            plt.plot(recall, precision, marker='.', label = str(sim)) #plot model curve
            plt.title(self.label[count])
            plt.xlabel('Recall')
            plt.ylabel('Precision')
            plt.legend() #show the legend
            plt.show() #show the plot

            average_precision = average_precision_score(self.y_test, self.y_score[count])
            auc_score = auc(recall, precision)
            logging.info('Average precision-recall score: {0:0.2f}'.format(average_precision))
            logging.info('Precision-Recall AUC: %.3f' % auc_score)
        pass

    def Compute_avg_precision_same_plot(self):
        '''Generated precision-recall curve'''

        # calculate the no skill line as the proportion of the positive class
        no_skill = len(self.y_test[self.y_test==1]) / len(self.y_test)
        plt.plot([0, 1], [no_skill, no_skill], linewidth=0.5, linestyle='--', label='No Skill [{0:0.2f}]'.format(no_skill)) #reference curve

        for count,sim in enumerate(self.sim_list):
            precision, recall, _ = precision_recall_curve(self.y_test, self.y_score[count]) #compute precision-recall curve
            average_precision = average_precision_score(self.y_test, self.y_score[count])
            auc_score = auc(recall, precision)
            logging.info('Average precision-recall score: {0:0.2f}'.format(average_precision))
            logging.info('Precision-Recall AUC: %.2f' % auc_score)

            #plt.plot(recall, precision, linewidth=0.4, marker='.', label = str(sim)) #plot model curve
            plt.plot(recall, precision, linewidth=1, label = str(sim)+  ' [auc:{0:0.2f}]'.format(auc_score)) #plot model curve
            pass

        plt.title(self.title)
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.legend(fontsize=9) #show the legend
        plt.show() #show the plot
        pass

    def Compute_roc_curve(self):

        plt.plot([0, 1], [0, 1],  linewidth=0.5, linestyle='--', label='No Skill') #reference curve
        for count,sim in enumerate(self.sim_list):
            fpr, tpr, _ = roc_curve(self.y_test, self.y_score[count]) #compute roc curve
            roc_auc = roc_auc_score(self.y_test, self.y_score[count])
            logging.info('ROC AUC %.2f' % roc_auc)

            plt.plot(fpr, tpr,  linewidth=1, label = str(sim)+  ' [auc:{0:0.2f}]'.format(roc_auc)) #plot model curve
            pass
        plt.title(self.title)
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.legend(fontsize=9) #show the legend
        plt.show() #show the plot

        pass