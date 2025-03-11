#!/bin/bash

# Base API URL
BASE_URL="http://localhost:8000"

# Check if the server is running
echo "Checking if FastAPI server is running..."
if curl -s "$BASE_URL" | grep -q "Welcome to inquiro server"; then
    echo "✅ Server is running."
else
    echo "❌ Server is not running. Start it with: uvicorn app.main:app --reload"
    exit 1
fi

echo "-----------------------------------------"

# Test GET /users - Get all users
echo "Testing GET /users"
curl -s -X GET "$BASE_URL/users/" | jq .
echo "-----------------------------------------"

# Test POST /users - Create a new user
echo "Testing POST /users"
POST_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d '{
        "name": "Test User",
        "email": "testuser@example.com"
      }')
echo $POST_RESPONSE | jq .
echo "-----------------------------------------"

# Extract user id from POST response (using _id field)
USER_ID=$(echo $POST_RESPONSE | jq -r '._id')

if [ "$USER_ID" = "null" ] || [ -z "$USER_ID" ]; then
  echo "Failed to extract user ID from the POST response."
  exit 1
fi

echo "Created user ID: $USER_ID"
echo "-----------------------------------------"

# Test GET /users/{user_id} - Get user by id
echo "Testing GET /users/$USER_ID"
curl -s -X GET "$BASE_URL/users/$USER_ID" | jq .
echo "-----------------------------------------"

# Test GET /users/{user_id}/favorites - Get user's favorites (should be empty)
echo "Testing GET /users/$USER_ID/favorites"
curl -s -X GET "$BASE_URL/users/$USER_ID/favorites" | jq .
echo "-----------------------------------------"

# Test POST /users/{user_id}/favorites - Add a favorite
# We'll use an arbitrary ObjectId string as a favorite, e.g., "67cdede2ddcae81d0b5487f7"
echo "Testing POST /users/$USER_ID/favorites"
FAVORITE_RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/favorites" \
  -H "Content-Type: application/json" \
  -d '{
        "favorite_id": "67cdede2ddcae81d0b5487f7"
      }')
echo $FAVORITE_RESPONSE | jq .
echo "-----------------------------------------"

# Test GET /users/{user_id}/favorites again (should now contain the added favorite)
echo "Testing GET /users/$USER_ID/favorites after adding favorite"
curl -s -X GET "$BASE_URL/users/$USER_ID/favorites" | jq .
echo "-----------------------------------------"

echo "All tests completed."
