import tkinter as tk
from tkinter import ttk
import urllib.request
import json
import pandas as pd
from tkinter import filedialog
from config import MISO_API_KEY

def get_miso_real_time_pricing(date, node, api_key):
    try:
        url = f"https://apim.misoenergy.org/pricing/v1/real-time/{date}/lmp-expost?node={node}"
        
        hdr = {
            # Request headers
            'Cache-Control': 'no-cache',
            'Ocp-Apim-Subscription-Key': api_key,
        }

        req = urllib.request.Request(url, headers=hdr)

        req.get_method = lambda: 'GET'
        response = urllib.request.urlopen(req)
        status_code = response.getcode()
        print(f"API response status code: {status_code}")

        if status_code == 200:
            # Parse the JSON response
            data = json.loads(response.read())["data"]

            # Convert the data to a pandas DataFrame
            df = pd.DataFrame(data)
            return df
        else:
            print(f"Error: {status_code}")
            return None

    except Exception as e:
        print(e)
        return None

def create_real_time_data_tab(notebook, node_var):
    # Create the frame for the new tab
    real_time_data_frame = ttk.Frame(notebook)

    # Add the new tab to the Notebook
    notebook.add(real_time_data_frame, text="Real-Time Data")

    # Real-Time Data
    real_time_pricing_api_key = MISO_API_KEY
    if real_time_pricing_api_key is None:
        print("Error: MISO_API_KEY not set in config.py")
        return

    real_time_pricing_df = get_miso_real_time_pricing("2023-04-01", node_var.get(), real_time_pricing_api_key)

    if real_time_pricing_df is not None:
        # Create the treeview in the real-time data frame
        real_time_pricing_tree = ttk.Treeview(real_time_data_frame)
        real_time_pricing_tree["columns"] = list(real_time_pricing_df.columns)
        real_time_pricing_tree.pack(in_=real_time_data_frame, fill="both", expand=True)

        # Add the column headers and data to the real-time pricing treeview
        for col in real_time_pricing_df.columns:
            real_time_pricing_tree.column(col, anchor="w")
            real_time_pricing_tree.heading(col, text=col, anchor="w")
        for _, row in real_time_pricing_df.iterrows():
            real_time_pricing_tree.insert("", "end", values=list(row))

        # Create the export to CSV button for real-time pricing data
        export_button_real_time_pricing = tk.Button(real_time_data_frame, text="Export to CSV", command=lambda: export_to_csv(real_time_pricing_df))
        export_button_real_time_pricing.pack(pady=10)
    else:
        # Display a message or placeholder data if the API call fails
        label = tk.Label(real_time_data_frame, text="No real-time data available.")
        label.pack(pady=20)

def handle_data_fetch_real_time(node_var, real_time_date):
    node = node_var.get()
    real_time_pricing_api_key = MISO_API_KEY
    if real_time_pricing_api_key is None:
        print("Error: MISO_API_KEY not set in config.py")
        return None
    real_time_pricing_df = get_miso_real_time_pricing(real_time_date, node, real_time_pricing_api_key)
    return real_time_pricing_df

def export_to_csv(df):
    try:
        # Open a file dialog to get the filename
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if filename:
            # Write the data to a CSV file
            df.to_csv(filename, index=False)
            print(f"Data exported to {filename}")
    except Exception as e:
        print(f"Error exporting data: {e}")