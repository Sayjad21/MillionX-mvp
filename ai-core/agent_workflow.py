"""
AI Agent Orchestrator - HACKATHON SIMPLIFIED VERSION
Multi-step reasoning for inventory decisions WITHOUT LangGraph

Usage:
    python agent_workflow.py

Author: MillionX Team
Phase: 3 (AI Core - Agent Swarm)
"""

import os
from typing import Dict, Any, List
from forecasting import DemandForecaster
from dotenv import load_dotenv
import logging
import json
import pandas as pd
from datetime import datetime

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# SIMPLIFIED AGENTS (No LangGraph)
# ============================================================================

class AnalystAgent:
    """
    Analyst Agent: Analyzes sales data and generates forecasts
    """
    
    def __init__(self):
        self.forecaster = DemandForecaster()
        logger.info("📊 Analyst Agent initialized")
    
    def analyze(self, product_id: str = None, product_name: str = None) -> Dict[str, Any]:
        """
        Analyze product and generate demand forecast
        """
        logger.info(f"📊 Analyst: Analyzing product {product_id or 'batch'}...")
        
        try:
            # Run forecast
            forecast = self.forecaster.predict_demand(product_id=product_id)
            
            if forecast['success']:
                logger.info(f"✅ Analyst: Forecast complete - {forecast['predicted_demand']:.0f} units predicted")
                return {
                    'success': True,
                    'product_id': product_id,
                    'product_name': product_name,
                    'forecast': forecast
                }
            else:
                logger.error(f"❌ Analyst: Forecast failed - {forecast['error']}")
                return {
                    'success': False,
                    'error': forecast['error']
                }
            
        except Exception as e:
            logger.error(f"❌ Analyst: Error - {e}")
            return {
                'success': False,
                'error': str(e)
            }


class AdvisorAgent:
    """
    Advisor Agent: Generates natural language recommendations
    Simple rule-based system (no LLM needed for hackathon)
    """
    
    def __init__(self):
        logger.info("💡 Advisor Agent initialized (Rule-based mode)")
    
    def advise(self, analysis_result: Dict[str, Any]) -> str:
        """
        Generate inventory recommendation based on forecast
        """
        if not analysis_result['success']:
            return f"❌ Unable to provide advice: {analysis_result.get('error', 'Unknown error')}"
        
        forecast = analysis_result['forecast']
        product_name = analysis_result.get('product_name', 'Product')
        
        # Rule-based recommendation
        predicted = forecast['predicted_demand']
        days = forecast['forecast_period_days']
        restock = forecast['restock_recommended']
        confidence = forecast['confidence_score']
        avg_daily = forecast['avg_daily_demand']
        
        logger.info(f"💡 Advisor: Generating recommendation for {product_name}...")
        
        if restock:
            urgency = "🚨 URGENT" if predicted > forecast['recent_avg_demand'] * 2 else "⚠️ RECOMMENDED"
            advice = (
                f"{urgency} - Restock {product_name}!\n"
                f"📊 Forecast: {predicted:.0f} units over next {days} days\n"
                f"📈 Daily demand: {avg_daily:.1f} units/day\n"
                f"💡 Action: Order {int(predicted * 1.2):.0f} units (20% buffer)\n"
                f"🎯 Confidence: {confidence:.0%}"
            )
        else:
            advice = (
                f"✅ {product_name} inventory is stable\n"
                f"📊 Expected demand: {predicted:.0f} units over {days} days\n"
                f"📉 Daily demand: {avg_daily:.1f} units/day\n"
                f"💡 Action: Monitor, no immediate restock needed\n"
                f"🎯 Confidence: {confidence:.0%}"
            )
        
        logger.info(f"✅ Advisor: Recommendation generated")
        return advice


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

class InventoryCopilot:
    """
    Main orchestrator that runs Analyst → Advisor pipeline
    SIMPLIFIED VERSION: No LangGraph needed
    """
    
    def __init__(self):
        self.analyst = AnalystAgent()
        self.advisor = AdvisorAgent()
        logger.info("🤖 Inventory Copilot initialized")
    
    def process(self, product_id: str = None, product_name: str = None) -> Dict[str, Any]:
        """
        Run full analysis pipeline for a product
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🤖 Processing: {product_name or product_id or 'Batch Products'}")
        logger.info(f"{'='*70}\n")
        
        # Step 1: Analyst runs forecast
        analysis = self.analyst.analyze(product_id=product_id, product_name=product_name)
        
        # Step 2: Advisor generates recommendation
        advice = self.advisor.advise(analysis)
        
        result = {
            'product_id': product_id,
            'product_name': product_name,
            'analysis': analysis,
            'recommendation': advice,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ Processing complete")
        logger.info(f"{'='*70}\n")
        
        return result
    
    def process_batch(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Run analysis for top products
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 BATCH PROCESSING: Top {limit} Products")
        logger.info(f"{'='*70}\n")
        
        # Get top products (returns a list)
        top_products = self.analyst.forecaster.get_top_products(limit=limit)
        
        if not top_products:
            logger.error("❌ No products found in database")
            return []
        
        results = []
        # FIXED: Handle list instead of DataFrame
        for product in top_products:  # Removed .iterrows()
            # product is now an item from the list
            if isinstance(product, dict):
                product_id = product.get('product_id')
                product_name = product.get('product_name')
            elif isinstance(product, tuple):
                # Assuming (product_id, product_name, ...) tuple
                product_id = product[0] if len(product) > 0 else None
                product_name = product[1] if len(product) > 1 else None
            else:
                logger.error(f"❌ Unexpected product format: {product}")
                continue
            
            result = self.process(
                product_id=product_id,
                product_name=product_name
            )
            results.append(result)
        
        logger.info(f"✅ Processed {len(results)} products")
        return results


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Command-line interface"""
    import sys
    
    copilot = InventoryCopilot()
    
    if len(sys.argv) > 1:
        # Single product mode
        product_id = sys.argv[1]
        result = copilot.process(product_id=product_id)
        
        print(f"\n{'='*70}")
        print(f"📊 RECOMMENDATION")
        print(f"{'='*70}")
        print(result['recommendation'])
        print(f"{'='*70}\n")
    else:
        # Batch mode
        results = copilot.process_batch(limit=5)
        
        print(f"\n{'='*70}")
        print(f"📊 BATCH RECOMMENDATIONS")
        print(f"{'='*70}\n")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['product_name'] or result['product_id']}")
            print("-" * 70)
            print(result['recommendation'])
            print()


if __name__ == "__main__":
    main()
