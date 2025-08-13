/**
 * Main App Component for Trading Bot Dashboard
 * 
 * Features:
 * - Three main tabs: Live Trading, Backtest, Optimization
 * - Real-time data updates
 * - Responsive design
 * - Clean, uncluttered interface
 * - Integration with backend API
 */

import React, { useState, useEffect, useCallback } from 'react';
import NavigationBar from './components/NavigationBar';
import LiveTradingTab from './components/LiveTradingTab';
import BacktestTab from './components/BacktestTab';
import OptimizationTab from './components/OptimizationTab';
import { backendAPI } from './api/backend';

const App = () => {
  // State management
  const [activeTab, setActiveTab] = useState('live');
  const [systemStatus, setSystemStatus] = useState({
    isOnline: false,
    portfolioValue: 0,
    dailyPnL: 0,
    activeStrategies: 0,
    lastUpdate: null
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Fetch current system status from backend
   */
  const fetchSystemStatus = useCallback(async () => {
    try {
      const status = await backendAPI.getSystemStatus();
      setSystemStatus({
        isOnline: status.is_running || false,
        portfolioValue: status.portfolio_value || 0,
        dailyPnL: status.daily_pnl || 0,
        activeStrategies: status.active_strategies || 0,
        lastUpdate: new Date()
      });
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        // console.error('Failed to fetch system status:', err);
      }
      setSystemStatus(prev => ({
        ...prev,
        isOnline: false,
        lastUpdate: new Date()
      }));
    }
  }, []);

  /**
   * Initialize the application
   */
  const initializeApp = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch initial system status
      await fetchSystemStatus();
      
      // Verify backend connectivity
      const healthCheck = await backendAPI.healthCheck();
      if (!healthCheck.success) {
        throw new Error('Backend connectivity check failed');
      }
      
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
      if (process.env.NODE_ENV === 'development') {
        // console.error('App initialization error:', err);
      }
    }
  }, [fetchSystemStatus]);

  /**
   * Initialize application and fetch initial data
   */
  useEffect(() => {
    initializeApp();
    
    // Set up real-time data polling
    const statusInterval = setInterval(fetchSystemStatus, 30000); // Every 30 seconds
    
    // Cleanup on unmount
    return () => {
      clearInterval(statusInterval);
    };
  }, [initializeApp, fetchSystemStatus]);

  /**
   * Handle tab change
   */
  const handleTabChange = (tabName) => {
    setActiveTab(tabName);
  };

  /**
   * Handle system actions (start/stop trading, etc.)
   */
  const handleSystemAction = async (action) => {
    try {
      setLoading(true);
      
      switch (action) {
        case 'start_trading':
          await backendAPI.startTrading();
          break;
        case 'stop_trading':
          await backendAPI.stopTrading();
          break;
        case 'emergency_stop':
          await backendAPI.emergencyStop();
          break;
        default:
          if (process.env.NODE_ENV === 'development') {
            // console.warn('Unknown system action:', action);
          }
      }
      
      // Refresh system status after action
      await fetchSystemStatus();
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
      // console.error('System action error:', err);
    }
  };

  /**
   * Render loading state
   */
  if (loading && !systemStatus.lastUpdate) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '50vh' }}>
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-3"></div>
          <h5>Initializing Trading Bot Dashboard...</h5>
          <p className="text-muted">Connecting to backend services</p>
        </div>
      </div>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <div className="container mt-5">
        <div className="alert alert-danger alert-custom" role="alert">
          <h4 className="alert-heading">
            <i className="fas fa-exclamation-triangle me-2"></i>
            System Error
          </h4>
          <p>{error}</p>
          <hr />
          <button 
            className="btn btn-outline-danger"
            onClick={() => window.location.reload()}
          >
            <i className="fas fa-redo me-2"></i>
            Reload Application
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Navigation Bar */}
      <NavigationBar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        systemStatus={systemStatus}
        onSystemAction={handleSystemAction}
        loading={loading}
      />

      {/* Main Content Area */}
      <div className="container-fluid mt-4">
        {/* System Status Overview */}
        <div className="row mb-4">
          <div className="col-md-3">
            <div className="metric-card">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <div className="metric-label">Portfolio Value</div>
                  <div className="metric-value">
                    ${systemStatus.portfolioValue.toLocaleString()}
                  </div>
                </div>
                <i className="fas fa-wallet fa-2x text-primary"></i>
              </div>
            </div>
          </div>
          
          <div className="col-md-3">
            <div className="metric-card">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <div className="metric-label">Daily P&L</div>
                  <div className={`metric-value ${systemStatus.dailyPnL >= 0 ? 'text-success' : 'text-danger'}`}>
                    {systemStatus.dailyPnL >= 0 ? '+' : ''}
                    ${systemStatus.dailyPnL.toLocaleString()}
                  </div>
                </div>
                <i className={`fas ${systemStatus.dailyPnL >= 0 ? 'fa-arrow-up' : 'fa-arrow-down'} fa-2x ${systemStatus.dailyPnL >= 0 ? 'text-success' : 'text-danger'}`}></i>
              </div>
            </div>
          </div>
          
          <div className="col-md-3">
            <div className="metric-card">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <div className="metric-label">Active Strategies</div>
                  <div className="metric-value">{systemStatus.activeStrategies}</div>
                </div>
                <i className="fas fa-cogs fa-2x text-info"></i>
              </div>
            </div>
          </div>
          
          <div className="col-md-3">
            <div className="metric-card">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <div className="metric-label">System Status</div>
                  <div className="metric-value">
                    <span className={`status-indicator ${systemStatus.isOnline ? 'status-active' : 'status-inactive'}`}></span>
                    {systemStatus.isOnline ? 'Online' : 'Offline'}
                  </div>
                </div>
                <i className={`fas ${systemStatus.isOnline ? 'fa-play-circle' : 'fa-stop-circle'} fa-2x ${systemStatus.isOnline ? 'text-success' : 'text-danger'}`}></i>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <ul className="nav nav-tabs" role="tablist">
          <li className="nav-item">
            <button
              className={`nav-link ${activeTab === 'live' ? 'active' : ''}`}
              onClick={() => handleTabChange('live')}
              type="button"
              role="tab"
            >
              <i className="fas fa-chart-line me-2"></i>
              Live Trading
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link ${activeTab === 'backtest' ? 'active' : ''}`}
              onClick={() => handleTabChange('backtest')}
              type="button"
              role="tab"
            >
              <i className="fas fa-history me-2"></i>
              Backtest
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link ${activeTab === 'optimization' ? 'active' : ''}`}
              onClick={() => handleTabChange('optimization')}
              type="button"
              role="tab"
            >
              <i className="fas fa-sliders-h me-2"></i>
              Optimization
            </button>
          </li>
        </ul>

        {/* Tab Content */}
        <div className="tab-content">
          {activeTab === 'live' && (
            <LiveTradingTab
              systemStatus={systemStatus}
              onRefresh={fetchSystemStatus}
              loading={loading}
            />
          )}
          
          {activeTab === 'backtest' && (
            <BacktestTab
              onRefresh={fetchSystemStatus}
              loading={loading}
            />
          )}
          
          {activeTab === 'optimization' && (
            <OptimizationTab
              onRefresh={fetchSystemStatus}
              loading={loading}
            />
          )}
        </div>
      </div>

      {/* Global Loading Overlay */}
      {loading && (
        <div className="position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center bg-dark bg-opacity-25" style={{ zIndex: 9999 }}>
          <div className="text-center text-white">
            <div className="loading-spinner mx-auto mb-3"></div>
            <h5>Processing...</h5>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;