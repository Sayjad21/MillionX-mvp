"""
Haggling Engine - PriceShift & Digital Twin Negotiation
Phase 3 Implementation

Features:
1. PriceShift: Dynamic pricing based on demand elasticity and competitor analysis
2. Haggling Twin: Monte Carlo simulation for negotiation outcomes
3. Counter-offer Generator: Natural language negotiation responses

Author: MillionX Team
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import random
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PriceStrategy(Enum):
    AGGRESSIVE = "aggressive"      # Maximize profit, risk losing customer
    BALANCED = "balanced"          # Balance profit and conversion
    CONSERVATIVE = "conservative"  # Prioritize conversion, accept lower margins


@dataclass
class PricePoint:
    """Represents a price point with conversion probability"""
    price: float
    conversion_prob: float
    expected_profit: float
    margin_pct: float


@dataclass
class NegotiationResult:
    """Result of a simulated negotiation"""
    original_price: float
    final_price: float
    discount_pct: float
    deal_closed: bool
    rounds: int
    customer_satisfaction: float


class PriceShiftEngine:
    """
    Dynamic Pricing Engine using demand elasticity and market signals
    
    Core algorithms:
    - Price elasticity of demand estimation
    - Competitor price indexing
    - Time-based surge/discount pricing
    - Weather-adjusted pricing (monsoon discounts, summer surge)
    """
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://millionx:millionx123@postgres:5432/millionx")
        self.engine = create_engine(self.db_url)
        
        # Default elasticity coefficients by category
        self.elasticity_map = {
            "Electronics": -1.8,      # Highly elastic - price sensitive
            "Fashion": -1.5,          # Moderately elastic
            "Food & Groceries": -0.5, # Inelastic - essential goods
            "Beauty": -1.2,           # Moderately elastic
            "Home & Living": -1.0,    # Unit elastic
            "default": -1.3
        }
        
        # Seasonal multipliers (Bangladesh context)
        self.seasonal_factors = {
            "eid": 1.15,           # Eid ul-Fitr/Adha premium
            "pohela_boishakh": 1.10,  # Bengali New Year
            "winter": 1.05,        # Winter season
            "monsoon": 0.95,       # Rainy season discount
            "regular": 1.0
        }
        
        logger.info("💰 PriceShift Engine initialized")
    
    def get_demand_elasticity(self, product_id: str, category: str = None) -> float:
        """
        Calculate price elasticity of demand for a product
        Uses historical sales data to estimate how demand changes with price
        
        Returns: elasticity coefficient (negative value, typically -0.5 to -2.5)
        """
        try:
            with self.engine.connect() as conn:
                # Get historical price-quantity data
                query = text("""
                    SELECT 
                        unit_price,
                        SUM(quantity) as total_qty,
                        COUNT(*) as order_count
                    FROM sales_history
                    WHERE product_id = :product_id
                    GROUP BY unit_price
                    ORDER BY unit_price
                """)
                result = conn.execute(query, {"product_id": product_id})
                rows = result.fetchall()
                
                if len(rows) >= 2:
                    # Calculate point elasticity between price points
                    prices = [float(r[0]) for r in rows]
                    quantities = [int(r[1]) for r in rows]
                    
                    # Use midpoint elasticity formula
                    p1, p2 = prices[0], prices[-1]
                    q1, q2 = quantities[0], quantities[-1]
                    
                    if p1 != p2 and q1 + q2 > 0:
                        pct_change_q = (q2 - q1) / ((q1 + q2) / 2)
                        pct_change_p = (p2 - p1) / ((p1 + p2) / 2)
                        
                        if pct_change_p != 0:
                            elasticity = pct_change_q / pct_change_p
                            return max(-3.0, min(-0.1, elasticity))  # Clamp to reasonable range
                
                # Fallback to category-based estimate
                return self.elasticity_map.get(category, self.elasticity_map["default"])
                
        except Exception as e:
            logger.warning(f"Elasticity calculation failed: {e}")
            return self.elasticity_map.get(category, self.elasticity_map["default"])
    
    def get_competitor_price(self, product_id: str) -> Optional[float]:
        """
        Get competitor price for a product (simulated for hackathon)
        In production, this would integrate with Daraz/AliExpress APIs
        """
        try:
            with self.engine.connect() as conn:
                # Get our average price
                query = text("""
                    SELECT AVG(unit_price) as avg_price
                    FROM sales_history
                    WHERE product_id = :product_id
                """)
                result = conn.execute(query, {"product_id": product_id})
                row = result.fetchone()
                
                if row and row[0]:
                    our_price = float(row[0])
                    # Simulate competitor price (typically 5-15% lower for similar products)
                    variation = random.uniform(-0.15, 0.05)
                    competitor_price = our_price * (1 + variation)
                    return round(competitor_price, 2)
                    
        except Exception as e:
            logger.warning(f"Competitor price lookup failed: {e}")
        
        return None
    
    def get_seasonal_factor(self) -> Tuple[str, float]:
        """
        Get current seasonal pricing factor based on Bangladesh calendar
        """
        now = datetime.now()
        month = now.month
        day = now.day
        
        # Eid ul-Fitr (varies by lunar calendar, approximate)
        # Pohela Boishakh: April 14
        # Winter: December-February
        # Monsoon: June-September
        
        if month == 4 and 10 <= day <= 20:
            return "pohela_boishakh", self.seasonal_factors["pohela_boishakh"]
        elif month in [12, 1, 2]:
            return "winter", self.seasonal_factors["winter"]
        elif month in [6, 7, 8, 9]:
            return "monsoon", self.seasonal_factors["monsoon"]
        else:
            return "regular", self.seasonal_factors["regular"]
    
    def calculate_optimal_price(
        self,
        product_id: str,
        current_price: float,
        cost: float,
        category: str = None,
        strategy: PriceStrategy = PriceStrategy.BALANCED
    ) -> Dict[str, Any]:
        """
        Calculate optimal price using demand elasticity and market factors
        
        Args:
            product_id: Product identifier
            current_price: Current selling price
            cost: Product cost (for margin calculation)
            category: Product category for elasticity lookup
            strategy: Pricing strategy to apply
            
        Returns:
            Optimal price recommendation with confidence
        """
        # Get elasticity
        elasticity = self.get_demand_elasticity(product_id, category)
        
        # Get competitor price
        competitor_price = self.get_competitor_price(product_id)
        
        # Get seasonal factor
        season, seasonal_mult = self.get_seasonal_factor()
        
        # Calculate markup based on elasticity
        # Higher elasticity (more negative) = lower markup
        # Formula: optimal_markup = -1 / (1 + elasticity)
        optimal_markup = -1 / (1 + elasticity) if elasticity != -1 else 0.5
        optimal_markup = max(0.1, min(2.0, optimal_markup))  # Clamp to 10%-200%
        
        # Calculate base optimal price
        base_optimal = cost * (1 + optimal_markup)
        
        # Apply seasonal adjustment
        seasonal_optimal = base_optimal * seasonal_mult
        
        # Apply strategy modifier
        strategy_mods = {
            PriceStrategy.AGGRESSIVE: 1.1,
            PriceStrategy.BALANCED: 1.0,
            PriceStrategy.CONSERVATIVE: 0.9
        }
        strategy_optimal = seasonal_optimal * strategy_mods[strategy]
        
        # Competitor adjustment (don't be more than 10% higher)
        if competitor_price:
            max_price = competitor_price * 1.10
            final_optimal = min(strategy_optimal, max_price)
        else:
            final_optimal = strategy_optimal
        
        # Calculate metrics
        margin = (final_optimal - cost) / final_optimal * 100
        price_change = (final_optimal - current_price) / current_price * 100
        
        # Confidence based on data quality
        confidence = 0.7 if competitor_price else 0.5
        
        return {
            "product_id": product_id,
            "current_price": round(current_price, 2),
            "optimal_price": round(final_optimal, 2),
            "price_change_pct": round(price_change, 1),
            "expected_margin_pct": round(margin, 1),
            "elasticity": round(elasticity, 2),
            "competitor_price": competitor_price,
            "season": season,
            "seasonal_factor": seasonal_mult,
            "strategy": strategy.value,
            "confidence": confidence,
            "recommendation": self._generate_price_recommendation(
                current_price, final_optimal, margin, competitor_price
            )
        }
    
    def _generate_price_recommendation(
        self,
        current: float,
        optimal: float,
        margin: float,
        competitor: Optional[float]
    ) -> str:
        """Generate natural language recommendation"""
        diff = optimal - current
        diff_pct = (diff / current) * 100
        
        if abs(diff_pct) < 2:
            return "Current price is optimal. No change recommended."
        elif diff_pct > 0:
            msg = f"Increase price by Tk {abs(diff):.0f} ({diff_pct:.0f}%) to maximize margin."
            if margin > 30:
                msg += " Healthy margin expected."
        else:
            msg = f"Decrease price by Tk {abs(diff):.0f} ({abs(diff_pct):.0f}%) to boost conversions."
            if competitor:
                msg += f" Competitor pricing at Tk {competitor:.0f}."
        
        return msg


class HagglingTwin:
    """
    Digital Twin for Negotiation Simulation
    
    Runs Monte Carlo simulations to predict negotiation outcomes
    before applying discounts. Finds the optimal counter-offer.
    """
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://millionx:millionx123@postgres:5432/millionx")
        self.engine = create_engine(self.db_url)
        
        # Customer archetypes with behavior profiles
        self.customer_profiles = {
            "price_sensitive": {
                "weight": 0.4,
                "max_accept_premium": 0.05,   # Will accept up to 5% above their target
                "walk_away_threshold": 0.15,   # Walks away if >15% above target
                "patience_rounds": 2           # Gives up after 2 rounds
            },
            "quality_focused": {
                "weight": 0.3,
                "max_accept_premium": 0.20,
                "walk_away_threshold": 0.35,
                "patience_rounds": 4
            },
            "bargain_hunter": {
                "weight": 0.2,
                "max_accept_premium": 0.0,
                "walk_away_threshold": 0.10,
                "patience_rounds": 3
            },
            "impulse_buyer": {
                "weight": 0.1,
                "max_accept_premium": 0.30,
                "walk_away_threshold": 0.50,
                "patience_rounds": 1
            }
        }
        
        logger.info("🤖 Haggling Twin initialized")
    
    def get_historical_negotiations(self, product_id: str = None) -> pd.DataFrame:
        """
        Get historical sales data to infer negotiation patterns
        """
        try:
            with self.engine.connect() as conn:
                if product_id:
                    query = text("""
                        SELECT 
                            product_id,
                            product_name,
                            unit_price,
                            quantity,
                            customer_region,
                            order_date
                        FROM sales_history
                        WHERE product_id = :product_id
                        ORDER BY order_date DESC
                        LIMIT 100
                    """)
                    result = conn.execute(query, {"product_id": product_id})
                else:
                    query = text("""
                        SELECT 
                            product_id,
                            product_name,
                            unit_price,
                            quantity,
                            customer_region,
                            order_date
                        FROM sales_history
                        ORDER BY order_date DESC
                        LIMIT 500
                    """)
                    result = conn.execute(query)
                
                df = pd.DataFrame(result.fetchall(), columns=[
                    'product_id', 'product_name', 'unit_price', 
                    'quantity', 'customer_region', 'order_date'
                ])
                
                # Convert Decimal to float for numpy compatibility
                if 'unit_price' in df.columns:
                    df['unit_price'] = df['unit_price'].astype(float)
                
                return df
                
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return pd.DataFrame()
    
    def simulate_single_negotiation(
        self,
        asking_price: float,
        customer_target: float,
        profile: Dict[str, Any],
        min_acceptable: float
    ) -> NegotiationResult:
        """
        Simulate a single negotiation between merchant and customer
        """
        current_offer = asking_price
        rounds = 0
        max_rounds = profile["patience_rounds"] + 1
        
        # Ensure customer_target is valid
        if customer_target <= 0:
            customer_target = asking_price * 0.8
        
        while rounds < max_rounds:
            rounds += 1
            
            # Customer evaluates current offer
            premium_over_target = (current_offer - customer_target) / customer_target
            
            # Customer accepts if within their tolerance
            max_accept = profile["max_accept_premium"]
            if premium_over_target <= max_accept:
                if max_accept > 0:
                    satisfaction = 1.0 - (premium_over_target / max_accept) * 0.5
                else:
                    satisfaction = 1.0 if premium_over_target <= 0 else 0.5
                return NegotiationResult(
                    original_price=asking_price,
                    final_price=current_offer,
                    discount_pct=((asking_price - current_offer) / asking_price) * 100 if asking_price > 0 else 0,
                    deal_closed=True,
                    rounds=rounds,
                    customer_satisfaction=max(0.5, min(1.0, satisfaction))
                )
            
            # Customer walks away if too expensive
            if premium_over_target > profile["walk_away_threshold"]:
                return NegotiationResult(
                    original_price=asking_price,
                    final_price=0,
                    discount_pct=0,
                    deal_closed=False,
                    rounds=rounds,
                    customer_satisfaction=0.0
                )
            
            # Merchant makes counter-offer (reduce by 5-10%)
            reduction = random.uniform(0.05, 0.10)
            new_offer = current_offer * (1 - reduction)
            
            # Don't go below minimum acceptable
            if new_offer < min_acceptable:
                # Final offer at minimum
                current_offer = min_acceptable
                if premium_over_target <= max_accept:
                    return NegotiationResult(
                        original_price=asking_price,
                        final_price=current_offer,
                        discount_pct=((asking_price - current_offer) / asking_price) * 100 if asking_price > 0 else 0,
                        deal_closed=True,
                        rounds=rounds,
                        customer_satisfaction=0.6
                    )
            else:
                current_offer = new_offer
        
        # Ran out of rounds - no deal
        return NegotiationResult(
            original_price=asking_price,
            final_price=0,
            discount_pct=0,
            deal_closed=False,
            rounds=rounds,
            customer_satisfaction=0.0
        )
    
    def run_simulation(
        self,
        product_id: str,
        asking_price: float,
        cost: float,
        num_simulations: int = 1000
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for negotiation outcomes
        
        Args:
            product_id: Product being negotiated
            asking_price: Initial asking price
            cost: Product cost (to determine min acceptable)
            num_simulations: Number of simulations to run (default 1000)
            
        Returns:
            Simulation results with optimal pricing strategy
        """
        # Minimum acceptable price (at least 10% margin)
        min_acceptable = cost * 1.10
        
        # Get historical data for calibration
        historical = self.get_historical_negotiations(product_id)
        
        # Calibrate customer targets based on historical prices
        if not historical.empty and 'unit_price' in historical.columns:
            avg_historical = float(historical['unit_price'].mean())
            price_std = float(historical['unit_price'].std()) or avg_historical * 0.1
        else:
            avg_historical = asking_price * 0.85
            price_std = asking_price * 0.1
        
        results = []
        
        for _ in range(num_simulations):
            # Randomly select customer profile
            profile_name = random.choices(
                list(self.customer_profiles.keys()),
                weights=[p["weight"] for p in self.customer_profiles.values()]
            )[0]
            profile = self.customer_profiles[profile_name]
            
            # Customer's target price (normally distributed around historical)
            customer_target = max(
                min_acceptable * 0.9,  # Won't go below near-cost
                np.random.normal(avg_historical, price_std)
            )
            
            # Run negotiation
            result = self.simulate_single_negotiation(
                asking_price, customer_target, profile, min_acceptable
            )
            results.append({
                "profile": profile_name,
                "target": customer_target,
                **result.__dict__
            })
        
        # Analyze results
        df_results = pd.DataFrame(results)
        
        closed_deals = df_results[df_results['deal_closed'] == True]
        lost_deals = df_results[df_results['deal_closed'] == False]
        
        if len(closed_deals) > 0:
            avg_final_price = closed_deals['final_price'].mean()
            avg_discount = closed_deals['discount_pct'].mean()
            avg_satisfaction = closed_deals['customer_satisfaction'].mean()
            avg_rounds = closed_deals['rounds'].mean()
        else:
            avg_final_price = 0
            avg_discount = 0
            avg_satisfaction = 0
            avg_rounds = 0
        
        conversion_rate = len(closed_deals) / num_simulations
        expected_revenue_per_100 = len(closed_deals) / num_simulations * 100 * avg_final_price if avg_final_price else 0
        
        # Find optimal starting price
        # Test different asking prices and find the one with best expected revenue
        price_tests = [asking_price * m for m in [0.85, 0.90, 0.95, 1.0, 1.05, 1.10]]
        best_price = asking_price
        best_expected_revenue = expected_revenue_per_100
        
        for test_price in price_tests:
            test_results = []
            for _ in range(100):  # Quick test with 100 sims
                profile_name = random.choices(
                    list(self.customer_profiles.keys()),
                    weights=[p["weight"] for p in self.customer_profiles.values()]
                )[0]
                profile = self.customer_profiles[profile_name]
                customer_target = max(min_acceptable * 0.9, np.random.normal(avg_historical, price_std))
                result = self.simulate_single_negotiation(test_price, customer_target, profile, min_acceptable)
                test_results.append(result)
            
            test_closed = [r for r in test_results if r.deal_closed]
            test_revenue = (len(test_closed) / 100) * 100 * (sum(r.final_price for r in test_closed) / len(test_closed) if test_closed else 0)
            
            if test_revenue > best_expected_revenue:
                best_expected_revenue = test_revenue
                best_price = test_price
        
        return {
            "product_id": product_id,
            "asking_price": round(asking_price, 2),
            "simulations_run": num_simulations,
            "results": {
                "conversion_rate": round(conversion_rate, 3),
                "avg_final_price": round(avg_final_price, 2),
                "avg_discount_pct": round(avg_discount, 1),
                "avg_negotiation_rounds": round(avg_rounds, 1),
                "customer_satisfaction": round(avg_satisfaction, 2),
                "deals_closed": len(closed_deals),
                "deals_lost": len(lost_deals)
            },
            "expected_revenue_per_100_customers": round(expected_revenue_per_100, 2),
            "optimal_asking_price": round(best_price, 2),
            "optimal_expected_revenue": round(best_expected_revenue, 2),
            "by_customer_profile": df_results.groupby('profile').agg({
                'deal_closed': 'mean',
                'final_price': 'mean',
                'discount_pct': 'mean'
            }).round(2).to_dict('index'),
            "recommendation": self._generate_negotiation_strategy(
                asking_price, best_price, conversion_rate, avg_discount
            )
        }
    
    def _generate_negotiation_strategy(
        self,
        current_ask: float,
        optimal_ask: float,
        conversion: float,
        avg_discount: float
    ) -> str:
        """Generate natural language negotiation strategy"""
        if conversion < 0.3:
            return (
                f"⚠️ Low conversion ({conversion:.0%}). Consider starting at Tk {optimal_ask:.0f} "
                f"and be prepared to offer up to {avg_discount:.0f}% discount."
            )
        elif conversion > 0.7:
            return (
                f"✅ Strong conversion ({conversion:.0%}). You can start higher at Tk {optimal_ask:.0f}. "
                f"Most customers accept with minimal negotiation."
            )
        else:
            return (
                f"📊 Balanced market ({conversion:.0%} conversion). "
                f"Optimal starting price: Tk {optimal_ask:.0f}. "
                f"Prepare counter-offers around {avg_discount:.0f}% discount."
            )
    
    def generate_counter_offer(
        self,
        asking_price: float,
        customer_offer: float,
        cost: float,
        round_number: int = 1
    ) -> Dict[str, Any]:
        """
        Generate a smart counter-offer for real-time negotiation
        
        This powers the "Haggling Engine" natural language negotiation
        """
        min_price = cost * 1.10  # 10% minimum margin
        
        # Calculate the gap
        gap = asking_price - customer_offer
        gap_pct = (gap / asking_price) * 100
        
        # Determine counter-offer based on round and gap
        if gap_pct <= 5:
            # Small gap - accept or minimal counter
            counter = customer_offer
            message = f"Deal! I'll accept Tk {counter:.0f}. 🤝"
            accept = True
        elif gap_pct <= 15:
            # Medium gap - meet in the middle
            counter = (asking_price + customer_offer) / 2
            if counter < min_price:
                counter = min_price
                message = f"Can't go lower than Tk {counter:.0f}. Final offer - best quality guaranteed! 💯"
            else:
                message = f"Can't do {customer_offer:.0f}, but Tk {counter:.0f} works for you? Fair deal! 🎯"
            accept = False
        elif gap_pct <= 30:
            # Large gap - counter higher
            counter = customer_offer + (gap * 0.7)
            if counter < min_price:
                counter = min_price
            message = f"Tk {customer_offer:.0f} is too low bhai. How about Tk {counter:.0f}? Premium quality! ⭐"
            accept = False
        else:
            # Very large gap - firm counter
            counter = asking_price * 0.90  # 10% off max
            if counter < min_price:
                counter = min_price
            message = f"I understand you want a deal. Tk {counter:.0f} is my best - can't go lower. 🏪"
            accept = False
        
        # Add quantity incentive for larger gaps
        quantity_message = ""
        if gap_pct > 10 and not accept:
            quantity_discount = counter * 0.95  # 5% more off for 2+
            quantity_message = f" Or get 2 for Tk {quantity_discount * 2:.0f} - better value!"
        
        margin = ((counter - cost) / counter) * 100 if counter > 0 else 0
        
        return {
            "customer_offer": round(customer_offer, 2),
            "counter_offer": round(counter, 2),
            "discount_from_asking": round(((asking_price - counter) / asking_price) * 100, 1),
            "margin_pct": round(margin, 1),
            "accept_deal": accept,
            "message": message + quantity_message,
            "negotiation_round": round_number,
            "next_move": "close_deal" if accept else "await_response"
        }


# Singleton instances
price_shift = PriceShiftEngine()
haggling_twin = HagglingTwin()


def get_optimal_price(product_id: str, current_price: float, cost: float, category: str = None) -> Dict:
    """Convenience function for price optimization"""
    return price_shift.calculate_optimal_price(product_id, current_price, cost, category)


def run_negotiation_simulation(product_id: str, asking_price: float, cost: float, simulations: int = 1000) -> Dict:
    """Convenience function for negotiation simulation"""
    return haggling_twin.run_simulation(product_id, asking_price, cost, simulations)


def get_counter_offer(asking_price: float, customer_offer: float, cost: float, round_num: int = 1) -> Dict:
    """Convenience function for counter-offer generation"""
    return haggling_twin.generate_counter_offer(asking_price, customer_offer, cost, round_num)


if __name__ == "__main__":
    # Test the engines
    print("\n" + "="*60)
    print("🧪 TESTING PRICESHIFT ENGINE")
    print("="*60)
    
    result = get_optimal_price(
        product_id="PROD-001",
        current_price=2500,
        cost=1800,
        category="Electronics"
    )
    print(f"\nOptimal Price Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")
    
    print("\n" + "="*60)
    print("🧪 TESTING HAGGLING TWIN (1000 simulations)")
    print("="*60)
    
    sim_result = run_negotiation_simulation(
        product_id="PROD-001",
        asking_price=2500,
        cost=1800,
        simulations=1000
    )
    print(f"\nSimulation Result:")
    print(f"  Conversion Rate: {sim_result['results']['conversion_rate']:.1%}")
    print(f"  Avg Final Price: Tk {sim_result['results']['avg_final_price']:.0f}")
    print(f"  Avg Discount: {sim_result['results']['avg_discount_pct']:.0f}%")
    print(f"  Optimal Starting Price: Tk {sim_result['optimal_asking_price']:.0f}")
    print(f"  Recommendation: {sim_result['recommendation']}")
    
    print("\n" + "="*60)
    print("🧪 TESTING COUNTER-OFFER GENERATION")
    print("="*60)
    
    counter = get_counter_offer(
        asking_price=2500,
        customer_offer=2000,
        cost=1800,
        round_num=1
    )
    print(f"\nCounter-Offer Result:")
    print(f"  Customer: Tk {counter['customer_offer']:.0f}")
    print(f"  Our Counter: Tk {counter['counter_offer']:.0f}")
    print(f"  Message: {counter['message']}")
