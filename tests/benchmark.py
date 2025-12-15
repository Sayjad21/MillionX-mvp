"""
Performance Benchmark Script for COD Shield API
Tests response time, throughput, and accuracy under load
"""
import requests
import time
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

BASE_URL = "http://localhost:8000"

# Test scenarios
TEST_SCENARIOS = {
    "low_risk": {
        "order_id": "BENCH-LOW-{i}",
        "merchant_id": "MERCH-BENCH",
        "customer_phone": "+8801700000000",
        "delivery_address": {
            "area": "Gulshan",
            "city": "Dhaka",
            "postal_code": "1212"
        },
        "order_details": {
            "total_amount": 500,
            "currency": "BDT",
            "items_count": 1,
            "is_first_order": False
        },
        "timestamp": "2025-12-15T10:00:00Z"
    },
    "medium_risk": {
        "order_id": "BENCH-MED-{i}",
        "merchant_id": "MERCH-BENCH",
        "customer_phone": "+8801700000001",
        "delivery_address": {
            "area": "Mirpur",
            "city": "Dhaka",
            "postal_code": "1216"
        },
        "order_details": {
            "total_amount": 1500,
            "currency": "BDT",
            "items_count": 3,
            "is_first_order": True
        },
        "timestamp": "2025-12-15T10:00:00Z"
    },
    "high_risk": {
        "order_id": "BENCH-HIGH-{i}",
        "merchant_id": "MERCH-BENCH",
        "customer_phone": "+8801799999999",
        "delivery_address": {
            "area": "Unknown",
            "city": "Dhaka",
            "postal_code": ""
        },
        "order_details": {
            "total_amount": 2500,
            "currency": "BDT",
            "items_count": 5,
            "is_first_order": True
        },
        "timestamp": "2025-12-15T10:00:00Z"
    }
}


def single_request(scenario_name: str, scenario_data: dict, index: int) -> Dict:
    """Execute a single API request and measure performance"""
    # Customize order_id for uniqueness
    payload = json.loads(json.dumps(scenario_data))
    payload["order_id"] = payload["order_id"].format(i=index)
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/risk-score",
            json=payload,
            timeout=5
        )
        elapsed_ms = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            return {
                "scenario": scenario_name,
                "success": True,
                "status_code": response.status_code,
                "response_time_ms": elapsed_ms,
                "api_processing_time_ms": data.get("processing_time_ms", 0),
                "risk_score": data.get("risk_score", 0),
                "risk_level": data.get("risk_level", "UNKNOWN")
            }
        else:
            return {
                "scenario": scenario_name,
                "success": False,
                "status_code": response.status_code,
                "response_time_ms": elapsed_ms,
                "error": response.text[:100]
            }
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "scenario": scenario_name,
            "success": False,
            "status_code": 0,
            "response_time_ms": elapsed_ms,
            "error": str(e)[:100]
        }


def benchmark_sequential(iterations: int = 100):
    """Benchmark API with sequential requests"""
    print(f"\n{'='*70}")
    print(f"🔄 SEQUENTIAL BENCHMARK ({iterations} requests per scenario)")
    print(f"{'='*70}\n")
    
    for scenario_name, scenario_data in TEST_SCENARIOS.items():
        print(f"Testing {scenario_name.upper()} scenario...")
        results = []
        
        for i in range(iterations):
            result = single_request(scenario_name, scenario_data, i)
            results.append(result)
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i + 1}/{iterations} requests")
        
        analyze_results(scenario_name, results)


def benchmark_concurrent(iterations: int = 100, workers: int = 10):
    """Benchmark API with concurrent requests"""
    print(f"\n{'='*70}")
    print(f"⚡ CONCURRENT BENCHMARK ({iterations} requests, {workers} workers)")
    print(f"{'='*70}\n")
    
    for scenario_name, scenario_data in TEST_SCENARIOS.items():
        print(f"Testing {scenario_name.upper()} scenario...")
        results = []
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(single_request, scenario_name, scenario_data, i)
                for i in range(iterations)
            ]
            
            completed = 0
            for future in as_completed(futures):
                results.append(future.result())
                completed += 1
                if completed % 20 == 0:
                    print(f"  Progress: {completed}/{iterations} requests")
        
        analyze_results(scenario_name, results)


def analyze_results(scenario_name: str, results: List[Dict]):
    """Analyze and display benchmark results"""
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    if not successful:
        print(f"❌ All requests failed for {scenario_name}")
        return
    
    response_times = [r["response_time_ms"] for r in successful]
    api_times = [r["api_processing_time_ms"] for r in successful]
    risk_scores = [r["risk_score"] for r in successful]
    
    # Calculate statistics
    avg_response = statistics.mean(response_times)
    median_response = statistics.median(response_times)
    p95_response = sorted(response_times)[int(len(response_times) * 0.95)]
    p99_response = sorted(response_times)[int(len(response_times) * 0.99)]
    min_response = min(response_times)
    max_response = max(response_times)
    
    avg_api = statistics.mean(api_times)
    avg_risk_score = statistics.mean(risk_scores)
    
    success_rate = (len(successful) / len(results)) * 100
    
    # Display results
    print(f"\n📊 Results for {scenario_name.upper()}:")
    print(f"  Success Rate: {success_rate:.1f}% ({len(successful)}/{len(results)})")
    print(f"\n  Response Times (including network):")
    print(f"    Average:  {avg_response:6.2f} ms")
    print(f"    Median:   {median_response:6.2f} ms")
    print(f"    P95:      {p95_response:6.2f} ms {'✅' if p95_response < 100 else '❌'}")
    print(f"    P99:      {p99_response:6.2f} ms")
    print(f"    Min:      {min_response:6.2f} ms")
    print(f"    Max:      {max_response:6.2f} ms")
    
    print(f"\n  API Processing Times:")
    print(f"    Average:  {avg_api:6.2f} ms {'✅' if avg_api < 100 else '❌'}")
    
    print(f"\n  Risk Assessment:")
    print(f"    Avg Score: {avg_risk_score:.1f}/100")
    
    if failed:
        print(f"\n  ⚠️  Failed Requests: {len(failed)}")
        error_types = {}
        for f in failed:
            error = f.get("error", "Unknown")[:50]
            error_types[error] = error_types.get(error, 0) + 1
        for error, count in error_types.items():
            print(f"    - {error}: {count} times")
    
    print(f"\n{'-'*70}")


def check_health():
    """Check if API is available"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ API is healthy: {response.json()}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False


def main():
    """Main benchmark execution"""
    print("\n" + "="*70)
    print("🚀 COD SHIELD API PERFORMANCE BENCHMARK")
    print("="*70)
    print(f"\nTarget API: {BASE_URL}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check API health
    print(f"\n{'='*70}")
    print("🏥 HEALTH CHECK")
    print(f"{'='*70}\n")
    
    if not check_health():
        print("\n❌ API is not available. Please start the server and try again.")
        print("   Run: uvicorn main:app --reload")
        return
    
    # Run benchmarks
    try:
        benchmark_sequential(iterations=100)
        benchmark_concurrent(iterations=100, workers=10)
        
        # Summary
        print(f"\n{'='*70}")
        print("📈 BENCHMARK SUMMARY")
        print(f"{'='*70}\n")
        print("✅ Performance Targets:")
        print("   - P95 Response Time < 100ms")
        print("   - API Processing Time < 100ms")
        print("   - Success Rate > 99%")
        print("\n✅ Check results above to verify all targets are met!")
        print(f"\n{'='*70}\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Benchmark failed: {e}")


if __name__ == "__main__":
    main()
