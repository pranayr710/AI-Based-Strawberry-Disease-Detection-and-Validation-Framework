import pandas as pd

# Load the CSV
df = pd.read_csv('output_cm.csv')

# Get the column index for the second last column (before 'Signed')
signed_index = df.columns.get_loc('Signed')

# Insert the new columns with 0s before 'Signed'
df.insert(signed_index, 'K-Leaf-Purple_Patches', 0)

# Save the updated CSV
df.to_csv('output_cm.csv', index=False)

print("Columns added and file saved as 'updated_file.csv'")
