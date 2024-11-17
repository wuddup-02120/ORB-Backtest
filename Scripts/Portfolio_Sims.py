import pandas as pd
import os
import matplotlib.pyplot as plt
import argparse

# Use a built-in style that is safe and available
plt.style.use('ggplot')
plt.rcParams.update({
    'axes.grid': True,            # Enable grid
    'grid.alpha': 0.6,            # Set grid transparency
    'axes.titlesize': 18,         # Title font size
    'axes.labelsize': 14,         # Label font size
    'legend.fontsize': 12,        # Legend font size
    'figure.figsize': (12, 8),    # Default figure size
    'lines.linewidth': 2          # Line width
})

def simulate_portfolio(file_path, initial_balance):
    data = pd.read_csv(file_path)

    # Ensure Entry_Time and Exit_Time columns are in datetime format
    data['Entry_Time'] = pd.to_datetime(data['Entry_Time'])
    data['Exit_Time'] = pd.to_datetime(data['Exit_Time'])

    # Filter data to include only rows from January 2020 onward
    data = data[data['Entry_Time'] >= '2020-01-01']

    if data.empty:
        print(f"No data available for the period starting January 2020 in file: {file_path}")
        return None, None, None

    # Initialize variables
    account_balance = initial_balance
    cumulative_returns = []
    trade_dates = []
    trade_counts = 0
    wins = 0
    losses = 0
    max_drawdown = 0
    peak_balance = initial_balance

    # Track the last exit time
    last_exit_time = None

    # Simulate trades
    for index, row in data.iterrows():
        # Skip trades whose entry time is before the last trade's exit time
        if last_exit_time and row['Entry_Time'] <= last_exit_time:
            continue

        trade_return = (row['Percentage_Return'] / 100) * account_balance
        account_balance += trade_return
        cumulative_returns.append(account_balance)
        trade_dates.append(row['Entry_Time'])
        trade_counts += 1

        # Update wins and losses
        if trade_return > 0:
            wins += 1
        else:
            losses += 1

        # Calculate max drawdown
        if account_balance > peak_balance:
            peak_balance = account_balance
        drawdown = (peak_balance - account_balance) / peak_balance
        max_drawdown = max(max_drawdown, drawdown)

        # Update the last exit time
        last_exit_time = row['Exit_Time']

    # Calculate final statistics
    total_return = (account_balance - initial_balance) / initial_balance * 100
    win_rate = (wins / trade_counts) * 100 if trade_counts > 0 else 0
    loss_rate = (losses / trade_counts) * 100 if trade_counts > 0 else 0

    stats = {
        'Initial Balance': initial_balance,
        'Final Balance': account_balance,
        'Total Return (%)': total_return,
        'Max Drawdown (%)': max_drawdown * 100,
        'Total Trades': trade_counts,
        'Wins': wins,
        'Losses': losses,
        'Win Rate (%)': win_rate,
        'Loss Rate (%)': loss_rate
    }

    return stats, cumulative_returns, trade_dates


def calculate_spy_hold_return(spy_file_path, initial_balance, start_date):
    spy_data = pd.read_csv(spy_file_path)

    # Ensure datetime format
    spy_data['Datetime'] = pd.to_datetime(spy_data['Datetime'])

    # Filter SPY data to align with the start date of the portfolio simulation
    spy_data = spy_data[spy_data['Datetime'] >= start_date]

    # Sort data by datetime just in case
    spy_data.sort_values('Datetime', inplace=True)

    if spy_data.empty:
        raise ValueError("SPY data does not contain any data from the start date onward.")

    # Use the first and last close prices to calculate returns
    start_price = spy_data.iloc[0]['Close']
    spy_equity_curve = initial_balance * (spy_data['Close'] / start_price)

    return spy_equity_curve, spy_data['Datetime']


def main(input_directory, output_directory, equity_curve_directory, spy_file_path, initial_balance):
    # Ensure output directories exist
    os.makedirs(output_directory, exist_ok=True)
    os.makedirs(equity_curve_directory, exist_ok=True)

    # Combined output file for portfolio simulation results
    combined_output_file = os.path.join(output_directory, "combined_portfolio_sim_results.csv")

    # List all RR_Level files
    rr_files = [f for f in os.listdir(input_directory) if f.endswith('.csv')]

    print(f"Found {len(rr_files)} RR Level files.")

    # Initialize list to store all results for combined output
    all_results = []

    # Define the start date for the simulation
    start_date = '2020-01-01'

    # Calculate SPY hold return
    spy_equity_curve, spy_dates = calculate_spy_hold_return(spy_file_path, initial_balance, start_date)

    # Simulate for each file
    for rr_file in rr_files:
        print(f"Simulating portfolio for {rr_file}...")
        file_path = os.path.join(input_directory, rr_file)
        stats, equity_curve, trade_dates = simulate_portfolio(file_path, initial_balance)

        if stats is None or equity_curve is None:
            continue

        # Add RR level to stats
        rr_level = os.path.splitext(rr_file)[0].split('_')[-1]
        stats['RR_Level'] = rr_level
        all_results.append(stats)

        # Generate and save equity curve plot
        equity_curve_file = os.path.join(equity_curve_directory, f"equity_curve_RR_{rr_level}.png")
        plt.figure(figsize=(12, 8))
        plt.plot(trade_dates, equity_curve, label=f"Strategy Equity Curve (RR {rr_level})", linewidth=2)
        plt.plot(spy_dates, spy_equity_curve, label="SPY Buy-and-Hold", linestyle='--', linewidth=2)
        plt.title(f"Equity Curve for RR Level {rr_level}", fontsize=18)
        plt.xlabel("Date", fontsize=14)
        plt.ylabel("Account Balance", fontsize=14)
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.6)
        plt.tight_layout()
        plt.savefig(equity_curve_file, dpi=300)
        plt.close()
        print(f"Equity curve plot saved to {equity_curve_file}.")

    # Save combined results to a single CSV file
    combined_results_df = pd.DataFrame(all_results)
    combined_results_df.to_csv(combined_output_file, index=False)
    print(f"Combined portfolio simulation results saved to {combined_output_file}.")

    print("All portfolio simulations and equity curve plots completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate portfolios based on RR Level datasets.")
    parser.add_argument("--input_directory", type=str, required=True, help="Path to the directory containing RR Level datasets.")
    parser.add_argument("--output_directory", type=str, required=True, help="Path to the directory for saving portfolio simulation results.")
    parser.add_argument("--equity_curve_directory", type=str, required=True, help="Path to the directory for saving equity curve plots.")
    parser.add_argument("--spy_file_path", type=str, required=True, help="Path to the SPY data file.")
    parser.add_argument("--initial_balance", type=float, default=100000, help="Initial account balance for portfolio simulation.")

    args = parser.parse_args()
    main(args.input_directory, args.output_directory, args.equity_curve_directory, args.spy_file_path, args.initial_balance)
