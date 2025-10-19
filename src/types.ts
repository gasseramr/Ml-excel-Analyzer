export interface AnalysisResult {
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

export interface UploadResponse {
  file_id: string;
  message: string;
  status: string;
}