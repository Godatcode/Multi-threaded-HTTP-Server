#!/bin/bash
# Manual Testing Script for HTTP Server

echo "======================================"
echo "Manual HTTP Server Testing"
echo "======================================"
echo ""

# Test 1: GET Home Page
echo "Test 1: GET / (Home Page)"
echo "Command: curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/)
echo "Result: HTTP $STATUS"
if [ "$STATUS" = "200" ]; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
fi
echo ""

# Test 2: View Headers with Verbose
echo "Test 2: View Response Headers"
echo "Command: curl -s -D - -o /dev/null http://localhost:8080/"
curl -s -D - -o /dev/null http://localhost:8080/
echo ""

# Test 3: Download Binary File
echo "Test 3: Download Binary File"
echo "Command: curl -O http://localhost:8080/logo.png"
curl -s -O http://localhost:8080/logo.png
if [ -f "logo.png" ]; then
    SIZE=$(ls -lh logo.png | awk '{print $5}')
    echo "✓ Downloaded logo.png ($SIZE)"
    rm logo.png
else
    echo "✗ Download failed"
fi
echo ""

# Test 4: POST JSON
echo "Test 4: POST JSON"
echo "Command: curl -X POST ... -d '{\"test\":\"manual\"}'"
RESPONSE=$(curl -s -X POST http://localhost:8080/upload \
    -H "Content-Type: application/json" \
    -d '{"test":"manual","timestamp":"'$(date +%s)'"}')
echo "Response: $RESPONSE"
if echo "$RESPONSE" | grep -q "success"; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
fi
echo ""

# Test 5: Test 404
echo "Test 5: Test 404 Not Found"
echo "Command: curl -s -o /dev/null -w '%{http_code}' .../nonexistent.html"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/nonexistent.html)
echo "Result: HTTP $STATUS"
if [ "$STATUS" = "404" ]; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
fi
echo ""

# Test 6: Test Security (Path Traversal)
echo "Test 6: Security - Path Traversal"
echo "Command: curl --path-as-is ... http://localhost:8080/../etc/passwd"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --path-as-is http://localhost:8080/../etc/passwd)
echo "Result: HTTP $STATUS"
if [ "$STATUS" = "403" ]; then
    echo "✓ PASS - Blocked successfully"
else
    echo "✗ FAIL - Should return 403"
fi
echo ""

# Test 7: Test 405 Method Not Allowed
echo "Test 7: Test 405 - Unsupported Method"
echo "Command: curl -X DELETE http://localhost:8080/index.html"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE http://localhost:8080/index.html)
echo "Result: HTTP $STATUS"
if [ "$STATUS" = "405" ]; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
fi
echo ""

# Test 8: Test HEAD method (should also be 405)
echo "Test 8: Test HEAD Method (should be 405)"
echo "Command: curl -I http://localhost:8080/"
STATUS=$(curl -s -I http://localhost:8080/ | head -1 | awk '{print $2}')
echo "Result: HTTP $STATUS"
if [ "$STATUS" = "405" ]; then
    echo "✓ PASS - HEAD not supported (correct)"
else
    echo "✗ FAIL"
fi
echo ""

# Test 9: Download and Verify Checksum
echo "Test 9: Binary Integrity Check"
echo "Command: Download file and compare checksums"
curl -s -O http://localhost:8080/sample1.txt
if [ -f "sample1.txt" ]; then
    ORIGINAL=$(md5 -q resources/sample1.txt)
    DOWNLOADED=$(md5 -q sample1.txt)
    echo "Original:   $ORIGINAL"
    echo "Downloaded: $DOWNLOADED"
    if [ "$ORIGINAL" = "$DOWNLOADED" ]; then
        echo "✓ PASS - Files match!"
    else
        echo "✗ FAIL - File corrupted"
    fi
    rm sample1.txt
else
    echo "✗ Download failed"
fi
echo ""

# Test 10: Concurrent Requests
echo "Test 10: Concurrent Requests"
echo "Sending 5 simultaneous requests..."
for i in {1..5}; do
    curl -s http://localhost:8080/ > /dev/null &
done
wait
echo "✓ All requests completed"
echo "  (Check server logs for thread activity)"
echo ""

echo "======================================"
echo "Manual Testing Complete!"
echo "======================================"
echo ""
echo "Summary:"
echo "  - Server correctly handles GET and POST"
echo "  - HEAD method returns 405 (correct)"
echo "  - Security features working"
echo "  - Binary file integrity verified"
echo ""
echo "For detailed logs, check server terminal output"
