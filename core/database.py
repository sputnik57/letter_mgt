  
import pandas as pd

def load_data(path: str = "../prisoner_13Aug2025.xlsx") -> pd.DataFrame:
    """
    Load prisoner data from Excel file. If not found, return sample data.
    """
    try:
        return pd.read_excel(path)
    except FileNotFoundError:
        sample_data = {
            'fName': ['John', 'Jane', 'Bob'],
            'lName': ['Doe', 'Smith', 'Johnson'],
            'CDCRno': ['A123456', 'B789012', 'C345678'],
            'housing': ['Block A', 'Block B', 'Block C'],
            'letter exchange (received only)': ['', '', '']
        }
        return pd.DataFrame(sample_data)

def save_data(df: pd.DataFrame, path: str = "../prisoner_13Aug2025.xlsx") -> None:
    """
    Save updated prisoner data to Excel.
    """
    df.to_excel(path, index=False)