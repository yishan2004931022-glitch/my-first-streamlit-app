import streamlit as st
import pandas as pd
import numpy as np
st.set_page_config(page_title="My First Streamlit App", layout="centered")
st.title("My First Streamlit App")
st.write("This app is built with Streamlit!")
st.write("HAHAHAHA!")

# Reading the data
link = "https://drive.google.com/uc?export=download&id=1zdxtFQSRAeG50Vx5Rpj5pzW47UB3UJ7C"
df = pd.read_csv(link)

# Show first few rows
print(df.head())

# create a download data button for original dataset
file_name = "myproject_finaldatabase.csv" # Define it first

# Create the download button
st.download_button(
    label="Download the data in csv format",
    data=df.to_csv(index=False).encode('utf-8'),
    file_name=file_name,
    mime='text/csv'
)

# Display data
st.header("A tiny dataset")
df = pd.DataFrame({
"x": np.arange(1, 11),
"y": np.random.randint(10, 100, size=10)
})
st.dataframe(df)
# Add a chart
st.header("A simple chart")
st.line_chart(df.set_index("x"))
# Add a widget
st.header("Your first widget")
number = st.slider("Pick a number", min_value=0, max_value=100, value=50)
st.write("You picked:", number)













