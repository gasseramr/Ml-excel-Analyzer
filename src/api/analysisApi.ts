import axios from 'axios';
import { AnalysisResult, UploadResponse } from '../types';

const API_BASE_URL = '/api';

export const analysisApi = {
  // Upload XLS file (100MB max)
  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 300000, // 5 minutes for large files
      onUploadProgress: (progressEvent) => {
        const progress = (progressEvent.loaded / (progressEvent.total || 1)) * 100;
        console.log(`Upload Progress: ${progress.toFixed(2)}%`);
      },
    });
    
    return response.data;
  },

  // Start analysis
  async startAnalysis(fileId: string): Promise<{ analysis_id: string }> {
    const response = await axios.post(`${API_BASE_URL}/analyze`, {
      file_id: fileId
    });
    return response.data;
  },

  // Get analysis results
  async getAnalysisResults(analysisId: string): Promise<AnalysisResult> {
    const response = await axios.get(`${API_BASE_URL}/results/${analysisId}`);
    return response.data;
  },

  // Check analysis status
  async checkAnalysisStatus(analysisId: string): Promise<{ status: string }> {
    const response = await axios.get(`${API_BASE_URL}/status/${analysisId}`);
    return response.data;
  }
};