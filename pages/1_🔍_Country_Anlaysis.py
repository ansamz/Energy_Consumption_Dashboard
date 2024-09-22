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

st.set_page_config(layout="wide", page_icon='🌍')

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

st.markdown(f"<h3 style='text-align: left; color: red;'>{selected_country} Energy Consumption</h3>", unsafe_allow_html=True)

country_data = data[data['country'] == selected_country]

daily_consumption = country_data.groupby(['date', 'country'])['load'].mean().reset_index()
hourly_consumption = country_data.groupby(['hour_start', 'country'])['load'].mean().reset_index()
daily_consumption['moving_avg'] = daily_consumption['load'].rolling(window=30).mean()

# X values as indices for regression
x_values = np.arange(len(daily_consumption))  
y_values = daily_consumption['load'].values

# Degree 1 for linear regression
slope, intercept = np.polyfit(x_values, y_values, 1)  
trend_line = slope * x_values + intercept

fig_daily = go.Figure()
fig_daily.add_trace(go.Scatter(x=daily_consumption['date'], 
                               y=daily_consumption['load'], 
                               mode='lines', 
                               name=selected_country,
                               hoverinfo='x+y'))

fig_daily.add_trace(go.Scatter(x=daily_consumption['date'], 
                               y=daily_consumption['moving_avg'], 
                               mode='lines', 
                               name='30-day Moving Average',
                               line=dict(color='orange', dash='dash'),
                               hoverinfo='x+y'))

fig_daily.add_trace(go.Scatter(x=daily_consumption['date'], 
                               y=trend_line, 
                               mode='lines', 
                               name='Trend Line',
                               line=dict(color='red', dash='dot'),
                               hoverinfo='x+y'))

fig_daily.update_layout(
    title=f"Average Daily Energy Consumption - {selected_country}",
    xaxis_title='Date',
    yaxis_title='Energy Consumption (Load)',
    template='plotly_white', width=800, height=700
)

st.plotly_chart(fig_daily, use_container_width=True)

month_col, week_day_col = st.columns(2)

average_load_by_month = country_data.groupby('month')['load'].mean().reset_index()
fig_month = px.bar(average_load_by_month, x='month', y='load', 
            labels={'load': 'Average Load (MW)', 'month': 'month'},
            width=800, height=700,
            title='Average Energy Consumption by Month')
month_col.plotly_chart(fig_month, use_container_width=True)

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
average_load_by_day = country_data.groupby('start_day_of_week')['load'].mean().reset_index()
average_load_by_day['day_order'] = average_load_by_day['start_day_of_week'].apply(lambda x: day_order.index(x))
average_load_by_day = average_load_by_day.sort_values(by='day_order')

fig_day_week = px.bar(average_load_by_day, x='start_day_of_week', y='load', 
            labels={'load': 'Average Load (MW)', 'start_day_of_week': 'Day of the Week'},
            width=800, height=700,
            title='Average Energy Consumption by Day of the Week')
week_day_col.plotly_chart(fig_day_week, use_container_width=True)

fig_hourly = go.Figure()
fig_hourly.add_trace(go.Scatter(x=hourly_consumption['hour_start'], 
                                y=hourly_consumption['load'], 
                                mode='lines', 
                                name=selected_country))

fig_hourly.update_layout(
    title=f"Average Hourly Energy Consumption",
    xaxis_title='Hour of the Day',
    yaxis_title='Energy Consumption (Load)',
    template='plotly_white',
    width=800, height=700
)

st.plotly_chart(fig_hourly, use_container_width=True)
