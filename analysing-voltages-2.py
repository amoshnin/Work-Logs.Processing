import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Data Loading and Preprocessing ---
@st.cache_data
def load_data(product):
    """Loads the CSV data for the given product."""
    file_path = f"output-voltages/{product}-output.csv"
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# --- Streamlit App ---
st.title("Voltage Analysis Dashboard")

# Product Selection
product_list = [x.replace("-output.csv", "") for x in os.listdir("output-voltages")]
product = st.selectbox("Select Product:", product_list)

# Load data
df = load_data(product)

# --- Sidebar Filters ---
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

# --- Main Visualization ---
st.subheader("Voltage Measurements Analysis")

# Create figure
fig = go.Figure()

# Add color selection dropdown
color_by = st.radio(
    "Color points by:",
    ['machine_number', 'control_number', 'test_step'],
    horizontal=True
)

# Create custom hover text
filtered_df['hover_text'] = (
    'Machine: ' + filtered_df['machine_number'].astype(str) + '<br>' +
    'Control: ' + filtered_df['control_number'].astype(str) + '<br>' +
    'Test Step: ' + filtered_df['test_step'].astype(str)
)

for category in filtered_df[color_by].unique():
    mask = filtered_df[color_by] == category
    category_df = filtered_df[mask]

    # Add both VSENSE and OVP measurements in a single trace group
    fig.add_trace(
        go.Scatter(
            x=category_df['timestamp'],
            y=category_df['S_VSENSE'],
            name=f'{category}',
            mode='markers',
            marker=dict(size=8, symbol='circle'),
            text=category_df['hover_text'],
            hovertemplate=
            '<b>VSENSE:</b> %{y:.3f}V<br>' +
            '%{text}<br>' +
            '<b>Time:</b> %{x}<extra></extra>',
            legendgroup=f'group_{category}',
            showlegend=True
        )
    )

    fig.add_trace(
        go.Scatter(
            x=category_df['timestamp'],
            y=category_df['S_OVP'],
            name=f'{category} (OVP)',
            mode='markers',
            marker=dict(size=8, symbol='diamond'),
            text=category_df['hover_text'],
            hovertemplate=
            '<b>OVP:</b> %{y:.3f}V<br>' +
            '%{text}<br>' +
            '<b>Time:</b> %{x}<extra></extra>',
            legendgroup=f'group_{category}',
            showlegend=False  # Hide duplicate legend entries
        )
    )

# Update layout
fig.update_layout(
    title=f"Voltage Measurements Over Time - {product}",
    xaxis_title="Timestamp",
    yaxis_title="Voltage (V)",
    hovermode='closest',
    height=600,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.05
    ),
    margin=dict(r=150)  # Add right margin for legend
)

# Display the plot
st.plotly_chart(fig, use_container_width=True)

# --- Summary Statistics ---
st.subheader("Summary Statistics")

col1, col2 = st.columns(2)

with col1:
    st.write("VSENSE Statistics")
    st.write(filtered_df['S_VSENSE'].describe().round(3))

with col2:
    st.write("OVP Statistics")
    st.write(filtered_df['S_OVP'].describe().round(3))

# Add correlation information
correlation = filtered_df['S_VSENSE'].corr(filtered_df['S_OVP']).round(3)
st.write(f"Correlation between VSENSE and OVP: {correlation}")

# --- Data Table ---
if st.checkbox("Show Raw Data"):
    st.subheader("Filtered Data")
    st.write(filtered_df)