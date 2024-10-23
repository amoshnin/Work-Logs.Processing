import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import re

def load_data(folder_path):
    """Load all CSV files from the specified folder and combine them into a structured dataset."""
    all_files = list(Path(folder_path).glob('*.csv'))
    data_dict = {}

    for file_path in all_files:
        # Parse filename components
        filename = file_path.stem
        zone, slot, product = filename.split('_', 2)

        # Read CSV file
        df = pd.read_csv(file_path)

        # Add metadata columns
        df['zone'] = zone
        df['slot'] = slot
        df['product'] = product
        df['timestamp'] = df.index  # Assuming index represents timestamps

        # Store in dictionary
        data_dict[filename] = df

    # Combine all dataframes
    combined_df = pd.concat(data_dict.values(), ignore_index=True)
    return combined_df

def restructure_data(df):
    """Restructure the data for easier plotting by converting wide format to long format."""
    # Identify measurement columns
    measure_cols = [col for col in df.columns if any(x in col for x in ['COOLDUTY', 'ES0_TEMP', 'HTR_DUTY', 'SNK_TEMP'])]

    # Melt the dataframe
    melted = pd.melt(
        df,
        id_vars=['timestamp', 'zone', 'slot', 'product'],
        value_vars=measure_cols,
        var_name='measurement',
        value_name='value'
    )

    # Extract socket number and measurement type
    melted[['measurement_type', 'socket']] = melted['measurement'].str.extract(r'(\w+)\.(\d+)')

    return melted

def create_socket_subplot(df, measurement_type, selected_zone, selected_slot, selected_product):
    """Create a subplot for a specific measurement type across all sockets."""
    filtered_df = df[
        (df['measurement_type'] == measurement_type) &
        (df['zone'] == selected_zone) &
        (df['slot'] == selected_slot) &
        (df['product'] == selected_product)
    ]

    fig = go.Figure()

    for socket in sorted(filtered_df['socket'].unique()):
        socket_data = filtered_df[filtered_df['socket'] == socket]
        fig.add_trace(
            go.Scatter(
                x=socket_data['timestamp'],
                y=socket_data['value'],
                name=f'Socket {socket}',
                mode='lines+markers'
            )
        )

    fig.update_layout(
        title=f'{measurement_type} vs Time - All Sockets',
        xaxis_title='Time',
        yaxis_title=measurement_type,
        height=400,
        showlegend=True
    )

    return fig

def create_correlation_plots(df, selected_zone, selected_slot, selected_product, socket):
    """Create correlation plots between different measurements for a specific socket."""
    filtered_df = df[
        (df['zone'] == selected_zone) &
        (df['slot'] == selected_slot) &
        (df['product'] == selected_product) &
        (df['socket'] == socket)
    ]

    # Pivot the data to get measurements as columns
    pivot_df = filtered_df.pivot(
        index='timestamp',
        columns='measurement_type',
        values='value'
    ).reset_index()

    # Create ES0_TEMP correlations
    fig1 = go.Figure()

    fig1.add_trace(
        go.Scatter(
            x=pivot_df['ES0_TEMP'],
            y=pivot_df['COOLDUTY'],
            mode='markers',
            name='COOLDUTY'
        )
    )

    fig1.add_trace(
        go.Scatter(
            x=pivot_df['ES0_TEMP'],
            y=pivot_df['HTR_DUTY'],
            mode='markers',
            name='HTR_DUTY'
        )
    )

    fig1.update_layout(
        title=f'ES0_TEMP Correlations - Socket {socket}',
        xaxis_title='ES0_TEMP',
        yaxis_title='Duty Cycle',
        height=400,
        showlegend=True
    )

    # Create SNK_TEMP correlations
    fig2 = go.Figure()

    fig2.add_trace(
        go.Scatter(
            x=pivot_df['SNK_TEMP'],
            y=pivot_df['COOLDUTY'],
            mode='markers',
            name='COOLDUTY'
        )
    )

    fig2.add_trace(
        go.Scatter(
            x=pivot_df['SNK_TEMP'],
            y=pivot_df['HTR_DUTY'],
            mode='markers',
            name='HTR_DUTY'
        )
    )

    fig2.update_layout(
        title=f'SNK_TEMP Correlations - Socket {socket}',
        xaxis_title='SNK_TEMP',
        yaxis_title='Duty Cycle',
        height=400,
        showlegend=True
    )

    return fig1, fig2

def main():
    st.set_page_config(page_title="Temperature Analysis Dashboard", layout="wide")

    st.title("Temperature Analysis Dashboard")

    # Sidebar for navigation and filters
    st.sidebar.header("Navigation")

    # File upload
    folder_path = "output-temperatures"

    if folder_path:
        try:
            # Load and process data
            df = load_data(folder_path)
            processed_df = restructure_data(df)

            # Filters
            zones = sorted(processed_df['zone'].unique())
            selected_zone = st.sidebar.selectbox("Select Zone", zones)

            slots = sorted(processed_df[processed_df['zone'] == selected_zone]['slot'].unique())
            selected_slot = st.sidebar.selectbox("Select Slot", slots)

            products = sorted(processed_df[
                (processed_df['zone'] == selected_zone) &
                (processed_df['slot'] == selected_slot)
            ]['product'].unique())
            selected_product = st.sidebar.selectbox("Select Product", products)

            # Main content area
            st.header(f"Analysis for {selected_zone}/{selected_slot}/{selected_product}")

            # Create tabs for different views
            tab1, tab2 = st.tabs(["Time Series Analysis", "Correlation Analysis"])

            with tab1:
                # Time series plots for each measurement type
                measurement_types = ['ES0_TEMP', 'COOLDUTY', 'HTR_DUTY', 'SNK_TEMP']

                for measurement_type in measurement_types:
                    st.subheader(f"{measurement_type} Analysis")
                    fig = create_socket_subplot(
                        processed_df,
                        measurement_type,
                        selected_zone,
                        selected_slot,
                        selected_product
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with tab2:
                st.subheader("Correlation Analysis")

                selected_socket = st.selectbox(
                    "Select Socket for Correlation Analysis",
                    sorted(processed_df['socket'].unique())
                )

                # Create correlation plots
                es0_temp_fig, snk_temp_fig = create_correlation_plots(
                    processed_df,
                    selected_zone,
                    selected_slot,
                    selected_product,
                    selected_socket
                )

                # Display correlation plots
                st.plotly_chart(es0_temp_fig, use_container_width=True)
                st.plotly_chart(snk_temp_fig, use_container_width=True)

                # Add summary statistics
                with st.expander("View Summary Statistics"):
                    summary_df = processed_df[
                        (processed_df['zone'] == selected_zone) &
                        (processed_df['slot'] == selected_slot) &
                        (processed_df['product'] == selected_product) &
                        (processed_df['socket'] == selected_socket)
                    ].pivot(
                        columns='measurement_type',
                        values='value'
                    ).describe()
                    st.dataframe(summary_df)

        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.info("Please ensure the folder path is correct and contains CSV files in the expected format.")

if __name__ == "__main__":
    main()