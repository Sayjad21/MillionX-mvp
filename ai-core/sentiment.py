"""
VADER Sentiment Analysis Module
Replaces mock sentiment with real polarity scoring

Features:
- Compound sentiment scores (-1 to +1)
- Works with English and partial Bangla/Romanized text
- No API required, runs locally
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Initialize VADER analyzer
analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text: str) -> Tuple[str, float, Dict[str, float]]:
    """
    Analyze sentiment of text using VADER
    
    Args:
        text: Input text to analyze
        
    Returns:
        Tuple of (label, score, detailed_scores)
        - label: 'positive', 'negative', or 'neutral'
        - score: Compound score (-1 to +1)
        - detailed_scores: {'neg', 'neu', 'pos', 'compound'}
    """
    if not text or not isinstance(text, str):
        return 'neutral', 0.0, {'neg': 0.0, 'neu': 1.0, 'pos': 0.0, 'compound': 0.0}
    
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    
    # Classify based on compound score
    if compound >= 0.05:
        label = 'positive'
    elif compound <= -0.05:
        label = 'negative'
    else:
        label = 'neutral'
    
    return label, compound, scores


def batch_analyze_sentiments(texts: list) -> list:
    """
    Analyze sentiment for multiple texts
    
    Args:
        texts: List of text strings
        
    Returns:
        List of dicts with label, score, and details
    """
    results = []
    for text in texts:
        label, score, details = analyze_sentiment(text)
        results.append({
            'text': text[:100],  # First 100 chars for reference
            'label': label,
            'score': score,
            'details': details
        })
    return results


def calculate_aggregate_sentiment(texts: list) -> Dict[str, float]:
    """
    Calculate aggregate sentiment across multiple texts
    
    Args:
        texts: List of text strings
        
    Returns:
        Dictionary with aggregate metrics
    """
    if not texts:
        return {
            'average_compound': 0.0,
            'positive_ratio': 0.0,
            'negative_ratio': 0.0,
            'neutral_ratio': 0.0,
            'total_count': 0
        }
    
    results = batch_analyze_sentiments(texts)
    
    positive_count = sum(1 for label, _, _ in results if label == 'positive')
    negative_count = sum(1 for label, _, _ in results if label == 'negative')
    neutral_count = sum(1 for label, _, _ in results if label == 'neutral')
    
    total = len(results)
    avg_compound = sum(score for _, score, _ in results) / total
    
    return {
        'average_compound': round(avg_compound, 3),
        'positive_ratio': round(positive_count / total, 3),
        'negative_ratio': round(negative_count / total, 3),
        'neutral_ratio': round(neutral_count / total, 3),
        'total_count': total
    }


# Example usage
if __name__ == "__main__":
    # Test cases
    test_texts = [
        "This product is amazing! Best purchase ever!",
        "Terrible quality, waste of money",
        "It's okay, nothing special",
        "Bhalo quality kintu dam beshi",  # Good quality but price high (mixed Bangla)
        "Darun! Highly recommend!",  # Excellent! (Bangla)
    ]
    
    print("Individual Sentiment Analysis:")
    print("-" * 60)
    for text in test_texts:
        label, score, details = analyze_sentiment(text)
        print(f"Text: {text}")
        print(f"Label: {label}, Score: {score:.3f}")
        print(f"Details: {details}")
        print()
    
    print("\nAggregate Sentiment:")
    print("-" * 60)
    aggregate = calculate_aggregate_sentiment(test_texts)
    for key, value in aggregate.items():
        print(f"{key}: {value}")
