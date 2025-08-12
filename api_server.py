"""
FastAPI server for the Cloud Trading Bot.
Designed for deployment behind AWS API Gateway or as an ECS container.
"""
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cloud Trading Bot API",
    description="API for the cloud-native trading bot with AWS integration",
    version="1.0.0"
)

# CORS middleware for API Gateway
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class MarketDataRequest(BaseModel):
    symbols: List[str]
    include_trends: bool = True

class TradeRequest(BaseModel):
    symbol: str
    action: str  # 'buy' or 'sell'
    shares: int
    price: Optional[float] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    environment: str

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        environment=os.getenv("ENV", "development")
    )

# Market data endpoints
@app.get("/api/market-data")
async def get_market_data(symbols: str = "AAPL,GOOGL,MSFT"):
    """
    Fetch current market data for specified symbols.
    
    Args:
        symbols: Comma-separated list of stock symbols
    
    Returns:
        Market data for the requested symbols
    """
    try:
        from backend.data_collector import fetch_market_data
        
        symbol_list = [s.strip() for s in symbols.split(',')]
        logger.info(f"Fetching market data for symbols: {symbol_list}")
        
        market_data = fetch_market_data(symbol_list)
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": market_data
        }
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/market-data")
async def post_market_data(request: MarketDataRequest):
    """
    Fetch market data for specified symbols via POST request.
    
    Args:
        request: Market data request with symbols and options
    
    Returns:
        Market data for the requested symbols
    """
    try:
        from backend.data_collector import fetch_market_data, fetch_market_trends
        
        logger.info(f"Fetching market data for symbols: {request.symbols}")
        
        market_data = fetch_market_data(request.symbols)
        response = {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": market_data
        }
        
        if request.include_trends:
            trends = fetch_market_trends()
            response["trends"] = trends
        
        return response
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trends")
async def get_market_trends():
    """
    Fetch current market trends.
    
    Returns:
        Market trend data
    """
    try:
        from backend.data_collector import fetch_market_trends
        
        logger.info("Fetching market trends")
        
        trends = fetch_market_trends()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": trends
        }
    except Exception as e:
        logger.error(f"Error fetching market trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Trading endpoints
@app.post("/api/trades")
async def execute_trade(request: TradeRequest, background_tasks: BackgroundTasks):
    """
    Execute a trade (paper trading mode).
    
    Args:
        request: Trade request with symbol, action, and shares
        background_tasks: FastAPI background tasks
    
    Returns:
        Trade execution result
    """
    try:
        from backend.paper_trader import execute_paper_trade
        
        logger.info(f"Executing trade: {request.action} {request.shares} shares of {request.symbol}")
        
        # Execute paper trade
        trade_data = {
            "symbol": request.symbol,
            "action": request.action,
            "shares": request.shares,
            "price": request.price
        }
        
        result = execute_paper_trade(trade_data)
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "trade_id": result.get("trade_id"),
            "result": result
        }
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trades")
async def get_trades(limit: int = 10):
    """
    Get recent trades.
    
    Args:
        limit: Maximum number of trades to return
    
    Returns:
        List of recent trades
    """
    try:
        # This would typically fetch from DynamoDB
        # For now, return a placeholder response
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "trades": [],
            "message": "Trade history would be retrieved from DynamoDB"
        }
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration endpoints
@app.get("/api/config")
async def get_config():
    """
    Get current bot configuration.
    
    Returns:
        Bot configuration
    """
    try:
        from backend.config import get_config
        
        config = get_config()
        
        # Remove sensitive information
        safe_config = {
            "environment": config.get("env"),
            "trading": {
                "enabled": config.get("trading", {}).get("enabled", False),
                "paper_trading": config.get("trading", {}).get("paper_trading", True),
                "default_symbols": config.get("trading", {}).get("default_symbols", [])
            },
            "features": config.get("features", {}),
            "logging": {
                "level": config.get("logging", {}).get("level", "INFO")
            }
        }
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "config": safe_config
        }
    except Exception as e:
        logger.error(f"Error fetching config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Strategy and optimization endpoints
@app.post("/api/optimize")
async def optimize_strategy(background_tasks: BackgroundTasks):
    """
    Trigger strategy optimization.
    
    Args:
        background_tasks: FastAPI background tasks
    
    Returns:
        Optimization status
    """
    try:
        logger.info("Starting strategy optimization")
        
        # Add optimization task to background
        def run_optimization():
            try:
                from backend.optimizer import optimize_strategy
                from backend.data_collector import fetch_market_data
                from backend.config import get_config
                
                config = get_config()
                symbols = config['trading']['default_symbols']
                market_data = fetch_market_data(symbols)
                
                if 'error' not in market_data:
                    result = optimize_strategy(market_data, n_trials=5)
                    logger.info(f"Optimization completed: {result}")
                else:
                    logger.error("Optimization failed: No market data available")
            except Exception as e:
                logger.error(f"Background optimization failed: {e}")
        
        background_tasks.add_task(run_optimization)
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Strategy optimization started in background"
        }
    except Exception as e:
        logger.error(f"Error starting optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AWS Lambda handler for API Gateway
def lambda_handler(event, context):
    """
    AWS Lambda handler for API Gateway integration.
    
    Args:
        event: API Gateway event
        context: Lambda context
    
    Returns:
        API Gateway response
    """
    import json
    from mangum import Mangum
    
    handler = Mangum(app)
    return handler(event, context)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": "Endpoint not found",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting API server on {host}:{port}")
    
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=os.getenv("ENV", "development") == "development",
        log_level="info"
    )