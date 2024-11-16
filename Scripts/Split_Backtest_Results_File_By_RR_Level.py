import pandas as pd
import os
import argparse

def main(results_file, output_directory):
    # Load the backtest results
    print("Loading backtest results...")
    data = pd.read_csv(results_file)

    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Get unique RR levels
    rr_levels = data['RR_Level'].unique()
    print(f"Found {len(rr_levels)} unique RR Levels.")

    # Create a dataset for each RR level
    for rr in rr_levels:
        print(f"Processing RR Level: {rr}")
        rr_data = data[data['RR_Level'] == rr]
        output_file = os.path.join(output_directory, f"backtest_results_RR_{rr:.3f}.csv")
        rr_data.to_csv(output_file, index=False)
        print(f"Saved dataset for RR Level {rr} to {output_file}.")

    print("All datasets created successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split backtest results into separate datasets based on RR Levels.")
    parser.add_argument("--results_file", type=str, required=True, help="Path to the backtest results CSV file.")
    parser.add_argument("--output_directory", type=str, required=True, help="Path to the directory for saving RR Level datasets.")

    args = parser.parse_args()
    main(args.results_file, args.output_directory)
