import pandas as pd
import argparse
import os

def main(input_file, output_dir):
    # Load 1-minute data with no headers, assign column names manually
    column_names = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
    data = pd.read_csv(input_file, header=None, names=column_names)

    # Convert 'Datetime' column to datetime format and set as index
    data['Datetime'] = pd.to_datetime(data['Datetime'])
    data.set_index('Datetime', inplace=True)

    # Resample to 15-minute intervals
    data_15min = data.resample('15T').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })

    # Drop rows with missing data or zero volume after resampling
    data_15min = data_15min.dropna()
    data_15min = data_15min[data_15min['Volume'] > 0]

    # Resample to 5-minute intervals
    data_5min = data.resample('5T').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })

    # Drop rows with missing data or zero volume after resampling
    data_5min = data_5min.dropna()
    data_5min = data_5min[data_5min['Volume'] > 0]

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Save the processed datasets
    file_15min = os.path.join(output_dir, "QQQ_15min.csv")
    file_5min = os.path.join(output_dir, "QQQ_5min.csv")

    data_15min.to_csv(file_15min)
    data_5min.to_csv(file_5min)

    print("Conversion complete. Files saved:")
    print(f"- 15-minute data: {file_15min}")
    print(f"- 5-minute data: {file_5min}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert 1-minute data to 15-minute and 5-minute intervals.")
    parser.add_argument("--input_file", type=str, required=True, help="Path to the input 1-minute dataset CSV file.")
    parser.add_argument("--output_dir", type=str, required=True, help="Path to the directory for saving resampled datasets.")

    args = parser.parse_args()
    main(args.input_file, args.output_dir)
