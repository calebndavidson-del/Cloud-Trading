/**
 * Navigation Bar Component
 * 
 * Provides main navigation and system control functionality.
 * Features:
 * - Tab navigation
 * - System status display
 * - Control buttons (start/stop trading)
 * - Real-time clock
 */

import React from 'react';

const NavigationBar = ({ 
  activeTab, 
  onTabChange, 
  systemStatus, 
  onSystemAction, 
  loading 
}) => {
  /**
   * Handle emergency stop with confirmation
   */
  const handleEmergencyStop = () => {
    const confirmed = window.confirm(
      'Are you sure you want to perform an emergency stop? This will cancel all active orders and stop trading immediately.'
    );
    
    if (confirmed) {
      onSystemAction('emergency_stop');
    }
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
      <div className="container">
        {/* Brand */}
        <button type="button" className="navbar-brand btn btn-link" style={{ border: 'none', color: 'inherit', textDecoration: 'none' }}>
          <i className="fas fa-robot me-2"></i>
          Trading Bot
        </button>

        {/* Mobile toggle */}
        <button 
          className="navbar-toggler" 
          type="button" 
          data-bs-toggle="collapse" 
          data-bs-target="#navbarContent"
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse" id="navbarContent">
          {/* Navigation Links */}
          <ul className="navbar-nav me-auto">
            <li className="nav-item">
              <button
                className={`nav-link btn btn-link ${activeTab === 'live' ? 'active' : ''}`}
                onClick={() => onTabChange('live')}
                style={{ border: 'none', background: 'none' }}
              >
                <i className="fas fa-chart-line me-1"></i>
                Live Trading
              </button>
            </li>
            <li className="nav-item">
              <button
                className={`nav-link btn btn-link ${activeTab === 'backtest' ? 'active' : ''}`}
                onClick={() => onTabChange('backtest')}
                style={{ border: 'none', background: 'none' }}
              >
                <i className="fas fa-history me-1"></i>
                Backtest
              </button>
            </li>
            <li className="nav-item">
              <button
                className={`nav-link btn btn-link ${activeTab === 'optimization' ? 'active' : ''}`}
                onClick={() => onTabChange('optimization')}
                style={{ border: 'none', background: 'none' }}
              >
                <i className="fas fa-sliders-h me-1"></i>
                Optimization
              </button>
            </li>
          </ul>

          {/* System Controls and Status */}
          <div className="navbar-nav">
            {/* System Status */}
            <span className="navbar-text me-3">
              <i className={`fas fa-circle me-1 ${systemStatus.isOnline ? 'text-success' : 'text-danger'}`}></i>
              {systemStatus.isOnline ? 'Online' : 'Offline'}
            </span>

            {/* Portfolio Value */}
            <span className="navbar-text me-3">
              <i className="fas fa-dollar-sign me-1"></i>
              ${systemStatus.portfolioValue.toLocaleString()}
            </span>

            {/* Daily P&L */}
            <span className={`navbar-text me-3 ${systemStatus.dailyPnL >= 0 ? 'text-success' : 'text-danger'}`}>
              <i className={`fas ${systemStatus.dailyPnL >= 0 ? 'fa-arrow-up' : 'fa-arrow-down'} me-1`}></i>
              {systemStatus.dailyPnL >= 0 ? '+' : ''}${systemStatus.dailyPnL.toLocaleString()}
            </span>

            {/* Control Buttons */}
            <div className="btn-group me-2" role="group">
              {systemStatus.isOnline ? (
                <button
                  className="btn btn-outline-warning btn-sm"
                  onClick={() => onSystemAction('stop_trading')}
                  disabled={loading}
                  title="Stop Trading"
                >
                  <i className="fas fa-stop me-1"></i>
                  Stop
                </button>
              ) : (
                <button
                  className="btn btn-outline-success btn-sm"
                  onClick={() => onSystemAction('start_trading')}
                  disabled={loading}
                  title="Start Trading"
                >
                  <i className="fas fa-play me-1"></i>
                  Start
                </button>
              )}
              
              <button
                className="btn btn-outline-danger btn-sm"
                onClick={handleEmergencyStop}
                disabled={loading}
                title="Emergency Stop"
              >
                <i className="fas fa-exclamation-triangle me-1"></i>
                E-Stop
              </button>
            </div>

            {/* Settings Dropdown */}
            <div className="dropdown">
              <button
                className="btn btn-outline-secondary btn-sm dropdown-toggle"
                type="button"
                id="settingsDropdown"
                data-bs-toggle="dropdown"
                aria-expanded="false"
              >
                <i className="fas fa-cog"></i>
              </button>
              <ul className="dropdown-menu dropdown-menu-end" aria-labelledby="settingsDropdown">
                <li>
                  <button className="dropdown-item" onClick={() => window.location.reload()}>
                    <i className="fas fa-sync-alt me-2"></i>
                    Refresh Dashboard
                  </button>
                </li>
                <li>
                  <button className="dropdown-item" onClick={() => {}}>
                    <i className="fas fa-download me-2"></i>
                    Export Logs
                  </button>
                </li>
                <li><hr className="dropdown-divider" /></li>
                <li>
                  <button className="dropdown-item" onClick={() => {}}>
                    <i className="fas fa-info-circle me-2"></i>
                    System Info
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default NavigationBar;