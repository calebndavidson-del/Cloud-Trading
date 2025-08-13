/**
 * Backend API Integration
 * 
 * Provides a unified interface for communicating with the Python backend.
 * Handles API requests, error handling, authentication, and data formatting.
 * 
 * Features:
 * - RESTful API calls
 * - Error handling and retry logic
 * - Request/response interceptors
 * - Authentication management
 * - Data transformation
 */

// Configuration
const API_CONFIG = {
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  timeout: parseInt(process.env.REACT_APP_API_TIMEOUT) || 30000,
  retryAttempts: 3,
  retryDelay: 1000
};

/**
 * HTTP client with retry logic and error handling
 */
class APIClient {
  constructor(config = API_CONFIG) {
    this.config = config;
    this.authToken = localStorage.getItem('authToken');
  }

  /**
   * Make HTTP request with retry logic
   */
  async request(endpoint, options = {}) {
    const url = `${this.config.baseURL}${endpoint}`;
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.authToken && { 'Authorization': `Bearer ${this.authToken}` })
      },
      timeout: this.config.timeout
    };

    const requestOptions = { ...defaultOptions, ...options };

    for (let attempt = 1; attempt <= this.config.retryAttempts; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), requestOptions.timeout);

        const response = await fetch(url, {
          ...requestOptions,
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text();
          let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
          
          try {
            const errorData = JSON.parse(errorText);
            if (errorData.error) {
              errorMessage = errorData.error;
            }
          } catch (e) {
            // Use default error message if parsing fails
            if (errorText) {
              errorMessage = errorText;
            }
          }
          
          throw new Error(errorMessage);
        }

        const data = await response.json();
        return data;
      } catch (error) {
        const errorMessage = error.name === 'AbortError' 
          ? 'Request timeout - please try again' 
          : error.message || 'Failed to connect to backend';
          
        if (process.env.NODE_ENV === 'development') {
          console.error(`API request attempt ${attempt} failed:`, error);
        }

        if (attempt === this.config.retryAttempts) {
          throw new Error(errorMessage);
        }

        // Wait before retry
        await new Promise(resolve => 
          setTimeout(resolve, this.config.retryDelay * attempt)
        );
      }
    }
  }

  /**
   * GET request
   */
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    
    return this.request(url, { method: 'GET' });
  }

  /**
   * POST request
   */
  async post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  /**
   * PUT request
   */
  async put(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  /**
   * DELETE request
   */
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  /**
   * Set authentication token
   */
  setAuthToken(token) {
    this.authToken = token;
    localStorage.setItem('authToken', token);
  }

  /**
   * Clear authentication token
   */
  clearAuthToken() {
    this.authToken = null;
    localStorage.removeItem('authToken');
  }
}

// Create API client instance
const apiClient = new APIClient();

/**
 * Backend API interface
 */
export const backendAPI = {
  /**
   * System Health and Status
   */
  async healthCheck() {
    return apiClient.get('/health');
  },

  async getSystemStatus() {
    return apiClient.get('/system/status');
  },

  async startTrading() {
    return apiClient.post('/system/start');
  },

  async stopTrading() {
    return apiClient.post('/system/stop');
  },

  async emergencyStop() {
    return apiClient.post('/system/emergency-stop');
  },

  /**
   * Live Trading
   */
  async getCurrentPositions() {
    return apiClient.get('/trading/positions');
  },

  async getActiveOrders() {
    return apiClient.get('/trading/orders/active');
  },

  async placeOrder(orderData) {
    return apiClient.post('/trading/orders', orderData);
  },

  async cancelOrder(orderId) {
    return apiClient.delete(`/trading/orders/${orderId}`);
  },

  async closePosition(symbol) {
    return apiClient.post('/trading/positions/close', { symbol });
  },

  async getPerformanceData(timeframe = '1D') {
    return apiClient.get('/trading/performance', { timeframe });
  },

  async getRiskMetrics() {
    return apiClient.get('/trading/risk-metrics');
  },

  /**
   * Strategies
   */
  async getAvailableStrategies() {
    return apiClient.get('/strategies');
  },

  async getStrategyParameters(strategyName) {
    return apiClient.get(`/strategies/${strategyName}/parameters`);
  },

  async updateStrategyParameters(strategyName, parameters) {
    return apiClient.put(`/strategies/${strategyName}/parameters`, parameters);
  },

  async getStrategyParameterSpace(strategyName) {
    return apiClient.get(`/strategies/${strategyName}/parameter-space`);
  },

  /**
   * Backtesting
   */
  async startBacktest(config) {
    return apiClient.post('/backtest/start', config);
  },

  async getBacktestStatus(jobId) {
    return apiClient.get(`/backtest/status/${jobId}`);
  },

  async getBacktestResults(jobId) {
    return apiClient.get(`/backtest/results/${jobId}`);
  },

  async downloadBacktestReport(reportId) {
    // Handle file download
    const url = `${API_CONFIG.baseURL}/backtest/report/${reportId}/download`;
    const response = await fetch(url, {
      headers: {
        ...(apiClient.authToken && { 'Authorization': `Bearer ${apiClient.authToken}` })
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to download report');
    }
    
    return response.blob();
  },

  /**
   * Optimization
   */
  async startOptimization(config) {
    return apiClient.post('/optimization/start', config);
  },

  async getOptimizationStatus(jobId) {
    return apiClient.get(`/optimization/status/${jobId}`);
  },

  async getOptimizationResults(jobId) {
    return apiClient.get(`/optimization/results/${jobId}`);
  },

  /**
   * Data and Analytics
   */
  async getMarketData(symbols, timeframe = '1D') {
    return apiClient.get('/data/market', { symbols: symbols.join(','), timeframe });
  },

  async getNewsData(symbols = [], limit = 50) {
    return apiClient.get('/data/news', { symbols: symbols.join(','), limit });
  },

  async getEarningsData(symbols) {
    return apiClient.get('/data/earnings', { symbols: symbols.join(',') });
  },

  /**
   * Autonomous Stock Selection
   */
  async getAutonomousSelection(maxSymbols = 15) {
    return apiClient.get('/data/autonomous-selection', { max_symbols: maxSymbols });
  },

  async refreshAutonomousSelection(criteria = {}) {
    return apiClient.post('/data/autonomous-selection/refresh', criteria);
  },

  async getPortfolioAnalytics(period = '1M') {
    return apiClient.get('/analytics/portfolio', { period });
  },

  /**
   * Configuration
   */
  async getConfiguration() {
    return apiClient.get('/config');
  },

  async updateConfiguration(config) {
    return apiClient.put('/config', config);
  },

  /**
   * Equity Management
   */
  async updateEquity(equity) {
    return apiClient.post('/update-equity', { equity });
  },

  /**
   * Logging and Monitoring
   */
  async getLogs(level = 'INFO', limit = 100) {
    return apiClient.get('/logs', { level, limit });
  },

  async getMetrics(metric_type = 'system') {
    return apiClient.get('/metrics', { metric_type });
  },

  async exportData(dataType, format = 'csv', startDate, endDate) {
    const params = { format };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    
    return apiClient.get(`/export/${dataType}`, params);
  },

  /**
   * Authentication (if required)
   */
  async login(username, password) {
    const response = await apiClient.post('/auth/login', { username, password });
    if (response.token) {
      apiClient.setAuthToken(response.token);
    }
    return response;
  },

  async logout() {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      apiClient.clearAuthToken();
    }
  },

  async refreshToken() {
    const response = await apiClient.post('/auth/refresh');
    if (response.token) {
      apiClient.setAuthToken(response.token);
    }
    return response;
  }
};

/**
 * WebSocket connection for real-time updates
 */
export class RealTimeConnection {
  constructor(url = 'ws://localhost:8000/ws') {
    this.url = url;
    this.socket = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
  }

  /**
   * Connect to WebSocket
   */
  connect() {
    try {
      this.socket = new WebSocket(this.url);
      
      this.socket.onopen = () => {
        if (process.env.NODE_ENV === 'development') {
          // console.log('WebSocket connected');
        }
        this.reconnectAttempts = 0;
        this.emit('connected');
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit(data.type, data.payload);
        } catch (error) {
          if (process.env.NODE_ENV === 'development') {
            // console.error('Failed to parse WebSocket message:', error);
          }
        }
      };

      this.socket.onclose = () => {
        if (process.env.NODE_ENV === 'development') {
          // console.log('WebSocket disconnected');
        }
        this.emit('disconnected');
        this.attemptReconnect();
      };

      this.socket.onerror = (error) => {
        if (process.env.NODE_ENV === 'development') {
          // console.error('WebSocket error:', error);
        }
        this.emit('error', error);
      };
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        // console.error('Failed to connect WebSocket:', error);
      }
    }
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  /**
   * Attempt to reconnect
   */
  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        if (process.env.NODE_ENV === 'development') {
          // console.log(`Attempting WebSocket reconnection (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        }
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  /**
   * Subscribe to events
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  /**
   * Unsubscribe from events
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * Emit events to listeners
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          if (process.env.NODE_ENV === 'development') {
            // console.error('Error in WebSocket event callback:', error);
          }
        }
      });
    }
  }

  /**
   * Send message to server
   */
  send(type, payload) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type, payload }));
    } else {
      if (process.env.NODE_ENV === 'development') {
        // console.warn('WebSocket not connected, message not sent');
      }
    }
  }
}

// Export default API client for direct use
export default apiClient;