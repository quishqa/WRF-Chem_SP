#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 24 17:23:49 2020

@author: mgavidia
"""


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def complete_cases(model_df, obs_df, var):
    '''
    Create a dataframe with complete cases rows
    for model evaluation for an evaluated variable

    Parameters
    ----------
    model_df : pandas DataFrame
        model results.
    obs_df : pandas DataFrame
        observations .
    var : str
        variable column name.

    Returns
    -------
    df : pandas DataFrame
        dataframe with no NaN values.

    '''
    df = pd.concat([model_df[var], obs_df[var]],
                   axis=1,
                   keys=["wrf", "obs"])
    df.dropna(how="any", inplace=True)
    return df


def mean_bias(model_df, obs_df, var):
    '''
    Calculate Mean Bias

    Parameters
    ----------
    model_df : pandas DataFrame
        DataFrame with model output.
    obs_df : pandas DataFrame
        DataFrame with observation.
    var : str
        Name of variable.

    Returns
    -------
    mb : numpy.float64
        mean bias.

    '''
    df = complete_cases(model_df, obs_df, var)
    mb = df.wrf.mean() - df.obs.mean()
    return mb

def mean_gross_error(model_df, obs_df, var):
    '''
    Calcualte mean gross error

    Parameters
    ----------
    model_df : pandas DataFrame
        DataFrame with model output.
    obs_df : pandas DataFrame
        DataFrame with observation.
    var : str
        Name of variable.

    Returns
    -------
    me : numpy.float64
        Mean gross error.

    '''
    df = complete_cases(model_df, obs_df, var)
    me = (df.wrf - df.obs).abs().mean()
    return me

def root_mean_square_error(model_df, obs_df, var):
    '''
    Calcualte Root mean square error

    Parameters
    ----------
    model_df : pandas DataFrame
        DataFrame with model output.
    obs_df : pandas DataFrame
        DataFrame with observation.
    var : str
        Name of variable.

    Returns
    -------
    rmse : numpy.float64
        root mean square error.

    '''
    df = complete_cases(model_df, obs_df, var)
    rmse = (((df.wrf - df.obs)**2).mean())**0.5
    return rmse


def normalized_mean_bias(model_df, obs_df, var):
    '''
    Calculate the normalized mean bais

    Parameters
    ----------
    model_df : pandas DataFrame
        DataFrame with model output.
    obs_df : pandas DataFrame
        DataFrame with observation.
    var : str
        Name of variable.

    Returns
    -------
    nmb : numpy.float64
        normalized mean bias.

    '''
    if obs_df[var].dropna().empty:
        nmb = np.nan
    else:
        df = complete_cases(model_df, obs_df, var)
        nmb = (df.wrf - df.obs).sum() / df.obs.sum() * 100
    return nmb

def normalized_mean_error(model_df, obs_df, var):
    '''
    Calcualte normalized mean error

    Parameters
    ----------
    model_df : pandas DataFrame
        DataFrame with model output.
    obs_df : pandas DataFrame
        DataFrame with observation.
    var : str
        Name of variable.

    Returns
    -------
    nme : numpy.float64
        normalized mean error.

    '''
    if obs_df[var].dropna().empty:
        nme = np.nan
    else:
        df = complete_cases(model_df, obs_df, var)
        nme = ((df.wrf - df.obs).abs().sum() / 
               df.obs.sum() * 100)
    return nme

def wind_dir_diff(Mi, Oi):
    '''
    Difference between Wind directions based in its
    periodic property. Based on Reboredo et al. 2015

    Parameters
    ----------
    Mi : np.float
        Model wind direction.
    Oi : TYPE
        Observed wind direction.

    Returns
    -------
    Wind difference.

    '''
    wd_dif = Mi - Oi
    if Mi < Oi:
        if (np.abs(wd_dif) < np.abs(360 + wd_dif)):
            ans = wd_dif
        elif (np.abs(wd_dif) > np.abs(360 + wd_dif)):
            ans = 360 + wd_dif
    elif Mi > Oi:
        if (np.abs(wd_dif) < np.abs(wd_dif - 360)):
            ans = wd_dif
        elif (np.abs(wd_dif) > np.abs(wd_dif -360)):
            ans = wd_dif - 360
    else:
        ans = 0.0
    
    return(ans)
    
def wind_dir_mb(model_df, obs_df, wd_name='wd'):
    '''
    Calculates wind direction mean bias based in 
    Reboredo et al. 2015

    Parameters
    ----------
    model_df : pandas DataFrame
        DataFrame with model output.
    obs_df : pandas DataFrame
        DataFrame with observations.
    wd_name : str, optional
        Wind direction column name. The default is 'wd'.

    Returns
    -------
    wd_mb : numpy.float64
        wind direction mean bias.

    '''
    wd_df = pd.DataFrame({
        'mi': model_df[wd_name].values,
        'oi': obs_df[wd_name].values}) 
    wd_df.dropna(how="any", inplace=True)
    dif = wd_df.apply(lambda row: wind_dir_diff(row['mi'], row['oi']),
                      axis=1)
    wd_mb = dif.mean()    
    return wd_mb


def wind_dir_mage(model_df, obs_df, wd_name='wd'):
    '''
    Calculate wind direction mean absolute error

    Parameters
    ----------
    model_df : pandas DataFrame
        DataFrame with model output.
    obs_df : pandas DataFrame
        DataaFrame with observations.
    wd_name : str, optional
        wind direction column name. The default is 'wd'.

    Returns
    -------
    mage : numpy.float64
        wind direction mean gross error.

    '''
    wd_df = pd.DataFrame({
        'mi': model_df[wd_name].values,
        'oi': obs_df[wd_name].values})
    wd_df.dropna(how="any", inplace=True)
    dif = wd_df.apply(lambda row: wind_dir_diff(row['mi'], row['oi']),
                      axis=1)
    if dif.isna().sum() == len(dif.index):
        mage = np.nan
    else:
        mage = dif.abs().mean()
    return mage


def all_stats(model_df, obs_df, var, to_df=False):
    '''
    Calculates recommended statistics from Emery et al. (2017)

    Parameters
    ----------
    model_df : pandas DataFrame
        DataFrame with model output.
    obs_df : pandas DataFrame
        DataFrame with observation.
    var : str
        Name of variable.
    to_df : Bool, optional
        Ouput in DataFrame. The default is False.    

    Returns
    -------
    results : dict or DataFrame
        MB, RMSE, NMB, NME, R, Model and Obs means and std.

    '''
    if var == 'wd':
        results = {
            'MB': wind_dir_mb(model_df, obs_df),
            'ME': wind_dir_mage(model_df, obs_df),
            'aqs': model_df.name.unique()[0]}
    else:
        results = {
            'MB': mean_bias(model_df, obs_df, var),
            'ME': mean_gross_error(model_df, obs_df, var),
            'RMSE': root_mean_square_error(model_df, obs_df, var),
            'NMB': normalized_mean_bias(model_df, obs_df, var),
            'NME': normalized_mean_error(model_df, obs_df, var),
            'R': model_df[var].corr(obs_df[var]),
            'Om': obs_df[var].mean(),
            'Mm': model_df[var].mean(),
            'Ostd': obs_df[var].std(),
            'Mstd': model_df[var].std(),
            'aqs': model_df.name.unique()[0]}
    
    if to_df:
        results = pd.DataFrame(results, index=[var])
    return results




def all_var_stats_per_station(model_df, obs_df, to_df=False):
    '''
    Calculate all stats for each observation parameter

    Parameters
    ----------
    model_df : pandas DataFrame
        DataFrame with model output.
    obs_df : pandas DataFrame
        DataFrame with observations.
    to_df : Bool, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    results : dict or DataFrame
        All Statistic for all observation variables.

    '''
    var_to_eval = obs_df.columns
    results = {}
    for var in var_to_eval:
        results[var] = all_stats(model_df, obs_df, var)
        
    if to_df:
        results = pd.DataFrame.from_dict(results, 
                                         orient='index')        
    return results

def some_vars_stats_per_station(model_df, obs_df, var, to_df=False):
    '''
    Calculate all stats for each observation parameter

    Parameters
    ----------
    model_df : pandas DataFrame
        DataFrame with model output.
    obs_df : pandas DataFrame
        DataFrame with observations.
    to_df : Bool, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    results : dict or DataFrame
        All Statistic for all observation variables.

    '''
    var_to_eval = var
    results = {}
    for var in var_to_eval:
        results[var] = all_stats(model_df, obs_df, var)
        
    if to_df:
        results = pd.DataFrame.from_dict(results, 
                                         orient='index')        
    return results



def all_aqs_all_vars(model_dic, obs_dic, to_df=True, 
                     sort_pol = False, csv = False):
    '''
    Calculate all statistic for all variables for all
    evaluated stations

    Parameters
    ----------
    model_dic : dict
        Dictionaryy containing data frames with station data from model.
    obs_dic : dict
        Dictionaryy containing data frames with station data from aqs.
    to_df : bool, optional
        Return a data frame. The default is True.
    sort_pol : bool, optional
        when to_df=True output sorted by pol. The default is False.
    csv : bool, optional
        When to_df=Truem export it to csv. The default is False.

    Returns
    -------
    result : pandas DataFrame or dict
        All statistic for all variaables for all aqs.

    '''
    result = {}
    for k in model_dic:
        result[k] = all_var_stats_per_station(model_dic[k],
                                               obs_dic[k],
                                               to_df=to_df)
    if to_df:
        result = pd.concat(result.values())
        if sort_pol:
            result.sort_index(inplace=True)
        if csv:
            file_name = '_'.join(result.index.unique().values) + "_stats.csv"
            result.to_csv(file_name, sep=",", index_label="pol")       
        
    return result

def all_aqs_some_vars(model_dic, obs_dic, var, to_df=True, 
                     sort_pol = False, csv = False):
    '''
    Calculate all statistic for all variables for all
    evaluated stations

    Parameters
    ----------
    model_dic : dict
        Dictionaryy containing data frames with station data from model.
    obs_dic : dict
        Dictionaryy containing data frames with station data from aqs.
    to_df : bool, optional
        Return a data frame. The default is True.
    sort_pol : bool, optional
        when to_df=True output sorted by pol. The default is False.
    csv : bool, optional
        When to_df=Truem export it to csv. The default is False.

    Returns
    -------
    result : pandas DataFrame or dict
        All statistic for all variaables for all aqs.

    '''
    result = {}
    for k in model_dic:
        result[k] = some_vars_stats_per_station(model_dic[k],
                                               obs_dic[k], var,
                                               to_df=to_df)
    if to_df:
        result = pd.concat(result.values())
        if sort_pol:
            result.sort_index(inplace=True)
        if csv:
            file_name = '_'.join(result.index.unique().values) + "_stats.csv"
            result.to_csv(file_name, sep=",", index_label="pol")       
        
    return result

def global_stat(model_dic, obs_dic, csv=False):
    '''
    Calculates the global statistics  

    Parameters
    ----------
    model_dic : dict
        Dictionary containing data frames with station data from model.
    obs_dic : dict
        Dictionary containing data frames with station data from aqs.
    csv : bool, optional
        Export the value as csv. The default is False.

    Returns
    -------
    stats : pandas DataFrame
        Contain global statistics.

    '''
    model_df = pd.concat(model_dic)
    obs_df =pd.concat(obs_dic)
    
    stats = all_var_stats_per_station(model_df, obs_df, to_df=True)
    stats.drop(labels='aqs', axis=1, inplace=True)
    if csv:
        file_name = '_'.join(stats.index.values) + "_global_stats.csv"
        stats.to_csv(file_name, sep=",", index_label='pol')
    return stats

    
def global_stat_some_vars(model_dic, obs_dic, var, csv=False):
    '''
    Calculates the global statistics  

    Parameters
    ----------
    model_dic : dict
        Dictionary containing data frames with station data from model.
    obs_dic : dict
        Dictionary containing data frames with station data from aqs.
    csv : bool, optional
        Export the value as csv. The default is False.

    Returns
    -------
    stats : pandas DataFrame
        Contain global statistics.

    '''
    model_df = pd.concat(model_dic)
    obs_df =pd.concat(obs_dic)
    
    stats = some_vars_stats_per_station(model_df, obs_df,var, to_df=True)
    stats.drop(labels='aqs', axis=1, inplace=True)
    if csv:
        file_name = '_'.join(stats.index.values) + "_global_stats.csv"
        stats.to_csv(file_name, sep=",", index_label='pol')
    return stats

def simple_vs_plot(model_df, obs_df, var, ylab, save_fig=False, fmt=None):
    '''
    Temporal serie of model and observe variable

    Parameters
    ----------
    model_df : pandas DataFrame
        DataFrame with model output.
    obs_df : pandas DataFrame
        DataFrame with observations.
    var : str
        Name of variable.
    ylab : str
        Y axis label.
    save_fig : Bool, optional
        ssave the plot. The default is False.
    fmt : str, optional
        Format of figure. The default is None.

    Returns
    -------
    Temporal serie.

    '''
    ax = obs_df[var].plot(label = 'Obs.', linewidth=2.5,
                          marker='D')
    ax.plot(model_df[var], color='orange', linewidth=-2.5, label='WRF',
            marker='o')
    ax.legend()
    ax.set_xlabel('')
    ax.set_ylabel(ylab)
    ax.set_title(model_df.name.unique()[0])
    if save_fig:
        file_name = (var + '_'+ model_df.name.unique()[0] 
                     + fmt)
        plt.savefig(file_name, bbox_inches="tight", dpi=300)
        plt.clf()


def photo_profile(df, main, ax = None, save_fig=False, frmt=None):
    '''
    Plot daily profile of NO, NO2 and O3 concentration.

    Parameters
    ----------
    df : pandas DataFrame
        Dataframe with columns of NO, NO2 and O3.
    main : str
        Plot title.
    ax : matplotlib axes, optional
        plot axe. The default is None.
    save_fig : TYPE, optional
        save the plot. The default is False.
    frmt : str, optional
        if save_fig=True, format of figure. The default is None.

    Returns
    -------
    Plot.

    '''
    df_d = df.groupby(df.index.hour).mean()
    if ax is None:
        ax = plt.gca()
    ax.plot(df_d.no, color='orange', label='NO')
    ax.plot(df_d.no2, color='red', label='NO2')
    ax.plot(df_d.o3, color='#1f77b4', label='O3')
    ax.set_xlabel('Hours')
    ax.set_ylabel('$\mu g / m^3$')
    ax.set_title(main)
    if save_fig:
        file_name = ('photo' + '_'+ df.name.unique()[0] 
                     + frmt)
        plt.savefig(file_name, bbox_inches="tight", dpi=300)
        plt.clf()
    ax.legend()


def photo_profile_comparison(model_df, obs_df, save_fig=False, frmt=None):
    '''
    Compare observation and model daily profile of NO, NO2 and O3
    concentration.

    Parameters
    ----------
    model_df : pandas DataFrame
        Model DataFrame with columns NO, NO2 and O3.
    obs_df : pandas DataFrame
        Observations DataFrame with columns NO, NO2 and O3.
    save_fig : Bool, optional
        save the plot. The default is False.
    frmt : str, optional
        if save_fig=True, format of figure. The default is None.

    Returns
    -------
    Plot.

    '''
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 5))
    photo_profile(obs_df, "Observations", ax=axes[0])
    photo_profile(model_df, "WRF-Chem", ax=axes[1])
    fig.suptitle(model_df.name.unique()[0])
    if save_fig:
        file_name = ('photo_comp' + '_'+ model_df.name.unique()[0] 
                     + frmt)
        plt.savefig(file_name, bbox_inches="tight", dpi=300)
        plt.clf()
    
    

 
