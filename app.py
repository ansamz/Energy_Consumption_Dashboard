import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from geopy.geocoders import Nominatim
import pycountry
import pypopulation
import glob

st.set_page_config(page_title="Energy Consumption", 
        		   page_icon="apple", 
                #    layout="wide", 
                   menu_items={
                       'About': "App using various models to detect fruits and vegetables"
                   })

st.markdown("<h1 style='text-align: center; color: blue;'>Energy Consumption Dashboard</h1>", unsafe_allow_html=True)

if ('data' not in st.session_state) and ('capital_data' not in st.session_state):
    files = glob.glob('data/*.parquet')
    dataframes = []
    
    for file in files:
        df = pd.read_parquet(file)
        df['country'] = file.split('\\')[-1].replace('.parquet', '')
        dataframes.append(df)

    data = pd.concat(dataframes, ignore_index=True)
    data['start'] = pd.to_datetime(data['start'])
    data['end'] = pd.to_datetime(data['end'])
    data['hour_start'] = data['start'].dt.hour
    data['hour_end'] = data['end'].dt.hour
    data['start_day_of_week'] = data['start'].dt.day_name()
    data['end_day_of_week'] = data['end'].dt.day_name()
    data['date'] = data['start'].dt.date
    data['year'] = data['start'].dt.year

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

annual_consumption = capital_data.groupby(['year', 'country', 'latitude', 'longitude'])['load'].mean().reset_index()

# -------------------------------------------------------------------------------
# app

# Plot 1: GeoPlot
fig_geo = px.scatter_mapbox(annual_consumption, lat='latitude', lon='longitude',
                            color='load', size='load',
                            animation_frame='year',
                            mapbox_style="open-street-map",
                            color_continuous_scale=px.colors.sequential.Blues,
                            size_max=15, zoom=3,
                            title='Energy Consumption by Country Over Time')
fig_geo.update_layout(width=1000, height=800)
st.plotly_chart(fig_geo)

selected_country = st.selectbox("Select a Country", options=data['country'].unique())

country_data = data[data['country'] == selected_country]

daily_consumption = country_data.groupby(['date', 'country'])['load'].mean().reset_index()
hourly_consumption = country_data.groupby(['hour_start', 'country'])['load'].mean().reset_index()

# Plot 2: Average Hourly Energy Consumption
fig_hourly = go.Figure()
fig_hourly.add_trace(go.Scatter(x=hourly_consumption['hour_start'], 
                                y=hourly_consumption['load'], 
                                mode='lines', 
                                name=selected_country))

fig_hourly.update_layout(
    title=f"Average Hourly Energy Consumption - {selected_country}",
    xaxis_title='Hour of the Day',
    yaxis_title='Energy Consumption (Load)',
    template='plotly_white'
)

st.plotly_chart(fig_hourly)

# Plot 3: Average Daily Energy Consumption
fig_daily = go.Figure()
fig_daily.add_trace(go.Scatter(x=daily_consumption['date'], 
                               y=daily_consumption['load'], 
                               mode='lines', 
                               name=selected_country))

fig_daily.update_layout(
    title=f"Average Daily Energy Consumption - {selected_country}",
    xaxis_title='Date',
    yaxis_title='Energy Consumption (Load)',
    template='plotly_white'
)

st.plotly_chart(fig_daily)
