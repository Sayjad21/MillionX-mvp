"""
Integration Test Script for Phase 3 AI Core
Tests the complete pipeline: Kafka -> Database -> Forecasting -> Agents -> API

Run this AFTER rebuilding containers with:
    docker-compose up -d --build fastapi
"""

import requests
import time
import sys
from colorama import Fore, Style, init

init(autoreset=True)

FASTAPI_URL = "http://localhost:8000"

def print_test(name, status, message):
    """Pretty print test results"""
    icon = "✅" if status else "❌"
    color = Fore.GREEN if status else Fore.RED
    print(f"{icon} {color}{name}{Style.RESET_ALL}: {message}")

def test_health_check():
    """Test 1: Verify FastAPI is running"""
    try:
        response = requests.get(f"{FASTAPI_URL}/health", timeout=5)
        success = response.status_code == 200
        print_test("Health Check", success, f"Status {response.status_code}")
        return success
    except Exception as e:
        print_test("Health Check", False, str(e))
        return False

def test_ai_available():
    """Test 2: Check if AI Core is loaded"""
    try:
        response = requests.get(f"{FASTAPI_URL}/api/v1/inventory/forecast?limit=1", timeout=10)
        data = response.json()
        
        if "error" in data and "not connected" in data.get("error", "").lower():
            print_test("AI Core Loading", False, "AI Core not found - check volume mount")
            return False
        
        success = response.status_code == 200
        print_test("AI Core Loading", success, "Copilot initialized")
        return success
    except Exception as e:
        print_test("AI Core Loading", False, str(e))
        return False

def test_batch_forecast():
    """Test 3: Batch forecast (top 3 products)"""
    try:
        response = requests.get(f"{FASTAPI_URL}/api/v1/inventory/forecast?limit=3", timeout=15)
        data = response.json()
        
        if response.status_code != 200:
            print_test("Batch Forecast", False, f"Status {response.status_code}")
            return False
        
        products = data.get("products", [])
        count = len(products)
        
        if count == 0:
            print_test("Batch Forecast", False, "No products returned")
            return False
        
        print_test("Batch Forecast", True, f"Forecasted {count} products")
        
        # Print sample output
        for i, p in enumerate(products[:2], 1):
            product_name = p.get('product_name', p.get('product_id', 'Unknown'))
            recommendation = p.get('recommendation', 'N/A')[:60]
            print(f"   {i}. {product_name}: {recommendation}...")
        
        return True
    except Exception as e:
        print_test("Batch Forecast", False, str(e))
        return False

def test_single_forecast():
    """Test 4: Single product forecast"""
    try:
        # Use PROD-130 (Samsung Galaxy S24)
        response = requests.get(f"{FASTAPI_URL}/api/v1/inventory/forecast?product_id=PROD-130", timeout=10)
        data = response.json()
        
        if response.status_code != 200:
            print_test("Single Forecast", False, f"Status {response.status_code}")
            return False
        
        recommendation = data.get("recommendation", "")
        if not recommendation:
            print_test("Single Forecast", False, "No recommendation returned")
            return False
        
        print_test("Single Forecast", True, f"PROD-130 analyzed")
        print(f"   Recommendation: {recommendation[:80]}...")
        
        return True
    except Exception as e:
        print_test("Single Forecast", False, str(e))
        return False

def test_risk_score():
    """Test 5: Legacy COD Shield still works"""
    try:
        response = requests.post(
            f"{FASTAPI_URL}/api/v1/risk-score",
            json={
                "order_id": "TEST-001",
                "merchant_id": "DEMO",
                "customer_phone": "+8801712345678",
                "delivery_address": {
                    "area": "Dhanmondi",
                    "city": "Dhaka",
                    "postal_code": "1205"
                },
                "order_details": {
                    "total_amount": 500,
                    "currency": "BDT",
                    "items_count": 2,
                    "is_first_order": False
                },
                "timestamp": "2025-12-24T10:00:00Z"
            },
            timeout=10
        )
        
        data = response.json()
        success = response.status_code == 200 and "risk_score" in data
        risk_score = data.get("risk_score", "N/A")
        
        print_test("COD Shield API", success, f"Risk score: {risk_score}")
        return success
    except Exception as e:
        print_test("COD Shield API", False, str(e))
        return False

def main():
    print("\n" + "="*60)
    print("🚀 PHASE 3 INTEGRATION TEST")
    print("="*60 + "\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("AI Core Loading", test_ai_available),
        ("Batch Forecast", test_batch_forecast),
        ("Single Forecast", test_single_forecast),
        ("Legacy COD Shield", test_risk_score)
    ]
    
    results = []
    
    for name, test_func in tests:
        print(f"\n🔄 Running: {name}...")
        results.append(test_func())
        time.sleep(1)  # Avoid rate limiting
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print(f"{Fore.GREEN}🎉 ALL TESTS PASSED! Integration complete.{Style.RESET_ALL}")
        print("\n✅ Ready for demo! Try:")
        print("   • WhatsApp: Send 'forecast' to bot")
        print("   • API: curl http://localhost:8000/api/v1/inventory/forecast")
        return 0
    else:
        print(f"{Fore.YELLOW}⚠️ Some tests failed. Check logs above.{Style.RESET_ALL}")
        print("\n🔧 Troubleshooting:")
        print("   • Is FastAPI running? docker ps")
        print("   • Rebuild: docker-compose up -d --build fastapi")
        print("   • Check logs: docker logs millionx-fastapi")
        print("   • Is ai-core mounted? docker exec millionx-fastapi ls -la /ai-core")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}")
        sys.exit(130)
