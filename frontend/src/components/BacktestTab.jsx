/**
 * Backtest Tab Component
 * 
 * Provides backtesting functionality including:
 * - Strategy configuration
 * - Historical data selection
 * - Backtest execution
 * - Results visualization
 * - Performance metrics analysis
 */

import React, { useState, useEffect, useCallback } from 'react';
import ResultsChart from './ResultsChart';
import { backendAPI } from '../api/backend';

const BacktestTab = ({ onRefresh, loading }) => {
  // State management
  const [backtestConfig, setBacktestConfig] = useState({
    startDate: '',
    endDate: '',
    initialCapital: 1000000,
    strategies: ['momentum', 'mean_reversion'],
    symbols: [], // Start empty - will be filled by autonomous selection
    useAutonomousSelection: true, // New setting
    maxSymbols: 15, // Limit for autonomous selection
    benchmarkSymbol: 'SPY'
  });
  const [backtestResults, setBacktestResults] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [autonomousSymbols, setAutonomousSymbols] = useState([]);

  /**
   * Load autonomous stock selection
   */
  const loadAutonomousSelection = useCallback(async () => {
    try {
      // In a real implementation, this would call the backend's autonomous selection
      // For now, simulate calling the market scanner
      const response = await backendAPI.getAutonomousSelection(backtestConfig.maxSymbols);
      setAutonomousSymbols(response.symbols || []);
      
      // Update config if using autonomous selection
      if (backtestConfig.useAutonomousSelection) {
        setBacktestConfig(prev => ({
          ...prev,
          symbols: response.symbols || []
        }));
      }
    } catch (error) {
      console.error('Error loading autonomous selection:', error);
      // Fallback to minimal set
      const fallback = ['AAPL', 'MSFT', 'GOOGL'];
      setAutonomousSymbols(fallback);
      if (backtestConfig.useAutonomousSelection) {
        setBacktestConfig(prev => ({
          ...prev,
          symbols: fallback
        }));
      }
    }
  }, [backtestConfig.maxSymbols, backtestConfig.useAutonomousSelection]);

  /**
   * Initialize component
   */
  useEffect(() => {
    loadAvailableStrategies();
    loadAutonomousSelection();
    setDefaultDates();
  }, [loadAutonomousSelection]);

  /**
   * Load available strategies from backend
   */
  const loadAvailableStrategies = async () => {
    try {
      const strategies = await backendAPI.getAvailableStrategies();
      setAvailableStrategies(strategies || []);
    } catch (error) {
      // // console.error('Failed to load strategies:', error);
    }
  };

  /**
   * Set default date range (last year)
   */
  const setDefaultDates = () => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(endDate.getFullYear() - 1);
    
    setBacktestConfig(prev => ({
      ...prev,
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0]
    }));
  };

  /**
   * Handle backtest configuration changes
   */
  const handleConfigChange = (field, value) => {
    setBacktestConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  /**
   * Run backtest
   */
  const runBacktest = async () => {
    try {
      setIsRunning(true);
      setProgress(0);
      setBacktestResults(null);

      // Start backtest
      const backtestJob = await backendAPI.startBacktest(backtestConfig);
      
      // Poll for progress updates
      const progressInterval = setInterval(async () => {
        try {
          const status = await backendAPI.getBacktestStatus(backtestJob.jobId);
          setProgress(status.progress || 0);
          
          if (status.completed) {
            clearInterval(progressInterval);
            setBacktestResults(status.results);
            setIsRunning(false);
            setProgress(100);
          }
        } catch (error) {
          // // console.error('Failed to get backtest status:', error);
          clearInterval(progressInterval);
          setIsRunning(false);
        }
      }, 2000);

    } catch (error) {
      // // console.error('Failed to run backtest:', error);
      setIsRunning(false);
      alert('Failed to run backtest: ' + error.message);
    }
  };

  /**
   * Download backtest report
   */
  const downloadReport = async () => {
    try {
      const reportData = await backendAPI.downloadBacktestReport(backtestResults.reportId);
      // Create download link
      const blob = new Blob([reportData], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `backtest_report_${new Date().toISOString().split('T')[0]}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      // // console.error('Failed to download report:', error);
      alert('Failed to download report: ' + error.message);
    }
  };

  return (
    <div className="backtest-tab">
      {/* Header */}
      <div className="row mb-4">
        <div className="col-12">
          <h4>
            <i className="fas fa-history me-2 text-primary"></i>
            Strategy Backtesting
          </h4>
          <p className="text-muted">
            Test trading strategies against historical data to evaluate performance and optimize parameters.
          </p>
        </div>
      </div>

      <div className="row">
        {/* Configuration Panel */}
        <div className="col-md-4">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">
                <i className="fas fa-cog me-2"></i>
                Backtest Configuration
              </h5>
            </div>
            <div className="card-body">
              {/* Date Range */}
              <div className="mb-3">
                <label className="form-label">Date Range</label>
                <div className="row">
                  <div className="col-6">
                    <input
                      type="date"
                      className="form-control"
                      value={backtestConfig.startDate}
                      onChange={(e) => handleConfigChange('startDate', e.target.value)}
                      disabled={isRunning}
                    />
                    <small className="text-muted">Start Date</small>
                  </div>
                  <div className="col-6">
                    <input
                      type="date"
                      className="form-control"
                      value={backtestConfig.endDate}
                      onChange={(e) => handleConfigChange('endDate', e.target.value)}
                      disabled={isRunning}
                    />
                    <small className="text-muted">End Date</small>
                  </div>
                </div>
              </div>

              {/* Initial Capital */}
              <div className="mb-3">
                <label className="form-label">Initial Capital</label>
                <div className="input-group">
                  <span className="input-group-text">$</span>
                  <input
                    type="number"
                    className="form-control"
                    value={backtestConfig.initialCapital}
                    onChange={(e) => handleConfigChange('initialCapital', parseInt(e.target.value))}
                    disabled={isRunning}
                  />
                </div>
              </div>

              {/* Trading Universe Selection */}
              <div className="mb-3">
                <label className="form-label">Trading Universe</label>
                
                {/* Autonomous Selection Toggle */}
                <div className="form-check mb-2">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    id="useAutonomousSelection"
                    checked={backtestConfig.useAutonomousSelection}
                    onChange={(e) => {
                      const useAutonomous = e.target.checked;
                      setBacktestConfig(prev => ({
                        ...prev,
                        useAutonomousSelection: useAutonomous,
                        symbols: useAutonomous ? autonomousSymbols : ['AAPL', 'MSFT', 'GOOGL']
                      }));
                    }}
                    disabled={isRunning}
                  />
                  <label className="form-check-label" htmlFor="useAutonomousSelection">
                    🤖 Use Autonomous Stock Selection
                  </label>
                </div>

                {backtestConfig.useAutonomousSelection ? (
                  <div>
                    <div className="input-group mb-2">
                      <span className="input-group-text">Max Stocks</span>
                      <input
                        type="number"
                        className="form-control"
                        value={backtestConfig.maxSymbols}
                        onChange={(e) => handleConfigChange('maxSymbols', parseInt(e.target.value))}
                        min="5"
                        max="50"
                        disabled={isRunning}
                      />
                      <button
                        type="button"
                        className="btn btn-outline-primary"
                        onClick={loadAutonomousSelection}
                        disabled={isRunning}
                      >
                        🔄 Refresh Selection
                      </button>
                    </div>
                    <div className="form-control" style={{ height: '80px', overflow: 'auto', backgroundColor: '#f8f9fa' }}>
                      <small className="text-muted">
                        {autonomousSymbols.length > 0 ? (
                          <>
                            <strong>Autonomously Selected ({autonomousSymbols.length}):</strong><br/>
                            {autonomousSymbols.join(', ')}
                          </>
                        ) : (
                          'Loading autonomous selection...'
                        )}
                      </small>
                    </div>
                  </div>
                ) : (
                  <textarea
                    className="form-control"
                    rows="3"
                    placeholder="Enter symbols separated by commas (e.g., AAPL, GOOGL, MSFT)"
                    value={backtestConfig.symbols.join(', ')}
                    onChange={(e) => handleConfigChange('symbols', e.target.value.split(',').map(s => s.trim()))}
                    disabled={isRunning}
                  />
                )}
              </div>

              {/* Benchmark */}
              <div className="mb-3">
                <label className="form-label">Benchmark Symbol</label>
                <input
                  type="text"
                  className="form-control"
                  value={backtestConfig.benchmarkSymbol}
                  onChange={(e) => handleConfigChange('benchmarkSymbol', e.target.value)}
                  disabled={isRunning}
                />
              </div>

              {/* Strategies */}
              <div className="mb-4">
                <label className="form-label">Strategies</label>
                {availableStrategies.map(strategy => (
                  <div key={strategy.name} className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id={strategy.name}
                      checked={backtestConfig.strategies.includes(strategy.name)}
                      onChange={(e) => {
                        const strategies = e.target.checked
                          ? [...backtestConfig.strategies, strategy.name]
                          : backtestConfig.strategies.filter(s => s !== strategy.name);
                        handleConfigChange('strategies', strategies);
                      }}
                      disabled={isRunning}
                    />
                    <label className="form-check-label" htmlFor={strategy.name}>
                      {strategy.displayName}
                    </label>
                  </div>
                ))}
              </div>

              {/* Run Button */}
              <button
                className="btn btn-primary w-100"
                onClick={runBacktest}
                disabled={isRunning || backtestConfig.strategies.length === 0}
              >
                {isRunning ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                    Running Backtest...
                  </>
                ) : (
                  <>
                    <i className="fas fa-play me-2"></i>
                    Run Backtest
                  </>
                )}
              </button>

              {/* Progress Bar */}
              {isRunning && (
                <div className="mt-3">
                  <div className="progress">
                    <div
                      className="progress-bar progress-bar-striped progress-bar-animated"
                      role="progressbar"
                      style={{ width: `${progress}%` }}
                    >
                      {progress.toFixed(0)}%
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Results Panel */}
        <div className="col-md-8">
          {!backtestResults ? (
            <div className="card">
              <div className="card-body text-center py-5">
                <i className="fas fa-chart-bar fa-4x text-muted mb-3"></i>
                <h5 className="text-muted">No Backtest Results</h5>
                <p className="text-muted">
                  Configure your backtest parameters and click "Run Backtest" to see results.
                </p>
              </div>
            </div>
          ) : (
            <>
              {/* Performance Metrics */}
              <div className="row mb-4">
                <div className="col-md-3">
                  <div className="metric-card">
                    <div className="metric-label">Total Return</div>
                    <div className={`metric-value ${backtestResults.totalReturn >= 0 ? 'text-success' : 'text-danger'}`}>
                      {backtestResults.totalReturn >= 0 ? '+' : ''}{backtestResults.totalReturn?.toFixed(2)}%
                    </div>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="metric-card">
                    <div className="metric-label">Sharpe Ratio</div>
                    <div className="metric-value text-info">
                      {backtestResults.sharpeRatio?.toFixed(2)}
                    </div>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="metric-card">
                    <div className="metric-label">Max Drawdown</div>
                    <div className="metric-value text-warning">
                      {backtestResults.maxDrawdown?.toFixed(2)}%
                    </div>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="metric-card">
                    <div className="metric-label">Win Rate</div>
                    <div className="metric-value text-success">
                      {backtestResults.winRate?.toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Performance Chart */}
              <div className="card mb-4">
                <div className="card-header d-flex justify-content-between align-items-center">
                  <h5 className="card-title mb-0">
                    <i className="fas fa-chart-line me-2"></i>
                    Cumulative Returns
                  </h5>
                  <button
                    className="btn btn-outline-secondary btn-sm"
                    onClick={downloadReport}
                  >
                    <i className="fas fa-download me-1"></i>
                    Download Report
                  </button>
                </div>
                <div className="card-body">
                  <ResultsChart
                    data={backtestResults.performanceChart}
                    type="line"
                    title="Portfolio vs Benchmark"
                    height={300}
                  />
                </div>
              </div>

              {/* Detailed Metrics */}
              <div className="card">
                <div className="card-header">
                  <h5 className="card-title mb-0">
                    <i className="fas fa-table me-2"></i>
                    Detailed Metrics
                  </h5>
                </div>
                <div className="card-body">
                  <div className="row">
                    <div className="col-md-6">
                      <table className="table table-sm">
                        <tbody>
                          <tr>
                            <td>Annual Return</td>
                            <td className="text-end">{backtestResults.annualReturn?.toFixed(2)}%</td>
                          </tr>
                          <tr>
                            <td>Annual Volatility</td>
                            <td className="text-end">{backtestResults.annualVolatility?.toFixed(2)}%</td>
                          </tr>
                          <tr>
                            <td>Information Ratio</td>
                            <td className="text-end">{backtestResults.informationRatio?.toFixed(2)}</td>
                          </tr>
                          <tr>
                            <td>Sortino Ratio</td>
                            <td className="text-end">{backtestResults.sortinoRatio?.toFixed(2)}</td>
                          </tr>
                          <tr>
                            <td>Calmar Ratio</td>
                            <td className="text-end">{backtestResults.calmarRatio?.toFixed(2)}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div className="col-md-6">
                      <table className="table table-sm">
                        <tbody>
                          <tr>
                            <td>Total Trades</td>
                            <td className="text-end">{backtestResults.totalTrades}</td>
                          </tr>
                          <tr>
                            <td>Winning Trades</td>
                            <td className="text-end">{backtestResults.winningTrades}</td>
                          </tr>
                          <tr>
                            <td>Average Trade</td>
                            <td className="text-end">{backtestResults.averageTrade?.toFixed(2)}%</td>
                          </tr>
                          <tr>
                            <td>Largest Win</td>
                            <td className="text-end text-success">{backtestResults.largestWin?.toFixed(2)}%</td>
                          </tr>
                          <tr>
                            <td>Largest Loss</td>
                            <td className="text-end text-danger">{backtestResults.largestLoss?.toFixed(2)}%</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default BacktestTab;