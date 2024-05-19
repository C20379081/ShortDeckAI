import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

# Pie chart used for the visulations of the AI tests, data stored ina csv file
def pie():
    df = pd.read_csv('5000vs1000.csv')

    # Calculate net wins for each hand
    df['Net Win'] = df['Player 0 Ending Chips'] - df['Player 1 Ending Chips']

    # Determine the winner of each hand, excluding ties
    conditions = [
        (df['Net Win'] > 0),  # Player 0 wins
        (df['Net Win'] < 0)   # Player 1 wins
    ]
    choices = ['AI Win', 'Random Bot Win']
    df['Result'] = pd.np.select(conditions, choices, default='Tie')

    result_counts = df['Result'].value_counts().drop('Tie')

    # Plotting the pie chart of wins excluding ties
    plt.figure(figsize=(8, 8))
    plt.pie(result_counts, labels=result_counts.index, autopct='%1.1f%%', startangle=140, colors=['blue', 'red'])
    plt.title('Distribution of Wins between 5000 iterations vs 1000 Iterations')
    plt.show()

# Line grpah to see who won or lost 
def plot_net_gain_loss():
    df = pd.read_csv('7000vs1000.csv')
    # Calculate the difference in chips after each hand
    df['Difference'] = df['Player 0 Ending Chips'] - df['Player 1 Ending Chips']
    # Calculate the cumulative difference 
    df['Cumulative Difference'] = df['Difference'].cumsum()
    # Calculate the net win per hand
    df['Net Win'] = df['Player 0 Ending Chips'] - df['Player 1 Ending Chips']
    # Calculate the cumulative net win after each hand
    df['Cumulative Net Win'] = df['Net Win'].cumsum()
    last_cumulative_win = df['Cumulative Net Win'].iloc[-1]
    # Calculate the average cumulative win per 100 hands
    total_hands_played = df.shape[0]
    average_cumulative_win_per_100_hands = (last_cumulative_win / total_hands_played) * 100
    average_cumulative_win_per_100_hands_rounded = round(average_cumulative_win_per_100_hands, 1)

    plt.figure(figsize=(10, 6))
    plt.plot(df['Simulation'], df['Cumulative Difference'], label='Cumulative Difference', color='green')

    ax = plt.gca()
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))

    title_text = f'Amount Won / Lost Between Players 7000 iterations vs 1000 iterations\nAverage Win per 100 Hands: {average_cumulative_win_per_100_hands_rounded}'
    plt.title(title_text)
    plt.xlabel('Simulation Number')
    plt.ylabel('Amount Won')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


pie()
plot_net_gain_loss()

