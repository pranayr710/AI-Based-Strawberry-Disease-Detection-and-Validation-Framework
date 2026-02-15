import pandas as pd

# Load CSV
df = pd.read_csv('output_cm.csv')

# List of base image names you want to mark as signed
images_to_sign = ["nihal_ooty_tnau_real_20230912_00047",
"nihal_ooty_tnau_real_20230912_00048",
"nihal_ooty_tnau_real_20230912_00049",
"nihal_ooty_tnau_real_20230912_00050",
"nihal_ooty_tnau_real_20230912_00051",
"nihal_ooty_tnau_real_20230912_00052",
"nihal_ooty_tnau_real_20230912_00053",
"nihal_ooty_tnau_real_20230912_00054",
"nihal_ooty_tnau_real_20230912_00055",
"nihal_ooty_tnau_real_20230912_00056",
"nihal_ooty_tnau_real_20230912_00057",
"nihal_ooty_tnau_real_20230912_00058",
"nihal_ooty_tnau_real_20230912_00059",
"nihal_ooty_tnau_real_20230912_00060",
"nihal_ooty_tnau_real_20230912_00061",
"nihal_ooty_tnau_real_20230912_00062",
"nihal_ooty_tnau_real_20230912_00063",
"nihal_ooty_tnau_real_20230912_00064",
"nihal_ooty_tnau_real_20230912_00065",
"nihal_ooty_tnau_real_20230912_00066",
"nihal_ooty_tnau_real_20230912_00067"]  # <-- replace with your actual list

# Loop through each row
for i in range(len(df)):
    image_name = df.loc[i, 'Image Name']
    for base_name in images_to_sign:
        if image_name.startswith(base_name):
            df.loc[i, 'Signed'] = 1
            break  # No need to check other base names if one matches

# Save the updated CSV
df.to_csv('updated_file_1.csv', index=False)

print("Updated 'Signed' column for specified images and saved as 'updated_file.csv'")
