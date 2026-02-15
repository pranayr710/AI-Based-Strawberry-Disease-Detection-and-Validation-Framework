import pandas as pd

# Load the CSV
df = pd.read_csv('output_cm.csv')

# Delete the column 'Mg-Leaf-Pink_Patches' if it exists
if 'Thrips-Fruit-Rusetting_Cracking' in df.columns:
    df = df.drop(columns=['Thrips-Fruit-Rusetting_Cracking'])
    print("Column 'Mg-Leaf-Yellowish_Green' deleted.")
else:
    print("Column 'Mg-Leaf-Yellowish_Green' does not exist.")

# Save the updated CSV
df.to_csv('output_cm.csv', index=False)

print("File saved as 'updated_file.csv'")
