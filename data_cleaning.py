import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
import warnings
warnings.filterwarnings('ignore')

def clean_data(df):
    """
    Comprehensive data cleaning pipeline
    Returns: cleaning_result dict, cleaned DataFrame
    """
    
    # Store original state
    original_shape = df.shape
    cleaning_result = {
        'original_rows': original_shape[0],
        'original_columns': original_shape[1],
        'missing_values': 0,
        'duplicates_removed': 0,
        'null_values': 0,
        'cleaned_rows': 0,
        'cleaned_columns': 0,
        'data_types': {},
        'cleaning_steps': []
    }
    
    # Create a copy to avoid modifying original
    cleaned_df = df.copy()
    
    # Step 1: Handle missing values
    cleaning_result['missing_values'] = cleaned_df.isnull().sum().sum()
    cleaned_df = handle_missing_values(cleaned_df)
    cleaning_result['cleaning_steps'].append(f"Handled {cleaning_result['missing_values']} missing values")
    
    # Step 2: Remove duplicates
    initial_rows = len(cleaned_df)
    cleaned_df = remove_duplicates(cleaned_df)
    duplicates_removed = initial_rows - len(cleaned_df)
    cleaning_result['duplicates_removed'] = duplicates_removed
    if duplicates_removed > 0:
        cleaning_result['cleaning_steps'].append(f"Removed {duplicates_removed} duplicate rows")
    
    # Step 3: Handle null values
    cleaning_result['null_values'] = cleaned_df.isna().sum().sum()
    cleaned_df = handle_null_values(cleaned_df)
    if cleaning_result['null_values'] > 0:
        cleaning_result['cleaning_steps'].append(f"Handled {cleaning_result['null_values']} null values")
    
    # Step 4: Clean column names
    cleaned_df = clean_column_names(cleaned_df)
    cleaning_result['cleaning_steps'].append("Cleaned column names")
    
    # Step 5: Handle data types
    cleaned_df = optimize_data_types(cleaned_df)
    cleaning_result['cleaning_steps'].append("Optimized data types")
    
    # Step 6: Remove constant columns
    initial_cols = len(cleaned_df.columns)
    cleaned_df = remove_constant_columns(cleaned_df)
    constant_cols_removed = initial_cols - len(cleaned_df.columns)
    if constant_cols_removed > 0:
        cleaning_result['cleaning_steps'].append(f"Removed {constant_cols_removed} constant columns")
    
    # Step 7: Handle outliers (for numerical columns only)
    numerical_cols = cleaned_df.select_dtypes(include=[np.number]).columns
    if len(numerical_cols) > 0:
        outlier_info = handle_outliers(cleaned_df, numerical_cols)
        if outlier_info['total_outliers'] > 0:
            cleaning_result['cleaning_steps'].append(f"Handled {outlier_info['total_outliers']} outliers across {outlier_info['columns_affected']} columns")
    
    # Step 8: Encode categorical variables
    categorical_cols = cleaned_df.select_dtypes(include=['object', 'category']).columns
    if len(categorical_cols) > 0:
        encoding_result = encode_categorical_variables(cleaned_df, categorical_cols)
        cleaned_df = encoding_result['df']
        cleaning_result['cleaning_steps'].append(f"Encoded {len(categorical_cols)} categorical columns")
        cleaning_result['label_encoders'] = encoding_result['encoders']
    
    # Step 9: Final validation
    cleaned_df = final_validation(cleaned_df)
    
    # Update final results
    cleaning_result['cleaned_rows'] = len(cleaned_df)
    cleaning_result['cleaned_columns'] = len(cleaned_df.columns)
    cleaning_result['data_types'] = {col: str(dtype) for col, dtype in cleaned_df.dtypes.items()}
    
    # Calculate data retention
    retention_rate = (cleaning_result['cleaned_rows'] / cleaning_result['original_rows']) * 100
    cleaning_result['retention_rate'] = round(retention_rate, 2)
    cleaning_result['cleaning_steps'].append(f"Final data retention: {retention_rate:.1f}%")
    
    return cleaning_result, cleaned_df

def handle_missing_values(df):
    """Handle missing values with appropriate strategies"""
    df_clean = df.copy()
    
    for column in df_clean.columns:
        missing_count = df_clean[column].isnull().sum()
        
        if missing_count > 0:
            # For numerical columns: fill with median
            if pd.api.types.is_numeric_dtype(df_clean[column]):
                df_clean[column].fillna(df_clean[column].median(), inplace=True)
            # For categorical columns: fill with mode
            else:
                mode_value = df_clean[column].mode()
                if len(mode_value) > 0:
                    df_clean[column].fillna(mode_value[0], inplace=True)
                else:
                    df_clean[column].fillna('Unknown', inplace=True)
    
    return df_clean

def remove_duplicates(df):
    """Remove duplicate rows"""
    return df.drop_duplicates()

def handle_null_values(df):
    """Handle any remaining null values"""
    df_clean = df.copy()
    
    # Fill any remaining nulls
    for column in df_clean.columns:
        if df_clean[column].isna().any():
            if pd.api.types.is_numeric_dtype(df_clean[column]):
                df_clean[column].fillna(0, inplace=True)
            else:
                df_clean[column].fillna('Missing', inplace=True)
    
    return df_clean

def clean_column_names(df):
    """Clean and standardize column names"""
    df_clean = df.copy()
    
    new_columns = []
    for col in df_clean.columns:
        # Convert to string, remove special characters, lowercase, replace spaces
        clean_col = str(col).strip().lower().replace(' ', '_').replace('-', '_')
        clean_col = ''.join(c for c in clean_col if c.isalnum() or c == '_')
        
        # Remove multiple underscores
        clean_col = '_'.join(filter(None, clean_col.split('_')))
        
        # Ensure column name is not empty
        if not clean_col:
            clean_col = 'unknown_column'
        
        new_columns.append(clean_col)
    
    df_clean.columns = new_columns
    return df_clean

def optimize_data_types(df):
    """Optimize data types for memory and processing"""
    df_clean = df.copy()
    
    for column in df_clean.columns:
        # For numerical columns, try to downcast to smaller types
        if pd.api.types.is_numeric_dtype(df_clean[column]):
            # Skip if column has NaN values that can't be handled by integer types
            if not df_clean[column].isna().any():
                # Try to convert to integer if possible
                if (df_clean[column] % 1 == 0).all():
                    df_clean[column] = pd.to_numeric(df_clean[column], downcast='integer')
                else:
                    df_clean[column] = pd.to_numeric(df_clean[column], downcast='float')
        
        # For categorical columns with few unique values, convert to category
        elif pd.api.types.is_string_dtype(df_clean[column]):
            unique_ratio = df_clean[column].nunique() / len(df_clean[column])
            if unique_ratio < 0.5:  # If less than 50% unique values
                df_clean[column] = df_clean[column].astype('category')
    
    return df_clean

def remove_constant_columns(df):
    """Remove columns with constant values"""
    df_clean = df.copy()
    
    constant_columns = []
    for column in df_clean.columns:
        if df_clean[column].nunique() <= 1:
            constant_columns.append(column)
    
    if constant_columns:
        df_clean = df_clean.drop(columns=constant_columns)
    
    return df_clean

def handle_outliers(df, numerical_columns):
    """Handle outliers using IQR method"""
    df_clean = df.copy()
    outlier_info = {'total_outliers': 0, 'columns_affected': 0}
    
    for column in numerical_columns:
        Q1 = df_clean[column].quantile(0.25)
        Q3 = df_clean[column].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = df_clean[(df_clean[column] < lower_bound) | (df_clean[column] > upper_bound)]
        
        if len(outliers) > 0:
            outlier_info['total_outliers'] += len(outliers)
            outlier_info['columns_affected'] += 1
            
            # Cap outliers instead of removing them to preserve data
            df_clean[column] = np.where(df_clean[column] < lower_bound, lower_bound, df_clean[column])
            df_clean[column] = np.where(df_clean[column] > upper_bound, upper_bound, df_clean[column])
    
    return outlier_info

def encode_categorical_variables(df, categorical_columns):
    """Encode categorical variables using Label Encoding"""
    df_clean = df.copy()
    encoders = {}
    
    for column in categorical_columns:
        # Use label encoding for categorical variables
        le = LabelEncoder()
        df_clean[column] = le.fit_transform(df_clean[column].astype(str))
        encoders[column] = le
    
    return {'df': df_clean, 'encoders': encoders}

def final_validation(df):
    """Final validation and cleanup"""
    df_clean = df.copy()
    
    # Ensure no infinite values
    numeric_columns = df_clean.select_dtypes(include=[np.number]).columns
    for column in numeric_columns:
        df_clean[column] = df_clean[column].replace([np.inf, -np.inf], np.nan)
        df_clean[column].fillna(df_clean[column].median(), inplace=True)
    
    # Reset index
    df_clean = df_clean.reset_index(drop=True)
    
    return df_clean

def get_data_quality_report(df):
    """Generate a comprehensive data quality report"""
    report = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'missing_values_per_column': df.isnull().sum().to_dict(),
        'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
        'unique_values_per_column': df.nunique().to_dict(),
        'memory_usage_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
    }
    
    return report

# Test function for the cleaning pipeline
def test_cleaning_pipeline():
    """Test function to verify the cleaning pipeline works"""
    # Create sample test data
    test_data = {
        'Name': ['Alice', 'Bob', 'Charlie', None, 'Eve', 'Alice'],
        'Age': [25, 30, None, 35, 35, 25],
        'Salary': [50000, 60000, 70000, 80000, 80000, 50000],
        'Department': ['IT', 'HR', 'IT', 'Finance', 'Finance', 'IT'],
        'Constant_Col': [1, 1, 1, 1, 1, 1]
    }
    
    test_df = pd.DataFrame(test_data)
    print("Original Data:")
    print(test_df)
    print(f"Original shape: {test_df.shape}")
    
    # Run cleaning pipeline
    cleaning_result, cleaned_df = clean_data(test_df)
    
    print("\nCleaned Data:")
    print(cleaned_df)
    print(f"Cleaned shape: {cleaned_df.shape}")
    
    print("\nCleaning Results:")
    for key, value in cleaning_result.items():
        if key != 'cleaning_steps':
            print(f"{key}: {value}")
    
    print("\nCleaning Steps:")
    for step in cleaning_result['cleaning_steps']:
        print(f"- {step}")

if __name__ == "__main__":
    # Run test if file is executed directly
    test_cleaning_pipeline()