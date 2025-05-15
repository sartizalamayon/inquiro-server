#!/usr/bin/env bash
# test_permission_api.sh
# Usage: bash test_permission_api.sh

set -euo pipefail

BASE_URL="http://localhost:8000"
# Now corrected: the *true* owner of the collection
OWNER_EMAIL="sartizayo.on@gmail.com"
# And the collaborator we share *to*
SHARED_EMAIL="ayonsartizalam@gmail.com"
COLLECTION_ID="6820d6b394791f109baa5850"

echo
echo "=== 1) Clean slate: revoke any existing permission for $SHARED_EMAIL ==="
status=$(curl -s -X DELETE \
  "$BASE_URL/permissions/$COLLECTION_ID/$SHARED_EMAIL" \
  -o /dev/null -w "%{http_code}")
echo "Status: $status"   # expect 204

echo
echo "=== 2) Grant SCAN permission to $SHARED_EMAIL ==="
curl -s -X POST "$BASE_URL/permissions/" \
  -H "Content-Type: application/json" \
  -d "{\"collection_id\":\"$COLLECTION_ID\",\"user_email\":\"$SHARED_EMAIL\",\"access_level\":\"scan\",\"granted_by\":\"$OWNER_EMAIL\"}" \
  | jq

echo
echo "=== 3) List permissions for collection $COLLECTION_ID ==="
curl -s "$BASE_URL/permissions/collections/$COLLECTION_ID" | jq

echo
echo "=== 4) List permissions for user $SHARED_EMAIL ==="
curl -s "$BASE_URL/permissions/users/$SHARED_EMAIL" | jq

echo
echo "=== 5) Fetch a paper ID from the collection ==="
PAPER_ID=$(curl -s "$BASE_URL/collections/$COLLECTION_ID" | jq -r '.papers[0]')
echo "Paper ID: $PAPER_ID"

echo
echo "=== 6) Check PAPER access for owner ($OWNER_EMAIL) — should be \"control\" ==="
curl -s "$BASE_URL/permissions/paper/$PAPER_ID/$OWNER_EMAIL" | jq
echo

echo "=== 7) Check PAPER access for shared user ($SHARED_EMAIL) — should be \"scan\" ==="
curl -s "$BASE_URL/permissions/paper/$PAPER_ID/$SHARED_EMAIL" | jq
echo

echo "=== 8) Upgrade to MODIFY permission ==="
curl -s -X POST "$BASE_URL/permissions/" \
  -H "Content-Type: application/json" \
  -d "{\"collection_id\":\"$COLLECTION_ID\",\"user_email\":\"$SHARED_EMAIL\",\"access_level\":\"modify\",\"granted_by\":\"$OWNER_EMAIL\"}" \
  | jq

echo
echo "=== 9) Verify MODIFY access on PAPER (should be \"modify\") ==="
curl -s "$BASE_URL/permissions/paper/$PAPER_ID/$SHARED_EMAIL" | jq
echo

echo "=== 10) Upgrade to CONTROL permission ==="
curl -s -X POST "$BASE_URL/permissions/" \
  -H "Content-Type: application/json" \
  -d "{\"collection_id\":\"$COLLECTION_ID\",\"user_email\":\"$SHARED_EMAIL\",\"access_level\":\"control\",\"granted_by\":\"$OWNER_EMAIL\"}" \
  | jq

echo
echo "=== 11) Verify CONTROL access on PAPER (should be \"control\") ==="
curl -s "$BASE_URL/permissions/paper/$PAPER_ID/$SHARED_EMAIL" | jq
echo

echo "=== 12) Revoke permission ==="
status=$(curl -s -X DELETE \
  "$BASE_URL/permissions/$COLLECTION_ID/$SHARED_EMAIL" \
  -o /dev/null -w "%{http_code}")
echo "Status: $status"   # expect 204

echo
echo "=== 13) Final check: no permission on PAPER (should be \"none\") ==="
curl -s "$BASE_URL/permissions/paper/$PAPER_ID/$SHARED_EMAIL" | jq
echo

echo "✅ All permission-route tests completed."
