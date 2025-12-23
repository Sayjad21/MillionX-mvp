"""
Demand Forecasting Engine using Statistical Methods
Predicts product demand and recommends restocking
HACKATHON VERSION: Lightweight, Windows-friendly, no Prophet headaches

Usage:
    from forecasting import DemandForecaster
    forecaster = DemandForecaster()
    prediction = forecaster.predict_demand(product_id="PROD-123")

Author: MillionX Team
Phase: 3 (AI Core - Forecasting)
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging

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
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/millionx')
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


class DemandForecaster:
    """
    Statistical demand forecasting using Linear Regression + Moving Averages
    Simple, fast, and Windows-friendly for hackathon demo
    """
    
    def __init__(self):
        self.engine = engine
        self.forecast_days = int(os.getenv('FORECAST_DAYS', 7))
        self.min_history_days = int(os.getenv('MIN_HISTORY_DAYS', 14))  # Less strict
        
        logger.info("🔮 Demand Forecaster initialized (Statistical Mode)")
    
    def fetch_sales_history(
        self, 
        product_id: Optional[str] = None,
        category: Optional[str] = None,
        days: int = 30
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
        Predict future demand using Linear Regression + Moving Averages
        HACKATHON VERSION: Fast, simple, effective
        
        Args:
            product_id: Specific product to forecast
            category: Product category to forecast
        
        Returns:
            Dictionary with prediction results
        """
        try:
            # Fetch historical data
            df = self.fetch_sales_history(
                product_id=product_id,
                category=category,
                days=60  # Use 60 days for trend detection
            )
            
            if len(df) < self.min_history_days:
                return {
                    "success": False,
                    "error": f"Insufficient data: only {len(df)} days available (need {self.min_history_days})",
                    "product_id": product_id,
                    "category": category
                }
            
            # Prepare data for regression
            logger.info("🧠 Training Linear Regression model...")
            df['days_index'] = range(len(df))
            X = df[['days_index']].values
            y = df['y'].values
            
            # Train model
            model = LinearRegression()
            model.fit(X, y)
            
            # Make predictions
            future_days = np.array([[len(df) + i] for i in range(1, self.forecast_days + 1)])
            raw_predictions = model.predict(future_days)
            
            # Apply exponential moving average smoothing
            window = min(7, len(df))  # 7-day window or less if not enough data
            ema = df['y'].ewm(span=window).mean().iloc[-1]
            
            # Blend regression with EMA (60% regression, 40% EMA trend)
            trend_factor = 0.6
            predictions = (raw_predictions * trend_factor + ema * (1 - trend_factor)).clip(min=0)
            
            # Create forecast dataframe
            forecast_dates = [datetime.now().date() + timedelta(days=i) for i in range(1, self.forecast_days + 1)]
            predictions_df = pd.DataFrame({
                'date': [d.isoformat() for d in forecast_dates],  # Convert to ISO string
                'predicted_quantity': [safe_float(p, 0.0) for p in predictions]  # Convert to safe float
            })
            
            # Calculate metrics
            total_predicted = predictions.sum()
            avg_daily_demand = predictions.mean()
            recent_actual = df['y'].tail(7).mean()
            
            # Determine if restock needed
            # Logic: If predicted demand > 150% of recent average, recommend restock
            restock_threshold = recent_actual * 1.5
            restock_recommended = total_predicted > restock_threshold
            
            # Confidence score (based on data availability and trend stability)
            data_score = min(len(df) / 60.0, 1.0)
            std_val = df['y'].std()
            mean_val = df['y'].mean()
            if pd.isna(std_val) or mean_val == 0:
                variance_score = 0.5  # Default confidence if not enough data
            else:
                variance_score = 1.0 - min(std_val / (mean_val + 1), 1.0)
            confidence = (data_score + variance_score) / 2
            
            # Calculate R² score
            r_squared = model.score(X, y)
            
            result = {
                "success": True,
                "product_id": product_id,
                "category": category,
                "forecast_period_days": int(self.forecast_days),
                "predicted_demand": safe_float(total_predicted, 0.0),
                "avg_daily_demand": safe_float(avg_daily_demand, 0.0),
                "recent_avg_demand": safe_float(recent_actual, 0.0),
                "restock_recommended": bool(restock_recommended),
                "confidence_score": safe_float(confidence, 0.5),
                "predictions": predictions_df.to_dict('records'),
                "model_metrics": {
                    "training_days": int(len(df)),
                    "r_squared": safe_float(r_squared, 0.0),
                    "slope": safe_float(model.coef_[0], 0.0)
                }
            }
            
            logger.info(f"✅ Forecast complete: Predicted {total_predicted:.0f} units over {self.forecast_days} days")
            logger.info(f"📈 Restock recommended: {restock_recommended}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Forecasting error: {e}")
            return {
                "success": False,
                "error": str(e),
                "product_id": product_id,
                "category": category
            }
    
    def get_top_products(self, limit: int = 10) -> List[Dict]:
        """
        Get top-selling products for batch forecasting
        
        Args:
            limit: Number of top products to return
        
        Returns:
            List of product dictionaries
        """
        query = text("""
            SELECT 
                product_id,
                product_name,
                product_category,
                SUM(quantity) as total_sold,
                COUNT(*) as order_count
            FROM sales_history
            WHERE order_date >= :cutoff_date
            GROUP BY product_id, product_name, product_category
            ORDER BY total_sold DESC
            LIMIT :limit
        """)
        
        cutoff_date = datetime.now() - timedelta(days=30)
        df = pd.read_sql(
            query, 
            self.engine, 
            params={"cutoff_date": cutoff_date, "limit": limit}
        )
        
        return df.to_dict('records')
    
    def batch_forecast(self, limit: int = 5) -> List[Dict]:
        """
        Run forecasts for top products
        
        Args:
            limit: Number of products to forecast
        
        Returns:
            List of forecast results
        """
        logger.info(f"🔄 Running batch forecast for top {limit} products...")
        
        top_products = self.get_top_products(limit=limit)
        results = []
        
        for product in top_products:
            logger.info(f"📦 Forecasting: {product['product_name']} ({product['product_id']})")
            prediction = self.predict_demand(product_id=product['product_id'])
            prediction['product_name'] = product['product_name']
            results.append(prediction)
        
        logger.info(f"✅ Batch forecast complete: {len(results)} products")
        return results


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    forecaster = DemandForecaster()
    
    if len(sys.argv) > 1:
        # Forecast specific product
        product_id = sys.argv[1]
        result = forecaster.predict_demand(product_id=product_id)
        
    else:
        # Batch forecast top products
        print("\n" + "=" * 70)
        print("🔮 DEMAND FORECASTING - TOP PRODUCTS")
        print("=" * 70 + "\n")
        
        results = forecaster.batch_forecast(limit=5)
        
        for i, result in enumerate(results, 1):
            if result['success']:
                print(f"{i}. {result.get('product_name', 'Unknown')}")
                print(f"   Product ID: {result['product_id']}")
                print(f"   Predicted Demand: {result['predicted_demand']:.0f} units (next {result['forecast_period_days']} days)")
                print(f"   Avg Daily: {result['avg_daily_demand']:.1f} units/day")
                print(f"   Restock: {'✅ YES' if result['restock_recommended'] else '⏸️  Not needed'}")
                print(f"   Confidence: {result['confidence_score']:.0%}\n")
            else:
                print(f"{i}. {result.get('product_name', 'Unknown')}")
                print(f"   ❌ Error: {result['error']}\n")
        
        print("=" * 70)
