"""
Enhanced Demand Forecasting Engine using statsforecast
Replaces LinearRegression with AutoARIMA and AutoETS for better accuracy

Features:
- AutoARIMA: Automatic ARIMA model selection
- AutoETS: Exponential smoothing
- Seasonal decomposition
- Confidence intervals
- Works with PostgreSQL/SQLite

Author: MillionX Team (Phase 2 Enhanced)
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging

# statsforecast imports
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA, AutoETS, SeasonalNaive

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///millionx_ai.db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def safe_float(value, default=0.0):
    """Convert value to JSON-safe float, handling NaN and Inf"""
    try:
        val = float(value)
        if np.isnan(val) or np.isinf(val):
            return default
        return val
    except (ValueError, TypeError):
        return default


class EnhancedDemandForecaster:
    """
    Statistical demand forecasting using AutoARIMA and AutoETS
    More accurate than LinearRegression, still fast and free
    """
    
    def __init__(self):
        self.engine = engine
        self.forecast_days = int(os.getenv('FORECAST_DAYS', 7))
        self.min_history_days = int(os.getenv('MIN_HISTORY_DAYS', 14))
        
        # Initialize statsforecast models
        self.models = [
            AutoARIMA(season_length=7),  # Weekly seasonality
            AutoETS(season_length=7),    # Exponential smoothing
            SeasonalNaive(season_length=7)  # Baseline
        ]
        
        logger.info("🔮 Enhanced Demand Forecaster initialized (statsforecast)")
    
    def fetch_sales_history(
        self, 
        product_id: Optional[str] = None,
        category: Optional[str] = None,
        days: int = 60
    ) -> pd.DataFrame:
        """
        Fetch sales history from database
        
        Args:
            product_id: Specific product to fetch (optional)
            category: Product category to fetch (optional)
            days: Number of days of history to fetch
        
        Returns:
            DataFrame with columns: ds (date), y (quantity)
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        if product_id:
            query = text("""
                SELECT 
                    DATE(order_date) as ds,
                    SUM(quantity) as y
                FROM sales_history
                WHERE product_id = :product_id
                  AND order_date >= :cutoff_date
                GROUP BY DATE(order_date)
                ORDER BY ds
            """)
            params = {"product_id": product_id, "cutoff_date": cutoff_date}
            
        elif category:
            query = text("""
                SELECT 
                    DATE(order_date) as ds,
                    SUM(quantity) as y
                FROM sales_history
                WHERE product_category = :category
                  AND order_date >= :cutoff_date
                GROUP BY DATE(order_date)
                ORDER BY ds
            """)
            params = {"category": category, "cutoff_date": cutoff_date}
            
        else:
            # All products
            query = text("""
                SELECT 
                    DATE(order_date) as ds,
                    SUM(quantity) as y
                FROM sales_history
                WHERE order_date >= :cutoff_date
                GROUP BY DATE(order_date)
                ORDER BY ds
            """)
            params = {"cutoff_date": cutoff_date}
        
        df = pd.read_sql(query, self.engine, params=params)
        
        logger.info(f"📊 Fetched {len(df)} days of sales history")
        return df
    
    def predict_demand(
        self, 
        product_id: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict:
        """
        Predict future demand using statsforecast models
        
        Args:
            product_id: Specific product to forecast
            category: Product category to forecast
        
        Returns:
            Dictionary with prediction results
        """
        try:
            # Fetch historical data
            df = self.fetch_sales_history(product_id=product_id, category=category)
            
            if len(df) < self.min_history_days:
                logger.warning(f"⚠️ Insufficient data: {len(df)} days (need {self.min_history_days})")
                return {
                    "product_id": product_id or "aggregate",
                    "forecast": [],
                    "confidence": "low",
                    "error": "Insufficient historical data",
                    "model": "statsforecast"
                }
            
            # Prepare data for statsforecast
            df['unique_id'] = product_id or 'aggregate'
            df['ds'] = pd.to_datetime(df['ds'])
            df = df[['unique_id', 'ds', 'y']]
            
            # Fill missing dates with 0 sales
            date_range = pd.date_range(start=df['ds'].min(), end=df['ds'].max(), freq='D')
            full_df = pd.DataFrame({
                'unique_id': product_id or 'aggregate',
                'ds': date_range
            })
            df = full_df.merge(df, on=['unique_id', 'ds'], how='left')
            df['y'] = df['y'].fillna(0)
            
            # Initialize StatsForecast
            sf = StatsForecast(
                models=self.models,
                freq='D',
                n_jobs=1
            )
            
            # Fit and forecast
            forecasts = sf.forecast(df=df, h=self.forecast_days, level=[80, 95])
            
            # Extract best forecast (AutoARIMA usually best)
            forecast_values = forecasts['AutoARIMA'].values.tolist()
            
            # Calculate confidence metrics
            recent_sales = df['y'].tail(7).mean()
            forecast_mean = np.mean(forecast_values)
            
            # Determine confidence level
            if len(df) >= 30 and df['y'].std() < df['y'].mean():
                confidence = "high"
            elif len(df) >= 20:
                confidence = "medium"
            else:
                confidence = "low"
            
            # Generate recommendation
            if forecast_mean > recent_sales * 1.2:
                recommendation = "RESTOCK SOON - Demand increasing"
            elif forecast_mean < recent_sales * 0.7:
                recommendation = "REDUCE INVENTORY - Demand decreasing"
            else:
                recommendation = "MAINTAIN - Stable demand"
            
            # Format forecast
            forecast_dates = pd.date_range(
                start=df['ds'].max() + timedelta(days=1),
                periods=self.forecast_days,
                freq='D'
            )
            
            forecast_list = [
                {
                    "date": date.strftime('%Y-%m-%d'),
                    "predicted_quantity": round(safe_float(val), 2),
                    "confidence_80_lower": round(safe_float(forecasts['AutoARIMA-lo-80'].iloc[i]), 2),
                    "confidence_80_upper": round(safe_float(forecasts['AutoARIMA-hi-80'].iloc[i]), 2)
                }
                for i, (date, val) in enumerate(zip(forecast_dates, forecast_values))
            ]
            
            return {
                "product_id": product_id or "aggregate",
                "category": category,
                "forecast": forecast_list,
                "summary": {
                    "average_predicted_demand": round(safe_float(forecast_mean), 2),
                    "recent_average": round(safe_float(recent_sales), 2),
                    "trend": "increasing" if forecast_mean > recent_sales else "decreasing",
                    "confidence": confidence,
                    "recommendation": recommendation
                },
                "historical_stats": {
                    "days_of_data": len(df),
                    "total_sales": int(df['y'].sum()),
                    "avg_daily_sales": round(safe_float(df['y'].mean()), 2),
                    "max_daily_sales": int(df['y'].max()),
                    "volatility": round(safe_float(df['y'].std()), 2)
                },
                "model": "AutoARIMA",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Forecast error: {e}")
            return {
                "product_id": product_id or "aggregate",
                "error": str(e),
                "model": "statsforecast"
            }
    
    def batch_forecast(self, limit: int = 5) -> List[Dict]:
        """
        Forecast top N products by sales volume
        
        Args:
            limit: Number of top products to forecast
        
        Returns:
            List of forecast dictionaries
        """
        try:
            # Get top products by sales
            query = text("""
                SELECT product_id, product_name, product_category, SUM(quantity) as total_quantity
                FROM sales_history
                WHERE order_date >= :cutoff_date
                GROUP BY product_id, product_name, product_category
                ORDER BY total_quantity DESC
                LIMIT :limit
            """)
            
            cutoff_date = datetime.now() - timedelta(days=60)
            results = pd.read_sql(query, self.engine, params={"cutoff_date": cutoff_date, "limit": limit})
            
            forecasts = []
            for _, row in results.iterrows():
                forecast = self.predict_demand(product_id=row['product_id'])
                forecast['product_name'] = row['product_name']
                forecast['category'] = row['product_category']
                forecasts.append(forecast)
            
            logger.info(f"✅ Generated {len(forecasts)} forecasts")
            return forecasts
            
        except Exception as e:
            logger.error(f"❌ Batch forecast error: {e}")
            return []


# Maintain backward compatibility
DemandForecaster = EnhancedDemandForecaster


# Test if run directly
if __name__ == "__main__":
    forecaster = EnhancedDemandForecaster()
    
    # Test batch forecast
    print("Testing Enhanced Demand Forecasting...")
    print("=" * 60)
    
    forecasts = forecaster.batch_forecast(limit=3)
    
    for forecast in forecasts:
        print(f"\nProduct: {forecast.get('product_name', 'Unknown')}")
        print(f"Confidence: {forecast.get('summary', {}).get('confidence', 'N/A')}")
        print(f"Recommendation: {forecast.get('summary', {}).get('recommendation', 'N/A')}")
        print(f"Forecast days: {len(forecast.get('forecast', []))}")
