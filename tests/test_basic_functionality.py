import pytest
from fastapi.testclient import TestClient
from main import app

class TestBasicFunctionality:
    def test_health_endpoint(self):
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_auth_endpoints_exist(self):
        client = TestClient(app)
        
        # Test register endpoint exists
        response = client.post("/auth/register", json={})
        assert response.status_code in [400, 422]  # Should exist but fail validation
        
        # Test login endpoint exists  
        response = client.post("/auth/login", json={})
        assert response.status_code in [400, 422]  # Should exist but fail validation
    
    def test_receipts_endpoints_exist(self):
        client = TestClient(app)
        
        # Test receipts endpoint exists (should require auth)
        response = client.get("/receipts/")
        assert response.status_code == 403  # Исправлено: 403 вместо 401
        
        response = client.post("/receipts/", json={})
        assert response.status_code == 403  # Исправлено: 403 вместо 401
