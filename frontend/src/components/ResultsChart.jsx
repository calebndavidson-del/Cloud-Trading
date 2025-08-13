/**
 * Results Chart Component
 * 
 * Reusable chart component for displaying various types of data visualizations.
 * Supports line charts, bar charts, and area charts using Chart.js.
 * 
 * Features:
 * - Multiple chart types
 * - Responsive design
 * - Customizable colors and styling
 * - Real-time data updates
 * - Export functionality
 */

import React, { useRef, useEffect, useCallback } from 'react';

const ResultsChart = ({ 
  data, 
  type = 'line', 
  title = '', 
  height = 400, 
  options = {},
  colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
}) => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  /**
   * Prepare chart data based on input format
   */
  const prepareChartData = useCallback((inputData) => {
    if (!inputData || inputData.length === 0) {
      return {
        labels: [],
        datasets: []
      };
    }

    // Handle different data formats
    if (Array.isArray(inputData)) {
      // Time series data
      if (inputData[0] && typeof inputData[0] === 'object' && inputData[0].timestamp) {
        return {
          labels: inputData.map(item => 
            new Date(item.timestamp).toLocaleDateString()
          ),
          datasets: [{
            label: 'Portfolio Value',
            data: inputData.map(item => item.value),
            borderColor: colors[0],
            backgroundColor: type === 'area' ? 
              `${colors[0]}20` : colors[0],
            fill: type === 'area',
            tension: 0.1
          }]
        };
      }

      // Simple array of values
      if (typeof inputData[0] === 'number') {
        return {
          labels: inputData.map((_, index) => index + 1),
          datasets: [{
            label: 'Values',
            data: inputData,
            borderColor: colors[0],
            backgroundColor: colors[0],
            fill: false
          }]
        };
      }
    }

    // Object with multiple series
    if (typeof inputData === 'object' && !Array.isArray(inputData)) {
      const labels = inputData.labels || [];
      const datasets = [];

      if (inputData.datasets) {
        inputData.datasets.forEach((dataset, index) => {
          datasets.push({
            ...dataset,
            borderColor: dataset.borderColor || colors[index % colors.length],
            backgroundColor: dataset.backgroundColor || 
              (type === 'bar' ? colors[index % colors.length] : `${colors[index % colors.length]}20`),
            fill: type === 'area'
          });
        });
      } else {
        // Single dataset from object values
        const values = Object.values(inputData);
        if (values.every(v => typeof v === 'number')) {
          datasets.push({
            label: 'Data',
            data: values,
            borderColor: colors[0],
            backgroundColor: type === 'bar' ? colors[0] : `${colors[0]}20`,
            fill: type === 'area'
          });
        }
      }

      return { labels, datasets };
    }

    // Fallback empty data
    return {
      labels: [],
      datasets: []
    };
  }, [colors, type]);

  /**
   * Initialize or update chart
   */
  useEffect(() => {
    if (chartRef.current && window.Chart) {
      // Destroy existing chart
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      // Create new chart
      const ctx = chartRef.current.getContext('2d');
      chartInstance.current = new window.Chart(ctx, {
        type: type,
        data: prepareChartData(data),
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: !!title,
              text: title,
              font: {
                size: 16,
                weight: 'bold'
              }
            },
            legend: {
              display: true,
              position: 'top'
            },
            tooltip: {
              mode: 'index',
              intersect: false,
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleColor: 'white',
              bodyColor: 'white',
              borderColor: '#3498db',
              borderWidth: 1
            }
          },
          scales: {
            x: {
              display: true,
              grid: {
                display: false
              }
            },
            y: {
              display: true,
              grid: {
                color: 'rgba(0, 0, 0, 0.1)'
              }
            }
          },
          interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
          },
          ...options
        }
      });
    }

    // Cleanup on unmount
    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [data, type, title, options, prepareChartData]);

  /**
   * Export chart as image
   */
  const exportChart = () => {
    if (chartInstance.current) {
      const canvas = chartInstance.current.canvas;
      const url = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.download = `chart_${Date.now()}.png`;
      link.href = url;
      link.click();
    }
  };

  return (
    <div className="chart-container" style={{ position: 'relative', height: `${height}px` }}>
      {/* Chart Canvas */}
      <canvas
        ref={chartRef}
        style={{ width: '100%', height: '100%' }}
      />

      {/* Loading Overlay */}
      {(!data || data.length === 0) && (
        <div 
          className="d-flex justify-content-center align-items-center position-absolute top-0 start-0 w-100 h-100"
          style={{ backgroundColor: 'rgba(255, 255, 255, 0.8)' }}
        >
          <div className="text-center">
            <div className="loading-spinner mx-auto mb-2"></div>
            <small className="text-muted">Loading chart data...</small>
          </div>
        </div>
      )}

      {/* Export Button */}
      <button
        className="btn btn-outline-secondary btn-sm position-absolute"
        style={{ top: '10px', right: '10px' }}
        onClick={exportChart}
        title="Export Chart"
      >
        <i className="fas fa-download"></i>
      </button>

      {/* Chart Controls */}
      <div className="chart-controls position-absolute bottom-0 start-0 p-2">
        <div className="btn-group btn-group-sm" role="group">
          <button
            className="btn btn-outline-secondary"
            onClick={() => chartInstance.current?.resetZoom()}
            title="Reset Zoom"
          >
            <i className="fas fa-search-minus"></i>
          </button>
          <button
            className="btn btn-outline-secondary"
            onClick={() => window.print()}
            title="Print Chart"
          >
            <i className="fas fa-print"></i>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ResultsChart;