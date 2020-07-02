#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 16:22:58 2020

@author: mgavidia
"""



import os
import pickle
import wrf as wrf
import pandas as pd
import xarray as xr
import wrf_sp_eval.qualar_py as qr

def ppm_to_ugm3(pol, t2, psfc, M):
    '''
    Transform concentration from ppm to ugm⁻3

    Parameters
    ----------
    pol : xarray DataArray
        Pollutant concentration in ppm.
    t2 : xarray DataArray
        Temperature at 2m (K).
    psfc : xarray DataArray
        Surface pressure (Pa).
    M : int
        Pollutant molecular mass.

    Returns
    -------
    None.

    '''
    R = 8.3142 # J/K mol
    pol_ugm3 = pol * psfc * M / (R * t2)    
    pol_ugm3 = pol_ugm3.rename(pol.name)
    return(pol_ugm3)


def stations_in_domains(station_file, wrfout, wrfvar):
    station = pd.read_csv(station_file)
    station_xy = wrf.ll_to_xy(wrfout,
                              longitude=station.lon,
                              latitude=station.lat)
    station['x'] = station_xy[0]
    station['y'] = station_xy[1]
    filter_dom = ((station.x >0) & (station.x < wrfvar.shape[2]) & 
                  (station.y > 0) & (station.y < wrfvar.shape[1]))
    station_dom = station[filter_dom]
    return station_dom



def wrf_var_retrieve(wrf_var, cetesb_dom, i):
    '''
    Extract point data from xarray 

    Parameters
    ----------
    wrf_var : xarray DataArray
        WRF var output.
    cetesb_dom : pandas Dataframe
        Inforamtion of stations .
    i : TYPE
        row number of interested station.

    Returns
    -------
    1 dim xarray with temporal information of variable in station.

    '''
    wrf_var = wrf_var.sel(south_north=cetesb_dom.y.values[i],
                          west_east=cetesb_dom.x.values[i])
    return(wrf_var)



    
def wrf_station_retrieve(i, cetesb_dom, *args, to_local=False,
                         time_zone="America/Sao_Paulo"):
    '''
    Extract wrf parameter from one station

    Parameters
    ----------
    i : int
        station row in cetesb_dom.
    cetesb_dom : pandas DataFrame
        Station information.
    *args : xarray DataArray
        wrfout extracted variables.
    to_local : Bool, optional
        Change the time zone to local. The default is False.
    time_zone : str, optional
        if to_local=true, transform date to local_time. The default is "America/Sao_Paulo".

    Returns
    -------
    Pandas Dataframe with station parameter in columns.

    '''
    wrf_sta = pd.DataFrame()
    wrf_sta['date'] = args[0].Time.values
    wrf_sta['code'] = cetesb_dom.code.values[i]
    wrf_sta['name'] = cetesb_dom.name.values[i]
    for arg in args:
        if arg.name == "uvmet10_wspd_wdir":
            wrf_sta['ws'] = wrf_var_retrieve(arg.sel(wspd_wdir="wspd"),
                                             cetesb_dom, i).values
            wrf_sta['wd'] = wrf_var_retrieve(arg.sel(wspd_wdir="wdir"),
                                             cetesb_dom, i).values
        else:            
            wrf_sta[arg.name.lower()] = wrf_var_retrieve(arg, cetesb_dom, i).values
        
        
    if to_local:
        wrf_sta['date'] = (
            wrf_sta['date']
            .dt.tz_localize('UTC')
            .dt.tz_convert(time_zone))
    else:
        wrf_sta['date'] = (
            wrf_sta['date']
            .dt.tz_localize('UTC'))
        

    wrf_sta.set_index('date', inplace=True)
        
    return(wrf_sta)





def cetesb_from_wrf(cetesb_dom, args, to_local=False):
    '''
    Extract all wrf parameter from station in cetesb_dom

    Parameters
    ----------
    cetesb_dom : pandas DataFrame
        Information of stations.
    *args : TYPE
        wrfout extracted variables..
    to_local : TYPE, optional
        Add local time. The default is False.

    Returns
    -------
    Dicitionary, each key is a station.

    '''
    wrf_cetesb ={}
    for i in range(len(cetesb_dom.index)):
        wrf_cetesb[cetesb_dom.name.iloc[i]] = wrf_station_retrieve(i, 
                                                                   cetesb_dom, 
                                                                   *args, 
                                                                   to_local=to_local)
    return(wrf_cetesb)
    
    

# Now we retrieve the data from CETESB

def qualar_st_end_time(wrf_var):
    '''
    Retrieve start and end date of simulation
    to be used to download CETESB qualar information

    Parameters
    ----------
    wrf_var : xarray DataArray
        wrfout_extracted data.

    Returns
    -------
    Tuple with start and end date in %d/%m/%Y format.

    '''
    start_end = (wrf_var
                 .Time
                 .to_dataframe()
                 .Time
                 .dt.tz_localize('UTC')
                 .dt.tz_convert('America/Sao_Paulo')
                 .dt.strftime('%d/%m/%Y'))
    return((start_end[0], start_end[-1]))




def model_eval_setup(wrf_dic, cet_dic, date_start):
    '''
    Prepare model output dictionary and obsrevation dictionary, 
    for model evaluation: remove model model spin-up and
    filter Observation dates according simulation data

    Parameters
    ----------
    wrf_dic : dict
        Dict with stations wrf ouput DataFrames.
    cet_dic : dict
        Dict with observation DataFrame.
    date_start : string
        Date after spin-up in %Y-%m-%d.

    Returns
    -------
    wrf_dic : Dict
        Model dictitonary ready to model evaluation.
    cet_dic : Dict
        Observation dictitonary ready to model evaluation.

    '''
    for aqs in wrf_dic:
        wrf_dic[aqs] = wrf_dic[aqs][date_start: ]
    
    for aqs in cet_dic:        
        cet_dic[aqs] = (cet_dic[aqs].loc[wrf_dic[aqs].index])
        
    return (wrf_dic, cet_dic)


def download_load_cetesb_met(cetesb_dom, cetesb_login, 
                             cetesb_pass, start, end):
    '''
    Download and save cetesb meteorological data for 
    wrfoutput times 

    Parameters
    ----------
    cetesb_dom : pandas DataFrame
        Information of stations.
    cetesb_login : str
        Cetesb qualAr user name.
    cetesb_pass : str
        Cetesb qualAr password.
    start : str
        Start date to download, use qualar_st_end_tim().
    end : str
        End date to download, use qualar_st_end_tim().

    Returns
    -------
    cet_dict : dict
        Dictionary containing dataframes with met data 
        per station.

    '''
    file_name = ("met_" + start.replace("/", "_") + 
                 '-' + end.replace("/", "_") + ".pkl")
    if os.path.exists(file_name):
        print("There is downloaded data, now opening")
        a_dict = open(file_name, "rb")
        cet_dict = pickle.load(a_dict)
        a_dict.close()
    else:
        print("No data available, now downloading ")
        cet_dict = {}
        for code in cetesb_dom.code:
            cet_dict[cetesb_dom.name[cetesb_dom.code == code].values[0]] = (
                qr.all_met(cetesb_login, cetesb_pass, start, end, 
                           code, in_k = True))
        a_dict = open(file_name, "wb")
        pickle.dump(cet_dict, a_dict)
        a_dict.close()
    return cet_dict


def download_load_cetesb_pol(cetesb_dom, cetesb_login, 
                             cetesb_pass, start, end):
    '''
    Download and save cetesb criteria pollutant data for 
    wrfoutput times 

    Parameters
    ----------
    cetesb_dom : pandas DataFrame
        Information of stations.
    cetesb_login : str
        Cetesb qualAr user name.
    cetesb_pass : str
        Cetesb qualAr password.
    start : str
        Start date to download, use qualar_st_end_tim().
    end : str
        End date to download, use qualar_st_end_tim().

    Returns
    -------
    cet_dict : dict
        Dict containing data frames with pollutatn information per
        station

    '''
    file_name = ("pol_" + start.replace("/", "_") + 
                 '-' + end.replace("/", "_") + ".pkl")
    if os.path.exists(file_name):
        print("There is downloaded data, now opening")
        a_dict = open(file_name, "rb")
        cet_dict = pickle.load(a_dict)
        a_dict.close()
    else:
        print("No data available, now downloading")
        cet_dict = {}
        for code in cetesb_dom.code:
            cet_dict[cetesb_dom.name[cetesb_dom.code == code].values[0]] = (
                qr.all_photo(cetesb_login, cetesb_pass, start, end, code))
        a_dict = open(file_name, "wb")
        pickle.dump(cet_dict, a_dict)
        a_dict.close()
    return cet_dict

def read_aqs_obs(code, sep, ident='_obs.csv', to_local=True, 
                 time_zone="America/Sao_Paulo"):
    '''
    Read AQS information from csv filrs

    Parameters
    ----------
    code : int
        AQS code.
    sep : str
        column separator.
    ident : str, optional
        aqs file name identifier. The default is '_obs.csv'.
    to_local : Bool, optional
        Localize date time zone. The default is True.
    time_zone : str, optional
        AQS date timezone. The default is "America/Sao_Paulo".

    Returns
    -------
    aqs : pandas DataFrame
        Data frame with aqs data.

    '''
    file_name = str(code) + ident
    aqs = pd.read_csv(file_name, sep=sep)
    aqs['date'] = pd.to_datetime(aqs['date'],
                                 format="%Y-%m-%d %H:%M:%S")
    if to_local:
        aqs['date'] = aqs['date'].dt.tz_localize(time_zone)
    else:
        aqs['date'] = aqs['date'].dt.tz_localize("UTC")
    aqs.set_index('date', inplace=True)
    return aqs