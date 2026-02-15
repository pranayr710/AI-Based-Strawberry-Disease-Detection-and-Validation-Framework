import pandas as pd

# Read both CSV files
df1 = pd.read_csv('output_cm.csv')
df2 = pd.read_csv('updated_file.csv')

# Get list of all columns (excluding 'Image Name' and 'Signed')
all_columns = [col for col in df1.columns if col not in ['Image Name', 'Signed']]

# Iterate through each row in df1
for index, row in df1.iterrows():
    image_name = row['Image Name']
    signed_in_1 = row['Signed']
    
    # If not signed in df1, check df2
    if signed_in_1 == 0:
        # Find matching row in df2
        matching_rows = df2[df2['Image Name'] == image_name]
        
        if not matching_rows.empty:
            matching_row = matching_rows.iloc[0]
            if matching_row['Signed'] == 1:
                # Update Signed status
                df1.at[index, 'Signed'] = 1
                
                # Update all other columns individually
                for col in all_columns:
                    df1.at[index, col] = matching_row[col]

# Save the updated df1 back to the original file
df1.to_csv('combined.csv', index=False)

print("Update complete. 1.csv has been modified.")