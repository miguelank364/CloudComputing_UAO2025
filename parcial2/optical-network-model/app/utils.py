import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import json

def load_data(file_path):
    """
    Load optical network data from a CSV file
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        pandas DataFrame with loaded data
    """
    try:
        data = pd.read_csv(file_path)
        print(f"Data loaded successfully with {data.shape[0]} rows and {data.shape[1]} columns")
        return data
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        # Return sample data for demonstration
        return generate_sample_data()

def generate_sample_data(n_samples=100):
    """Generate sample optical network data for demonstration"""
    np.random.seed(42)
    
    # Generate features
    power_levels = np.random.uniform(-30, 0, n_samples)  # Power in dBm
    distances = np.random.uniform(0, 100, n_samples)     # Distance in km
    wavelengths = np.random.uniform(1520, 1570, n_samples)  # Wavelength in nm
    snr = np.random.uniform(5, 30, n_samples)            # Signal-to-noise ratio in dB
    chromatic_dispersion = np.random.uniform(-500, 500, n_samples)  # ps/nm
    
    # Additional features
    polarization_mode_dispersion = np.random.uniform(0, 10, n_samples)
    bit_rate = np.random.choice([10, 40, 100], n_samples)  # Gbps
    modulation = np.random.choice([0, 1, 2, 3], n_samples)  # Encoding different modulation schemes
    temperature = np.random.uniform(20, 40, n_samples)  # Celsius
    humidity = np.random.uniform(30, 80, n_samples)  # Percentage
    
    # Generate target (binary classification - e.g., signal quality good/bad)
    # Using a simple rule: if power is above -20 dBm and SNR is above 15 dB, signal is good
    target = ((power_levels > -20) & (snr > 15)).astype(int)
    
    # Create DataFrame
    data = pd.DataFrame({
        'power_level': power_levels,
        'distance': distances,
        'wavelength': wavelengths,
        'snr': snr,
        'chromatic_dispersion': chromatic_dispersion,
        'polarization_mode_dispersion': polarization_mode_dispersion,
        'bit_rate': bit_rate,
        'modulation': modulation,
        'temperature': temperature,
        'humidity': humidity,
        'target': target
    })
    
    return data

def preprocess_data(data_string):
    """
    Preprocess input data for the model
    
    Args:
        data_string: JSON string with feature values
        
    Returns:
        numpy array ready for model prediction
    """
    try:
        # Parse JSON string to dictionary
        if isinstance(data_string, str):
            features = json.loads(data_string)
        else:
            features = data_string
            
        # Convert to numpy array
        if isinstance(features, dict):
            # Single sample
            feature_names = ['power_level', 'distance', 'wavelength', 'snr', 'chromatic_dispersion',
                            'polarization_mode_dispersion', 'bit_rate', 'modulation', 
                            'temperature', 'humidity']
            X = np.array([[features.get(name, 0) for name in feature_names]])
        else:
            # Already numpy array or list
            X = np.array(features)
            
        # Perform scaling (normally we would use a pre-fitted scaler)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return X_scaled
        
    except Exception as e:
        print(f"Error preprocessing data: {str(e)}")
        # Return dummy data in case of error
        return np.zeros((1, 10))

def calculate_correlation_matrix(data):
    """
    Calculate correlation matrix for features
    
    Args:
        data: pandas DataFrame with features
        
    Returns:
        correlation matrix as a JSON string
    """
    corr_matrix = data.corr().round(2)
    return corr_matrix.to_json()
