import os
import pandas as pd

def read_inv_files(directory="."):
    inv_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".INV"):
                file_path = os.path.join(root, file)
                inv_files.append(file_path)

    return inv_files

# Create an empty DataFrame to store results

def my_fun(df_new, electrode, elevation):
    df_new['electrode'] = electrode
    df_new['elevation'] = elevation

    # convert the elevation column to numeric

    df_new['elevation'] = pd.to_numeric(df_new['elevation'], errors='coerce')

    # drop row if any of the values in elevation column is not unique

    df_new.drop_duplicates(subset=['elevation'], keep='first', inplace=True)

    # sort the df by elevation

    df_new.sort_values(by=['electrode'], inplace=True, ascending=True)

    df_new.reset_index(drop=True, inplace=True)

    return df_new

# Example usage:
current_directory = r"D:\consultancy works squ\sultan_ert_plot\Inversion"  # You can specify the directory path if needed
inv_files = read_inv_files(current_directory)

# Process each file and update the result table
for inv_file in inv_files:

    print(f"Processing file: {inv_file}")
    try:
        # Read the CSV file using pandas to get the value from row 7
        with open(inv_file, 'r') as f:
            for i, line in enumerate(f):
                if i == 6:  # Assuming the row number is 7 (0-indexed)
                    nrows_value = int(line.strip())
                    break

        # Read the CSV file using pandas, starting from row 10 and using the obtained nrows_value
        df = pd.read_csv(inv_file, sep='\s+', header=None, skiprows=9, nrows=nrows_value, engine='python')

        ## check number of columns
        if len(df.columns) == 8:
            df.columns = ["electrode_number", "A", "A_ele", "M", "M_elv", "N", "N_elv", "app_res"]
            # drop "electrode_number" and "app_res" columns
            df.drop(["electrode_number", "app_res"], axis=1, inplace=True)

            df_new = pd.DataFrame(columns=["electrode", "elevation"])
            electrode = df[['A', 'M', 'N']].values.ravel()
            elevation = df[['A_ele', 'M_elv', 'N_elv']].values.ravel()
            df_new = my_fun(df_new, electrode, elevation)

        elif len(df.columns) == 10:
            df.columns = ["electrode_number", "A", "A_ele", "B", "B_elv", "M", "M_elv", "N", "N_elv","app_res"]
            # drop "electrode_number" and "app_res" columns

            df.drop(["electrode_number", "app_res"], axis=1, inplace=True)


            df_new = pd.DataFrame(columns=["electrode", "elevation"])
            electrode = df[['A', 'B', 'M', 'N']].values.ravel()
            elevation = df[['A_ele', 'B_elv', 'M_elv', 'N_elv']].values.ravel()

            df_new = my_fun(df_new, electrode, elevation)
        

        # save the df_new to excel file in the same directory as an excel file but add -elevation to the file name

        file_name = os.path.splitext(os.path.basename(inv_file))[0]
        file_name = file_name + "-elevation.xlsx"
        file_name = os.path.join(os.path.dirname(inv_file), file_name)

        df_new.to_excel(file_name, index=False)
        


    except Exception as e:
        print(f"Error reading file: {inv_file} - {e}")
        continue
