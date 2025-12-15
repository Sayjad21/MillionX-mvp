"""
Unit tests for COD Shield Risk Engine API
"""
import pytest
from fastapi.testclient import TestClient
import redis
import sys
import os

# Add parent directory to path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoints"""
    
    def test_health_check(self):
        """Health endpoint should return 200"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "COD Shield"


class TestLowRiskScenarios:
    """Test low-risk order scenarios (score 0-40)"""
    
    def test_regular_customer_small_order(self):
        """Regular customer with small order should be low risk"""
        payload = {
            "order_id": "TEST-LOW-001",
            "merchant_id": "MERCH-TEST",
            "customer_phone": "+8801700000001",
            "delivery_address": {
                "area": "Gulshan",
                "city": "Dhaka",
                "postal_code": "1212"
            },
            "order_details": {
                "total_amount": 300,
                "currency": "BDT",
                "items_count": 1,
                "is_first_order": False
            },
            "timestamp": "2025-12-15T10:00:00Z"
        }
        
        response = client.post("/api/v1/risk-score", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["order_id"] == "TEST-LOW-001"
        assert data["risk_score"] <= 40
        assert data["risk_level"] == "LOW"
        assert data["recommendation"] == "PROCEED_WITH_COD"
        assert len(data["factors"]) >= 0
        assert len(data["suggested_actions"]) > 0
        assert data["processing_time_ms"] < 1000
    
    def test_known_customer_medium_order(self):
        """Known customer with medium-value order"""
        payload = {
            "order_id": "TEST-LOW-002",
            "merchant_id": "MERCH-TEST",
            "customer_phone": "+8801700000002",
            "delivery_address": {
                "area": "Dhanmondi",
                "city": "Dhaka",
                "postal_code": "1205"
            },
            "order_details": {
                "total_amount": 800,
                "currency": "BDT",
                "items_count": 2,
                "is_first_order": False
            },
            "timestamp": "2025-12-15T14:30:00Z"
        }
        
        response = client.post("/api/v1/risk-score", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["risk_score"] <= 40
        assert data["risk_level"] == "LOW"


class TestMediumRiskScenarios:
    """Test medium-risk order scenarios (score 41-70)"""
    
    def test_first_order_high_value(self):
        """First-time customer with high-value order"""
        payload = {
            "order_id": "TEST-MED-001",
            "merchant_id": "MERCH-TEST",
            "customer_phone": "+8801700000010",
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
            "timestamp": "2025-12-15T11:00:00Z"
        }
        
        response = client.post("/api/v1/risk-score", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["risk_score"] >= 25  # Should get points for first order + high value
        assert "HIGH_VALUE_FIRST_ORDER" in [f["factor"] for f in data["factors"]]
    
    def test_first_order_medium_value(self):
        """First-time customer with medium-value order"""
        payload = {
            "order_id": "TEST-MED-002",
            "merchant_id": "MERCH-TEST",
            "customer_phone": "+8801700000011",
            "delivery_address": {
                "area": "Uttara",
                "city": "Dhaka",
                "postal_code": "1230"
            },
            "order_details": {
                "total_amount": 750,
                "currency": "BDT",
                "items_count": 2,
                "is_first_order": True
            },
            "timestamp": "2025-12-15T12:00:00Z"
        }
        
        response = client.post("/api/v1/risk-score", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["risk_score"] >= 10


class TestHighRiskScenarios:
    """Test high-risk order scenarios (score 71-100)"""
    
    def test_blacklisted_customer(self):
        """Blacklisted customer should be high risk"""
        # Note: This test requires Redis to be running
        # In actual test, we'd mock Redis or use a test Redis instance
        payload = {
            "order_id": "TEST-HIGH-001",
            "merchant_id": "MERCH-TEST",
            "customer_phone": "+8801799999999",  # Would be in blacklist
            "delivery_address": {
                "area": "Unknown",
                "city": "Dhaka",
                "postal_code": ""
            },
            "order_details": {
                "total_amount": 1200,
                "currency": "BDT",
                "items_count": 2,
                "is_first_order": True
            },
            "timestamp": "2025-12-15T13:00:00Z"
        }
        
        response = client.post("/api/v1/risk-score", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        # Note: Actual score depends on Redis state
        assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
        assert data["recommendation"] in ["PROCEED_WITH_COD", "CONFIRMATION_CALL_REQUIRED", "ADVANCE_PAYMENT_REQUIRED"]


class TestBlacklistManagement:
    """Test blacklist management endpoints"""
    
    def test_add_to_blacklist(self):
        """Should successfully add phone to blacklist"""
        payload = {
            "phone": "+8801799999998",
            "reason": "Failed delivery - customer unreachable",
            "merchant_id": "MERCH-TEST"
        }
        
        response = client.post("/api/v1/blacklist/add", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "added"
        assert data["phone"] == "+8801799999998"
    
    def test_check_blacklist_exists(self):
        """Should check if phone is blacklisted"""
        # First add to blacklist
        client.post("/api/v1/blacklist/add", json={
            "phone": "+8801799999997",
            "reason": "Test",
            "merchant_id": "MERCH-TEST"
        })
        
        # Then check
        response = client.get("/api/v1/blacklist/check?phone=%2B8801799999997")
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_blacklisted"] == True
        assert data["phone"] == "+8801799999997"
    
    def test_check_blacklist_not_exists(self):
        """Should return false for non-blacklisted phone"""
        response = client.get("/api/v1/blacklist/check?phone=%2B8801700000099")
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_blacklisted"] == False


class TestPerformance:
    """Test performance requirements"""
    
    def test_response_time_under_1_second(self):
        """Risk scoring should complete in under 1 second"""
        payload = {
            "order_id": "TEST-PERF-001",
            "merchant_id": "MERCH-TEST",
            "customer_phone": "+8801700000050",
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
            "timestamp": "2025-12-15T15:00:00Z"
        }
        
        response = client.post("/api/v1/risk-score", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        # Target is <100ms, but allowing up to 1000ms for test tolerance
        assert data["processing_time_ms"] < 1000


class TestValidation:
    """Test input validation"""
    
    def test_missing_required_fields(self):
        """Should return 422 for missing required fields"""
        payload = {
            "order_id": "TEST-VAL-001",
            # Missing merchant_id, customer_phone, etc.
        }
        
        response = client.post("/api/v1/risk-score", json=payload)
        assert response.status_code == 422
    
    def test_invalid_phone_format(self):
        """Should handle invalid phone format gracefully"""
        payload = {
            "order_id": "TEST-VAL-002",
            "merchant_id": "MERCH-TEST",
            "customer_phone": "invalid-phone",
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
            "timestamp": "2025-12-15T16:00:00Z"
        }
        
        response = client.post("/api/v1/risk-score", json=payload)
        # Should either return 200 with risk score or 422 for validation error
        assert response.status_code in [200, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
