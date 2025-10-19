import React from 'react';

// Define the interface directly here to avoid import issues
interface AnalysisResult {
  data_cleaning: {
    original_rows: number;
    cleaned_rows: number;
    missing_values: number;
    duplicates_removed: number;
    null_values: number;
  };
  ml_results: {
    [key: string]: {
      accuracy?: number;
      precision?: number;
      recall?: number;
      f1_score?: number;
      mse?: number;
      r2?: number;
      algorithm: string;
      type: 'classification' | 'regression' | 'clustering';
    };
  };
  data_summary: {
    columns: string[];
    data_types: { [key: string]: string };
    descriptive_stats: { [key: string]: any };
    correlations: { [key: string]: number }[];
  };
  insights: string[];
}

interface DashboardProps {
  data: AnalysisResult;
}

const Dashboard: React.FC<DashboardProps> = ({ data }) => {
  // Add safe access checks
  const dataCleaning = data?.data_cleaning || {
    original_rows: 0,
    cleaned_rows: 0,
    missing_values: 0,
    duplicates_removed: 0,
    null_values: 0
  };

  const mlResults = data?.ml_results || {};
  const insights = data?.insights || [];
  const dataSummary = data?.data_summary || {
    columns: [],
    data_types: {},
    descriptive_stats: {},
    correlations: []
  };

  return (
    <div className="dashboard">
      <h2>Analysis Dashboard</h2>
      
      <div className="dashboard-section">
        <h3>Data Cleaning Summary</h3>
        <div className="cleaning-stats">
          <div className="stat-card">
            <span className="stat-value">{dataCleaning.original_rows}</span>
            <span className="stat-label">Original Rows</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{dataCleaning.cleaned_rows}</span>
            <span className="stat-label">Cleaned Rows</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{dataCleaning.missing_values}</span>
            <span className="stat-label">Missing Values</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{dataCleaning.duplicates_removed}</span>
            <span className="stat-label">Duplicates Removed</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{dataCleaning.null_values}</span>
            <span className="stat-label">Null Values</span>
          </div>
        </div>
      </div>

      <div className="dashboard-section">
        <h3>Machine Learning Results</h3>
        <div className="ml-results">
          {Object.entries(mlResults).map(([algorithm, result]) => (
            <div key={algorithm} className="ml-card">
              <h4>{result.algorithm}</h4>
              <div className="ml-metrics">
                {result.accuracy !== undefined && (
                  <div className="metric">
                    <span>Accuracy:</span>
                    <span>{(result.accuracy * 100).toFixed(2)}%</span>
                  </div>
                )}
                {result.precision !== undefined && (
                  <div className="metric">
                    <span>Precision:</span>
                    <span>{(result.precision * 100).toFixed(2)}%</span>
                  </div>
                )}
                {result.recall !== undefined && (
                  <div className="metric">
                    <span>Recall:</span>
                    <span>{(result.recall * 100).toFixed(2)}%</span>
                  </div>
                )}
                {result.f1_score !== undefined && (
                  <div className="metric">
                    <span>F1-Score:</span>
                    <span>{(result.f1_score * 100).toFixed(2)}%</span>
                  </div>
                )}
                {result.mse !== undefined && (
                  <div className="metric">
                    <span>MSE:</span>
                    <span>{result.mse.toFixed(4)}</span>
                  </div>
                )}
                {result.r2 !== undefined && (
                  <div className="metric">
                    <span>R²:</span>
                    <span>{result.r2.toFixed(4)}</span>
                  </div>
                )}
              </div>
              <span className={`ml-type ${result.type}`}>{result.type}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="dashboard-section">
        <h3>Key Insights</h3>
        <div className="insights">
          {insights.map((insight, index) => (
            <div key={index} className="insight-card">
              <span className="insight-bullet">💡</span>
              <p>{insight}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="dashboard-section">
        <h3>Data Summary</h3>
        <div className="data-summary">
          <div className="summary-item">
            <strong>Columns:</strong> {dataSummary.columns.join(', ')}
          </div>
          <div className="summary-item">
            <strong>Data Types:</strong>
            <ul>
              {Object.entries(dataSummary.data_types).map(([col, type]) => (
                <li key={col}>{col}: {String(type)}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;