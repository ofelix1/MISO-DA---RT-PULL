import urllib.request, json
import pandas as pd
import tkinter as tk
from tkinter import ttk, StringVar, Toplevel, filedialog
from tkcalendar import Calendar, DateEntry
import csv
from datetime import datetime, timedelta
from real_time_data import create_real_time_data_tab, handle_data_fetch_real_time #real time tab and function imported
import time
import multiprocessing
from config import MISO_API_KEY

def get_miso_day_ahead_pricing(date, node, api_key):
    try:
        url = f"https://apim.misoenergy.org/pricing/v1/day-ahead/{date}/lmp-expost?node={node}"
        print(f"Fetching data from: {url}")
        
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

def display_data_day_ahead_pricing(day_ahead_pricing_df, progress_label):
    if day_ahead_pricing_df is not None:
        # Create the main window
        root = tk.Tk()
        root.title("MISO Data - Day-Ahead Pricing")

        # Create the frame for the Notebook
        day_ahead_pricing_frame = ttk.Frame(root)
        day_ahead_pricing_frame.pack(fill="both", expand=True)

        # Create a progress label
        progress_label.place(relx=0.5, rely=0.05, anchor="center")

        # Day-Ahead Pricing Data
        if day_ahead_pricing_df is not None:
            # Create the treeview in the day-ahead pricing frame
            day_ahead_pricing_tree = ttk.Treeview(day_ahead_pricing_frame)
            day_ahead_pricing_tree["columns"] = list(day_ahead_pricing_df.columns)
            day_ahead_pricing_tree.pack(in_=day_ahead_pricing_frame, fill="both", expand=True)

            # Add the column headers and data to the day-ahead pricing treeview
            for col in day_ahead_pricing_df.columns:
                day_ahead_pricing_tree.column(col, anchor="w")
                day_ahead_pricing_tree.heading(col, text=col, anchor="w")
            for _, row in day_ahead_pricing_df.iterrows():
                day_ahead_pricing_tree.insert("", "end", values=list(row))

            # Create the export to CSV button for day-ahead pricing data
            export_button_day_ahead_pricing = tk.Button(day_ahead_pricing_frame, text="Export to CSV", command=lambda: export_to_csv(day_ahead_pricing_df))
            export_button_day_ahead_pricing.pack(pady=10)

        # Update the progress label to indicate the data fetch is complete
        progress_label.configure(text="Data fetch complete")
        root.mainloop()
    else:
        print("No data available to display.")

def display_data_real_time(real_time_pricing_df):
    if real_time_pricing_df is not None:
        # Create the main window
        root = tk.Tk()
        root.title("MISO Data - Real-Time Data")

        # Create the frame for the Notebook
        real_time_data_frame = ttk.Frame(root)
        real_time_data_frame.pack(fill="both", expand=True)

        # Real-Time Data
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

        root.mainloop()
    else:
        print("No data available to display.")

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

def handle_data_fetch_day_ahead_pricing(start_date, end_date, node_var, progress_label):
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    node = node_var.get()
    day_ahead_pricing_api_key = MISO_API_KEY

    if day_ahead_pricing_api_key is None:
        print("Error: MISO_API_KEY not set in config.py")
        return None

    # Limit the number of API calls to 40 per minute
    max_calls_per_minute = 40
    calls_made = 0
    start_time = time.time()
    day_ahead_pricing_dfs = []

    with multiprocessing.Pool(processes=4) as pool:
        while start_date <= end_date:
            date_str = start_date.strftime("%Y-%m-%d")
            day_ahead_pricing_df = pool.apply_async(get_miso_day_ahead_pricing, args=(date_str, node, day_ahead_pricing_api_key))
            day_ahead_pricing_dfs.append(day_ahead_pricing_df)
            calls_made += 1
            progress_label.configure(text=f"Fetching data: {calls_made}/{max_calls_per_minute * ((end_date - start_date).days + 1)}")
            progress_label.update()
            if calls_made >= max_calls_per_minute:
                calls_made = 0
                time.sleep(60)  # Wait for a minute to avoid exceeding the rate limit
            start_date += timedelta(days=1)

        day_ahead_pricing_dfs = [df.get() for df in day_ahead_pricing_dfs]

    total_calls = len(day_ahead_pricing_dfs)

    if day_ahead_pricing_dfs:
        return pd.concat(day_ahead_pricing_dfs)
    else:
        return None

def main():
    global root, node_var, start_date_entry, end_date_entry, real_time_date_entry

    # Create the main window
    root = tk.Tk()
    root.title("MISO Data")

    # Set the window size
    root.geometry("1200x800")

    # Day-Ahead Pricing Data
    # Create dropdown menus for node
    node_var = StringVar(root)
    node_var.set("MINN.HUB")
    node_options = ["MINN.HUB", "MICHIGAN.HUB", "ILLINOISE.HUB", "INDIANA.HUB", "ARKANSAS.HUB", "MS.HUB", "TEXAS.HUB", "LOUISIANA.HUB"]
    node_dropdown = ttk.Combobox(root, textvariable=node_var, values=node_options)
    node_dropdown.pack(pady=10)

    # Create date entry fields with calendar buttons for start and end dates
    start_date_label = tk.Label(root, text="Enter Start Date (YYYY-MM-DD):")
    start_date_label.pack(pady=10)
    start_date_entry = DateEntry(root, width=12, background="darkblue", foreground="white", borderwidth=2)
    start_date_entry.pack(pady=10)

    end_date_label = tk.Label(root, text="Enter End Date (YYYY-MM-DD):")
    end_date_label.pack(pady=10)
    end_date_entry = DateEntry(root, width=12, background="darkblue", foreground="white", borderwidth=2)
    end_date_entry.pack(pady=10)

    # Create date entry field with calendar button for real-time data
    real_time_date_label = tk.Label(root, text="Enter Real-Time Data Date (YYYY-MM-DD):")
    real_time_date_label.pack(pady=10)
    real_time_date_entry = DateEntry(root, width=12, background="darkblue", foreground="white", borderwidth=2)
    real_time_date_entry.pack(pady=10)

    # Create a progress label
    progress_label = tk.Label(root, text="", font=("Arial", 14))
    progress_label.pack(pady=20)

    # Create a button to fetch and display the day-ahead pricing data
    fetch_button_day_ahead_pricing = tk.Button(root, text="Fetch Day-Ahead Pricing Data", command=lambda: [progress_label.configure(text="Fetching data..."), display_data_day_ahead_pricing(handle_data_fetch_day_ahead_pricing(start_date_entry.get_date().strftime("%Y-%m-%d"), end_date_entry.get_date().strftime("%Y-%m-%d"), node_var, progress_label), progress_label)])
    fetch_button_day_ahead_pricing.pack(pady=20)

    # Create a button to fetch and display the real-time data
    fetch_button_real_time = tk.Button(root, text="Fetch Real-Time Data", command=lambda: display_data_real_time(handle_data_fetch_real_time(node_var, real_time_date_entry.get_date().strftime("%Y-%m-%d"))))
    fetch_button_real_time.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()