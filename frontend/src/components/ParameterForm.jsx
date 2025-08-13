/**
 * Parameter Form Component
 * 
 * Dynamic form component for configuring strategy parameters.
 * Supports different input types and validation.
 * 
 * Features:
 * - Dynamic parameter fields
 * - Input validation
 * - Parameter descriptions
 * - Default value handling
 * - Real-time parameter updates
 */

import React, { useState, useEffect, useCallback } from 'react';

const ParameterForm = ({ 
  strategy, 
  parameters = {}, 
  onParameterChange,
  readonly = false
}) => {
  const [parameterValues, setParameterValues] = useState({});
  const [validationErrors, setValidationErrors] = useState({});
  const [parameterDefinitions, setParameterDefinitions] = useState({});

  /**
   * Get parameter definitions based on strategy type
   */
  const getParameterDefinitions = (strategyType) => {
    const definitions = {
      momentum: {
        lookback_period: {
          type: 'number',
          label: 'Lookback Period',
          description: 'Number of periods to calculate momentum',
          default: 20,
          min: 5,
          max: 100,
          step: 1
        },
        momentum_threshold: {
          type: 'number',
          label: 'Momentum Threshold',
          description: 'Minimum momentum required for signal',
          default: 0.02,
          min: 0.001,
          max: 0.1,
          step: 0.001
        },
        position_size: {
          type: 'number',
          label: 'Position Size',
          description: 'Position size as fraction of portfolio',
          default: 0.1,
          min: 0.01,
          max: 0.5,
          step: 0.01
        },
        enable_stop_loss: {
          type: 'boolean',
          label: 'Enable Stop Loss',
          description: 'Use stop loss orders',
          default: true
        }
      },
      mean_reversion: {
        lookback_window: {
          type: 'number',
          label: 'Lookback Window',
          description: 'Statistical window for mean calculation',
          default: 50,
          min: 10,
          max: 200,
          step: 1
        },
        z_threshold: {
          type: 'number',
          label: 'Z-Score Threshold',
          description: 'Z-score threshold for entry signals',
          default: 2.0,
          min: 1.0,
          max: 4.0,
          step: 0.1
        },
        exit_threshold: {
          type: 'number',
          label: 'Exit Threshold',
          description: 'Z-score threshold for exit signals',
          default: 0.5,
          min: 0.1,
          max: 2.0,
          step: 0.1
        },
        max_holding_period: {
          type: 'number',
          label: 'Max Holding Period',
          description: 'Maximum days to hold position',
          default: 30,
          min: 1,
          max: 100,
          step: 1
        }
      },
      ml_prediction: {
        prediction_horizon: {
          type: 'number',
          label: 'Prediction Horizon',
          description: 'Number of periods to predict ahead',
          default: 1,
          min: 1,
          max: 10,
          step: 1
        },
        confidence_threshold: {
          type: 'number',
          label: 'Confidence Threshold',
          description: 'Minimum prediction confidence',
          default: 0.6,
          min: 0.5,
          max: 0.95,
          step: 0.05
        },
        model_type: {
          type: 'select',
          label: 'Model Type',
          description: 'Machine learning model to use',
          default: 'xgboost',
          options: [
            { value: 'xgboost', label: 'XGBoost' },
            { value: 'random_forest', label: 'Random Forest' },
            { value: 'neural_network', label: 'Neural Network' },
            { value: 'svm', label: 'Support Vector Machine' }
          ]
        },
        retrain_frequency: {
          type: 'select',
          label: 'Retrain Frequency',
          description: 'How often to retrain the model',
          default: 'weekly',
          options: [
            { value: 'daily', label: 'Daily' },
            { value: 'weekly', label: 'Weekly' },
            { value: 'monthly', label: 'Monthly' }
          ]
        }
      }
    };

    return definitions[strategyType] || {};
  };

  /**
   * Load parameter definitions for the strategy
   */
  const loadParameterDefinitions = useCallback(() => {
    // This would typically come from the backend API
    const definitions = getParameterDefinitions(strategy);
    setParameterDefinitions(definitions);
    
    // Initialize parameter values with defaults
    const defaultValues = {};
    Object.keys(definitions).forEach(param => {
      defaultValues[param] = definitions[param].default;
    });
    setParameterValues(prev => ({ ...defaultValues, ...prev }));
  }, [strategy]);

  /**
   * Initialize component with parameter definitions
   */
  useEffect(() => {
    if (strategy) {
      loadParameterDefinitions();
    }
  }, [strategy, loadParameterDefinitions]);

  /**
   * Update parameter values when props change
   */
  useEffect(() => {
    setParameterValues(parameters);
  }, [parameters]);

  /**
   * Handle parameter value changes
   */
  const handleParameterChange = (paramName, value) => {
    const newValues = {
      ...parameterValues,
      [paramName]: value
    };
    
    setParameterValues(newValues);
    
    // Validate parameter
    const error = validateParameter(paramName, value);
    setValidationErrors(prev => ({
      ...prev,
      [paramName]: error
    }));
    
    // Notify parent component
    if (onParameterChange && !error) {
      onParameterChange(newValues);
    }
  };

  /**
   * Validate parameter value
   */
  const validateParameter = (paramName, value) => {
    const definition = parameterDefinitions[paramName];
    if (!definition) return null;

    if (definition.type === 'number') {
      const numValue = parseFloat(value);
      if (isNaN(numValue)) {
        return 'Must be a valid number';
      }
      if (definition.min !== undefined && numValue < definition.min) {
        return `Must be at least ${definition.min}`;
      }
      if (definition.max !== undefined && numValue > definition.max) {
        return `Must be at most ${definition.max}`;
      }
    }

    if (definition.required && (!value || value === '')) {
      return 'This field is required';
    }

    return null;
  };

  /**
   * Render parameter input based on type
   */
  const renderParameterInput = (paramName, definition) => {
    const value = parameterValues[paramName] || definition.default;
    const error = validationErrors[paramName];

    switch (definition.type) {
      case 'number':
        return (
          <input
            type="number"
            className={`form-control ${error ? 'is-invalid' : ''}`}
            value={value}
            min={definition.min}
            max={definition.max}
            step={definition.step}
            onChange={(e) => handleParameterChange(paramName, parseFloat(e.target.value))}
            disabled={readonly}
          />
        );

      case 'boolean':
        return (
          <div className="form-check">
            <input
              type="checkbox"
              className="form-check-input"
              checked={value}
              onChange={(e) => handleParameterChange(paramName, e.target.checked)}
              disabled={readonly}
            />
          </div>
        );

      case 'select':
        return (
          <select
            className={`form-select ${error ? 'is-invalid' : ''}`}
            value={value}
            onChange={(e) => handleParameterChange(paramName, e.target.value)}
            disabled={readonly}
          >
            {definition.options?.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );

      case 'text':
      default:
        return (
          <input
            type="text"
            className={`form-control ${error ? 'is-invalid' : ''}`}
            value={value}
            onChange={(e) => handleParameterChange(paramName, e.target.value)}
            disabled={readonly}
          />
        );
    }
  };

  /**
   * Reset parameters to defaults
   */
  const resetToDefaults = () => {
    const defaultValues = {};
    Object.keys(parameterDefinitions).forEach(param => {
      defaultValues[param] = parameterDefinitions[param].default;
    });
    setParameterValues(defaultValues);
    setValidationErrors({});
    
    if (onParameterChange) {
      onParameterChange(defaultValues);
    }
  };

  if (!strategy || Object.keys(parameterDefinitions).length === 0) {
    return (
      <div className="text-center text-muted py-4">
        <i className="fas fa-sliders-h fa-2x mb-2"></i>
        <p>No parameters available for this strategy</p>
      </div>
    );
  }

  return (
    <div className="parameter-form">
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h6 className="mb-0">Strategy Parameters</h6>
        {!readonly && (
          <button
            className="btn btn-outline-secondary btn-sm"
            onClick={resetToDefaults}
            title="Reset to Defaults"
          >
            <i className="fas fa-undo me-1"></i>
            Reset
          </button>
        )}
      </div>

      {/* Parameter Fields */}
      {Object.entries(parameterDefinitions).map(([paramName, definition]) => (
        <div key={paramName} className="mb-3">
          <label className="form-label">
            {definition.label}
            {definition.required && <span className="text-danger">*</span>}
          </label>
          
          {renderParameterInput(paramName, definition)}
          
          {/* Description */}
          {definition.description && (
            <div className="form-text">
              <small className="text-muted">{definition.description}</small>
            </div>
          )}
          
          {/* Validation Error */}
          {validationErrors[paramName] && (
            <div className="invalid-feedback d-block">
              {validationErrors[paramName]}
            </div>
          )}
          
          {/* Parameter Range Info */}
          {definition.type === 'number' && (definition.min !== undefined || definition.max !== undefined) && (
            <div className="form-text">
              <small className="text-muted">
                Range: {definition.min || '∞'} to {definition.max || '∞'}
                {definition.step && `, Step: ${definition.step}`}
              </small>
            </div>
          )}
        </div>
      ))}

      {/* Summary */}
      <div className="mt-4 p-3 bg-light rounded">
        <h6 className="mb-2">Current Parameters</h6>
        <div className="row">
          {Object.entries(parameterValues).map(([param, value]) => (
            <div key={param} className="col-6 mb-1">
              <small>
                <strong>{parameterDefinitions[param]?.label || param}:</strong> {
                  typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value
                }
              </small>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ParameterForm;