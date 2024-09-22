import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from geopy.geocoders import Nominatim
import pycountry
import pypopulation
import glob
import pyodbc
import json
import os

st.set_page_config( layout="wide", page_icon='🌍')

text_contents = '''Coming Soon :D'''
st.download_button("Download dashboard as pdf", text_contents)

# -------------------------------------------------------
# Connection to SQL server
# server = st.secrets["azure_sql"]["server"]
# database = st.secrets["azure_sql"]["database"]
# username = st.secrets["azure_sql"]["username"]
# password = st.secrets["azure_sql"]["password"]
# driver = '{ODBC Driver 17 for SQL Server}'
# conn = pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}')

if 'data' not in st.session_state:
    # -------------------------
    # Read data from computer
    # -------------------------
    files = glob.glob('data/*.parquet')
    dataframes = []
    
    for file in files:
        df = pd.read_parquet(file)
        # change to / on linux and deployment
        df['country'] = file.split('\\')[-1].replace('.parquet', '')
        dataframes.append(df)

    data = pd.concat(dataframes, ignore_index=True)

    # ------------------------
    # read data from azure DB
    # query = 'SELECT * FROM [dbo].[EnergyConsumption]'
    # data = pd.read_sql(query, conn)
    # data = data.drop_duplicates()

    data['start'] = pd.to_datetime(data['start'])
    data['end'] = pd.to_datetime(data['end'])
    data['hour_start'] = data['start'].dt.hour
    data['hour_end'] = data['end'].dt.hour
    data['start_day_of_week'] = data['start'].dt.day_name()
    data['end_day_of_week'] = data['end'].dt.day_name()
    data['date'] = data['start'].dt.date
    data['year'] = data['start'].dt.year
    data['month'] = data['start'].dt.month

    population_data = {}
    for country in data['country'].unique():
        try:
            population_data[country] = pypopulation.get_population(country.upper())
        except:
            population_data[country] = None

    data['population'] = data['country'].replace(population_data)

    capital_cities = {
        'at': 'Vienna', 'be': 'Brussels', 'ch': 'Bern', 'de': 'Berlin', 'dk': 'Copenhagen',
        'es': 'Madrid', 'fr': 'Paris', 'gb': 'London', 'ie': 'Dublin', 'it': 'Rome',
        'lu': 'Luxembourg', 'nl': 'Amsterdam', 'no': 'Oslo', 'pt': 'Lisbon', 'se': 'Stockholm'
    }

    country_map = {
        'at': 'Austria', 'be': 'Belgium', 'ch': 'Switzerland', 'de': 'Germany', 'dk': 'Denmark',
        'es': 'Spain', 'fr': 'France', 'gb': 'United Kingdom', 'ie': 'Ireland', 'it': 'Italy',
        'lu': 'Luxembourg', 'nl': 'Netherlands', 'no': 'Norway', 'pt': 'Portugal', 'se': 'Sweden'
    }

    data['capital_city'] = data['country'].replace(capital_cities)
    data['country'] = data['country'].replace(country_map)

    st.session_state.data = data

data = st.session_state.data

selected_country = st.selectbox("Select a Country", options=data['country'].unique())

st.markdown(f"<h3 style='text-align: left; color: red;'>{selected_country} Energy Consumption Anomaly Detector</h3>", unsafe_allow_html=True)

country_data = data[data['country'] == selected_country]

year_col, month_col, _ = st.columns([0.2, 0.2, 0.6])

select_year = year_col.selectbox('Select a year', country_data.year.unique())
country_data_year = country_data[country_data['year'] == select_year]

select_month = month_col.selectbox('Select a month', country_data_year.month.unique())
country_data_month = country_data_year[country_data_year['month']==select_month]

country_data_month['z_score'] = (country_data_month['load'] - country_data_month['load'].mean()) / country_data_month['load'].std()

# define outliers as points with Z-score > 2 or < -2
country_data_month['outlier'] = country_data_month['z_score'].abs() > 2

fig_outliers = go.Figure()
fig_outliers.add_trace(go.Scatter(x=country_data_month['start'], y=country_data_month['load'], 
                         mode='lines+markers', 
                         name='Normal Load'))
outliers = country_data_month[country_data_month['outlier']]
fig_outliers.add_trace(go.Scatter(x=outliers['start'], y=outliers['load'], 
                         mode='markers', 
                         name='Outliers', 
                         marker=dict(color='red', size=10, symbol='circle')))

fig_outliers.update_layout(
    title='Hourly Energy Consumption with Outliers',
    xaxis_title='Hour',
    yaxis_title='Energy Consumption (MW)',
    template='plotly_white',
    width=900, height=600
)

st.plotly_chart(fig_outliers, use_container_width=True)
