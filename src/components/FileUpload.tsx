import React, { useState, useRef } from 'react';

interface FileUploadProps {
  setAnalysisResult: (result: any) => void;
  setIsAnalyzing: (analyzing: boolean) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ setAnalysisResult, setIsAnalyzing }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    setError('');

    if (!file) return;

    if (!file.name.match(/\.(xls|xlsx)$/i)) {
      setError('Please select a valid Excel file (.xls or .xlsx)');
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError('File size must be less than 100MB');
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setError('');

    try {
      // Step 1: Upload file to backend
      const formData = new FormData();
      formData.append('file', selectedFile);

      const uploadResponse = await fetch('http://localhost:5000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error(`Upload failed: ${uploadResponse.statusText}`);
      }

      const uploadResult = await uploadResponse.json();
      console.log('Upload result:', uploadResult);

      // Step 2: Start analysis
      const analyzeResponse = await fetch('http://localhost:5000/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_id: uploadResult.file_id
        }),
      });

      if (!analyzeResponse.ok) {
        throw new Error(`Analysis failed to start: ${analyzeResponse.statusText}`);
      }

      const analyzeResult = await analyzeResponse.json();
      console.log('Analysis started:', analyzeResult);

      // Step 3: Poll for results
      await pollForResults(uploadResult.file_id, analyzeResult.analysis_id);

    } catch (err: any) {
      setError(err.message || 'Upload failed. Please try again.');
      setIsAnalyzing(false);
    }
  };

  const pollForResults = async (fileId: string, analysisId: string) => {
    let attempts = 0;
    const maxAttempts = 120; // 10 minutes max (5 seconds * 120)

    const poll = async () => {
      try {
        // Check status
        const statusResponse = await fetch(`http://localhost:5000/api/status/${fileId}`);
        if (!statusResponse.ok) {
          throw new Error('Failed to check status');
        }

        const status = await statusResponse.json();
        console.log('Current status:', status);

        if (status.status === 'completed') {
          // Get final results
          const resultsResponse = await fetch(`http://localhost:5000/api/results/${analysisId}`);
          if (!resultsResponse.ok) {
            throw new Error('Failed to get results');
          }

          const results = await resultsResponse.json();
          console.log('Final results:', results);
          setAnalysisResult(results);
          setIsAnalyzing(false);
          return;

        } else if (status.status === 'failed') {
          setError('Analysis failed. Please try again.');
          setIsAnalyzing(false);
          return;
        }

        // Continue polling if still analyzing
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000); // Poll every 5 seconds
        } else {
          setError('Analysis timeout. Please try again.');
          setIsAnalyzing(false);
        }
      } catch (err: any) {
        setError('Error checking analysis status: ' + err.message);
        setIsAnalyzing(false);
      }
    };

    await poll();
  };

  return (
    <div className="file-upload-container">
      <div
        className={`drop-zone ${selectedFile ? 'has-file' : ''}`}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xls,.xlsx"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        
        {!selectedFile ? (
          <div className="drop-zone-content">
            <div className="upload-icon">📊</div>
            <p>Drag & drop your Excel file here</p>
            <p className="file-types">Supports .xls, .xlsx (Max 100MB)</p>
            <button type="button" className="browse-btn">
              Browse Files
            </button>
          </div>
        ) : (
          <div className="file-selected">
            <div className="file-icon">📄</div>
            <div className="file-info">
              <p className="file-name">{selectedFile.name}</p>
              <p className="file-size">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
          </div>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      {selectedFile && (
        <button 
          className="analyze-btn"
          onClick={handleUpload}
        >
          Start Analyze
        </button>
      )}
    </div>
  );
};

export default FileUpload;