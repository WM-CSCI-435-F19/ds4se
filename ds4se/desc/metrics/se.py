# AUTOGENERATED! DO NOT EDIT! File to edit: dev/6.1_desc.metrics.se.ipynb (unless otherwise specified).

__all__ = ['get_desc_stats', 'confidence_interval', 'report_stats']

# Cell
# Imports
from scipy.stats import sem, t, median_absolute_deviation as mad
from statistics import mean, median, stdev

# Cell
'''
Returns max, min, mena, median, standard deviation, mean absolute deviation of a list

:param l: input list
:returns: see above
'''
def get_desc_stats(l):
    return max(l), min(l), mean(l), median(l), stdev(l), mad(l)

# Cell
'''
Calculates confidence interval of a list

:param l: input list
:param c: confidence value
:returns: start of interval and end of interval
'''
def confidence_interval(l, c = 0.95):
    n = len(l)
    m = mean(l)
    std_err = sem(l)
    h = std_err * t.ppf((1 + c) / 2, n - 1)

    start = m - h
    end = m + h

    return start, end

# Cell
'''
Returns formatted version of stats

:param l: list of integers
:param c: confidence interval
:returns: prints out all stats and confidence interval with nice formatting
'''
def report_stats(l, c = 0.95):
    mini, maxi, μ, med, σ, med_σ = get_desc_stats(l)
    print("Max:", mini)
    print("Min:", maxi)
    print("Average:", μ)
    print("Median:", med)
    print("Standard Deviation:", σ)
    print("Median Absolute Deviation:", med_σ)

    start, end = confidence_interval(l, c = 0.95)
    print(f"{int(c * 100)}% of the data fall within {start} and {end}")