#pip install pytest-notebook
#pip install ipytest
#pip install pyxlsb
#pip install jellyfish
#pip install pyensae
#pip install folium
%matplotlib inline

import pandas as pd
import numpy as np
import warnings
warnings.simplefilter("ignore")
from sqlalchemy import create_engine
import seaborn as sb
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import plotly.offline as py
from pandas.plotting import scatter_matrix
from pandas_profiling import ProfileReport
import jellyfish
import re
import ipytest
import folium


# chargement de la bdd
engine = create_engine('sqlite:///data.db', echo=False)
con = engine.connect()
df_patient = pd.read_sql('select * from patient', con=con)
df_pcr = pd.read_sql('select * from test', con=con)
con.close()

# conversion resultat pcr en boolean
def pcr_status(df):
    df.loc[df.pcr == 'Negative', 'pcr'] = False
    df.loc[df.pcr == 'N', 'pcr'] = False
    df.loc[df.pcr == 'Positive', 'pcr'] = True
    df.loc[df.pcr == 'P', 'pcr'] = True
    return df

def regex_filter(val):
    if val:
        mo = re.search(r'\d',val)
        if mo:
            return True
        else:
            return False
    else:
        return False

# Cette fonction a pour but de corriger les permutations entre les codes postaux et les villes
def change_P_S(df):
    for index, row in df.iterrows():
        pc = row['postcode']
        sb = row['suburb']
        if(regex_filter(pc) != True and pc != None):
            df.suburb[index] = pc
            df.postcode[index] = sb
    return df

# Cette fonction a pour but de corriger les erreurs de frappe sur les abréviations du nom des etats
def correct_state(df):
    state_list = ['sa','wa','nsw','qld','tas','vic','act','jbt','nt','cx','cc','hm']
    for index, row in df.iterrows():
        for index1, row2 in enumerate(state_list):
            value = row['state']
            score = jellyfish.jaro_distance(str(value),str(row2))
            if(value != None and value not in (state_list)):
                df.state[index] = None
            elif(score > 0.62 and score < 1 and value != None  and value != 'sa' and value != 'wa'): #sa et wa etant trop proche on ne les compare pas
                df.state[index] = row2
    return df


def detect_duplicates(df):
    size = len(df)
    df.date_of_birth = df.date_of_birth.fillna(0).astype(int) # changement type du champs date de naissance 
    df.street_number = df.street_number.fillna(0).astype(int) # changement type du champs numéro de rue 
    df.age = df.age.fillna(0).astype(int) # changement type de l'age
    mergedDf = pd.merge(df,df_pcr_dev)
    df = mergedDf
    change_P_S(df)
    correct_state(df)
    df = df.sort_values('patient_id').drop_duplicates('patient_id', keep='first').sort_index()
    df = df.drop_duplicates(subset=['given_name','surname','postcode','state','date_of_birth'], keep='first')
    print('Pourcentage de données dupliquéees : ',((size-len(df))/size)*100,'%')
    return df

cleandf = detect_duplicates(df_patient)


ipytest.autoconfig()


%%run_pytest[clean]
expected_len_cleandf = len(cleandf)
expected_len_df_patient = len(df_patient)
def test_detect_duplicates():
    assert len(detect_duplicates(df_patient)) == expected_len_cleandf
    assert len(df_patient) == expected_len_df_patient
    assert type(df_patient) == pd.core.frame.DataFrame









