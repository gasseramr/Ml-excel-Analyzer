import React, { useState } from "react";
import FileUpload from "./components/FileUpload";
import Dashboard from "./components/Dashboard";
import type { AnalysisResult } from "./types";
import "./App.css";

function App() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(
    null
  );
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);

  return (
    <div className="App">
      <header className="app-header">
        <h1>Welcome to XLS File Analyzer</h1>
        <p>If you see this, your React app is working!</p>
      </header>

      <main className="app-main">
        {!analysisResult && (
          <div className="upload-section">
            <FileUpload
              setAnalysisResult={setAnalysisResult}
              setIsAnalyzing={setIsAnalyzing}
            />
          </div>
        )}

        {isAnalyzing && (
          <div className="analyzing-overlay">
            <div className="analyzing-spinner"></div>
            <h3>Analyzing Your Data...</h3>
            <p>
              This may take a few minutes. We're running 15 ML algorithms on
              your data.
            </p>
            <div className="analyzing-steps">
              <div className="step">✅ Data Cleaning</div>
              <div className="step">🔄 Running ML Algorithms</div>
              <div className="step">⏳ Generating Insights</div>
            </div>
          </div>
        )}

        {analysisResult && (
          <div className="results-section">
            <Dashboard data={analysisResult} />
            <button
              className="new-analysis-btn"
              onClick={() => {
                setAnalysisResult(null);
                setIsAnalyzing(false);
              }}
            >
              Start New Analysis
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
