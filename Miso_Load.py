import tkinter as tk
from tkinter import ttk
import urllib.request
import json
import pandas as pd
from tkinter import filedialog
from config import Load_API_Key
from datetime import datetime, timedelta

def get_miso_load_data(date, region, api_key):
    try:
        url = f"https://apim.misoenergy.org/lgi/v1/forecast/{date}/load?region={region}&timeResolution=hourly"
        # f"https://apim.misoenergy.org/lgi/v1/forecast/{date}/load?&timeResolution=hourly"
        hdr = {
            'Cache-Control': 'no-cache',
            'Ocp-Apim-Subscription-Key': api_key,
        }

        req = urllib.request.Request(url, headers=hdr)
        req.get_method = lambda: 'GET'
        response = urllib.request.urlopen(req)
        status_code = response.getcode()
        print(f"API response status code: {status_code}")

        if status_code == 200:
            data = json.loads(response.read())["data"]
            df = pd.DataFrame(data)
            return df
        else:
            print(f"Error: {status_code}")
            return None

    except Exception as e:
        print(e)
        return None

def handle_data_fetch_miso_load(region_var, load_date):
    region = region_var.get()
    miso_load_api_key = Load_API_Key
    if miso_load_api_key is None:
        print("Error: MISO_API_KEY not set in config.py")
        return None
    
    load_date = datetime.strptime(load_date, "%Y-%m-%d")
    miso_load_df = get_miso_load_data(load_date.strftime("%Y-%m-%d"), region, miso_load_api_key)
    return miso_load_df

def export_to_csv(df):
    try:
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if filename:
            df.to_csv(filename, index=False)
            print(f"Data exported to {filename}")
    except Exception as e:
        print(f"Error exporting data: {e}")

def create_Load_Data_tab(parent, load_date_entry, region_var):
    load_data_frame = ttk.Frame(parent)
    load_data_frame.pack(fill="both", expand=True)

    miso_load_df = handle_data_fetch_miso_load(region_var, load_date_entry.get_date().strftime("%Y-%m-%d"))

    if miso_load_df is not None:
        miso_load_tree = ttk.Treeview(load_data_frame)
        miso_load_tree["columns"] = list(miso_load_df.columns)
        miso_load_tree.pack(in_=load_data_frame, fill="both", expand=True)

        for col in miso_load_df.columns:
            miso_load_tree.column(col, anchor="w")
            miso_load_tree.heading(col, text=col, anchor="w")
        for _, row in miso_load_df.iterrows():
            miso_load_tree.insert("", "end", values=list(row))

        export_button_miso_load = tk.Button(load_data_frame, text="Export to CSV", command=lambda: export_to_csv(miso_load_df))
        export_button_miso_load.pack(pady=10)
    else:
        label = tk.Label(load_data_frame, text="No MISO load data available.")
        label.pack(pady=20)