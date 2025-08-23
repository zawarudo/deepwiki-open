#!/usr/bin/env python3
"""Test Google API key with correct embedding model."""

import os
import requests
import json

# Get API key from environment
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY not set in environment")
    exit(1)

print(f"✓ Found API key: {api_key[:10]}...{api_key[-4:]}")

# Test with the correct model name
model = "text-embedding-preview-0815"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}"

payload = {
    "model": f"models/{model}",
    "content": {
        "parts": [{"text": "This is a test embedding request"}]
    }
}

print(f"\nTesting model: {model}")
print(f"URL: {url}")

response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})

print(f"\nResponse Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if "embedding" in data and "values" in data["embedding"]:
        dims = len(data["embedding"]["values"])
        print(f"✅ SUCCESS! Got {dims}-dimensional embedding")
        print(f"First 5 values: {data['embedding']['values'][:5]}")
    else:
        print("⚠️ Unexpected response structure:")
        print(json.dumps(data, indent=2)[:500])
else:
    print(f"❌ FAILED: {response.text[:500]}")
    
    # Try alternative models
    print("\n--- Testing alternative models ---")
    alt_models = ["text-embedding-preview-0409", "embedding-001"]
    
    for alt_model in alt_models:
        alt_url = f"https://generativelanguage.googleapis.com/v1beta/models/{alt_model}:embedContent?key={api_key}"
        alt_payload = {
            "model": f"models/{alt_model}",
            "content": {"parts": [{"text": "test"}]}
        }
        alt_response = requests.post(alt_url, json=alt_payload, headers={"Content-Type": "application/json"})
        print(f"{alt_model}: Status {alt_response.status_code}")
        if alt_response.status_code == 200:
            print(f"  ✅ This model works!")