#!/usr/bin/env python3
"""
Simple backend test to debug import issues
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test each import individually to identify issues"""
    print("Testing backend imports...")
    
    try:
        print("1. Testing core.config...")
        from backend.core.config import settings
        print(f"   ✓ Config loaded: {settings.app_name}")
    except Exception as e:
        print(f"   ✗ Config failed: {e}")
        return False
    
    try:
        print("2. Testing data.models...")
        from backend.data.models import User, Company, Internship
        print("   ✓ Models imported successfully")
    except Exception as e:
        print(f"   ✗ Models failed: {e}")
        return False
    
    try:
        print("3. Testing data.schemas...")
        from backend.data.schemas import InternshipListResponse, UserResponse
        print("   ✓ Schemas imported successfully")
    except Exception as e:
        print(f"   ✗ Schemas failed: {e}")
        return False
    
    try:
        print("4. Testing database...")
        from backend.core.database import create_db_and_tables, get_session
        print("   ✓ Database functions imported")
    except Exception as e:
        print(f"   ✗ Database failed: {e}")
        return False
    
    try:
        print("5. Testing API modules...")
        from backend.api import internships, users, resumes, scrape
        print("   ✓ API modules imported")
    except Exception as e:
        print(f"   ✗ API modules failed: {e}")
        return False
    
    try:
        print("6. Testing main app...")
        from backend.main import app
        print("   ✓ FastAPI app created successfully")
        return True
    except Exception as e:
        print(f"   ✗ Main app failed: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n🎉 All imports successful! Backend should start properly.")
        print("Run: python3 -m uvicorn backend.main:app --reload --port 8000")
    else:
        print("\n❌ Import issues found. Check the errors above.")
    
    sys.exit(0 if success else 1)
