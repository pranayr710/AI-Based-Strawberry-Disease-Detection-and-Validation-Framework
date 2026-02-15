import pandas as pd

def ensure_signed_column(csv_path="output_cm.csv"):
    """
    Ensures all rows have 0 or 1 in 'Signed' column.
    Fills missing values with 0. Creates column if it doesn't exist.
    """
    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Process 'Signed' column
        if 'Signed' not in df.columns:
            df['Signed'] = 0  # Create column if missing
        else:
            df['Signed'] = df['Signed'].fillna(0)  # Fill NA/NULL with 0
            df['Signed'] = pd.to_numeric(df['Signed'], errors='coerce').fillna(0)  # Handle non-numeric
            df['Signed'] = df['Signed'].astype(int).clip(0, 1)  # Ensure only 0 or 1
        
        # Save back to CSV
        df.to_csv(csv_path, index=False)
        print(f"Successfully updated {csv_path} - all rows now have Signed=0 or 1")
        return True
        
    except Exception as e:
        print(f"Error processing {csv_path}: {str(e)}")
        return False

# Usage example in your main function:
if __name__ == "__main__":
    # Just call this function - it will handle everything
    ensure_signed_column("output_cm.csv")  # You can change the path if needed