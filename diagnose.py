#!/usr/bin/env python
"""
Diagnostic script to test if all imports work
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("CV ANALYZER - DIAGNOSTIC CHECK")
print("=" * 50)

try:
    print("\n1. Testing FastAPI import...")
    from fastapi import FastAPI
    print("   ✅ FastAPI OK")
except Exception as e:
    print(f"   ❌ FastAPI Error: {e}")
    sys.exit(1)

try:
    print("\n2. Testing pydantic models import...")
    from app.models.schemas import HealthResponse, CVAnalysisResponse
    print("   ✅ Schemas OK")
except Exception as e:
    print(f"   ❌ Schemas Error: {e}")
    sys.exit(1)

try:
    print("\n3. Testing CV Analyzer Service import...")
    from app.services.cv_analyzer import CVAnalyzerService
    print("   ✅ CVAnalyzerService OK")
except Exception as e:
    print(f"   ❌ CVAnalyzerService Error: {e}")
    sys.exit(1)

try:
    print("\n4. Testing main app import...")
    from app.main import app
    print("   ✅ Main app OK")
except Exception as e:
    print(f"   ❌ Main app Error: {e}")
    sys.exit(1)

try:
    print("\n5. Initializing FastAPI app...")
    if app:
        print("   ✅ App initialized")
    else:
        print("   ❌ App is None")
except Exception as e:
    print(f"   ❌ Initialization Error: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("✅ ALL CHECKS PASSED - Service should work!")
print("=" * 50)
print("\nNow run: python run.py")
