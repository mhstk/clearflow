#!/usr/bin/env python3
"""
Simple test script to verify API is working correctly.
Run after starting the server with: python run.py
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")
    return response.status_code == 200


def test_get_accounts():
    """Test get accounts endpoint"""
    print("📊 Testing get accounts endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/accounts")
    print(f"   Status: {response.status_code}")
    print(f"   Accounts: {len(response.json())}\n")
    return response.status_code == 200


def test_upload_csv():
    """Test CSV upload endpoint"""
    print("📤 Testing CSV upload endpoint...")
    csv_path = Path(__file__).parent / "sample_statement.csv"

    if not csv_path.exists():
        print(f"   ⚠️  Sample CSV not found at {csv_path}")
        return False

    with open(csv_path, "rb") as f:
        files = {"file": ("sample_statement.csv", f, "text/csv")}
        response = requests.post(
            f"{BASE_URL}/api/v1/transactions/upload_csv",
            files=files
        )

    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Inserted: {data['inserted_count']} transactions")
        print(f"   Skipped: {data['skipped_count']} transactions")
        print(f"   Account ID: {data['account_id']}\n")
        return True
    else:
        print(f"   Error: {response.text}\n")
        return False


def test_get_transactions():
    """Test get transactions endpoint"""
    print("📋 Testing get transactions endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/transactions/view?page_size=5")
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   Total transactions: {data['pagination']['total_count']}")
        print(f"   Returned: {len(data['rows'])} transactions")
        print(f"   Total spent: ${abs(data['aggregates']['total_spent']):.2f}")
        print(f"   Total income: ${data['aggregates']['total_income']:.2f}\n")
        return True
    else:
        print(f"   Error: {response.text}\n")
        return False


def test_categorize_merchant():
    """Test AI categorization endpoint"""
    print("🤖 Testing AI categorization endpoint...")

    payload = {
        "merchant_key": "MCDONALDS",
        "sample_descriptions": [
            "MCDONALD'S #41147 OSHAWA",
            "MCDONALD'S #12345 TORONTO"
        ]
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/ai/categorize_merchant",
        json=payload
    )

    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   Category: {data['category']}")
        print(f"   Note: {data['note']}")
        print(f"   Explanation: {data['explanation']}\n")
        return True
    else:
        print(f"   Error: {response.text}\n")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Personal Finance Intelligence API - Test Suite")
    print("=" * 60)
    print()

    # Check if server is running
    try:
        requests.get(BASE_URL, timeout=2)
    except requests.exceptions.ConnectionError:
        print("❌ Error: API server is not running!")
        print("   Please start the server first with: python run.py\n")
        return

    # Run tests
    tests = [
        ("Health Check", test_health),
        ("Get Accounts", test_get_accounts),
        ("Upload CSV", test_upload_csv),
        ("Get Transactions", test_get_transactions),
        ("AI Categorization", test_categorize_merchant),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"   ❌ Exception: {e}\n")
            results.append((name, False))

    # Print summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    passed = sum(1 for _, result in results if result)
    print(f"\nPassed: {passed}/{len(results)} tests")
    print()


if __name__ == "__main__":
    main()
