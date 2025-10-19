import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, r2_score, silhouette_score
import warnings
warnings.filterwarnings('ignore')

# Classification Algorithms
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB

# Regression Algorithms
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor  # FIX: Added missing import

# Clustering Algorithms
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering

# Dimensionality Reduction
from sklearn.decomposition import PCA

# Neural Networks
from sklearn.neural_network import MLPClassifier, MLPRegressor

def run_ml_analysis(df):
    """
    Run comprehensive ML analysis on the dataset
    Returns: Dictionary with results from ML algorithms
    """
    results = {}
    
    # Basic dataset information
    n_samples, n_features = df.shape
    print(f"Running ML analysis on {n_samples} samples with {n_features} features...")
    
    # Prepare data for ML
    X, y, problem_type, target_column = prepare_data_for_ml(df)
    
    if X is None or y is None:
        return {"error": "Dataset too small or no suitable target column found for ML analysis"}
    
    print(f"Problem type: {problem_type}, Target: {target_column}")
    print(f"Features shape: {X.shape}, Target unique values: {y.nunique()}")
    
    # For classification, check if we have enough samples per class
    if problem_type == 'classification':
        class_counts = y.value_counts()
        print(f"Class distribution: {class_counts.to_dict()}")
        
        # If any class has less than 2 samples, switch to regression
        if (class_counts < 2).any():
            print("Switching to regression due to insufficient class samples")
            problem_type = 'regression'
    
    # Split data with appropriate parameters
    try:
        if problem_type == 'classification' and y.nunique() > 1:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=min(0.3, 0.8 - (20/len(X))),  # Dynamic test size
                random_state=42, 
                stratify=y
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=min(0.3, 0.8 - (20/len(X))),  # Dynamic test size
                random_state=42
            )
    except Exception as e:
        print(f"Train-test split failed: {e}. Using simpler split.")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42
        )
    
    print(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Run appropriate algorithms based on problem type
    if problem_type == 'classification' and y.nunique() > 1:
        results.update(run_classification_algorithms(X_train_scaled, X_test_scaled, y_train, y_test))
    else:  # regression
        results.update(run_regression_algorithms(X_train_scaled, X_test_scaled, y_train, y_test))
    
    # Run clustering algorithms (unsupervised) - only if we have enough samples
    if len(X_train_scaled) >= 10:
        results.update(run_clustering_algorithms(X_train_scaled))
    
    # Run dimensionality reduction - only if we have enough features
    if X_train_scaled.shape[1] >= 2:
        results.update(run_dimensionality_reduction(X_train_scaled, y_train if problem_type == 'classification' and y.nunique() > 1 else None))
    
    # Run neural networks
    if problem_type == 'classification' and y.nunique() > 1:
        results.update(run_neural_networks(X_train_scaled, X_test_scaled, y_train, y_test, 'classification'))
    else:
        results.update(run_neural_networks(X_train_scaled, X_test_scaled, y_train, y_test, 'regression'))
    
    # Generate summary
    results['_summary'] = generate_ml_summary(results)
    
    return results

def prepare_data_for_ml(df):
    """
    Prepare data for machine learning by identifying target variable and features
    """
    df_clean = df.copy()
    
    # Remove any remaining non-numeric columns for feature matrix
    numeric_columns = df_clean.select_dtypes(include=[np.number]).columns
    
    if len(numeric_columns) < 2:
        print("Not enough numeric columns for ML")
        return None, None, None, None
    
    # Try to identify target column (last column is often the target)
    potential_targets = []
    
    for col in numeric_columns:
        unique_vals = df_clean[col].nunique()
        total_vals = len(df_clean[col])
        
        # If less than 10 unique values or less than 10% unique, potential classification target
        if unique_vals <= 10 or unique_vals / total_vals <= 0.1:
            potential_targets.append((col, 'classification', unique_vals))
        else:
            potential_targets.append((col, 'regression', unique_vals))
    
    # Sort by number of unique values (prefer classification with fewer classes)
    potential_targets.sort(key=lambda x: x[2])
    
    # Select the best target
    if potential_targets:
        target_column, problem_type, _ = potential_targets[0]
        
        # Features are all numeric columns except target
        feature_columns = [col for col in numeric_columns if col != target_column]
        
        if len(feature_columns) == 0:
            # If no features left, use all but target
            feature_columns = [col for col in df_clean.columns if col != target_column]
            # Convert non-numeric features using one-hot encoding
            X = pd.get_dummies(df_clean[feature_columns], drop_first=True)
        else:
            X = df_clean[feature_columns]
        
        y = df_clean[target_column]
        
        # For classification, ensure y has at least 2 classes and enough samples
        if problem_type == 'classification':
            if y.nunique() < 2:
                print(f"Target '{target_column}' has only 1 class, switching to regression")
                problem_type = 'regression'
            elif (y.value_counts() < 2).any():
                print(f"Target '{target_column}' has classes with insufficient samples, switching to regression")
                problem_type = 'regression'
        
        print(f"Selected target: {target_column}, Type: {problem_type}")
        print(f"Features: {len(feature_columns)}, Samples: {len(X)}")
        
        return X, y, problem_type, target_column
    
    print("No suitable target column found")
    return None, None, None, None

def run_classification_algorithms(X_train, X_test, y_train, y_test):
    """Run classification algorithms with error handling"""
    results = {}
    
    algorithms = {
        'random_forest': RandomForestClassifier(n_estimators=50, random_state=42),
        'logistic_regression': LogisticRegression(random_state=42, max_iter=1000),
        'decision_tree': DecisionTreeClassifier(random_state=42),
        'knn': KNeighborsClassifier(n_neighbors=min(5, len(X_train))),
    }
    
    # Only add these if we have enough samples
    if len(X_train) > 100:
        algorithms['svm'] = SVC(random_state=42, probability=True)
        algorithms['gradient_boosting'] = GradientBoostingClassifier(random_state=42)
    
    if len(X_train) > 50:
        algorithms['naive_bayes'] = GaussianNB()
    
    for algo_name, model in algorithms.items():
        try:
            print(f"Running {algo_name}...")
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            
            # Cross-validation score (with fewer folds for small datasets)
            cv_folds = min(5, len(X_train) // 3)
            if cv_folds >= 2:
                cv_scores = cross_val_score(model, X_train, y_train, cv=cv_folds, scoring='accuracy')
                cv_mean = cv_scores.mean()
            else:
                cv_mean = accuracy
            
            results[algo_name] = {
                'algorithm': algo_name.replace('_', ' ').title(),
                'type': 'classification',
                'accuracy': round(accuracy, 4),
                'precision': round(precision, 4),
                'recall': round(recall, 4),
                'f1_score': round(f1, 4),
                'cross_val_mean': round(cv_mean, 4),
            }
            
        except Exception as e:
            print(f"Error in {algo_name}: {str(e)}")
            results[algo_name] = {
                'algorithm': algo_name.replace('_', ' ').title(),
                'type': 'classification',
                'error': str(e)
            }
    
    return results

def run_regression_algorithms(X_train, X_test, y_train, y_test):
    """Run regression algorithms with error handling"""
    results = {}
    
    algorithms = {
        'linear_regression': LinearRegression(),
        'ridge_regression': Ridge(random_state=42),
        'lasso_regression': Lasso(random_state=42),
        'random_forest_regressor': RandomForestRegressor(n_estimators=50, random_state=42),
        'decision_tree_regressor': DecisionTreeRegressor(random_state=42),  # FIX: Now imported
    }
    
    # Only add these if we have enough samples
    if len(X_train) > 100:
        algorithms['gradient_boosting_regressor'] = GradientBoostingRegressor(random_state=42)
        algorithms['svr'] = SVR()
    
    for algo_name, model in algorithms.items():
        try:
            print(f"Running {algo_name}...")
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Cross-validation score
            cv_folds = min(5, len(X_train) // 3)
            if cv_folds >= 2:
                cv_scores = cross_val_score(model, X_train, y_train, cv=cv_folds, scoring='r2')
                cv_mean = cv_scores.mean()
            else:
                cv_mean = r2
            
            results[algo_name] = {
                'algorithm': algo_name.replace('_', ' ').title(),
                'type': 'regression',
                'mse': round(mse, 4),
                'r2': round(r2, 4),
                'cross_val_mean': round(cv_mean, 4),
            }
            
        except Exception as e:
            print(f"Error in {algo_name}: {str(e)}")
            results[algo_name] = {
                'algorithm': algo_name.replace('_', ' ').title(),
                'type': 'regression',
                'error': str(e)
            }
    
    return results

def run_clustering_algorithms(X):
    """Run clustering algorithms with error handling"""
    results = {}
    
    algorithms = {
        'kmeans': KMeans(n_clusters=min(3, len(X)//3), random_state=42),
    }
    
    # Only run DBSCAN and hierarchical if we have enough samples
    if len(X) >= 20:
        algorithms['dbscan'] = DBSCAN(eps=0.5, min_samples=min(5, len(X)//10))
        algorithms['hierarchical'] = AgglomerativeClustering(n_clusters=min(3, len(X)//3))
    
    for algo_name, model in algorithms.items():
        try:
            print(f"Running {algo_name}...")
            labels = model.fit_predict(X)
            
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            
            if n_clusters > 1:
                silhouette = silhouette_score(X, labels)
            else:
                silhouette = -1
            
            results[algo_name] = {
                'algorithm': algo_name.replace('_', ' ').title(),
                'type': 'clustering',
                'n_clusters': n_clusters,
                'silhouette_score': round(silhouette, 4) if silhouette != -1 else 'N/A',
            }
            
        except Exception as e:
            print(f"Error in {algo_name}: {str(e)}")
            results[algo_name] = {
                'algorithm': algo_name.replace('_', ' ').title(),
                'type': 'clustering',
                'error': str(e)
            }
    
    return results

def run_dimensionality_reduction(X, y=None):
    """Run PCA for dimensionality reduction"""
    results = {}
    
    try:
        print("Running PCA...")
        n_components = min(2, X.shape[1], X.shape[0] - 1)
        if n_components >= 1:
            pca = PCA(n_components=n_components)
            X_pca = pca.fit_transform(X)
            
            explained_variance = pca.explained_variance_ratio_
            cumulative_variance = explained_variance.cumsum()
            
            results['pca'] = {
                'algorithm': 'Principal Component Analysis',
                'type': 'dimensionality_reduction',
                'n_components': len(explained_variance),
                'explained_variance_ratio': [round(val, 4) for val in explained_variance],
                'cumulative_variance': [round(val, 4) for val in cumulative_variance],
                'total_variance_explained': round(cumulative_variance[-1], 4) if len(cumulative_variance) > 0 else 0
            }
        
    except Exception as e:
        print(f"Error in PCA: {str(e)}")
        results['pca'] = {
            'algorithm': 'Principal Component Analysis',
            'type': 'dimensionality_reduction',
            'error': str(e)
        }
    
    return results

def run_neural_networks(X_train, X_test, y_train, y_test, problem_type):
    """Run Neural Networks (MLP) with error handling"""
    results = {}
    
    # Only run neural networks if we have enough data
    if len(X_train) < 50:
        return results
    
    try:
        print("Running Neural Network...")
        
        if problem_type == 'classification':
            model = MLPClassifier(hidden_layer_sizes=(50, 25), random_state=42, max_iter=500)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            
            results['neural_network'] = {
                'algorithm': 'Neural Network (MLP)',
                'type': 'classification',
                'accuracy': round(accuracy, 4),
                'precision': round(precision, 4),
                'recall': round(recall, 4),
                'f1_score': round(f1, 4),
            }
        else:
            model = MLPRegressor(hidden_layer_sizes=(50, 25), random_state=42, max_iter=500)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            results['neural_network'] = {
                'algorithm': 'Neural Network (MLP)',
                'type': 'regression',
                'mse': round(mse, 4),
                'r2': round(r2, 4),
            }
            
    except Exception as e:
        print(f"Error in Neural Network: {str(e)}")
    
    return results

def generate_ml_summary(results):
    """Generate a summary of ML results"""
    summary = {
        'total_algorithms_run': len([r for r in results.values() if 'error' not in r]),
        'best_classification': None,
        'best_regression': None,
        'best_clustering': None
    }
    
    classification_results = {k: v for k, v in results.items() if v.get('type') == 'classification' and 'accuracy' in v}
    regression_results = {k: v for k, v in results.items() if v.get('type') == 'regression' and 'r2' in v}
    clustering_results = {k: v for k, v in results.items() if v.get('type') == 'clustering' and 'silhouette_score' in v and v['silhouette_score'] != 'N/A'}
    
    if classification_results:
        best_classification = max(classification_results.items(), key=lambda x: x[1].get('accuracy', 0))
        summary['best_classification'] = {
            'algorithm': best_classification[1]['algorithm'],
            'accuracy': best_classification[1]['accuracy']
        }
    
    if regression_results:
        best_regression = max(regression_results.items(), key=lambda x: x[1].get('r2', -1))
        summary['best_regression'] = {
            'algorithm': best_regression[1]['algorithm'],
            'r2': best_regression[1]['r2']
        }
    
    if clustering_results:
        best_clustering = max(clustering_results.items(), key=lambda x: x[1].get('silhouette_score', -1))
        summary['best_clustering'] = {
            'algorithm': best_clustering[1]['algorithm'],
            'silhouette_score': best_clustering[1]['silhouette_score']
        }
    
    return summary

# Test function
def test_ml_pipeline():
    """Test the ML pipeline with sample data"""
    from sklearn.datasets import make_classification, make_regression
    
    print("Testing Classification...")
    X_class, y_class = make_classification(n_samples=100, n_features=5, n_classes=2, random_state=42)
    df_class = pd.DataFrame(X_class, columns=[f'feature_{i}' for i in range(5)])
    df_class['target'] = y_class
    
    results_class = run_ml_analysis(df_class)
    print(f"Classification algorithms run: {len(results_class)}")
    
    print("\nTesting Regression...")
    X_reg, y_reg = make_regression(n_samples=100, n_features=5, random_state=42)
    df_reg = pd.DataFrame(X_reg, columns=[f'feature_{i}' for i in range(5)])
    df_reg['target'] = y_reg
    
    results_reg = run_ml_analysis(df_reg)
    print(f"Regression algorithms run: {len(results_reg)}")
    
    return results_class, results_reg

if __name__ == "__main__":
    # Run test if file is executed directly
    test_ml_pipeline()