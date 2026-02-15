import pandas as pd

# Load the CSV file
df = pd.read_csv("updated_file_1.csv")

# Keep only the label columns (assuming first 5 columns are not labels)
label_df = df.iloc[:, 5:]

# Sum each label column
label_counts = label_df.sum()

# Convert to a DataFrame so we can save to CSV
label_counts_df = label_counts.reset_index()
label_counts_df.columns = ['Label', 'Count']

# Save to CSV
label_counts_df.to_csv("label_counts.csv", index=False)

print("Label counts saved to 'label_counts.csv'")
