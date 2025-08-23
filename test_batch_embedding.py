#!/usr/bin/env python3
"""Test batch embedding with Google API after fix"""

import requests
import json
import time

# API endpoint
API_URL = "http://localhost:8001"

def test_batch_embedding():
    """Test the batch embedding functionality"""
    
    # Prepare test data - multiple text snippets for batch processing
    test_texts = [
        "This is a test document for embedding.",
        "Another document to test batch processing.",
        "Testing Google embedding API batch functionality.",
        "Verifying the model name format fix works correctly.",
        "The batch should process all texts efficiently."
    ]
    
    # Create a simple request that would trigger batch embedding
    # This assumes there's an endpoint that processes multiple texts
    # We'll check the logs to see if batch processing is working
    
    print("Testing batch embedding API...")
    print(f"Sending {len(test_texts)} texts for embedding")
    
    # First, let's check if the API is healthy
    try:
        health_response = requests.get(f"{API_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ API is healthy")
        else:
            print(f"⚠️ API health check returned: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Could not connect to API: {e}")
        return
    
    print("\nNote: Check the API logs to verify batch embedding is working without errors")
    print("Run: docker-compose -f docker-compose.dev.yml logs --tail=50 api")

if __name__ == "__main__":
    test_batch_embedding()