import streamlit as st
import pandas as pd
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

st.set_page_config(page_title="Energy Consumption", 
        		   page_icon='🌍',
                   layout="wide", 
                   menu_items={
                       'About': "App using various models to detect fruits and vegetables"
                   })

st.markdown("<h1 style='text-align: center; color: orange;'>Energy Consumption Dashboard</h1>", unsafe_allow_html=True)

# fake button for demonstration
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

if ('data' not in st.session_state) and ('capital_data' not in st.session_state):
    # -------------------------
    # Read data from computer
    # -------------------------
    files = glob.glob('data/*.parquet')
    dataframes = []
    
    for file in files:
        df = pd.read_parquet(file)
        df = df.dropna()
        df = df.drop_duplicates().reset_index(drop=True)
        # change to / on linux and deployment
        # df['country'] = file.split('\\')[-1].replace('.parquet', '')
        df['country'] = file.split('/')[-1].replace('.parquet', '')
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

    def get_capital_coordinates(country_code, capital_city):
        try:
            country_name = pycountry.countries.get(alpha_2=country_code.upper()).name
            geolocator = Nominatim(user_agent="my_application")
            location = geolocator.geocode(f"{capital_city}, {country_name}")

            if location:
                return {
                    "country": country_name,
                    "capital_city": capital_city,
                    "latitude": location.latitude,
                    "longitude": location.longitude
                }
            else:
                return None
        except Exception as e:
            print(f"Error getting coordinates for {capital_city}, {country_code}: {str(e)}")
            return None

    coordinates = [get_capital_coordinates(code, city) for code, city in capital_cities.items()]
    capital_coords_df = pd.DataFrame(coordinates)

    capital_data = pd.merge(data, capital_coords_df[['capital_city', 'latitude', 'longitude']], left_on='capital_city', right_on='capital_city', how='left')

    st.session_state.data = data
    st.session_state.capital_data = capital_data

capital_data = st.session_state.capital_data
data = st.session_state.data

# -------------------------------------------------------------------------------
# app

annual_consumption = capital_data.groupby(['year', 'country', 'latitude', 'longitude', 'population'])['load'].mean().reset_index()

st.markdown("<h2 style='text-align: left; color: red;'>🌍 Overview of Annual Energy Consumption Patterns Across Europe</h2>", unsafe_allow_html=True)

deo_col, bar_col = st.columns(2)

with open('data/countries.geojson') as f:
    countries_geojson = json.load(f)

# map plot
fig_geo = px.choropleth_mapbox(annual_consumption, 
                            geojson=countries_geojson, 
                            locations='country', 
                            featureidkey="properties.ADMIN",
                            color='load', 
                            animation_frame='year',
                            mapbox_style="white-bg",
                            color_continuous_scale=px.colors.sequential.Turbo)

fig_geo.update_layout(mapbox_zoom=2.5, mapbox_center={"lat": 54.5260, "lon": 15.2551},
                        width=1000, height=800)

deo_col.plotly_chart(fig_geo, use_container_width=True)

# barplot per country
fig_bar_country = px.bar(annual_consumption, x='country', y='load', 
            labels={'load': 'Annual Consumption (MW)', 'country': 'Country'},
            animation_frame='year',
            width=800, height=800)

fig_bar_country.update_layout(xaxis={'categoryorder':'total ascending'})
bar_col.plotly_chart(fig_bar_country, use_container_width=True)

# Distribution of overall evergy consumption
show_histogram_checkbox = st.checkbox('Show Overall Distribution of Energy consumption')
if show_histogram_checkbox:
    fig_dist = px.histogram(data, x='load', title="Distribution of Energy Consumption (Load)", width=800, height=600)
    st.plotly_chart(fig_dist)

st.markdown("<h3 style='text-align: left; color: red;'>Energy Consumption per Country</h3>", unsafe_allow_html=True)

box_col, box_norm_col = st.columns(2)

fig_box = go.Figure()
fig_box.add_trace(go.Box(x=data['country'], y=data['load'], name='Load Distribution'))
fig_box.update_layout(title="Distribution of Load by Country", width=1000, height=800)
box_col.plotly_chart(fig_box, use_container_width=True)

data['normalized_load'] = data['load'] / data['population']
fig_box2 = go.Figure()
fig_box2.add_trace(go.Box(x=data['country'], y=data['normalized_load'], name='Normalized Load per Capita'))
fig_box2.update_layout(title="Distribution of Normalized Load by Country", width=1000, height=800)
box_norm_col.plotly_chart(fig_box2, use_container_width=True)
