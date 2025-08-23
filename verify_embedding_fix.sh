#!/bin/bash

echo "🔍 Verifying Google Embedding Batch Fix"
echo "========================================"

# Check for errors before the fix (around 12:00)
echo -e "\n📊 Before Fix (11:55-12:00):"
BEFORE_ERRORS=$(docker-compose -f docker-compose.dev.yml logs api 2>&1 | \
                grep "2025-08-23 11:5[5-9]" | \
                grep -c "Batch embeddings error" || echo "0")
echo "Batch embedding errors: $BEFORE_ERRORS"

# Check for errors after the fix (after 12:04 when reloaded)
echo -e "\n📊 After Fix (12:04-now):"
AFTER_ERRORS=$(docker-compose -f docker-compose.dev.yml logs api 2>&1 | \
               grep "2025-08-23 12:0[4-9]" | \
               grep -c "Batch embeddings error" || echo "0")
echo "Batch embedding errors: $AFTER_ERRORS"

# Check the last error timestamp
echo -e "\n⏰ Last batch error timestamp:"
docker-compose -f docker-compose.dev.yml logs api 2>&1 | \
    grep "Batch embeddings error" | \
    tail -1 | \
    grep -oE "2025-08-23 [0-9]{2}:[0-9]{2}:[0-9]{2}" || echo "No batch errors found"

# Check if API is healthy
echo -e "\n💚 API Health:"
curl -s http://localhost:8001/health | python3 -m json.tool 2>/dev/null || echo "API health check failed"

# Summary
echo -e "\n📈 Summary:"
if [ "$AFTER_ERRORS" -eq 0 ]; then
    echo "✅ Fix appears successful - no batch errors after restart"
else
    echo "⚠️ Still seeing batch errors after fix"
fi

# Check current embedding client code
echo -e "\n🔧 Current batch request format (lines 99-104):"
sed -n '99,104p' /app/api/google_embedding_client.py 2>/dev/null || \
sed -n '99,104p' api/google_embedding_client.py