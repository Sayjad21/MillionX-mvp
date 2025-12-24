"""
Graph Analytics using NetworkX
Analyzes product-merchant relationships, co-purchase patterns, and product bundles

Features:
- Product co-purchase network
- Centrality analysis (PageRank, Betweenness, Degree)
- Bundle recommendations
- Community detection
- Works with PostgreSQL/SQLite

Author: MillionX Team (Phase 2 Enhanced)
"""

import os
from typing import Dict, List, Optional, Tuple
import pandas as pd
import networkx as nx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from collections import defaultdict
import logging

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


class ProductGraphAnalytics:
    """
    Analyzes product relationships using graph analytics
    FREE alternative to Neo4j with NetworkX
    """
    
    def __init__(self):
        self.engine = engine
        self.graph = nx.Graph()
        logger.info("📊 Product Graph Analytics initialized (NetworkX)")
    
    def build_copurchase_graph(self, min_frequency: int = 2) -> nx.Graph:
        """
        Build a graph of products that are frequently purchased together
        
        Args:
            min_frequency: Minimum number of times products must be bought together
        
        Returns:
            NetworkX Graph object
        """
        try:
            # Fetch co-purchase data (products bought in same order)
            query = text("""
                WITH product_pairs AS (
                    SELECT 
                        a.product_id as product_a,
                        b.product_id as product_b,
                        a.product_name as name_a,
                        b.product_name as name_b,
                        COUNT(*) as copurchase_count
                    FROM sales_history a
                    JOIN sales_history b ON a.order_id = b.order_id
                        AND a.product_id < b.product_id
                    GROUP BY a.product_id, b.product_id, a.product_name, b.product_name
                    HAVING COUNT(*) >= :min_freq
                )
                SELECT * FROM product_pairs
                ORDER BY copurchase_count DESC
            """)
            
            df = pd.read_sql(query, self.engine, params={"min_freq": min_frequency})
            
            if len(df) == 0:
                logger.warning("⚠️ No co-purchase patterns found")
                return self.graph
            
            # Build graph
            self.graph.clear()
            
            for _, row in df.iterrows():
                self.graph.add_edge(
                    row['product_a'],
                    row['product_b'],
                    weight=row['copurchase_count'],
                    name_a=row['name_a'],
                    name_b=row['name_b']
                )
            
            logger.info(f"📈 Built graph: {len(self.graph.nodes)} products, {len(self.graph.edges)} relationships")
            return self.graph
            
        except Exception as e:
            logger.error(f"❌ Graph build error: {e}")
            return self.graph
    
    def calculate_product_centrality(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate centrality metrics for products
        
        Returns:
            Dictionary with product_id -> {pagerank, betweenness, degree}
        """
        if len(self.graph.nodes) == 0:
            logger.warning("⚠️ Graph is empty, building...")
            self.build_copurchase_graph()
        
        if len(self.graph.nodes) == 0:
            return {}
        
        try:
            # Calculate centrality metrics
            pagerank = nx.pagerank(self.graph, weight='weight')
            betweenness = nx.betweenness_centrality(self.graph, weight='weight')
            degree = dict(self.graph.degree(weight='weight'))
            
            # Combine metrics
            centrality = {}
            for node in self.graph.nodes:
                centrality[node] = {
                    'pagerank': round(pagerank.get(node, 0), 4),
                    'betweenness': round(betweenness.get(node, 0), 4),
                    'degree': round(degree.get(node, 0), 2),
                    'importance_score': round(
                        pagerank.get(node, 0) * 0.5 + 
                        betweenness.get(node, 0) * 0.3 + 
                        (degree.get(node, 0) / max(degree.values())) * 0.2,
                        4
                    )
                }
            
            logger.info(f"✅ Calculated centrality for {len(centrality)} products")
            return centrality
            
        except Exception as e:
            logger.error(f"❌ Centrality calculation error: {e}")
            return {}
    
    def recommend_bundles(self, product_id: str, limit: int = 3) -> List[Dict]:
        """
        Recommend product bundles based on co-purchase patterns
        
        Args:
            product_id: Product to find bundles for
            limit: Maximum number of recommendations
        
        Returns:
            List of recommended products with scores
        """
        if len(self.graph.nodes) == 0:
            self.build_copurchase_graph()
        
        if product_id not in self.graph.nodes:
            logger.warning(f"⚠️ Product {product_id} not found in graph")
            return []
        
        try:
            # Get neighbors (products frequently bought together)
            neighbors = list(self.graph.neighbors(product_id))
            
            if not neighbors:
                return []
            
            # Calculate recommendation scores
            recommendations = []
            for neighbor in neighbors:
                edge_data = self.graph.get_edge_data(product_id, neighbor)
                weight = edge_data.get('weight', 1)
                
                # Get product info
                query = text("""
                    SELECT product_name, product_category, AVG(unit_price) as avg_price
                    FROM sales_history
                    WHERE product_id = :product_id
                    GROUP BY product_name, product_category
                    LIMIT 1
                """)
                
                result = pd.read_sql(query, self.engine, params={"product_id": neighbor})
                
                if len(result) > 0:
                    recommendations.append({
                        'product_id': neighbor,
                        'product_name': result.iloc[0]['product_name'],
                        'category': result.iloc[0]['product_category'],
                        'copurchase_frequency': int(weight),
                        'recommendation_score': round(weight / max([self.graph.get_edge_data(product_id, n).get('weight', 1) for n in neighbors]), 2),
                        'avg_price': round(float(result.iloc[0]['avg_price']), 2)
                    })
            
            # Sort by score and return top N
            recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
            
            logger.info(f"✅ Generated {len(recommendations[:limit])} bundle recommendations")
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"❌ Bundle recommendation error: {e}")
            return []
    
    def detect_product_communities(self) -> Dict[str, List[str]]:
        """
        Detect product communities (clusters of related products)
        
        Returns:
            Dictionary mapping community_id -> [product_ids]
        """
        if len(self.graph.nodes) == 0:
            self.build_copurchase_graph()
        
        if len(self.graph.nodes) == 0:
            return {}
        
        try:
            # Use Louvain community detection
            from networkx.algorithms import community
            
            communities = community.greedy_modularity_communities(self.graph, weight='weight')
            
            # Format output
            community_dict = {}
            for i, comm in enumerate(communities):
                community_dict[f"community_{i+1}"] = list(comm)
            
            logger.info(f"✅ Detected {len(community_dict)} product communities")
            return community_dict
            
        except Exception as e:
            logger.error(f"❌ Community detection error: {e}")
            return {}
    
    def get_graph_stats(self) -> Dict:
        """
        Get overall graph statistics
        
        Returns:
            Dictionary with graph metrics
        """
        if len(self.graph.nodes) == 0:
            self.build_copurchase_graph()
        
        if len(self.graph.nodes) == 0:
            return {"error": "Graph is empty"}
        
        try:
            stats = {
                'total_products': len(self.graph.nodes),
                'total_relationships': len(self.graph.edges),
                'average_degree': round(sum(dict(self.graph.degree()).values()) / len(self.graph.nodes), 2),
                'density': round(nx.density(self.graph), 4),
                'is_connected': nx.is_connected(self.graph),
                'number_of_components': nx.number_connected_components(self.graph)
            }
            
            # Add clustering coefficient
            if len(self.graph.nodes) > 2:
                stats['average_clustering'] = round(nx.average_clustering(self.graph, weight='weight'), 4)
            
            logger.info("✅ Generated graph statistics")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Graph stats error: {e}")
            return {"error": str(e)}


# Test if run directly
if __name__ == "__main__":
    analytics = ProductGraphAnalytics()
    
    print("Testing Product Graph Analytics...")
    print("=" * 60)
    
    # Build graph
    print("\n1. Building co-purchase graph...")
    graph = analytics.build_copurchase_graph(min_frequency=1)
    print(f"   Nodes: {len(graph.nodes)}, Edges: {len(graph.edges)}")
    
    # Calculate centrality
    print("\n2. Calculating product centrality...")
    centrality = analytics.calculate_product_centrality()
    if centrality:
        top_products = sorted(centrality.items(), key=lambda x: x[1]['importance_score'], reverse=True)[:3]
        for product_id, metrics in top_products:
            print(f"   {product_id}: Importance = {metrics['importance_score']}")
    
    # Recommend bundles
    if len(graph.nodes) > 0:
        print("\n3. Generating bundle recommendations...")
        first_product = list(graph.nodes)[0]
        bundles = analytics.recommend_bundles(first_product, limit=3)
        print(f"   Found {len(bundles)} bundles for {first_product}")
        for bundle in bundles:
            print(f"   - {bundle['product_name']} (score: {bundle['recommendation_score']})")
    
    # Graph stats
    print("\n4. Graph statistics:")
    stats = analytics.get_graph_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
