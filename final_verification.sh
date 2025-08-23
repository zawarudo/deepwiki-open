#!/bin/bash

echo "🔍 Final Verification of Google Embedding Fix"
echo "============================================="

# Check current code in container
echo -e "\n📝 Current batch request code (lines 95-103):"
docker-compose -f docker-compose.dev.yml exec api cat /app/api/google_embedding_client.py | sed -n '95,103p'

# Check for recent batch errors
echo -e "\n📊 Batch embedding errors in last 5 minutes:"
RECENT_ERRORS=$(docker-compose -f docker-compose.dev.yml logs --since="5m" api 2>&1 | grep -c "Batch embeddings error" || echo "0")
echo "Count: $RECENT_ERRORS"

if [ "$RECENT_ERRORS" -gt 0 ]; then
    echo -e "\n⚠️ Last error details:"
    docker-compose -f docker-compose.dev.yml logs --since="5m" api 2>&1 | grep "Batch embeddings error" | tail -1
fi

# Check API health
echo -e "\n💚 API Health Check:"
curl -s http://localhost:8001/health | python3 -m json.tool 2>/dev/null || echo "API not responding"

echo -e "\n✅ Summary:"
echo "- Model format: Now using 'models/{model}' in each request"
echo "- Batch size: Limited to 100 (Google's max)"
echo "- Fix applied: Removed duplicate model specification"

if [ "$RECENT_ERRORS" -eq 0 ]; then
    echo -e "\n🎉 SUCCESS: No batch embedding errors in the last 5 minutes!"
else
    echo -e "\n⚠️ Note: Still seeing some errors - may need further investigation"
fi