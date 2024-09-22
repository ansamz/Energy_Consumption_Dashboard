# Streamlit App for Energy Consumption

![alternative text](img/energy.jpeg)

## Project Intro/Objective
The purpose of this project is to create a Streamlit dashboard to visualize energy consumption patterns across European countries. The dashboard provides detailed insights into annual, daily, and hourly energy consumption, allowing users to analyze trends and detect anomalies.

### Partners
This project is developed for **Energy Company X** as part of their digitalization efforts, aiming to provide clear and actionable insights into European energy consumption as part of Big Data HSLU block seminar.

### Methods Used
* Exploratory Data Analysis (EDA)
* Data Visualization
* Time Series Analysis
* Anomaly Detection

### Technologies
* Python
* Streamlit
* Pandas, Jupyter
* Plotly, Plotly Express
* Geopy, PyCountry, PyPopulation
* PyODBC (for database connectivity)
* JSON, Parquet

## Project Description
The Streamlit app is designed to present energy consumption data in a clear and interactive manner. The app features:

1. **Annual Consumption Overview**: Visualizing energy consumption across Europe using choropleth maps and bar plots.
2. **Country-Specific Analysis**: Users can select individual countries to explore daily, hourly, and monthly trends in energy consumption, as well as moving averages and trend lines.
3. **Anomaly Detection**: The app includes functionality to detect and highlight consumption anomalies based on z-scores, helping users identify unusual patterns.
4. **Data Processing**: Data is processed from parquet files and SQL databases, with transformations like date-time conversions, population normalization, and geographical data integration.


