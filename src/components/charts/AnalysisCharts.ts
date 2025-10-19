import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import { AnalysisResult } from '../../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface AnalysisChartsProps {
  data: AnalysisResult;
}

const AnalysisCharts: React.FC<AnalysisChartsProps> = ({ data }) => {
  // ML Performance Comparison Chart
  const mlPerformanceData = {
    labels: Object.keys(data.ml_results),
    datasets: [
      {
        label: 'Accuracy',
        data: Object.values(data.ml_results).map(result => 
          (result.accuracy || 0) * 100
        ),
        backgroundColor: 'rgba(54, 162, 235, 0.8)',
      },
      {
        label: 'F1-Score',
        data: Object.values(data.ml_results).map(result => 
          (result.f1_score || 0) * 100
        ),
        backgroundColor: 'rgba(255, 99, 132, 0.8)',
      }
    ],
  };

  // Data Cleaning Chart
  const cleaningData = {
    labels: ['Original', 'After Cleaning'],
    datasets: [
      {
        label: 'Number of Rows',
        data: [data.data_cleaning.original_rows, data.data_cleaning.cleaned_rows],
        backgroundColor: ['rgba(255, 99, 132, 0.8)', 'rgba(75, 192, 192, 0.8)'],
      },
    ],
  };

  // Data Issues Chart
  const issuesData = {
    labels: ['Missing Values', 'Duplicates', 'Null Values'],
    datasets: [
      {
        label: 'Data Issues Found',
        data: [
          data.data_cleaning.missing_values,
          data.data_cleaning.duplicates_removed,
          data.data_cleaning.null_values
        ],
        backgroundColor: [
          'rgba(255, 99, 132, 0.8)',
          'rgba(255, 205, 86, 0.8)',
          'rgba(54, 162, 235, 0.8)'
        ],
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
  };

  return (
    <div className="charts-container">
      <div className="chart-row">
        <div className="chart-card">
          <h4>ML Algorithm Performance</h4>
          <Bar data={mlPerformanceData} options={chartOptions} />
        </div>
        <div className="chart-card">
          <h4>Data Cleaning Impact</h4>
          <Bar data={cleaningData} options={chartOptions} />
        </div>
      </div>
      <div className="chart-row">
        <div className="chart-card">
          <h4>Data Issues Distribution</h4>
          <Doughnut data={issuesData} options={chartOptions} />
        </div>
      </div>
    </div>
  );
};

export default AnalysisCharts;