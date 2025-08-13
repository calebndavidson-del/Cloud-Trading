"""
Market Liquidity Predictor

Predicts market liquidity conditions using market microstructure signals
and machine learning techniques. Helps optimize trade timing and execution.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error


class LiquidityPredictor:
    """
    Predicts market liquidity conditions using market microstructure signals.
    
    Features:
    - Real-time liquidity prediction
    - Market microstructure feature extraction
    - Machine learning-based forecasting
    - Multi-timeframe analysis
    - Trading impact estimation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize liquidity predictor.
        
        Args:
            config: Configuration dictionary containing:
                - symbols: List of symbols to predict
                - prediction_horizon: Forecast horizon in minutes
                - feature_window: Historical window for features
                - model_type: ML model type ('rf', 'gb', 'ensemble')
                - retrain_interval: Model retraining frequency
        """
        self.config = config
        self.symbols = config.get('symbols', [])
        self.prediction_horizon = config.get('prediction_horizon', 5)  # minutes
        self.feature_window = config.get('feature_window', 60)  # minutes
        self.model_type = config.get('model_type', 'ensemble')
        self.retrain_interval = config.get('retrain_interval', 60)  # minutes
        
        # Data storage
        self.market_data_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.spread_data_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.order_flow_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Models and scalers
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.feature_importance: Dict[str, Dict[str, float]] = {}
        
        # Predictions
        self.current_predictions: Dict[str, Dict[str, Any]] = {}
        self.prediction_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=200))
        
        # Training data
        self.training_data: Dict[str, pd.DataFrame] = {}
        self.last_training_time: Dict[str, datetime] = {}
        
        self.logger = logging.getLogger(__name__)
        
    async def start_prediction_service(self, spread_monitor) -> None:
        """
        Start liquidity prediction service.
        
        Args:
            spread_monitor: SpreadMonitor instance for real-time data
        """
        self.spread_monitor = spread_monitor
        self.logger.info(f"Starting liquidity prediction for {len(self.symbols)} symbols")
        
        # Initialize models
        await self._initialize_models()
        
        # Start prediction loop
        while True:
            try:
                await self._update_predictions()
                await asyncio.sleep(60)  # Update every minute
            except Exception as e:
                self.logger.error(f"Error in prediction service: {e}")
                await asyncio.sleep(60)
    
    async def _initialize_models(self) -> None:
        """Initialize prediction models for all symbols."""
        for symbol in self.symbols:
            self.models[symbol] = self._create_model()
            self.scalers[symbol] = StandardScaler()
            self.last_training_time[symbol] = datetime.now() - timedelta(hours=1)  # Force initial training
            
        self.logger.info("Liquidity prediction models initialized")
    
    def _create_model(self) -> Any:
        """Create machine learning model based on configuration."""
        if self.model_type == 'rf':
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'gb':
            return GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        else:  # ensemble
            return {
                'rf': RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42),
                'gb': GradientBoostingRegressor(n_estimators=50, max_depth=4, learning_rate=0.1, random_state=42)
            }
    
    async def _update_predictions(self) -> None:
        """Update liquidity predictions for all symbols."""
        for symbol in self.symbols:
            try:
                # Collect recent data
                await self._collect_microstructure_data(symbol)
                
                # Check if model needs retraining
                if self._should_retrain_model(symbol):
                    await self._retrain_model(symbol)
                
                # Generate prediction
                prediction = await self._generate_prediction(symbol)
                
                if prediction:
                    self.current_predictions[symbol] = prediction
                    self.prediction_history[symbol].append(prediction)
                    
            except Exception as e:
                self.logger.error(f"Error updating prediction for {symbol}: {e}")
    
    async def _collect_microstructure_data(self, symbol: str) -> None:
        """Collect market microstructure data for prediction."""
        # Get current spread data
        if hasattr(self.spread_monitor, 'spread_history') and symbol in self.spread_monitor.spread_history:
            spread_data = list(self.spread_monitor.spread_history[symbol])
            if spread_data:
                self.spread_data_history[symbol].extend(spread_data[-10:])  # Last 10 observations
        
        # Simulate order flow data (in live trading, this would come from real order book)
        order_flow = self._simulate_order_flow_data(symbol)
        self.order_flow_history[symbol].append(order_flow)
        
        # Get market data
        market_data = await self._get_market_data(symbol)
        if market_data:
            self.market_data_history[symbol].append(market_data)
    
    def _simulate_order_flow_data(self, symbol: str) -> Dict[str, Any]:
        """
        Simulate order flow data for demonstration.
        
        In live trading, this would be replaced with real order book data.
        """
        timestamp = datetime.now()
        
        # Simulate realistic order flow patterns
        base_volume = np.random.lognormal(10, 1)
        buy_ratio = np.random.beta(2, 2)  # Tends toward 0.5 (balanced)
        
        order_flow = {
            'timestamp': timestamp,
            'total_volume': base_volume,
            'buy_volume': base_volume * buy_ratio,
            'sell_volume': base_volume * (1 - buy_ratio),
            'trade_count': max(1, int(np.random.poisson(10))),
            'avg_trade_size': base_volume / max(1, int(np.random.poisson(10))),
            'price_impact': np.random.normal(0, 0.001),  # Small random price impact
            'order_imbalance': (buy_ratio - 0.5) * 2  # -1 to 1 scale
        }
        
        return order_flow
    
    async def _get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current market data for symbol."""
        if hasattr(self.spread_monitor, 'quote_history') and symbol in self.spread_monitor.quote_history:
            quotes = list(self.spread_monitor.quote_history[symbol])
            if quotes:
                return quotes[-1]
        return None
    
    def _should_retrain_model(self, symbol: str) -> bool:
        """Check if model should be retrained."""
        if symbol not in self.last_training_time:
            return True
        
        time_since_training = datetime.now() - self.last_training_time[symbol]
        return time_since_training.total_seconds() > (self.retrain_interval * 60)
    
    async def _retrain_model(self, symbol: str) -> None:
        """Retrain prediction model for symbol."""
        try:
            # Prepare training data
            features, targets = self._prepare_training_data(symbol)
            
            if len(features) < 50:  # Insufficient data
                self.logger.warning(f"Insufficient data for training {symbol} model")
                return
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, targets, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scalers[symbol].fit_transform(X_train)
            X_test_scaled = self.scalers[symbol].transform(X_test)
            
            # Train model
            if isinstance(self.models[symbol], dict):  # Ensemble
                for model_name, model in self.models[symbol].items():
                    model.fit(X_train_scaled, y_train)
                    
                    # Calculate feature importance
                    if hasattr(model, 'feature_importances_'):
                        self.feature_importance[f"{symbol}_{model_name}"] = dict(
                            zip(self._get_feature_names(), model.feature_importances_)
                        )
            else:
                self.models[symbol].fit(X_train_scaled, y_train)
                
                if hasattr(self.models[symbol], 'feature_importances_'):
                    self.feature_importance[symbol] = dict(
                        zip(self._get_feature_names(), self.models[symbol].feature_importances_)
                    )
            
            # Evaluate model
            y_pred = await self._predict_with_model(symbol, X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            
            self.logger.info(f"Retrained {symbol} model - MSE: {mse:.4f}, MAE: {mae:.4f}")
            self.last_training_time[symbol] = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error retraining model for {symbol}: {e}")
    
    def _prepare_training_data(self, symbol: str) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data with features and targets."""
        features = []
        targets = []
        
        # Get historical data
        spread_history = list(self.spread_data_history[symbol])
        order_flow_history = list(self.order_flow_history[symbol])
        market_history = list(self.market_data_history[symbol])
        
        # Create feature vectors
        min_length = min(len(spread_history), len(order_flow_history), len(market_history))
        
        for i in range(10, min_length - self.prediction_horizon):  # Need history and future
            # Extract features for time i
            feature_vector = self._extract_features(
                spread_history[i-10:i],
                order_flow_history[i-10:i],
                market_history[i-10:i]
            )
            
            # Extract target (future liquidity condition)
            future_spread = spread_history[i + self.prediction_horizon] if i + self.prediction_horizon < len(spread_history) else spread_history[-1]
            target = self._calculate_liquidity_target(future_spread)
            
            features.append(feature_vector)
            targets.append(target)
        
        return np.array(features), np.array(targets)
    
    def _extract_features(self, spread_data: List[Dict], order_flow_data: List[Dict], market_data: List[Dict]) -> List[float]:
        """Extract features from historical data."""
        features = []
        
        # Spread-based features
        if spread_data:
            spreads = [s['spread_pct'] for s in spread_data]
            features.extend([
                np.mean(spreads),  # Average spread
                np.std(spreads),   # Spread volatility
                spreads[-1],       # Current spread
                max(spreads) - min(spreads),  # Spread range
                np.median(spreads)  # Median spread
            ])
        else:
            features.extend([0.1, 0.01, 0.1, 0.01, 0.1])  # Default values
        
        # Order flow features
        if order_flow_data:
            volumes = [o['total_volume'] for o in order_flow_data]
            imbalances = [o['order_imbalance'] for o in order_flow_data]
            impacts = [o['price_impact'] for o in order_flow_data]
            
            features.extend([
                np.mean(volumes),      # Average volume
                np.std(volumes),       # Volume volatility
                np.mean(imbalances),   # Average order imbalance
                np.std(imbalances),    # Imbalance volatility
                np.mean(impacts),      # Average price impact
                volumes[-1] if volumes else 0,  # Current volume
                imbalances[-1] if imbalances else 0  # Current imbalance
            ])
        else:
            features.extend([1000000, 100000, 0, 0.1, 0, 1000000, 0])
        
        # Market-based features
        if market_data:
            prices = [m.get('price', 100) for m in market_data]
            volumes = [m.get('volume', 1000000) for m in market_data if 'volume' in m]
            
            features.extend([
                np.std(prices) / np.mean(prices),  # Price volatility
                prices[-1],                       # Current price
                np.mean(volumes) if volumes else 1000000,  # Average volume
                len([p for p in prices[1:] if p > prices[prices.index(p)-1]]) / max(1, len(prices)-1)  # Up move ratio
            ])
        else:
            features.extend([0.02, 100, 1000000, 0.5])
        
        # Time-based features
        now = datetime.now()
        features.extend([
            now.hour / 24.0,           # Hour of day (normalized)
            now.weekday() / 6.0,       # Day of week (normalized)
            (now.hour >= 9 and now.hour <= 16),  # Market hours (boolean as int)
        ])
        
        return features
    
    def _get_feature_names(self) -> List[str]:
        """Get feature names for interpretation."""
        return [
            'avg_spread', 'spread_volatility', 'current_spread', 'spread_range', 'median_spread',
            'avg_volume', 'volume_volatility', 'avg_imbalance', 'imbalance_volatility', 'avg_impact',
            'current_volume', 'current_imbalance',
            'price_volatility', 'current_price', 'avg_market_volume', 'up_move_ratio',
            'hour_of_day', 'day_of_week', 'market_hours'
        ]
    
    def _calculate_liquidity_target(self, spread_data: Dict[str, Any]) -> float:
        """Calculate target liquidity score from spread data."""
        spread_pct = spread_data.get('spread_pct', 0.1)
        
        # Convert spread to liquidity score (inverse relationship)
        # Lower spreads = higher liquidity scores
        liquidity_score = max(0.0, 100.0 - (spread_pct * 1000))  # Scale appropriately
        return float(min(100.0, liquidity_score))
    
    async def _generate_prediction(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Generate liquidity prediction for symbol."""
        try:
            # Get recent data for features
            if (len(self.spread_data_history[symbol]) < 10 or
                len(self.order_flow_history[symbol]) < 10 or
                len(self.market_data_history[symbol]) < 10):
                return None
            
            # Extract current features
            spread_data = list(self.spread_data_history[symbol])[-10:]
            order_flow_data = list(self.order_flow_history[symbol])[-10:]
            market_data = list(self.market_data_history[symbol])[-10:]
            
            features = self._extract_features(spread_data, order_flow_data, market_data)
            features_array = np.array(features).reshape(1, -1)
            
            # Scale features
            if symbol in self.scalers and hasattr(self.scalers[symbol], 'mean_'):
                features_scaled = self.scalers[symbol].transform(features_array)
            else:
                features_scaled = features_array  # Use unscaled if scaler not fitted
            
            # Make prediction
            prediction = await self._predict_with_model(symbol, features_scaled)
            
            if prediction is not None:
                # Calculate confidence based on recent prediction accuracy
                confidence = self._calculate_prediction_confidence(symbol)
                
                return {
                    'symbol': symbol,
                    'timestamp': datetime.now(),
                    'prediction_horizon_minutes': self.prediction_horizon,
                    'predicted_liquidity_score': float(prediction[0]),
                    'confidence': confidence,
                    'current_spread_pct': spread_data[-1]['spread_pct'],
                    'current_liquidity_score': self._calculate_liquidity_target(spread_data[-1]),
                    'liquidity_trend': self._assess_liquidity_trend(symbol),
                    'features': dict(zip(self._get_feature_names(), features))
                }
            
        except Exception as e:
            self.logger.error(f"Error generating prediction for {symbol}: {e}")
        
        return None
    
    async def _predict_with_model(self, symbol: str, features: np.ndarray) -> Optional[np.ndarray]:
        """Make prediction using trained model."""
        if symbol not in self.models:
            return None
        
        try:
            if isinstance(self.models[symbol], dict):  # Ensemble
                predictions = []
                for model in self.models[symbol].values():
                    if hasattr(model, 'predict'):
                        pred = model.predict(features)
                        predictions.append(pred)
                
                if predictions:
                    # Average ensemble predictions
                    return np.mean(predictions, axis=0)
            else:
                if hasattr(self.models[symbol], 'predict'):
                    return self.models[symbol].predict(features)
        
        except Exception as e:
            self.logger.error(f"Error making prediction for {symbol}: {e}")
        
        return None
    
    def _calculate_prediction_confidence(self, symbol: str) -> float:
        """Calculate confidence in prediction based on recent accuracy."""
        if len(self.prediction_history[symbol]) < 5:
            return 0.5  # Neutral confidence
        
        # Simple confidence based on prediction consistency
        recent_predictions = list(self.prediction_history[symbol])[-10:]
        prediction_values = [p['predicted_liquidity_score'] for p in recent_predictions]
        
        # Higher consistency = higher confidence
        if len(prediction_values) > 1:
            volatility = np.std(prediction_values) / (np.mean(prediction_values) + 1e-6)
            confidence = max(0.1, 1.0 - min(1.0, volatility))
        else:
            confidence = 0.5
        
        return confidence
    
    def _assess_liquidity_trend(self, symbol: str) -> str:
        """Assess trend in predicted liquidity."""
        if len(self.prediction_history[symbol]) < 5:
            return 'unknown'
        
        recent_scores = [p['predicted_liquidity_score'] for p in list(self.prediction_history[symbol])[-5:]]
        
        if len(recent_scores) >= 3:
            early_avg = np.mean(recent_scores[:2])
            recent_avg = np.mean(recent_scores[-2:])
            
            if recent_avg > early_avg * 1.05:
                return 'improving'
            elif recent_avg < early_avg * 0.95:
                return 'deteriorating'
        
        return 'stable'
    
    def get_current_predictions(self) -> Dict[str, Dict[str, Any]]:
        """Get current liquidity predictions for all symbols."""
        return dict(self.current_predictions)
    
    def get_prediction_summary(self) -> Dict[str, Any]:
        """Get summary of current liquidity predictions."""
        if not self.current_predictions:
            return {'status': 'no_predictions'}
        
        predictions = list(self.current_predictions.values())
        
        avg_liquidity = np.mean([p['predicted_liquidity_score'] for p in predictions])
        avg_confidence = np.mean([p['confidence'] for p in predictions])
        
        trend_counts = defaultdict(int)
        for p in predictions:
            trend_counts[p['liquidity_trend']] += 1
        
        dominant_trend = max(trend_counts, key=trend_counts.get) if trend_counts else 'unknown'
        
        return {
            'timestamp': datetime.now(),
            'symbols_count': len(predictions),
            'avg_predicted_liquidity': avg_liquidity,
            'avg_confidence': avg_confidence,
            'dominant_trend': dominant_trend,
            'trend_distribution': dict(trend_counts),
            'market_liquidity_condition': self._assess_market_liquidity_condition(avg_liquidity)
        }
    
    def _assess_market_liquidity_condition(self, avg_liquidity: float) -> str:
        """Assess overall market liquidity condition."""
        if avg_liquidity >= 80:
            return 'excellent'
        elif avg_liquidity >= 60:
            return 'good'
        elif avg_liquidity >= 40:
            return 'moderate'
        elif avg_liquidity >= 20:
            return 'poor'
        else:
            return 'very_poor'
    
    def get_feature_importance(self, symbol: str = None) -> Dict[str, Dict[str, float]]:
        """Get feature importance for models."""
        if symbol:
            return {k: v for k, v in self.feature_importance.items() if symbol in k}
        return dict(self.feature_importance)
    
    def predict_optimal_trade_timing(self, symbol: str, trade_size: float) -> Dict[str, Any]:
        """
        Predict optimal timing for trade execution based on liquidity forecasts.
        
        Args:
            symbol: Symbol to trade
            trade_size: Trade size in dollars
            
        Returns:
            Dictionary with timing recommendations
        """
        if symbol not in self.current_predictions:
            return {'error': 'No prediction available for symbol'}
        
        current_pred = self.current_predictions[symbol]
        
        # Simple timing logic based on predicted liquidity
        predicted_score = current_pred['predicted_liquidity_score']
        confidence = current_pred['confidence']
        trend = current_pred['liquidity_trend']
        
        if predicted_score >= 70 and confidence >= 0.7:
            timing = 'execute_now'
            reason = 'High liquidity predicted with good confidence'
        elif trend == 'improving' and confidence >= 0.6:
            timing = 'wait_short'
            reason = 'Liquidity improving, wait 2-5 minutes'
        elif predicted_score <= 30:
            timing = 'wait_long'
            reason = 'Poor liquidity predicted, consider delaying'
        else:
            timing = 'execute_moderate'
            reason = 'Moderate conditions, proceed with caution'
        
        # Estimate trading costs
        estimated_cost_bp = max(5, 100 - predicted_score) * 0.5  # Rough estimation
        estimated_cost_dollar = trade_size * estimated_cost_bp / 10000
        
        return {
            'symbol': symbol,
            'timing_recommendation': timing,
            'reason': reason,
            'predicted_liquidity_score': predicted_score,
            'confidence': confidence,
            'trend': trend,
            'estimated_cost_bp': estimated_cost_bp,
            'estimated_cost_dollar': estimated_cost_dollar,
            'trade_size': trade_size
        }