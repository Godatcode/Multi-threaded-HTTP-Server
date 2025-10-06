#!/bin/bash
# Quick test script for HTTP server

echo "=========================================="
echo "HTTP Server Quick Test"
echo "=========================================="
echo ""

# Check if server is running
echo "Testing if server is running on localhost:8080..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ | grep -q "200"; then
    echo "✓ Server is running"
else
    echo "✗ Server is NOT running"
    echo "Please start the server first: python3 server.py"
    exit 1
fi

echo ""
echo "Running quick tests..."
echo ""

# Test 1: GET HTML
echo "1. Testing GET / (HTML)..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/)
if [ "$STATUS" = "200" ]; then
    echo "   ✓ PASSED: GET / returned 200 OK"
else
    echo "   ✗ FAILED: Expected 200, got $STATUS"
fi

# Test 2: GET Binary
echo "2. Testing GET /logo.png (Binary)..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/logo.png)
if [ "$STATUS" = "200" ]; then
    echo "   ✓ PASSED: Binary file download successful"
else
    echo "   ✗ FAILED: Expected 200, got $STATUS"
fi

# Test 3: POST JSON
echo "3. Testing POST /upload (JSON)..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/upload \
    -H "Content-Type: application/json" \
    -d '{"test": "data"}')
if [ "$STATUS" = "201" ]; then
    echo "   ✓ PASSED: POST JSON returned 201 Created"
else
    echo "   ✗ FAILED: Expected 201, got $STATUS"
fi

# Test 4: 404 Error
echo "4. Testing 404 Not Found..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/nonexistent.html)
if [ "$STATUS" = "404" ]; then
    echo "   ✓ PASSED: 404 error handled correctly"
else
    echo "   ✗ FAILED: Expected 404, got $STATUS"
fi

# Test 5: Path Traversal
echo "5. Testing security (path traversal)..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --path-as-is http://localhost:8080/../etc/passwd)
if [ "$STATUS" = "403" ]; then
    echo "   ✓ PASSED: Path traversal blocked (403 Forbidden)"
else
    echo "   ✗ FAILED: Expected 403, got $STATUS"
fi

echo ""
echo "=========================================="
echo "Quick tests completed!"
echo "For comprehensive testing, run:"
echo "  python3 test_client.py"
echo "=========================================="

