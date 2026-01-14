import streamlit as st
import pandas as pd
import numpy as np
st.set_page_config(page_title="My First Streamlit App", layout="centered")
st.title("My First Streamlit App")
st.write("This app is built with Streamlit!")
st.write("HAHAHAHA!")
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






