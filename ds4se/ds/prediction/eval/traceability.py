# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/9.0_ds.prediction.eval.traceability.ipynb (unless otherwise specified).

__all__ = ['SupervisedVectorEvaluation', 'ManifoldEntropy']

# Cell
from prg import prg

# Cell
import ds4se as ds
from ....mining.ir import VectorizationType
from ....mining.ir import SimilarityMetric
from ....mining.ir import EntropyMetric

# Cell
#Description importation
from ...description.eval.traceability import VectorEvaluation

# Cell
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

# Cell
import gensim
import pandas as pd
from itertools import product
from random import sample
import functools
import os
from enum import Enum, unique, auto

# Cell
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import plot_precision_recall_curve
from sklearn.metrics import auc
import math as m
import random as r
import collections
from sklearn.metrics.pairwise import cosine_similarity
import seaborn as sns

# Cell
from scipy.spatial import distance
from scipy.stats import pearsonr

# Cell
from sklearn.metrics import average_precision_score
from sklearn.metrics import roc_curve
from sklearn.metrics import roc_auc_score
from sklearn.metrics import confusion_matrix

# Cell
import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# Cell
class SupervisedVectorEvaluation(VectorEvaluation):

    def __init__(self, params):
        super().__init__(params)

        self.sys = params['system']

        #Word2vec
        similarities_w2v = self.sim_list_w2v + ['Linked?']
        similarities_w2v = [str(i) for i in similarities_w2v]
        self.df_filtered_w2v = self.df_w2v.copy()
        self.df_filtered_w2v = self.df_filtered_w2v[similarities_w2v]
        self.df_filtered_w2v = self.df_filtered_w2v[~self.df_filtered_w2v.isin([np.nan, np.inf, -np.inf]).any(1)]

        #Doc2vec
        similarities_d2v = self.sim_list_d2v + ['Linked?']
        similarities_d2v = [str(i) for i in similarities_d2v]
        self.df_filtered_d2v = self.df_d2v.copy()
        self.df_filtered_d2v = self.df_filtered_d2v[similarities_d2v]
        self.df_filtered_d2v = self.df_filtered_d2v[~self.df_filtered_d2v.isin([np.nan, np.inf, -np.inf]).any(1)]

    def vecTypeVerification(self, vecType= VectorizationType.word2vec):
        if vecType == VectorizationType.word2vec:
            self.sim_list = self.sim_list_w2v
            y_test = self.df_filtered_w2v['Linked?'].values
            y_score = [self.df_filtered_w2v[ str(sim) ].values for sim in self.sim_list]
            logging.info('Vectorization: ' +  str(vecType) )
        elif vecType == VectorizationType.doc2vec:
            self.sim_list = self.sim_list_d2v
            y_test = self.df_filtered_d2v['Linked?'].values
            y_score = [self.df_filtered_d2v[ str(sim) ].values for sim in self.sim_list]
            logging.info('Vectorization: ' +  str(vecType) )
        return y_test,y_score

    def vecTypeVerificationSim(self, vecType= VectorizationType.word2vec,sim=SimilarityMetric.SCM_sim):
        if vecType == VectorizationType.word2vec:
            self.sim_list = self.sim_list_w2v
            y_test = self.df_filtered_w2v['Linked?'].values
            y_score = self.df_filtered_w2v[ str(sim) ].values
            logging.info('Vectorization: ' +  str(vecType) + " " + str(sim))
        elif vecType == VectorizationType.doc2vec:
            self.sim_list = self.sim_list_d2v
            y_test = self.df_filtered_d2v['Linked?'].values
            y_score = self.df_filtered_d2v[ str(sim) ].values
            logging.info('Vectorization: ' +  str(vecType) + " " + str(sim))
        return y_test,y_score

    def Compute_precision_recall_gain(self, vecType = VectorizationType.word2vec, sim=SimilarityMetric.SCM_sim):
        '''One might choose PRG if there is little interest in identifying false negatives '''
        y_test,y_score = self.vecTypeVerificationSim(vecType=vecType, sim=sim)

        fig = go.Figure(layout_yaxis_range=[-0.05,1.02],layout_xaxis_range=[-0.05,1.02])
        prg_curve = prg.create_prg_curve(y_test, y_score)
        indices = np.arange(np.argmax(prg_curve['in_unit_square']) - 1,
                        len(prg_curve['in_unit_square']))
        pg = prg_curve['precision_gain']
        rg = prg_curve['recall_gain']
        fig.add_trace(go.Scatter(x=rg[indices], y=pg[indices],
                        line = dict(color="cyan", width=2,dash="solid")))

        indices = np.logical_or(prg_curve['is_crossing'],
                    prg_curve['in_unit_square'])
        fig.add_trace(go.Scatter(x=rg[indices], y=pg[indices],
                    line = dict(color="blue", width=2,dash="solid")))

        indices = np.logical_and(prg_curve['in_unit_square'],
                        True - prg_curve['is_crossing'])
        fig.add_trace(go.Scatter(x=rg[indices], y=pg[indices],mode='markers'))

        valid_points = np.logical_and( ~ np.isnan(rg), ~ np.isnan(pg))
        upper_hull = prg.convex_hull(zip(rg[valid_points],pg[valid_points]))
        rg_hull, pg_hull = zip(*upper_hull)
        fig.add_trace(go.Scatter(x=rg_hull, y=pg_hull, mode = "lines",
                           line = dict(color="red", width=2,dash="dash")))
        auprg = prg.calc_auprg(prg_curve)

        logging.info('auprg:  %.3f' %  auprg)
        logging.info("compute_precision_recall_gain Complete: "+str(sim))

        fig.update_layout(
            title=self.sys + "-[" + str(sim) + "]",
            height = 600,
            width = 600,
            xaxis_title='Recall Gain',
            xaxis = dict(
                tickmode = 'linear',
                tick0 = 0,
                dtick = 0.25),
            yaxis_title='Precision Gain',
            yaxis = dict(
                tickmode = 'linear',
                tick0 = 0,
                dtick = 0.25)
            )
        fig.update_yaxes(
            scaleanchor = "x",
            scaleratio = 1,
            )


        return fig

    def Compute_avg_precision(self, vecType = VectorizationType.word2vec):
        '''Generated precision-recall curve enhanced'''
        y_test,y_score = self.vecTypeVerification(vecType=vecType)

        linestyles = ['solid','dash','dashdot','dotted']

        color = 'red'

        # calculate the no skill line as the proportion of the positive class
        no_skill = len(y_test[y_test==1]) / len(y_test)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[0, 1], y=[no_skill, no_skill], name='No Skill [{0:0.2f}]'.format(no_skill), mode = "lines",
                         line = dict(color='red', width=.5, dash='dash')))

        for count,sim in enumerate(self.sim_list):
            precision, recall, _ = precision_recall_curve(y_test, y_score[count]) #compute precision-recall curve
            average_precision = average_precision_score(y_test, y_score[count])
            auc_score = auc(recall, precision)
            logging.info('Average precision-recall score: {0:0.2f}'.format(average_precision))
            logging.info('Precision-Recall AUC: %.2f' % auc_score)


            fig.add_trace(go.Scatter(x=recall, y=precision, name=str(sim.name)+' [auc:{0:0.2f}]'.format(auc_score),
                         line = dict(color=color, width=1, dash=linestyles[count])))



        ##AUC
        color = 'blue'

        fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], name='No Skill', mode = "lines",
                         line = dict(color='blue', width=.5, dash='dot')))
        for count,sim in enumerate(self.sim_list):
            fpr, tpr, _ = roc_curve(y_test, y_score[count]) #compute roc curve
            roc_auc = roc_auc_score(y_test, y_score[count])
            logging.info('ROC AUC %.2f' % roc_auc)
            fig.add_trace(go.Scatter(x=fpr, y=tpr, name=str(sim.name)+' [auc:{0:0.2f}]'.format(roc_auc),
                         line = dict(color=color, width=1, dash=linestyles[count])))


        fig.update_layout(
            title=self.sys + "-[" + str(vecType) + "]",
            xaxis_title='recall [fpr]',
            yaxis_title='tpr')
        return fig

    def Compute_avg_precision_same_plot(self, vecType = VectorizationType.word2vec):
        '''Generated precision-recall curve'''

        linestyles = ['solid','dash','dashdot','dotted']

        fig = go.Figure()
        color = 'red'
        y_test,y_score = self.vecTypeVerification(vecType=vecType)

        # calculate the no skill line as the proportion of the positive class
        no_skill = len(y_test[y_test==1]) / len(y_test)
        fig.add_trace(go.Scatter(x=[0, 1], y=[no_skill, no_skill], name='No Skill [{0:0.2f}]'.format(no_skill), mode = "lines",
                         line = dict(color='red', width=.5, dash='dash'))) #reference curve

        for count,sim in enumerate(self.sim_list):
            precision, recall, _ = precision_recall_curve(y_test, y_score[count]) #compute precision-recall curve
            average_precision = average_precision_score(y_test, y_score[count])
            auc_score = auc(recall, precision)
            logging.info('Average precision-recall score: {0:0.2f}'.format(average_precision))
            logging.info('Precision-Recall AUC: %.2f' % auc_score)

            fig.add_trace(go.Scatter(x=recall, y=precision, name=str(sim.name)+' [auc:{0:0.2f}]'.format(auc_score),
                         line = dict(color=color, width=1, dash=linestyles[count]))) #plot model curve

        fig.update_layout(
            title=self.sys + "-[" + str(vecType) + "]",
            xaxis_title='Recall',
            yaxis_title='Precision')
        return fig

    def Compute_roc_curve(self, vecType = VectorizationType.word2vec):

        linestyles = ['solid','dash','dashdot','dotted']

        fig = go.Figure()
        color = 'blue'
        y_test,y_score = self.vecTypeVerification(vecType = vecType)

        fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], name='No Skill', mode = "lines",
                         line = dict(color='blue', width=.5, dash='dot'))) #reference curve

        for count,sim in enumerate(self.sim_list):
            fpr, tpr, _ = roc_curve(y_test, y_score[count]) #compute roc curve
            roc_auc = roc_auc_score(y_test, y_score[count])
            logging.info('ROC AUC %.2f' % roc_auc)

            fig.add_trace(go.Scatter(x=fpr, y=tpr, name=str(sim.name)+' [auc:{0:0.2f}]'.format(roc_auc),
                         line = dict(color=color, width=1, dash=linestyles[count]))) #plot model curve #plot model curve

        fig.update_layout(
            title=self.sys + "-[" + str(vecType) + "]",
            xaxis_title='False Positive Rate',
            yaxis_title='True Positive Rate')

        return fig

    def CofusionMatrix(self, vecType = VectorizationType.word2vec):
        ##TODO This implementatin is incomplete and not verify it yet
        y_test,y_score = self.vecTypeVerification(vecType=vecType)
        y_score_threshold = [0 if elem<=0.8 else 1 for elem in supevisedEval.y_score] #Hardcoded 0.7 Threshold
        #TODO a Variation threshold analysis
        tn, fp, fn, tp = confusion_matrix(supevisedEval.y_test, y_score_threshold).ravel()
        return tn, fp, fn, tp

# Cell
class ManifoldEntropy(VectorEvaluation):
    def __init__(self, params):
        super().__init__(params)
        self.sharedEntropy_filtered = self.sharedInfo.copy()
        self.sharedEntropy_filtered.dropna(inplace=True)
        self.sys = params['system']

    def minimum_shared_entropy(self,dist = SimilarityMetric.WMD_sim, extropy=False):
        '''Minimum Shared Plot'''
        ent = EntropyMetric.MSI_I
        color = 'dark blue'
        if extropy:
            ent = EntropyMetric.MSI_X
            color = 'red'
        columns = [str(i) for i in [ent, dist ]]

        corr = self.compute_spearman_corr(self.sharedEntropy_filtered, columns)
        logging.info('Correlation {%.2f}' % corr)
        fig = px.scatter(self.sharedEntropy_filtered,
                                 x = columns[0], y = columns[1], color_discrete_sequence=[color])
        fig.update_layout(
            title = self.sys +': ['+ dist.name + '-' + ent.name + '] Correlation {%.2f}' % corr
        )
        return fig


    def manifold_entropy_plot(self, manifold = EntropyMetric.MI, dist = SimilarityMetric.WMD_sim):
        '''Manifold Entropy'''

        columns = [str(i) for i in [manifold, dist]]
        corr = self.compute_spearman_corr(self.manifoldEntropy, columns)

        logging.info('Correlation {%.2f}' % corr)

        fig = px.scatter(self.manifoldEntropy,
                                 x = columns[0], y = columns[1], color_continuous_scale=["dark blue"])
        fig.update_layout(
            title = self.sys +': ['+ dist.name + '-' + manifold.name + '] Correlation {%.2f}' % corr
        )
        return fig

    def composable_entropy_plot(self,
                                manifold_x = EntropyMetric.MI,
                                manifold_y = EntropyMetric.Loss,
                                dist = SimilarityMetric.WMD_sim,
                                ground = False
                               ):

        columns = [str(i) for i in [manifold_x, manifold_y, dist]]

        if ground:
            title = params['system']+': Information-Semantic Interactions by GT '
        else:
            title = params['system']+': Information-Semantic Interactions '+ dist.name


        fig = px.scatter(self.manifoldEntropy,x = columns[0], y = columns[1], color = columns[2],
                         color_continuous_scale=px.colors.sequential.Viridis)
        fig.update_layout(
            title = title
        )
        return fig

    def composable_shared_plot(self,
                                manifold_x = EntropyMetric.MSI_I,
                                manifold_y = EntropyMetric.Loss,
                                dist = SimilarityMetric.WMD_sim
                               ):

        columns = [str(i) for i in [manifold_x, manifold_y, dist]]


        title = params['system']+': Information-Semantic Interactions '+ dist.name

        df = self.df_w2v.dropna(inplace=False)
        print(df.columns)
        fig = px.scatter(df,x = columns[0], y = columns[1], color = columns[2],
                         color_continuous_scale=px.colors.sequential.Viridis)
        fig.update_layout(
            title = title
        )
        return fig

    def compute_spearman_corr(self, filter_metrics_01, columns):
        df_correlation = filter_metrics_01.copy()
        correlation = df_correlation[columns].corr(method='spearman')
        #correlation = df_correlation.corr(method='spearman')
        return correlation[columns[0]].values[1]