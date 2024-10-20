import os
import streamlit as st
import pandas as pd
import plotly.express as px

# --- Data Loading and Preprocessing ---

@st.cache_data  # Cache the data for faster loading
def load_data(product):
    """Loads the CSV data for the given product."""
    # Replace 'data_folder' with the actual path to your data folder
    file_path = f"output-voltages/{product}-output.csv"
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])  # Convert timestamp to datetime
    return df

# --- Streamlit App ---

st.title("Product Test Data Visualization")

# Product Selection
product_list = products = os.listdir("data-voltages")
product = st.selectbox("Select Product:", product_list)

# Load data for the selected product
df = load_data(product)

# --- Filtering ---

st.sidebar.header("Filters")

# Machine Number Filter
machine_numbers = df['machine_number'].unique()
selected_machine_number = st.sidebar.multiselect(
    "Machine Number:", machine_numbers, default=machine_numbers
)

# Control Number Filter
control_numbers = df['control_number'].unique()
selected_control_number = st.sidebar.multiselect(
    "Control Number:", control_numbers, default=control_numbers
)

# Test Step Filter
test_steps = df['test_step'].unique()
selected_test_step = st.sidebar.multiselect(
    "Test Step:", test_steps, default=test_steps
)

# Apply Filters
filtered_df = df[
    (df['machine_number'].isin(selected_machine_number)) &
    (df['control_number'].isin(selected_control_number)) &
    (df['test_step'].isin(selected_test_step))
]

# --- Visualization ---

st.subheader("Data Visualization")

# Y-axis Variable Selection
y_axis_var = st.radio("Select Y-axis Variable:", ["S_VSENSE", "S_OVP"])

# Create Plotly figure
fig = px.scatter(
    filtered_df,
    x="timestamp",
    y=y_axis_var,
    color="machine_number",
    hover_data=["control_number", "test_step", "S_VSENSE", "S_OVP"],
    title=f"{y_axis_var} over Time for {product}"
)

# Display the plot
st.plotly_chart(fig)

# --- Data Table ---

st.subheader("Filtered Data")
st.write(filtered_df)