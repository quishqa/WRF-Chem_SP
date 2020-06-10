import requests
import pandas as pd
import datetime as dt
from bs4 import BeautifulSoup


# SOS from:
# https://stackoverflow.com/questions/43359479/pandas-parsing-2400-instead-of-0000

 
def my_to_datetime(date_str):
    if date_str[11:13] != '24':
        return pd.to_datetime(date_str, format='%d/%m/%Y_%H:%M')

    date_str = date_str[0:11] + '00' + date_str[13:]
    return pd.to_datetime(date_str, format='%d/%m/%Y_%H:%M') + \
           dt.timedelta(days=1)


def cetesb_data_download(cetesb_login, cetesb_password, 
                        start_date, end_date, 
                        parameter, station, csv=False):     
  
    login_data = {
        'cetesb_login': cetesb_login,
        'cetesb_password': cetesb_password
    }
    
    search_data = {
        'irede': 'A',
        'dataInicialStr':start_date,
        'dataFinalStr':end_date,
        'iTipoDado': 'P',
        'estacaoVO.nestcaMonto':station,
        'parametroVO.nparmt':parameter
    }
    
    with requests.Session() as s:
        url = "https://qualar.cetesb.sp.gov.br/qualar/autenticador"
        r = s.post(url, data=login_data)
        url2 = "https://qualar.cetesb.sp.gov.br/qualar/exportaDados.do?method=pesquisar"
        r = s.post(url2, data=search_data)
        soup = BeautifulSoup(r.content, 'lxml')
        
    data = []
    table = soup.find('table', attrs={'id':'tbl'})
    rows = table.find_all('tr')
    row_data = rows[2:]
    for row in row_data:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols if ele])    
        
    dat = pd.DataFrame(data)
           
    # Creating a complete df with all dates
    day1 = pd.to_datetime(start_date, format='%d/%m/%Y')
    day2 = pd.to_datetime(end_date, format='%d/%m/%Y') + dt.timedelta(days=1)
    all_date = pd.DataFrame(index=pd.date_range(day1.strftime('%m/%d/%Y'), 
                                                day2.strftime('%m/%d/%Y'),
                                                freq='H'))
    if len(dat) <= 1:
        dat = pd.DataFrame(columns=['day', 'hour', 'name', 'pol_name', 'units', 'val'])        
    else:    
        dat = dat[[3, 4, 6, 7, 8, 9]]
        dat.columns = ['day', 'hour', 'name', 'pol_name', 'units', 'val']
        dat['date'] = dat.day + '_' + dat.hour

        # Changing date type to string to datestamp
        dat['date'] = dat.date.apply(my_to_datetime)

        # Changing val type from string/object to numeric
        dat['val'] = dat.val.str.replace(',', '.').astype(float)

        # Filling empy dates
        dat.set_index('date', inplace=True)
       
    
    dat_complete = all_date.join(dat)
    file_name = str(parameter) + '_' + str(station) +' .csv'
    if csv:
        dat_complete.to_csv(file_name, index_label='date')
    else:
        return dat_complete


def all_photo(cetesb_login, cetesb_password, start_date, end_date, station, 
              csv_photo=False):
    o3 = cetesb_data_download(cetesb_login, cetesb_password, 
                              start_date, end_date, 63, station)
    no = cetesb_data_download(cetesb_login, cetesb_password, 
                              start_date, end_date, 17, station)
    no2 = cetesb_data_download(cetesb_login, cetesb_password, 
                               start_date, end_date, 15, station)
    co = cetesb_data_download(cetesb_login, cetesb_password, 
                              start_date, end_date, 16, station)
    
    all_photo_df = pd.DataFrame({
        'o3': o3.val,
        'no': no.val,
        'no2': no2.val,
        'co': co.val
    }, index=o3.index)
    
    all_photo_df.index = all_photo_df.index.tz_localize('America/Sao_Paulo')
    
    if csv_photo:
        all_photo_df.to_csv('all_photo_' + str(station) + '.csv',
                            index_label='date')
    else:
        return all_photo_df

    
def all_met(cetesb_login, cetesb_password, start_date, end_date, station, 
            in_k = False, rm_flag = True, csv_met=False):
    tc = cetesb_data_download(cetesb_login, cetesb_password, 
                              start_date, end_date, 25, station)
    rh = cetesb_data_download(cetesb_login, cetesb_password, 
                              start_date, end_date, 28, station)
    ws = cetesb_data_download(cetesb_login, cetesb_password, 
                              start_date, end_date, 24, station)
    wd = cetesb_data_download(cetesb_login, cetesb_password, 
                              start_date, end_date, 23, station)
    if in_k:
        K = 273.15
    else:
        K = 0
    
    all_met_df = pd.DataFrame({
        't2': tc.val + K,
        'rh2': rh.val,
        'ws': ws.val,
        'wd': wd.val
    }, index=tc.index)
    
    all_met_df.index = all_met_df.index.tz_localize('America/Sao_Paulo')
    
    # Filtering 777 and 888 values
    if rm_flag:
        filter_flags = all_met_df['wd'] <= 360
        all_met_df['wd'].where(filter_flags, inplace=True)
    
    # Export to csv
    if csv_met:
        all_met_df.to_csv('all_met_' + str(station) + '.csv',
                            index_label='date')
    else:
        return all_met_df

    
