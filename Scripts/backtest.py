import pandas as pd
import numpy as np
from datetime import timedelta
import argparse
import os

def main(file_15min, file_5min, file_1min, output_file):
    # Load datasets
    print("Loading datasets...")
    data_15min = pd.read_csv(file_15min, parse_dates=['Datetime'], index_col='Datetime')
    data_5min = pd.read_csv(file_5min, parse_dates=['Datetime'], index_col='Datetime')

    # Load 1-minute data without headers and assign column names
    column_names = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
    data_1min = pd.read_csv(file_1min, header=None, names=column_names, parse_dates=['Datetime'], index_col='Datetime')
    print("Datasets loaded successfully.")

    # Filter data to start from January 1, 2020
    data_15min = data_15min[data_15min.index >= '2024-06-01']
    data_5min = data_5min[data_5min.index >= '2024-06-01']
    data_1min = data_1min[data_1min.index >= '2024-06-01']

    # Initialize results list
    results = []

    # Define risk-reward levels
    rr_levels = np.arange(0.001, 0.02 + 0.001, 0.001)  # 0.10% to 2% in 0.10% increments

    # Backtest logic for each risk-reward level
    print("Starting backtest...")
    for rr in rr_levels:
        print(f"Testing RR Level: {rr}")
        active_trade = None  # To track if a trade is active

        for date, day_data in data_15min.groupby(data_15min.index.date):
            print(f"Processing date: {date}")

            # Extract the range for the day (first 15-minute candle)
            try:
                range_high = day_data.between_time('09:30', '09:45')['High'].iloc[0]
                range_low = day_data.between_time('09:30', '09:45')['Low'].iloc[0]
                print(f"Range for the day: High = {range_high}, Low = {range_low}")
            except IndexError:
                print("No data for the range time period. Skipping date.")
                continue

            # Filter 5-minute data for the day and after 09:45 until 11:30
            day_5min = data_5min[data_5min.index.date == date]
            day_5min = day_5min.between_time('09:50', '11:30')

            # Skip if an active trade is ongoing
            if active_trade:
                print(f"Skipping day {date} due to ongoing trade.")
                continue

            # Scan for entry conditions
            entry_found = False
            direction = None
            entry_price = None
            entry_time = None

            for i, row in day_5min.iterrows():
                if not entry_found:
                    # Check for breakout above the high or below the low
                    if row['Close'] > range_high:
                        direction = 'long'
                        entry_found = True
                        print(f"Breakout detected above high at {i}. Looking for re-entry.")
                    elif row['Close'] < range_low:
                        direction = 'short'
                        entry_found = True
                        print(f"Breakout detected below low at {i}. Looking for re-entry.")
                else:
                    # Check for wick re-entry
                    if direction == 'long' and row['Low'] <= range_high and row['Close'] > range_high:
                        entry_price = row['Close']
                        entry_time = i
                        print(f"Entry signal detected for long at {i} with entry price {entry_price}.")
                        break
                    elif direction == 'short' and row['High'] >= range_low and row['Close'] < range_low:
                        entry_price = row['Close']
                        entry_time = i
                        print(f"Entry signal detected for short at {i} with entry price {entry_price}.")
                        break

            # If no entry found, move to the next day
            if not entry_price:
                print(f"No entry found for {date}. Moving to next day.")
                continue

            # Define stop-loss and target based on RR level
            stop_loss = entry_price * (1 - rr) if direction == 'long' else entry_price * (1 + rr)
            target = entry_price * (1 + 2 * rr) if direction == 'long' else entry_price * (1 - 2 * rr)

            # Simulate trade outcomes using 1-minute data
            day_1min = data_1min[data_1min.index.date >= entry_time.date()]
            exit_price = None
            exit_time = None
            max_drawdown = None

            for j, row in day_1min[day_1min.index >= entry_time].iterrows():
                # Update drawdown during the trade
                if direction == 'long':
                    max_drawdown = min(max_drawdown, row['Low']) if max_drawdown else row['Low']
                    if row['Low'] <= stop_loss or row['High'] >= target:
                        exit_price = stop_loss if row['Low'] <= stop_loss else target
                        exit_time = j
                        print(f"Trade exited for long at {exit_time} with exit price {exit_price}.")
                        break
                elif direction == 'short':
                    max_drawdown = max(max_drawdown, row['High']) if max_drawdown else row['High']
                    if row['High'] >= stop_loss or row['Low'] <= target:
                        exit_price = stop_loss if row['High'] >= stop_loss else target
                        exit_time = j
                        print(f"Trade exited for short at {exit_time} with exit price {exit_price}.")
                        break

            # If no exit condition met, mark trade as active and continue
            if not exit_price:
                print(f"No exit condition met for active trade starting at {entry_time}. Holding trade.")
                active_trade = {
                    'Direction': direction,
                    'Entry_Price': entry_price,
                    'Entry_Time': entry_time,
                    'Stop_Loss': stop_loss,
                    'Target': target
                }
                continue

            # Record the trade outcome
            max_drawdown_percentage = (
                (max_drawdown - entry_price) / entry_price * 100 if direction == 'long' else
                (entry_price - max_drawdown) / entry_price * 100
            )
            percentage_return = (
                (exit_price - entry_price) / entry_price * 100 if direction == 'long' else
                (entry_price - exit_price) / entry_price * 100
            )

            results.append({
                'RR_Level': rr,
                'Direction': direction,
                'Entry_Time': entry_time,
                'Entry_Price': entry_price,
                'Exit_Time': exit_time,
                'Exit_Price': exit_price,
                'Max_Drawdown': max_drawdown_percentage,
                'Percentage_Return': percentage_return
            })
            print(f"Recorded trade for RR Level {rr}: Percentage Return = {percentage_return:.2f}%.")

            # Reset active trade state
            active_trade = None

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Save results
    results_df.to_csv(output_file, index=False)
    print(f"Backtest complete. Results saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backtest based on RR Level.")
    parser.add_argument("--file_15min", type=str, required=True, help="Path to the 15-minute dataset CSV file.")
    parser.add_argument("--file_5min", type=str, required=True, help="Path to the 5-minute dataset CSV file.")
    parser.add_argument("--file_1min", type=str, required=True, help="Path to the 1-minute dataset CSV file.")
    parser.add_argument("--output_file", type=str, required=True, help="Path to save the backtest results CSV file.")

    args = parser.parse_args()
    main(args.file_15min, args.file_5min, args.file_1min, args.output_file)
