/**
 * Live Trading Tab Component
 * 
 * Displays real-time trading information including:
 * - Current positions and P&L
 * - Active orders
 * - Performance charts
 * - Trading controls
 * - Risk metrics
 */

import React, { useState, useEffect } from 'react';
import ResultsChart from './ResultsChart';
import { backendAPI } from '../api/backend';

const LiveTradingTab = ({ systemStatus, onRefresh, loading }) => {
  // State management
  const [positions, setPositions] = useState([]);
  const [activeOrders, setActiveOrders] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  const [riskMetrics, setRiskMetrics] = useState({});
  const [selectedTimeframe, setSelectedTimeframe] = useState('1D');
  const [autoRefresh, setAutoRefresh] = useState(true);

  /**
   * Initialize component and set up data polling
   */
  useEffect(() => {
    if (systemStatus.isOnline) {
      fetchLiveTradingData();
    }

    // Set up auto-refresh interval
    let refreshInterval;
    if (autoRefresh && systemStatus.isOnline) {
      refreshInterval = setInterval(fetchLiveTradingData, 10000); // Every 10 seconds
    }

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [systemStatus.isOnline, autoRefresh]);

  /**
   * Fetch live trading data from backend
   */
  const fetchLiveTradingData = async () => {
    try {
      const [positionsData, ordersData, performanceData, riskData] = await Promise.all([
        backendAPI.getCurrentPositions(),
        backendAPI.getActiveOrders(),
        backendAPI.getPerformanceData(selectedTimeframe),
        backendAPI.getRiskMetrics()
      ]);

      setPositions(positionsData || []);
      setActiveOrders(ordersData || []);
      setPerformanceData(performanceData || []);
      setRiskMetrics(riskData || {});
    } catch (error) {
      console.error('Failed to fetch live trading data:', error);
    }
  };

  /**
   * Handle manual order placement
   */
  const handlePlaceOrder = async (orderData) => {
    try {
      await backendAPI.placeOrder(orderData);
      await fetchLiveTradingData(); // Refresh data
      onRefresh(); // Refresh parent component
    } catch (error) {
      console.error('Failed to place order:', error);
      alert('Failed to place order: ' + error.message);
    }
  };

  /**
   * Handle order cancellation
   */
  const handleCancelOrder = async (orderId) => {
    try {
      await backendAPI.cancelOrder(orderId);
      await fetchLiveTradingData(); // Refresh data
    } catch (error) {
      console.error('Failed to cancel order:', error);
      alert('Failed to cancel order: ' + error.message);
    }
  };

  /**
   * Handle position closure
   */
  const handleClosePosition = async (symbol) => {
    const confirmed = window.confirm(`Are you sure you want to close position in ${symbol}?`);
    if (confirmed) {
      try {
        await backendAPI.closePosition(symbol);
        await fetchLiveTradingData(); // Refresh data
        onRefresh(); // Refresh parent component
      } catch (error) {
        console.error('Failed to close position:', error);
        alert('Failed to close position: ' + error.message);
      }
    }
  };

  return (
    <div className="live-trading-tab">
      {/* Control Panel */}
      <div className="row mb-4">
        <div className="col-md-8">
          <div className="d-flex align-items-center">
            <h4 className="mb-0">
              <i className="fas fa-chart-line me-2 text-primary"></i>
              Live Trading Dashboard
            </h4>
            <div className="ms-auto">
              <div className="form-check form-switch">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="autoRefreshSwitch"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                />
                <label className="form-check-label" htmlFor="autoRefreshSwitch">
                  Auto Refresh
                </label>
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-4 text-end">
          <button
            className="btn btn-outline-primary btn-sm me-2"
            onClick={fetchLiveTradingData}
            disabled={loading}
          >
            <i className="fas fa-sync-alt me-1"></i>
            Refresh
          </button>
          <div className="btn-group" role="group">
            {['1D', '1W', '1M'].map(timeframe => (
              <button
                key={timeframe}
                className={`btn btn-sm ${selectedTimeframe === timeframe ? 'btn-primary' : 'btn-outline-primary'}`}
                onClick={() => setSelectedTimeframe(timeframe)}
              >
                {timeframe}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Chart */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">
                <i className="fas fa-chart-area me-2"></i>
                Portfolio Performance
              </h5>
            </div>
            <div className="card-body">
              <ResultsChart
                data={performanceData}
                type="line"
                title="Portfolio Value Over Time"
                height={300}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Current Positions */}
      <div className="row mb-4">
        <div className="col-md-8">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">
                <i className="fas fa-briefcase me-2"></i>
                Current Positions ({positions.length})
              </h5>
            </div>
            <div className="card-body">
              {positions.length === 0 ? (
                <div className="text-center text-muted py-4">
                  <i className="fas fa-inbox fa-3x mb-3"></i>
                  <p>No open positions</p>
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th>Quantity</th>
                        <th>Avg Price</th>
                        <th>Current Price</th>
                        <th>P&L</th>
                        <th>P&L %</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {positions.map((position, index) => (
                        <tr key={index}>
                          <td>
                            <strong>{position.symbol}</strong>
                          </td>
                          <td>{position.quantity}</td>
                          <td>${position.avgPrice?.toFixed(2)}</td>
                          <td>${position.currentPrice?.toFixed(2)}</td>
                          <td className={position.pnl >= 0 ? 'text-success' : 'text-danger'}>
                            {position.pnl >= 0 ? '+' : ''}${position.pnl?.toFixed(2)}
                          </td>
                          <td className={position.pnlPercent >= 0 ? 'text-success' : 'text-danger'}>
                            {position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent?.toFixed(2)}%
                          </td>
                          <td>
                            <button
                              className="btn btn-outline-danger btn-sm"
                              onClick={() => handleClosePosition(position.symbol)}
                              title="Close Position"
                            >
                              <i className="fas fa-times"></i>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Risk Metrics */}
        <div className="col-md-4">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">
                <i className="fas fa-shield-alt me-2"></i>
                Risk Metrics
              </h5>
            </div>
            <div className="card-body">
              <div className="row">
                <div className="col-12 mb-3">
                  <div className="metric-card">
                    <div className="metric-label">Value at Risk (95%)</div>
                    <div className="metric-value text-warning">
                      ${riskMetrics.var?.toLocaleString() || '0'}
                    </div>
                  </div>
                </div>
                <div className="col-12 mb-3">
                  <div className="metric-card">
                    <div className="metric-label">Max Drawdown</div>
                    <div className="metric-value text-danger">
                      {riskMetrics.maxDrawdown?.toFixed(2) || '0'}%
                    </div>
                  </div>
                </div>
                <div className="col-12 mb-3">
                  <div className="metric-card">
                    <div className="metric-label">Sharpe Ratio</div>
                    <div className="metric-value text-info">
                      {riskMetrics.sharpeRatio?.toFixed(2) || '0'}
                    </div>
                  </div>
                </div>
                <div className="col-12">
                  <div className="metric-card">
                    <div className="metric-label">Portfolio Beta</div>
                    <div className="metric-value text-secondary">
                      {riskMetrics.beta?.toFixed(2) || '0'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Active Orders */}
      <div className="row">
        <div className="col-12">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">
                <i className="fas fa-list-ul me-2"></i>
                Active Orders ({activeOrders.length})
              </h5>
            </div>
            <div className="card-body">
              {activeOrders.length === 0 ? (
                <div className="text-center text-muted py-4">
                  <i className="fas fa-clipboard fa-3x mb-3"></i>
                  <p>No active orders</p>
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Order ID</th>
                        <th>Symbol</th>
                        <th>Side</th>
                        <th>Type</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Status</th>
                        <th>Time</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activeOrders.map((order, index) => (
                        <tr key={index}>
                          <td>
                            <small className="font-monospace">{order.orderId}</small>
                          </td>
                          <td><strong>{order.symbol}</strong></td>
                          <td>
                            <span className={`badge ${order.side === 'buy' ? 'bg-success' : 'bg-danger'}`}>
                              {order.side.toUpperCase()}
                            </span>
                          </td>
                          <td>{order.type}</td>
                          <td>{order.quantity}</td>
                          <td>${order.price?.toFixed(2) || 'Market'}</td>
                          <td>
                            <span className="badge bg-warning">{order.status}</span>
                          </td>
                          <td>
                            <small>{new Date(order.timestamp).toLocaleTimeString()}</small>
                          </td>
                          <td>
                            <button
                              className="btn btn-outline-danger btn-sm"
                              onClick={() => handleCancelOrder(order.orderId)}
                              title="Cancel Order"
                            >
                              <i className="fas fa-times"></i>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* System Offline Message */}
      {!systemStatus.isOnline && (
        <div className="alert alert-warning mt-4" role="alert">
          <i className="fas fa-exclamation-triangle me-2"></i>
          <strong>Trading System Offline</strong> - 
          Real-time data and trading functions are not available. 
          Please start the trading system to access live functionality.
        </div>
      )}
    </div>
  );
};

export default LiveTradingTab;