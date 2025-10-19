from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
import uuid
import joblib
from datetime import datetime
import traceback
import json

# Import our custom modules
from ml_analysis import run_ml_analysis
from data_cleaning import clean_data

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Store analysis status and results in memory (use database in production)
analysis_status = {}
analysis_results = {}

# Custom JSON encoder to handle numpy types and LabelEncoder
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle numpy types
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        # Handle LabelEncoder and other non-serializable objects
        elif hasattr(obj, '__class__') and 'LabelEncoder' in str(obj.__class__):
            return str(obj)  # Convert to string representation
        # Handle other non-serializable objects
        elif hasattr(obj, '__dict__'):
            return str(obj)
        else:
            return super().default(obj)

app.json_encoder = CustomJSONEncoder

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Backend is running"})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload - supports .xls and .xlsx files up to 100MB"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Validate file type
        if not (file.filename.endswith('.xls') or file.filename.endswith('.xlsx')):
            return jsonify({"error": "Only .xls and .xlsx files are supported"}), 400
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        file.save(file_path)
        
        # Store file info
        analysis_status[file_id] = {
            'status': 'uploaded',
            'filename': filename,
            'upload_time': datetime.now().isoformat()
        }
        
        return jsonify({
            "file_id": file_id,
            "message": "File uploaded successfully",
            "status": "uploaded",
            "filename": file.filename
        })
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    """Start data cleaning and ML analysis on uploaded file"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        
        if not file_id:
            return jsonify({"error": "File ID is required"}), 400
        
        if file_id not in analysis_status:
            return jsonify({"error": "File not found"}), 404
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Update status
        analysis_status[file_id]['analysis_id'] = analysis_id
        analysis_status[file_id]['status'] = 'analyzing'
        analysis_status[file_id]['analysis_start_time'] = datetime.now().isoformat()
        
        # Start analysis in background (in production, use Celery or similar)
        def run_analysis():
            try:
                file_info = analysis_status[file_id]
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info['filename'])
                
                # Read and clean data
                df = pd.read_excel(file_path)
                cleaning_result, cleaned_df = clean_data(df)
                
                # Remove non-serializable objects from cleaning result
                if 'label_encoders' in cleaning_result:
                    # Convert LabelEncoders to string representations
                    cleaning_result['label_encoders'] = {
                        col: str(encoder) for col, encoder in cleaning_result['label_encoders'].items()
                    }
                
                # Run ML analysis
                ml_results = run_ml_analysis(cleaned_df)
                
                # Generate insights
                insights = generate_insights(cleaning_result, ml_results, cleaned_df)
                
                # Prepare final results
                analysis_results[analysis_id] = {
                    'data_cleaning': cleaning_result,
                    'ml_results': ml_results,
                    'data_summary': generate_data_summary(cleaned_df),
                    'insights': insights
                }
                
                # Update status
                analysis_status[file_id]['status'] = 'completed'
                analysis_status[file_id]['completion_time'] = datetime.now().isoformat()
                
                print(f"Analysis completed successfully for {analysis_id}")
                
            except Exception as e:
                analysis_status[file_id]['status'] = 'failed'
                analysis_status[file_id]['error'] = str(e)
                print(f"Analysis error: {traceback.format_exc()}")
        
        # Run analysis (in production, this would be a background task)
        run_analysis()
        
        return jsonify({
            "analysis_id": analysis_id,
            "message": "Analysis started successfully",
            "status": "analyzing"
        })
        
    except Exception as e:
        print(f"Analysis start error: {str(e)}")
        return jsonify({"error": f"Analysis failed to start: {str(e)}"}), 500

@app.route('/api/status/<file_id>', methods=['GET'])
def get_analysis_status(file_id):
    """Check analysis status"""
    if file_id not in analysis_status:
        return jsonify({"error": "File not found"}), 404
    
    status_info = analysis_status[file_id].copy()
    return jsonify({"status": status_info['status']})

@app.route('/api/results/<analysis_id>', methods=['GET'])
def get_analysis_results(analysis_id):
    """Get analysis results"""
    if analysis_id not in analysis_results:
        return jsonify({"error": "Analysis results not found"}), 404
    
    try:
        results = analysis_results[analysis_id]
        # Ensure all data is JSON serializable
        serializable_results = make_serializable(results)
        return jsonify(serializable_results)
    except Exception as e:
        print(f"Error serializing results: {str(e)}")
        return jsonify({"error": f"Failed to serialize results: {str(e)}"}), 500

def make_serializable(obj):
    """Recursively make object JSON serializable"""
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, dict):
        return {key: make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif hasattr(obj, '__dict__'):
        return str(obj)
    else:
        return str(obj)

def generate_data_summary(df):
    """Generate data summary for dashboard"""
    summary = {
        'columns': df.columns.tolist(),
        'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
        'descriptive_stats': {},
        'correlations': []
    }
    
    # Handle descriptive stats for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        try:
            desc_stats = df[numeric_cols].describe()
            summary['descriptive_stats'] = {
                col: {
                    'count': int(desc_stats[col]['count']),
                    'mean': float(desc_stats[col]['mean']),
                    'std': float(desc_stats[col]['std']),
                    'min': float(desc_stats[col]['min']),
                    '25%': float(desc_stats[col]['25%']),
                    '50%': float(desc_stats[col]['50%']),
                    '75%': float(desc_stats[col]['75%']),
                    'max': float(desc_stats[col]['max'])
                } for col in numeric_cols
            }
        except Exception as e:
            print(f"Error generating descriptive stats: {e}")
    
    # Handle correlations for numeric columns
    if len(numeric_cols) >= 2:
        try:
            corr_matrix = df[numeric_cols].corr().fillna(0)
            summary['correlations'] = corr_matrix.to_dict('records')
        except Exception as e:
            print(f"Error generating correlations: {e}")
    
    return summary

def generate_insights(cleaning_result, ml_results, df):
    """Generate insights based on analysis results"""
    insights = []
    
    # Data cleaning insights
    total_removed = (cleaning_result['original_rows'] - cleaning_result['cleaned_rows'])
    if total_removed > 0:
        removal_percentage = (total_removed / cleaning_result['original_rows']) * 100
        insights.append(f"Data cleaning removed {total_removed} rows ({removal_percentage:.1f}% of data) due to quality issues")
    else:
        insights.append("Excellent data quality - no rows removed during cleaning")
    
    if cleaning_result['missing_values'] > 0:
        insights.append(f"Found and handled {cleaning_result['missing_values']} missing values")
    
    if cleaning_result['duplicates_removed'] > 0:
        insights.append(f"Removed {cleaning_result['duplicates_removed']} duplicate rows")
    
    # ML insights
    if ml_results and '_summary' in ml_results:
        summary = ml_results['_summary']
        
        if summary.get('best_classification'):
            best_clf = summary['best_classification']
            insights.append(f"Best classification algorithm: {best_clf['algorithm']} with {best_clf['accuracy']*100:.1f}% accuracy")
        
        if summary.get('best_regression'):
            best_reg = summary['best_regression']
            insights.append(f"Best regression algorithm: {best_reg['algorithm']} with R² score of {best_reg['r2']:.3f}")
    
    # Data insights
    insights.append(f"Dataset contains {len(df.columns)} features and {len(df)} samples")
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        insights.append(f"Found {len(numeric_cols)} numerical features suitable for ML analysis")
    
    return insights

if __name__ == '__main__':
    print("Starting XLS Analyzer Backend...")
    print("Available endpoints:")
    print("  POST /api/upload - Upload Excel file")
    print("  POST /api/analyze - Start analysis")
    print("  GET /api/status/<file_id> - Check status")
    print("  GET /api/results/<analysis_id> - Get results")
    print("  GET /api/health - Health check")
    
    app.run(debug=True, host='0.0.0.0', port=5000)