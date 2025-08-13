/**
 * Optimization Tab Component
 * 
 * Provides strategy optimization functionality including:
 * - Parameter optimization
 * - Multi-objective optimization
 * - Genetic algorithm optimization
 * - Results visualization
 * - Best parameter discovery
 */

import React, { useState, useEffect, useCallback } from 'react';
import ResultsChart from './ResultsChart';
import { backendAPI } from '../api/backend';

const OptimizationTab = ({ onRefresh, loading }) => {
  // State management
  const [optimizationConfig, setOptimizationConfig] = useState({
    strategy: '',
    objective: 'sharpe_ratio',
    optimizationMethod: 'genetic_algorithm',
    generations: 50,
    populationSize: 100,
    parameterRanges: {}
  });
  const [optimizationResults, setOptimizationResults] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [parameterSpace, setParameterSpace] = useState({});

  /**
   * Load parameter space for selected strategy
   */
  const loadParameterSpace = useCallback(async (strategyName) => {
    try {
      const space = await backendAPI.getStrategyParameterSpace(strategyName);
      setParameterSpace(space || {});
      
      // Initialize parameter ranges with defaults
      const defaultRanges = {};
      Object.keys(space).forEach(param => {
        defaultRanges[param] = {
          min: space[param].min,
          max: space[param].max,
          step: space[param].step || 1
        };
      });
      setOptimizationConfig(prev => ({
        ...prev,
        parameterRanges: defaultRanges
      }));
    } catch (error) {
      // console.error('Failed to load parameter space:', error);
    }
  }, []);

  /**
   * Load available strategies from backend
   */
  const loadAvailableStrategies = useCallback(async () => {
    try {
      const strategies = await backendAPI.getAvailableStrategies();
      setAvailableStrategies(strategies || []);
      
      if (strategies && strategies.length > 0) {
        setOptimizationConfig(prev => ({
          ...prev,
          strategy: strategies[0].name
        }));
        loadParameterSpace(strategies[0].name);
      }
    } catch (error) {
      // console.error('Failed to load strategies:', error);
    }
  }, [loadParameterSpace]);

  /**
   * Initialize component
   */
  useEffect(() => {
    loadAvailableStrategies();
  }, [loadAvailableStrategies]);

  /**
   * Handle configuration changes
   */
  const handleConfigChange = (field, value) => {
    setOptimizationConfig(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Load parameter space when strategy changes
    if (field === 'strategy') {
      loadParameterSpace(value);
    }
  };

  /**
   * Handle parameter range changes
   */
  const handleParameterRangeChange = (parameter, field, value) => {
    setOptimizationConfig(prev => ({
      ...prev,
      parameterRanges: {
        ...prev.parameterRanges,
        [parameter]: {
          ...prev.parameterRanges[parameter],
          [field]: value
        }
      }
    }));
  };

  /**
   * Run optimization
   */
  const runOptimization = async () => {
    try {
      setIsRunning(true);
      setProgress(0);
      setOptimizationResults(null);

      // Start optimization
      const optimizationJob = await backendAPI.startOptimization(optimizationConfig);
      
      // Poll for progress updates
      const progressInterval = setInterval(async () => {
        try {
          const status = await backendAPI.getOptimizationStatus(optimizationJob.jobId);
          setProgress(status.progress || 0);
          
          if (status.completed) {
            clearInterval(progressInterval);
            setOptimizationResults(status.results);
            setIsRunning(false);
            setProgress(100);
          }
        } catch (error) {
          // console.error('Failed to get optimization status:', error);
          clearInterval(progressInterval);
          setIsRunning(false);
        }
      }, 3000);

    } catch (error) {
      // console.error('Failed to run optimization:', error);
      setIsRunning(false);
      alert('Failed to run optimization: ' + error.message);
    }
  };

  /**
   * Apply optimized parameters to live trading
   */
  const applyOptimizedParameters = async (parameters) => {
    try {
      await backendAPI.updateStrategyParameters(optimizationConfig.strategy, parameters);
      alert('Parameters applied successfully!');
      onRefresh();
    } catch (error) {
      // console.error('Failed to apply parameters:', error);
      alert('Failed to apply parameters: ' + error.message);
    }
  };

  return (
    <div className="optimization-tab">
      {/* Header */}
      <div className="row mb-4">
        <div className="col-12">
          <h4>
            <i className="fas fa-sliders-h me-2 text-primary"></i>
            Strategy Optimization
          </h4>
          <p className="text-muted">
            Optimize trading strategy parameters using advanced algorithms to maximize performance metrics.
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
                Optimization Settings
              </h5>
            </div>
            <div className="card-body">
              {/* Strategy Selection */}
              <div className="mb-3">
                <label className="form-label">Strategy</label>
                <select
                  className="form-select"
                  value={optimizationConfig.strategy}
                  onChange={(e) => handleConfigChange('strategy', e.target.value)}
                  disabled={isRunning}
                >
                  {availableStrategies.map(strategy => (
                    <option key={strategy.name} value={strategy.name}>
                      {strategy.displayName}
                    </option>
                  ))}
                </select>
              </div>

              {/* Optimization Objective */}
              <div className="mb-3">
                <label className="form-label">Optimization Objective</label>
                <select
                  className="form-select"
                  value={optimizationConfig.objective}
                  onChange={(e) => handleConfigChange('objective', e.target.value)}
                  disabled={isRunning}
                >
                  <option value="sharpe_ratio">Sharpe Ratio</option>
                  <option value="total_return">Total Return</option>
                  <option value="calmar_ratio">Calmar Ratio</option>
                  <option value="sortino_ratio">Sortino Ratio</option>
                  <option value="information_ratio">Information Ratio</option>
                  <option value="multi_objective">Multi-Objective</option>
                </select>
              </div>

              {/* Optimization Method */}
              <div className="mb-3">
                <label className="form-label">Optimization Method</label>
                <select
                  className="form-select"
                  value={optimizationConfig.optimizationMethod}
                  onChange={(e) => handleConfigChange('optimizationMethod', e.target.value)}
                  disabled={isRunning}
                >
                  <option value="genetic_algorithm">Genetic Algorithm</option>
                  <option value="particle_swarm">Particle Swarm</option>
                  <option value="bayesian_optimization">Bayesian Optimization</option>
                  <option value="grid_search">Grid Search</option>
                  <option value="random_search">Random Search</option>
                </select>
              </div>

              {/* Algorithm Parameters */}
              <div className="row mb-3">
                <div className="col-6">
                  <label className="form-label">Generations</label>
                  <input
                    type="number"
                    className="form-control"
                    value={optimizationConfig.generations}
                    onChange={(e) => handleConfigChange('generations', parseInt(e.target.value))}
                    disabled={isRunning}
                  />
                </div>
                <div className="col-6">
                  <label className="form-label">Population Size</label>
                  <input
                    type="number"
                    className="form-control"
                    value={optimizationConfig.populationSize}
                    onChange={(e) => handleConfigChange('populationSize', parseInt(e.target.value))}
                    disabled={isRunning}
                  />
                </div>
              </div>

              {/* Run Button */}
              <button
                className="btn btn-primary w-100"
                onClick={runOptimization}
                disabled={isRunning || !optimizationConfig.strategy}
              >
                {isRunning ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                    Optimizing...
                  </>
                ) : (
                  <>
                    <i className="fas fa-play me-2"></i>
                    Start Optimization
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
                  <small className="text-muted">
                    Generation {Math.floor(progress * optimizationConfig.generations / 100)} 
                    of {optimizationConfig.generations}
                  </small>
                </div>
              )}
            </div>
          </div>

          {/* Parameter Ranges */}
          <div className="card mt-3">
            <div className="card-header">
              <h6 className="card-title mb-0">
                <i className="fas fa-adjust me-2"></i>
                Parameter Ranges
              </h6>
            </div>
            <div className="card-body">
              {Object.keys(parameterSpace).map(param => (
                <div key={param} className="mb-3">
                  <label className="form-label text-capitalize">
                    {param.replace(/_/g, ' ')}
                  </label>
                  <div className="row">
                    <div className="col-4">
                      <input
                        type="number"
                        className="form-control form-control-sm"
                        placeholder="Min"
                        value={optimizationConfig.parameterRanges[param]?.min || ''}
                        onChange={(e) => handleParameterRangeChange(param, 'min', parseFloat(e.target.value))}
                        disabled={isRunning}
                      />
                    </div>
                    <div className="col-4">
                      <input
                        type="number"
                        className="form-control form-control-sm"
                        placeholder="Max"
                        value={optimizationConfig.parameterRanges[param]?.max || ''}
                        onChange={(e) => handleParameterRangeChange(param, 'max', parseFloat(e.target.value))}
                        disabled={isRunning}
                      />
                    </div>
                    <div className="col-4">
                      <input
                        type="number"
                        className="form-control form-control-sm"
                        placeholder="Step"
                        value={optimizationConfig.parameterRanges[param]?.step || ''}
                        onChange={(e) => handleParameterRangeChange(param, 'step', parseFloat(e.target.value))}
                        disabled={isRunning}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Results Panel */}
        <div className="col-md-8">
          {!optimizationResults ? (
            <div className="card">
              <div className="card-body text-center py-5">
                <i className="fas fa-search fa-4x text-muted mb-3"></i>
                <h5 className="text-muted">No Optimization Results</h5>
                <p className="text-muted">
                  Configure your optimization settings and click "Start Optimization" to find the best parameters.
                </p>
              </div>
            </div>
          ) : (
            <>
              {/* Best Results */}
              <div className="card mb-4">
                <div className="card-header">
                  <h5 className="card-title mb-0">
                    <i className="fas fa-trophy me-2"></i>
                    Best Parameters Found
                  </h5>
                </div>
                <div className="card-body">
                  <div className="row">
                    <div className="col-md-8">
                      <div className="table-responsive">
                        <table className="table table-sm">
                          <thead>
                            <tr>
                              <th>Parameter</th>
                              <th>Optimized Value</th>
                              <th>Original Value</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(optimizationResults.bestParameters).map(([param, value]) => (
                              <tr key={param}>
                                <td className="text-capitalize">{param.replace(/_/g, ' ')}</td>
                                <td><strong>{value}</strong></td>
                                <td className="text-muted">{parameterSpace[param]?.default || 'N/A'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="metric-card">
                        <div className="metric-label">Best {optimizationConfig.objective.replace('_', ' ')}</div>
                        <div className="metric-value text-success">
                          {optimizationResults.bestScore?.toFixed(4)}
                        </div>
                      </div>
                      <button
                        className="btn btn-success w-100 mt-2"
                        onClick={() => applyOptimizedParameters(optimizationResults.bestParameters)}
                      >
                        <i className="fas fa-check me-2"></i>
                        Apply Parameters
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Optimization Progress Chart */}
              <div className="card mb-4">
                <div className="card-header">
                  <h5 className="card-title mb-0">
                    <i className="fas fa-chart-line me-2"></i>
                    Optimization Progress
                  </h5>
                </div>
                <div className="card-body">
                  <ResultsChart
                    data={optimizationResults.progressChart}
                    type="line"
                    title="Best Score by Generation"
                    height={250}
                  />
                </div>
              </div>

              {/* Parameter Sensitivity Analysis */}
              <div className="card mb-4">
                <div className="card-header">
                  <h5 className="card-title mb-0">
                    <i className="fas fa-chart-bar me-2"></i>
                    Parameter Sensitivity
                  </h5>
                </div>
                <div className="card-body">
                  <ResultsChart
                    data={optimizationResults.sensitivityChart}
                    type="bar"
                    title="Parameter Importance"
                    height={200}
                  />
                </div>
              </div>

              {/* Top Results Table */}
              <div className="card">
                <div className="card-header">
                  <h5 className="card-title mb-0">
                    <i className="fas fa-list me-2"></i>
                    Top Results ({optimizationResults.topResults?.length || 0})
                  </h5>
                </div>
                <div className="card-body">
                  <div className="table-responsive">
                    <table className="table table-hover">
                      <thead>
                        <tr>
                          <th>Rank</th>
                          <th>Score</th>
                          {Object.keys(optimizationResults.bestParameters).map(param => (
                            <th key={param} className="text-capitalize">
                              {param.replace(/_/g, ' ')}
                            </th>
                          ))}
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {optimizationResults.topResults?.map((result, index) => (
                          <tr key={index}>
                            <td>
                              <span className={`badge ${index < 3 ? 'bg-warning' : 'bg-secondary'}`}>
                                #{index + 1}
                              </span>
                            </td>
                            <td>{result.score?.toFixed(4)}</td>
                            {Object.keys(optimizationResults.bestParameters).map(param => (
                              <td key={param}>{result.parameters[param]}</td>
                            ))}
                            <td>
                              <button
                                className="btn btn-outline-primary btn-sm"
                                onClick={() => applyOptimizedParameters(result.parameters)}
                              >
                                Apply
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
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

export default OptimizationTab;