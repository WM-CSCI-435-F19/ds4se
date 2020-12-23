# AUTOGENERATED! DO NOT EDIT! File to edit: dev/6.0_eval.mining.ir.unsupervised.x2v.ipynb (unless otherwise specified).

__all__ = ['VectorEvaluation', 'SupervisedVectorEvaluation']

# Cell
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import plot_precision_recall_curve
from sklearn.metrics import auc
import matplotlib.pyplot as plt
from pandas.plotting import scatter_matrix
from pandas.plotting import lag_plot
import math as m
import random as r
import collections
from sklearn.metrics.pairwise import cosine_similarity
import seaborn as sns

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
class VectorEvaluation():
    '''Approaches Common Evaluations and Interpretations (statistical analysis)
       Loading unsupervised results
       w2v includes entropy evaluation
    '''
    def __init__(self, params):
        self.df_w2v = pd.read_csv(params['experiment_path_w2v'], header=0, index_col=0, sep=' ')
        self.df_w2v = pd.read_csv(params['experiment_path_d2v'], header=0, index_col=0, sep=' ')

# Cell
#export
class SupervisedVectorEvaluation(VectorEvaluation):
    def __init__(self, params, sim_list):
        super().__init__(params)
        self.sim_list = sim_list

        #Word2vec
        self.df_filtered_w2v = df_w2v.copy()
        self.df_filtered_w2v = self.df_filtered_w2v[~self.df_filtered_w2v.isin([np.nan, np.inf, -np.inf]).any(1)]

        #Doc2vec
        self.df_filtered_d2v= df_d2v.copy()
        self.df_filtered_d2v = self.df_filtered_d2v[~self.df_filtered_d2v.isin([np.nan, np.inf, -np.inf]).any(1)]
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