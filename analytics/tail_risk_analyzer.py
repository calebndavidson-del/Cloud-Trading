"""
Tail Risk Analyzer

Advanced tail risk analysis module that focuses on extreme event risk assessment
rather than traditional standard deviation-based measures. Implements VaR, CVaR,
drawdown analysis, and other sophisticated risk metrics.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from scipy import stats
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')


class TailRiskAnalyzer:
    """
    Comprehensive tail risk analysis for extreme event risk management.
    
    Features:
    - Value at Risk (VaR) calculation with multiple methods
    - Conditional Value at Risk (CVaR/Expected Shortfall)
    - Maximum drawdown and drawdown probability analysis
    - Extreme value theory applications
    - Stress testing and scenario analysis
    - Risk decomposition by asset and time
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize tail risk analyzer.
        
        Args:
            config: Configuration dictionary containing:
                - confidence_levels: List of confidence levels for VaR (e.g., [0.95, 0.99])
                - lookback_periods: Historical lookback periods in days
                - portfolio_value: Current portfolio value
                - stress_scenarios: Custom stress test scenarios
                - update_frequency: Risk update frequency in minutes
        """
        self.config = config
        self.confidence_levels = config.get('confidence_levels', [0.95, 0.99, 0.995])
        self.lookback_periods = config.get('lookback_periods', [30, 90, 252])
        self.portfolio_value = config.get('portfolio_value', 1000000)
        self.stress_scenarios = config.get('stress_scenarios', {})
        self.update_frequency = config.get('update_frequency', 15)  # minutes
        
        # Risk data storage
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.return_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.portfolio_history: deque = deque(maxlen=1000)
        
        # Risk metrics
        self.var_estimates: Dict[str, Dict[str, float]] = {}
        self.cvar_estimates: Dict[str, Dict[str, float]] = {}
        self.drawdown_metrics: Dict[str, Any] = {}
        self.tail_risk_summary: Dict[str, Any] = {}
        
        # Model parameters
        self.var_methods = ['historical', 'parametric', 'monte_carlo', 'evt']
        self.last_update = None
        
        self.logger = logging.getLogger(__name__)
        
    def update_market_data(self, symbol: str, price_data: Dict[str, Any]) -> None:
        """
        Update market data for risk calculations.
        
        Args:
            symbol: Asset symbol
            price_data: Dictionary containing price and timestamp information
        """
        timestamp = price_data.get('timestamp', datetime.now())
        price = price_data.get('price', price_data.get('regularMarketPrice', 0))
        
        if price > 0:
            self.price_history[symbol].append({
                'timestamp': timestamp,
                'price': price
            })
            
            # Calculate returns if we have previous price
            if len(self.price_history[symbol]) > 1:
                prev_price = self.price_history[symbol][-2]['price']
                return_val = (price - prev_price) / prev_price
                
                self.return_history[symbol].append({
                    'timestamp': timestamp,
                    'return': return_val
                })
    
    def update_portfolio_value(self, portfolio_value: float, positions: Dict[str, float] = None) -> None:
        """
        Update portfolio value and positions for risk calculation.
        
        Args:
            portfolio_value: Current total portfolio value
            positions: Dictionary of current positions {symbol: value}
        """
        portfolio_data = {
            'timestamp': datetime.now(),
            'value': portfolio_value,
            'positions': positions or {}
        }
        
        self.portfolio_history.append(portfolio_data)
        self.portfolio_value = portfolio_value
        
        # Calculate portfolio returns
        if len(self.portfolio_history) > 1:
            prev_value = self.portfolio_history[-2]['value']
            if prev_value > 0:
                portfolio_return = (portfolio_value - prev_value) / prev_value
                
                self.return_history['PORTFOLIO'].append({
                    'timestamp': datetime.now(),
                    'return': portfolio_return
                })
    
    def calculate_comprehensive_risk_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive tail risk metrics for all assets and portfolio.
        
        Returns:
            Dictionary containing all risk metrics
        """
        results = {
            'timestamp': datetime.now(),
            'portfolio_value': self.portfolio_value,
            'individual_assets': {},
            'portfolio': {},
            'correlation_analysis': {},
            'stress_tests': {},
            'risk_alerts': []
        }
        
        # Calculate metrics for individual assets
        for symbol in self.return_history.keys():
            if symbol != 'PORTFOLIO' and len(self.return_history[symbol]) >= 30:
                results['individual_assets'][symbol] = self._calculate_asset_risk_metrics(symbol)
        
        # Calculate portfolio-level metrics
        if len(self.return_history.get('PORTFOLIO', [])) >= 30:
            results['portfolio'] = self._calculate_portfolio_risk_metrics()
        
        # Correlation analysis
        results['correlation_analysis'] = self._calculate_correlation_risk()
        
        # Stress testing
        results['stress_tests'] = self._perform_stress_tests()
        
        # Risk alerts
        results['risk_alerts'] = self._generate_risk_alerts(results)
        
        # Update internal state
        self.tail_risk_summary = results
        self.last_update = datetime.now()
        
        return results
    
    def _calculate_asset_risk_metrics(self, symbol: str) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics for individual asset."""
        returns = [r['return'] for r in self.return_history[symbol]]
        returns_array = np.array(returns)
        
        metrics = {
            'basic_stats': self._calculate_basic_statistics(returns_array),
            'var_estimates': {},
            'cvar_estimates': {},
            'drawdown_analysis': self._calculate_drawdown_metrics(symbol),
            'extreme_value_analysis': self._calculate_evt_metrics(returns_array),
            'tail_metrics': self._calculate_tail_metrics(returns_array)
        }
        
        # Calculate VaR and CVaR for different confidence levels
        for confidence in self.confidence_levels:
            var_results = self._calculate_var_multiple_methods(returns_array, confidence)
            cvar_results = self._calculate_cvar_multiple_methods(returns_array, confidence)
            
            metrics['var_estimates'][f'{confidence*100:.1f}%'] = var_results
            metrics['cvar_estimates'][f'{confidence*100:.1f}%'] = cvar_results
        
        return metrics
    
    def _calculate_portfolio_risk_metrics(self) -> Dict[str, Any]:
        """Calculate risk metrics for overall portfolio."""
        portfolio_returns = [r['return'] for r in self.return_history['PORTFOLIO']]
        returns_array = np.array(portfolio_returns)
        
        metrics = {
            'basic_stats': self._calculate_basic_statistics(returns_array),
            'var_estimates': {},
            'cvar_estimates': {},
            'drawdown_analysis': self._calculate_portfolio_drawdown_metrics(),
            'risk_decomposition': self._calculate_risk_decomposition(),
            'tail_metrics': self._calculate_tail_metrics(returns_array),
            'risk_adjusted_returns': self._calculate_risk_adjusted_returns(returns_array)
        }
        
        # Calculate VaR and CVaR
        for confidence in self.confidence_levels:
            var_results = self._calculate_var_multiple_methods(returns_array, confidence)
            cvar_results = self._calculate_cvar_multiple_methods(returns_array, confidence)
            
            metrics['var_estimates'][f'{confidence*100:.1f}%'] = var_results
            metrics['cvar_estimates'][f'{confidence*100:.1f}%'] = cvar_results
        
        return metrics
    
    def _calculate_basic_statistics(self, returns: np.ndarray) -> Dict[str, float]:
        """Calculate basic statistical measures."""
        return {
            'mean': float(np.mean(returns)),
            'std': float(np.std(returns)),
            'skewness': float(stats.skew(returns)),
            'kurtosis': float(stats.kurtosis(returns)),
            'min': float(np.min(returns)),
            'max': float(np.max(returns)),
            'median': float(np.median(returns)),
            'iqr': float(np.percentile(returns, 75) - np.percentile(returns, 25))
        }
    
    def _calculate_var_multiple_methods(self, returns: np.ndarray, confidence: float) -> Dict[str, float]:
        """Calculate VaR using multiple methodologies."""
        var_estimates = {}
        
        # Historical VaR (non-parametric)
        var_estimates['historical'] = self._calculate_historical_var(returns, confidence)
        
        # Parametric VaR (normal distribution)
        var_estimates['parametric_normal'] = self._calculate_parametric_var(returns, confidence, 'normal')
        
        # Parametric VaR (t-distribution)
        var_estimates['parametric_t'] = self._calculate_parametric_var(returns, confidence, 't')
        
        # Monte Carlo VaR
        var_estimates['monte_carlo'] = self._calculate_monte_carlo_var(returns, confidence)
        
        # Extreme Value Theory VaR
        var_estimates['evt'] = self._calculate_evt_var(returns, confidence)
        
        # Cornish-Fisher VaR (accounts for skewness and kurtosis)
        var_estimates['cornish_fisher'] = self._calculate_cornish_fisher_var(returns, confidence)
        
        return var_estimates
    
    def _calculate_historical_var(self, returns: np.ndarray, confidence: float) -> float:
        """Calculate historical VaR (empirical quantile)."""
        return float(-np.percentile(returns, (1 - confidence) * 100))
    
    def _calculate_parametric_var(self, returns: np.ndarray, confidence: float, distribution: str) -> float:
        """Calculate parametric VaR assuming specific distribution."""
        mean = np.mean(returns)
        std = np.std(returns)
        
        if distribution == 'normal':
            z_score = stats.norm.ppf(1 - confidence)
        elif distribution == 't':
            # Fit t-distribution
            dof, loc, scale = stats.t.fit(returns)
            z_score = stats.t.ppf(1 - confidence, dof, loc, scale)
            return float(-(mean + z_score))
        else:
            z_score = stats.norm.ppf(1 - confidence)
        
        return float(-(mean + z_score * std))
    
    def _calculate_monte_carlo_var(self, returns: np.ndarray, confidence: float, n_simulations: int = 10000) -> float:
        """Calculate VaR using Monte Carlo simulation."""
        mean = np.mean(returns)
        std = np.std(returns)
        
        # Generate random returns assuming normal distribution
        simulated_returns = np.random.normal(mean, std, n_simulations)
        
        return float(-np.percentile(simulated_returns, (1 - confidence) * 100))
    
    def _calculate_evt_var(self, returns: np.ndarray, confidence: float) -> float:
        """Calculate VaR using Extreme Value Theory (Peaks Over Threshold)."""
        try:
            # Use negative returns for tail analysis
            losses = -returns
            
            # Select threshold (90th percentile)
            threshold = np.percentile(losses, 90)
            exceedances = losses[losses > threshold] - threshold
            
            if len(exceedances) < 10:  # Insufficient extreme values
                return self._calculate_historical_var(returns, confidence)
            
            # Fit Generalized Pareto Distribution to exceedances
            shape, loc, scale = stats.genpareto.fit(exceedances, floc=0)
            
            # Calculate VaR using EVT formula
            n = len(returns)
            nu = len(exceedances)
            
            if shape != 0:
                var_evt = threshold + (scale / shape) * (((n / nu) * (1 - confidence)) ** (-shape) - 1)
            else:
                var_evt = threshold + scale * np.log((n / nu) * (1 - confidence))
            
            return float(var_evt)
            
        except Exception as e:
            self.logger.warning(f"EVT VaR calculation failed: {e}")
            return self._calculate_historical_var(returns, confidence)
    
    def _calculate_cornish_fisher_var(self, returns: np.ndarray, confidence: float) -> float:
        """Calculate VaR using Cornish-Fisher expansion for non-normal distributions."""
        mean = np.mean(returns)
        std = np.std(returns)
        skew = stats.skew(returns)
        kurt = stats.kurtosis(returns)
        
        # Get normal quantile
        z = stats.norm.ppf(1 - confidence)
        
        # Cornish-Fisher adjustment
        z_cf = (z +
                (z**2 - 1) * skew / 6 +
                (z**3 - 3*z) * kurt / 24 -
                (2*z**3 - 5*z) * skew**2 / 36)
        
        return float(-(mean + z_cf * std))
    
    def _calculate_cvar_multiple_methods(self, returns: np.ndarray, confidence: float) -> Dict[str, float]:
        """Calculate Conditional VaR (Expected Shortfall) using multiple methods."""
        cvar_estimates = {}
        
        # Historical CVaR
        var_historical = self._calculate_historical_var(returns, confidence)
        tail_losses = returns[returns <= -var_historical]
        if len(tail_losses) > 0:
            cvar_estimates['historical'] = float(-np.mean(tail_losses))
        else:
            cvar_estimates['historical'] = var_historical
        
        # Parametric CVaR (normal)
        cvar_estimates['parametric_normal'] = self._calculate_parametric_cvar(returns, confidence, 'normal')
        
        # Parametric CVaR (t-distribution)
        cvar_estimates['parametric_t'] = self._calculate_parametric_cvar(returns, confidence, 't')
        
        return cvar_estimates
    
    def _calculate_parametric_cvar(self, returns: np.ndarray, confidence: float, distribution: str) -> float:
        """Calculate parametric CVaR."""
        mean = np.mean(returns)
        std = np.std(returns)
        
        if distribution == 'normal':
            # For normal distribution: CVaR = mean - std * pdf(z) / (1 - confidence)
            z = stats.norm.ppf(1 - confidence)
            cvar = -(mean - std * stats.norm.pdf(z) / (1 - confidence))
        elif distribution == 't':
            # For t-distribution, use numerical integration
            try:
                dof, loc, scale = stats.t.fit(returns)
                var_t = self._calculate_parametric_var(returns, confidence, 't')
                
                # Numerical approximation for t-distribution CVaR
                tail_returns = returns[returns <= -var_t]
                if len(tail_returns) > 0:
                    cvar = float(-np.mean(tail_returns))
                else:
                    cvar = var_t
            except:
                cvar = self._calculate_parametric_cvar(returns, confidence, 'normal')
        
        return float(cvar)
    
    def _calculate_drawdown_metrics(self, symbol: str) -> Dict[str, Any]:
        """Calculate drawdown metrics for individual asset."""
        prices = [p['price'] for p in self.price_history[symbol]]
        if len(prices) < 2:
            return {}
        
        prices_array = np.array(prices)
        
        # Calculate running maximum (peak)
        running_max = np.maximum.accumulate(prices_array)
        
        # Calculate drawdown
        drawdown = (prices_array - running_max) / running_max
        
        # Calculate metrics
        max_drawdown = float(np.min(drawdown))
        current_drawdown = float(drawdown[-1])
        
        # Drawdown duration analysis
        drawdown_periods = self._analyze_drawdown_periods(drawdown)
        
        return {
            'current_drawdown': current_drawdown,
            'max_drawdown': max_drawdown,
            'average_drawdown': float(np.mean(drawdown[drawdown < 0])) if np.any(drawdown < 0) else 0.0,
            'drawdown_volatility': float(np.std(drawdown)),
            'time_underwater_pct': float(np.sum(drawdown < -0.01) / len(drawdown) * 100),
            'drawdown_periods': drawdown_periods
        }
    
    def _calculate_portfolio_drawdown_metrics(self) -> Dict[str, Any]:
        """Calculate drawdown metrics for portfolio."""
        if len(self.portfolio_history) < 2:
            return {}
        
        values = [p['value'] for p in self.portfolio_history]
        values_array = np.array(values)
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(values_array)
        
        # Calculate drawdown
        drawdown = (values_array - running_max) / running_max
        
        max_drawdown = float(np.min(drawdown))
        current_drawdown = float(drawdown[-1])
        
        # Probability of drawdown exceeding thresholds
        drawdown_probabilities = {
            '5%': float(np.sum(drawdown <= -0.05) / len(drawdown) * 100),
            '10%': float(np.sum(drawdown <= -0.10) / len(drawdown) * 100),
            '20%': float(np.sum(drawdown <= -0.20) / len(drawdown) * 100)
        }
        
        return {
            'current_drawdown': current_drawdown,
            'max_drawdown': max_drawdown,
            'average_drawdown': float(np.mean(drawdown[drawdown < 0])) if np.any(drawdown < 0) else 0.0,
            'drawdown_probabilities': drawdown_probabilities,
            'recovery_time_estimate': self._estimate_recovery_time(drawdown)
        }
    
    def _analyze_drawdown_periods(self, drawdown: np.ndarray) -> Dict[str, Any]:
        """Analyze distinct drawdown periods."""
        # Find drawdown periods (consecutive negative values)
        in_drawdown = drawdown < -0.01  # 1% threshold
        
        if not np.any(in_drawdown):
            return {'count': 0, 'avg_duration': 0, 'max_duration': 0}
        
        # Find start and end of drawdown periods
        starts = np.where(np.diff(np.concatenate(([False], in_drawdown))) == True)[0]
        ends = np.where(np.diff(np.concatenate((in_drawdown, [False]))) == -1)[0]
        
        # Ensure equal number of starts and ends
        min_len = min(len(starts), len(ends))
        if min_len == 0:
            return {'count': 0, 'avg_duration': 0, 'max_duration': 0}
        
        starts = starts[:min_len]
        ends = ends[:min_len]
        durations = ends - starts + 1
        
        return {
            'count': len(durations),
            'avg_duration': float(np.mean(durations)),
            'max_duration': int(np.max(durations)),
            'current_duration': int(durations[-1]) if in_drawdown[-1] and len(durations) > 0 else 0
        }
    
    def _estimate_recovery_time(self, drawdown: np.ndarray) -> int:
        """Estimate time to recover from current drawdown."""
        if drawdown[-1] >= -0.01:  # Not in significant drawdown
            return 0
        
        # Simple estimation based on historical recovery patterns
        recovery_times = []
        in_drawdown = drawdown < -0.01
        
        starts = np.where(np.diff(np.concatenate(([False], in_drawdown))) == True)[0]
        ends = np.where(np.diff(np.concatenate((in_drawdown, [False]))) == -1)[0]
        
        if len(starts) > 0 and len(ends) > 0:
            for start, end in zip(starts, ends):
                if end < len(drawdown) - 1:  # Complete recovery
                    recovery_times.append(end - start + 1)
        
        if recovery_times:
            return int(np.median(recovery_times))
        else:
            return 30  # Default estimate
    
    def _calculate_evt_metrics(self, returns: np.ndarray) -> Dict[str, Any]:
        """Calculate Extreme Value Theory metrics."""
        try:
            losses = -returns
            threshold = np.percentile(losses, 90)
            exceedances = losses[losses > threshold] - threshold
            
            if len(exceedances) < 10:
                return {'status': 'insufficient_data'}
            
            # Fit GPD
            shape, loc, scale = stats.genpareto.fit(exceedances, floc=0)
            
            # Calculate tail index and extreme quantiles
            return {
                'shape_parameter': float(shape),
                'scale_parameter': float(scale),
                'threshold': float(threshold),
                'tail_index': float(1/shape) if shape != 0 else np.inf,
                'exceedances_count': len(exceedances),
                'extreme_99_9_quantile': float(threshold + (scale/shape) * (((len(returns)/len(exceedances)) * 0.001)**(-shape) - 1)) if shape != 0 else np.nan
            }
            
        except Exception as e:
            self.logger.warning(f"EVT metrics calculation failed: {e}")
            return {'status': 'calculation_failed', 'error': str(e)}
    
    def _calculate_tail_metrics(self, returns: np.ndarray) -> Dict[str, float]:
        """Calculate additional tail risk metrics."""
        sorted_returns = np.sort(returns)
        n = len(returns)
        
        # Tail ratios
        left_tail_5 = np.mean(sorted_returns[:int(n*0.05)])
        left_tail_1 = np.mean(sorted_returns[:int(n*0.01)]) if int(n*0.01) > 0 else sorted_returns[0]
        center = np.mean(sorted_returns[int(n*0.25):int(n*0.75)])
        
        return {
            'left_tail_mean_5pct': float(left_tail_5),
            'left_tail_mean_1pct': float(left_tail_1),
            'tail_ratio_5pct': float(abs(left_tail_5 / center)) if center != 0 else 0,
            'tail_ratio_1pct': float(abs(left_tail_1 / center)) if center != 0 else 0,
            'beyond_var_95_count': int(np.sum(returns < -self._calculate_historical_var(returns, 0.95))),
            'beyond_var_99_count': int(np.sum(returns < -self._calculate_historical_var(returns, 0.99)))
        }
    
    def _calculate_correlation_risk(self) -> Dict[str, Any]:
        """Analyze correlation structure and tail dependence."""
        if len(self.return_history) < 3:
            return {'status': 'insufficient_assets'}
        
        # Get symbols (exclude PORTFOLIO)
        symbols = [s for s in self.return_history.keys() if s != 'PORTFOLIO']
        
        if len(symbols) < 2:
            return {'status': 'insufficient_assets'}
        
        # Align returns by timestamp (simplified - assumes same frequency)
        min_length = min(len(self.return_history[s]) for s in symbols)
        
        returns_matrix = []
        for symbol in symbols:
            returns = [r['return'] for r in self.return_history[symbol][-min_length:]]
            returns_matrix.append(returns)
        
        returns_df = pd.DataFrame(returns_matrix, index=symbols).T
        
        # Calculate correlation matrix
        correlation_matrix = returns_df.corr()
        
        # Tail correlation (correlation in extreme events)
        tail_correlations = {}
        for i, sym1 in enumerate(symbols):
            for j, sym2 in enumerate(symbols):
                if i < j:
                    tail_corr = self._calculate_tail_correlation(returns_df[sym1], returns_df[sym2])
                    tail_correlations[f"{sym1}_{sym2}"] = tail_corr
        
        return {
            'correlation_matrix': correlation_matrix.to_dict(),
            'avg_correlation': float(correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()),
            'max_correlation': float(correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].max()),
            'tail_correlations': tail_correlations,
            'diversification_ratio': self._calculate_diversification_ratio(returns_df)
        }
    
    def _calculate_tail_correlation(self, returns1: pd.Series, returns2: pd.Series, threshold_pct: float = 0.05) -> float:
        """Calculate correlation in tail events."""
        try:
            # Define tail events (bottom 5% for both series)
            thresh1 = returns1.quantile(threshold_pct)
            thresh2 = returns2.quantile(threshold_pct)
            
            # Find joint tail events
            tail_mask = (returns1 <= thresh1) & (returns2 <= thresh2)
            
            if tail_mask.sum() < 5:  # Insufficient tail events
                return np.nan
            
            return float(returns1[tail_mask].corr(returns2[tail_mask]))
            
        except Exception:
            return np.nan
    
    def _calculate_diversification_ratio(self, returns_df: pd.DataFrame) -> float:
        """Calculate portfolio diversification ratio."""
        try:
            weights = np.ones(len(returns_df.columns)) / len(returns_df.columns)  # Equal weights
            portfolio_vol = np.sqrt(weights @ returns_df.cov() @ weights)
            weighted_avg_vol = weights @ returns_df.std()
            
            return float(weighted_avg_vol / portfolio_vol) if portfolio_vol > 0 else 1.0
            
        except Exception:
            return 1.0
    
    def _calculate_risk_decomposition(self) -> Dict[str, Any]:
        """Decompose portfolio risk by component."""
        if len(self.portfolio_history) < 30:
            return {'status': 'insufficient_data'}
        
        # Get recent portfolio positions
        recent_positions = self.portfolio_history[-1]['positions']
        
        if not recent_positions:
            return {'status': 'no_position_data'}
        
        # Calculate marginal contributions to risk
        total_value = sum(recent_positions.values())
        weights = {symbol: value/total_value for symbol, value in recent_positions.items()}
        
        # Simplified risk decomposition
        risk_contributions = {}
        for symbol, weight in weights.items():
            if symbol in self.return_history and len(self.return_history[symbol]) >= 30:
                asset_returns = [r['return'] for r in self.return_history[symbol][-30:]]
                asset_vol = np.std(asset_returns)
                risk_contributions[symbol] = {
                    'weight': weight,
                    'volatility': float(asset_vol),
                    'risk_contribution': float(weight * asset_vol)  # Simplified
                }
        
        return risk_contributions
    
    def _calculate_risk_adjusted_returns(self, returns: np.ndarray) -> Dict[str, float]:
        """Calculate risk-adjusted return metrics."""
        if len(returns) == 0:
            return {}
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Sharpe ratio (assuming risk-free rate = 0 for simplicity)
        sharpe = float(mean_return / std_return) if std_return > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else std_return
        sortino = float(mean_return / downside_std) if downside_std > 0 else 0
        
        # Calmar ratio (return / max drawdown)
        if hasattr(self, 'tail_risk_summary') and 'portfolio' in self.tail_risk_summary:
            max_dd = abs(self.tail_risk_summary['portfolio'].get('drawdown_analysis', {}).get('max_drawdown', 0.01))
            calmar = float(mean_return / max_dd) if max_dd > 0 else 0
        else:
            calmar = 0
        
        return {
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar
        }
    
    def _perform_stress_tests(self) -> Dict[str, Any]:
        """Perform various stress test scenarios."""
        stress_results = {}
        
        # Market crash scenario (-30% market move)
        stress_results['market_crash_30pct'] = self._scenario_test(-0.30)
        
        # Volatility spike (2x current volatility)
        stress_results['volatility_spike_2x'] = self._volatility_stress_test(2.0)
        
        # Correlation breakdown (all correlations go to 1)
        stress_results['correlation_breakdown'] = self._correlation_stress_test()
        
        # Custom scenarios from config
        for scenario_name, scenario_params in self.stress_scenarios.items():
            stress_results[scenario_name] = self._custom_scenario_test(scenario_params)
        
        return stress_results
    
    def _scenario_test(self, market_shock: float) -> Dict[str, float]:
        """Test portfolio performance under market shock."""
        if not self.portfolio_history:
            return {'status': 'no_portfolio_data'}
        
        current_value = self.portfolio_value
        shocked_value = current_value * (1 + market_shock)
        
        return {
            'scenario': f'{market_shock*100:.0f}% market shock',
            'current_value': current_value,
            'shocked_value': shocked_value,
            'loss_amount': current_value - shocked_value,
            'loss_percentage': -market_shock * 100
        }
    
    def _volatility_stress_test(self, vol_multiplier: float) -> Dict[str, Any]:
        """Test under increased volatility conditions."""
        portfolio_returns = [r['return'] for r in self.return_history.get('PORTFOLIO', [])]
        
        if len(portfolio_returns) < 30:
            return {'status': 'insufficient_data'}
        
        current_vol = np.std(portfolio_returns)
        stressed_vol = current_vol * vol_multiplier
        
        # Estimate VaR under stressed volatility
        mean_return = np.mean(portfolio_returns)
        var_95_stressed = -(mean_return - 1.645 * stressed_vol)
        var_99_stressed = -(mean_return - 2.326 * stressed_vol)
        
        return {
            'scenario': f'{vol_multiplier}x volatility stress',
            'current_volatility': float(current_vol),
            'stressed_volatility': float(stressed_vol),
            'var_95_stressed': float(var_95_stressed),
            'var_99_stressed': float(var_99_stressed),
            'var_95_dollar': float(var_95_stressed * self.portfolio_value),
            'var_99_dollar': float(var_99_stressed * self.portfolio_value)
        }
    
    def _correlation_stress_test(self) -> Dict[str, Any]:
        """Test under correlation breakdown scenario."""
        # Simplified: assume all assets become perfectly correlated
        # In reality, this would require more sophisticated portfolio modeling
        
        symbols = [s for s in self.return_history.keys() if s != 'PORTFOLIO']
        
        if len(symbols) < 2:
            return {'status': 'insufficient_assets'}
        
        # Calculate current diversification benefit
        portfolio_returns = [r['return'] for r in self.return_history.get('PORTFOLIO', [])]
        
        if len(portfolio_returns) < 30:
            return {'status': 'insufficient_data'}
        
        current_portfolio_vol = np.std(portfolio_returns)
        
        # Estimate volatility if all correlations = 1 (no diversification)
        avg_asset_vol = np.mean([np.std([r['return'] for r in self.return_history[s][-30:]]) 
                                for s in symbols if len(self.return_history[s]) >= 30])
        
        return {
            'scenario': 'correlation breakdown (all correlations = 1)',
            'current_portfolio_volatility': float(current_portfolio_vol),
            'undiversified_volatility': float(avg_asset_vol),
            'diversification_loss': float(avg_asset_vol - current_portfolio_vol),
            'volatility_increase_pct': float((avg_asset_vol / current_portfolio_vol - 1) * 100) if current_portfolio_vol > 0 else 0
        }
    
    def _custom_scenario_test(self, scenario_params: Dict[str, Any]) -> Dict[str, Any]:
        """Run custom stress test scenario."""
        # Implementation would depend on scenario parameters
        # This is a placeholder for custom scenarios
        return {
            'scenario': 'custom',
            'parameters': scenario_params,
            'result': 'not_implemented'
        }
    
    def _generate_risk_alerts(self, risk_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate risk alerts based on calculated metrics."""
        alerts = []
        
        # Portfolio-level alerts
        portfolio_metrics = risk_metrics.get('portfolio', {})
        
        # VaR breach alert
        var_estimates = portfolio_metrics.get('var_estimates', {})
        if '95.0%' in var_estimates:
            var_95 = var_estimates['95.0%'].get('historical', 0)
            if var_95 > 0.05:  # 5% threshold
                alerts.append({
                    'type': 'high_var',
                    'severity': 'medium',
                    'message': f'Portfolio VaR(95%) is {var_95*100:.2f}%, exceeding 5% threshold',
                    'timestamp': datetime.now()
                })
        
        # Drawdown alert
        drawdown_metrics = portfolio_metrics.get('drawdown_analysis', {})
        current_drawdown = drawdown_metrics.get('current_drawdown', 0)
        if current_drawdown < -0.10:  # 10% drawdown threshold
            alerts.append({
                'type': 'high_drawdown',
                'severity': 'high',
                'message': f'Portfolio in {abs(current_drawdown)*100:.1f}% drawdown',
                'timestamp': datetime.now()
            })
        
        # Correlation alert
        correlation_analysis = risk_metrics.get('correlation_analysis', {})
        avg_correlation = correlation_analysis.get('avg_correlation', 0)
        if avg_correlation > 0.8:
            alerts.append({
                'type': 'high_correlation',
                'severity': 'medium',
                'message': f'High average correlation {avg_correlation:.2f} may reduce diversification benefits',
                'timestamp': datetime.now()
            })
        
        return alerts
    
    def get_risk_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary for risk management dashboard."""
        if not self.tail_risk_summary:
            return {'status': 'no_data'}
        
        portfolio_metrics = self.tail_risk_summary.get('portfolio', {})
        
        # Extract key metrics
        var_95 = portfolio_metrics.get('var_estimates', {}).get('95.0%', {}).get('historical', 0)
        cvar_95 = portfolio_metrics.get('cvar_estimates', {}).get('95.0%', {}).get('historical', 0)
        max_drawdown = portfolio_metrics.get('drawdown_analysis', {}).get('max_drawdown', 0)
        current_drawdown = portfolio_metrics.get('drawdown_analysis', {}).get('current_drawdown', 0)
        
        return {
            'timestamp': datetime.now(),
            'portfolio_value': self.portfolio_value,
            'key_metrics': {
                'var_95_pct': float(var_95 * 100),
                'var_95_dollar': float(var_95 * self.portfolio_value),
                'cvar_95_pct': float(cvar_95 * 100),
                'cvar_95_dollar': float(cvar_95 * self.portfolio_value),
                'max_drawdown_pct': float(abs(max_drawdown) * 100),
                'current_drawdown_pct': float(abs(current_drawdown) * 100)
            },
            'risk_level': self._assess_overall_risk_level(),
            'active_alerts': len(self.tail_risk_summary.get('risk_alerts', [])),
            'last_update': self.last_update
        }
    
    def _assess_overall_risk_level(self) -> str:
        """Assess overall portfolio risk level."""
        if not self.tail_risk_summary:
            return 'unknown'
        
        portfolio_metrics = self.tail_risk_summary.get('portfolio', {})
        var_95 = portfolio_metrics.get('var_estimates', {}).get('95.0%', {}).get('historical', 0)
        current_drawdown = abs(portfolio_metrics.get('drawdown_analysis', {}).get('current_drawdown', 0))
        
        # Simple risk assessment
        if var_95 > 0.10 or current_drawdown > 0.15:
            return 'high'
        elif var_95 > 0.05 or current_drawdown > 0.10:
            return 'medium'
        elif var_95 > 0.02 or current_drawdown > 0.05:
            return 'low'
        else:
            return 'very_low'