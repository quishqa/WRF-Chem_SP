#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 16:37:44 2020

@author: quisqa
"""

import wrf as wrf
from netCDF4 import Dataset
import wrf_sp_eval.data_preparation as dp
import wrf_sp_eval.qualar_py as qr
import wrf_sp_eval.model_stats as ms


# Reading wrfout
wrfout = Dataset("wrfout_d02_2018-06-21_00:00:00")

# Extracting met variables
t2 = wrf.getvar(wrfout, "T2", timeidx=wrf.ALL_TIMES, method="cat")
rh2 = wrf.getvar(wrfout, "rh2", timeidx=wrf.ALL_TIMES, method="cat")
psfc = wrf.getvar(wrfout, "PSFC", timeidx=wrf.ALL_TIMES, method="cat")
wind = wrf.getvar(wrfout, "uvmet10_wspd_wdir", timeidx=wrf.ALL_TIMES,
                  method="cat")
ws = wind.sel(wspd_wdir="wspd")
wd = wind.sel(wspd_wdir="wdir")

# Extracting pollutants variables
o3 = wrf.getvar(wrfout, "o3", timeidx=wrf.ALL_TIMES, method="cat")
co = wrf.getvar(wrfout, "co", timeidx=wrf.ALL_TIMES, method="cat")
no = wrf.getvar(wrfout, "no", timeidx=wrf.ALL_TIMES, method="cat")
no2 = wrf.getvar(wrfout, "no2", timeidx=wrf.ALL_TIMES, method="cat")


# Retrieving pollutants from surface
o3_sfc = o3.isel(bottom_top=0)
co_sfc = co.isel(bottom_top=0)
no_sfc = no.isel(bottom_top=0)
no2_sfc = no2.isel(bottom_top=0)

# Transform surface polutant from ppm to ug/m3
o3_u = dp.ppm_to_ugm3(o3_sfc, t2, psfc, 48)
no_u = dp.ppm_to_ugm3(no_sfc, t2, psfc, 30)
no2_u = dp.ppm_to_ugm3(no2_sfc, t2, psfc, 46)


# Downloading CETESB data for  model evaluation

# CETESB qualR username and password
cetesb_login = 'your_user_name'
cetesb_pass = 'your_password'

# Getting dates to download from wrfout t2 variable
start_date, end_date = dp.qualar_st_end_time(t2)

# Loading List of stations and use only the stations inside wrfout
cetesb_dom = dp.stations_in_domains("./test.dat", wrfout, t2)

# Downloading meteorological data and pollutant data from CETESB QUALAR
cetesb_met = dp.download_load_cetesb_met(cetesb_dom, cetesb_login, cetesb_pass,
                                      start_date, end_date)
cetesb_pol = dp.download_load_cetesb_pol(cetesb_dom, cetesb_login, cetesb_pass,
                                      start_date, end_date)

# Extracting model result from station locations, note that the variables
# to extract is a tupple (). to_local=True is to tranform model UTC to
# Sao Paulo local time
wrf_met = dp.cetesb_from_wrf(cetesb_dom, ( t2, rh2, wind),
                          to_local=True)
wrf_pol = dp.cetesb_from_wrf(cetesb_dom, ( o3_u, no_u, no2_u, co_sfc),
                          to_local=True)


# Preparing model and observation dictionaries for model evaluation:
# Remove spin_up time, extracting use same times in model and observation
# dictionary

model_met, obs_met = dp.model_eval_setup(wrf_met, cetesb_met, date_start='2018-06-24')
model_pol, obs_pol = dp.model_eval_setup(wrf_pol, cetesb_pol, date_start='2018-06-24')


# Calculating performance statistic for each staion
pol_eval = ms.all_aqs_all_vars(wrf_pol, cetesb_pol, csv=True)
met_eval = ms.all_aqs_all_vars(wrf_met, cetesb_met, csv=True)

# Calculating global statistic for each variable
pol_glob_eval = ms.global_stat(model_pol, obs_pol, csv=True)
met_global_eval = ms.global_stat(model_met, obs_met, csv=True)


# Time series comparison
for k in model_met:
    ms.simple_vs_plot(model_met[k], obs_met[k], 't2', '$T2 \; (K)$',
                      True, '.png')
    ms.simple_vs_plot(model_met[k], obs_met[k], 'rh2', '$RH2 \; (\%)$',
                      True, '.png')
    ms.simple_vs_plot(model_met[k], obs_met[k], 'ws', '$WS10 \; (m/s)$',
                      True, '.png')

for k in model_pol:
    ms.simple_vs_plot(model_pol[k], obs_pol[k], 'o3', '$O_3 \; (\mu g / m^3)$',
                      True, '.png')
    ms.simple_vs_plot(model_pol[k], obs_pol[k], 'no', '$NO \; (\mu g / m^3)$',
                      True, '.png')
    ms.simple_vs_plot(model_pol[k], obs_pol[k], 'no2', '$NO_2 \; (\mu g / m^3)$',
                      True, '.png')
    ms.simple_vs_plot(model_pol[k], obs_pol[k], 'co', '$CO \; (ppm)$',
                      True, '.png')

# Photochemical profile comparison

pin_wrf = model_pol['Pinheiros']
pin_obs = obs_pol['Pinheiros']

ms.photo_profile_comparison(pin_wrf, pin_obs, save_fig=True, frmt=".png")
