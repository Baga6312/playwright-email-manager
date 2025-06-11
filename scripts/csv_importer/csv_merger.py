import pandas as pd

emails = pd.read_csv('emails.csv')
proxies = pd.read_csv('proxies.csv')
user_data = pd.read_csv('user_statuses.csv')

# Merge into one DataFrame (adjust 'join_column' as needed)
master_df = pd.merge(
    emails, 
    proxies, 
    on='join_column',  # e.g., 'username' or 'user_id'
    how='left'
).merge(
    user_data, 
    on='join_column',
    how='left'
)

master_df.to_csv('master_data.csv', index=False)