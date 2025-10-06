#!/usr/bin/env python3
"""
Comprehensive Test Client for Multi-threaded HTTP Server
Tests all required functionality and edge cases
"""

import socket
import json
import time
import hashlib
import os
from datetime import datetime
import threading

# Server configuration
HOST = '127.0.0.1'
PORT = 8080

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def log(message, color=RESET):
    """Print colored log message"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{color}[{timestamp}] {message}{RESET}")


def send_request(method, path, headers=None, body=None, host=HOST, port=PORT, skip_default_host=False):
    """Send HTTP request and return response"""
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        
        # Build request
        request = f"{method} {path} HTTP/1.1\r\n"
        
        # Default headers
        if headers is None:
            headers = {}
        
        if 'Host' not in headers and not skip_default_host:
            headers['Host'] = f'{host}:{port}'
        
        # Add body-related headers
        if body:
            if isinstance(body, str):
                body = body.encode('utf-8')
            headers['Content-Length'] = str(len(body))
        
        # Add headers to request
        for key, value in headers.items():
            request += f"{key}: {value}\r\n"
        
        request += "\r\n"
        
        # Send request
        sock.sendall(request.encode('utf-8'))
        
        # Send body if present
        if body:
            sock.sendall(body)
        
        # Receive response
        response = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            
            # Check if we've received the complete response
            if b'\r\n\r\n' in response:
                # Parse headers to check for Content-Length
                header_end = response.find(b'\r\n\r\n')
                headers_part = response[:header_end].decode('utf-8', errors='replace')
                
                # Extract Content-Length
                content_length = None
                for line in headers_part.split('\r\n'):
                    if line.lower().startswith('content-length:'):
                        content_length = int(line.split(':', 1)[1].strip())
                        break
                
                if content_length is not None:
                    body_start = header_end + 4
                    body_received = len(response) - body_start
                    
                    if body_received >= content_length:
                        break
        
        sock.close()
        return response
        
    except Exception as e:
        log(f"Error sending request: {e}", RED)
        return None


def parse_response(response):
    """Parse HTTP response"""
    if not response:
        return None, None, None
    
    # Split headers and body
    parts = response.split(b'\r\n\r\n', 1)
    headers_part = parts[0].decode('utf-8', errors='replace')
    body = parts[1] if len(parts) > 1 else b''
    
    # Parse status line
    lines = headers_part.split('\r\n')
    status_line = lines[0]
    status_code = int(status_line.split()[1])
    
    # Parse headers
    headers = {}
    for line in lines[1:]:
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip().lower()] = value.strip()
    
    return status_code, headers, body


def test_get_html():
    """Test GET request for HTML file"""
    log("TEST: GET / (HTML file)", BLUE)
    
    response = send_request('GET', '/')
    status_code, headers, body = parse_response(response)
    
    if status_code == 200:
        if 'content-type' in headers and 'text/html' in headers['content-type']:
            log(f"✓ GET / returned 200 OK with text/html", GREEN)
            log(f"  Content-Length: {headers.get('content-length', 'N/A')} bytes", GREEN)
            return True
        else:
            log(f"✗ Wrong Content-Type: {headers.get('content-type', 'N/A')}", RED)
            return False
    else:
        log(f"✗ Expected 200, got {status_code}", RED)
        return False


def test_get_binary():
    """Test GET request for binary file"""
    log("TEST: GET /logo.png (Binary file)", BLUE)
    
    response = send_request('GET', '/logo.png')
    status_code, headers, body = parse_response(response)
    
    if status_code == 200:
        if 'content-type' in headers and 'octet-stream' in headers['content-type']:
            if 'content-disposition' in headers and 'attachment' in headers['content-disposition']:
                size = len(body)
                log(f"✓ GET /logo.png returned 200 OK with correct headers", GREEN)
                log(f"  Content-Type: application/octet-stream", GREEN)
                log(f"  Content-Disposition: {headers['content-disposition']}", GREEN)
                log(f"  File size: {size} bytes", GREEN)
                return True
            else:
                log(f"✗ Missing or incorrect Content-Disposition header", RED)
                return False
        else:
            log(f"✗ Wrong Content-Type: {headers.get('content-type', 'N/A')}", RED)
            return False
    else:
        log(f"✗ Expected 200, got {status_code}", RED)
        return False


def test_binary_integrity():
    """Test binary file integrity"""
    log("TEST: Binary file integrity (checksum verification)", BLUE)
    
    # Download the file
    response = send_request('GET', '/logo.png')
    status_code, headers, body = parse_response(response)
    
    if status_code == 200:
        # Calculate checksum of received data
        received_checksum = hashlib.md5(body).hexdigest()
        
        # Calculate checksum of original file
        with open('resources/logo.png', 'rb') as f:
            original_data = f.read()
            original_checksum = hashlib.md5(original_data).hexdigest()
        
        if received_checksum == original_checksum:
            log(f"✓ Binary file integrity verified (MD5: {received_checksum})", GREEN)
            log(f"  Original size: {len(original_data)} bytes", GREEN)
            log(f"  Received size: {len(body)} bytes", GREEN)
            return True
        else:
            log(f"✗ Checksum mismatch!", RED)
            log(f"  Original: {original_checksum}", RED)
            log(f"  Received: {received_checksum}", RED)
            return False
    else:
        log(f"✗ Could not download file for integrity check", RED)
        return False


def test_large_file():
    """Test large file transfer (>1MB)"""
    log("TEST: Large file transfer (>1MB)", BLUE)
    
    response = send_request('GET', '/large_image.png')
    status_code, headers, body = parse_response(response)
    
    if status_code == 200:
        size_mb = len(body) / (1024 * 1024)
        if size_mb > 1:
            log(f"✓ Large file transferred successfully ({size_mb:.2f} MB)", GREEN)
            
            # Verify integrity
            with open('resources/large_image.png', 'rb') as f:
                original_data = f.read()
            
            if body == original_data:
                log(f"✓ Large file integrity verified", GREEN)
                return True
            else:
                log(f"✗ Large file corrupted during transfer", RED)
                return False
        else:
            log(f"✗ File size < 1MB ({size_mb:.2f} MB)", RED)
            return False
    else:
        log(f"✗ Expected 200, got {status_code}", RED)
        return False


def test_post_json():
    """Test POST request with JSON"""
    log("TEST: POST /upload (JSON data)", BLUE)
    
    test_data = {
        "name": "Test Client",
        "email": "test@example.com",
        "message": "Automated test from test_client.py",
        "timestamp": datetime.now().isoformat()
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    body = json.dumps(test_data)
    
    response = send_request('POST', '/upload', headers=headers, body=body)
    status_code, headers_resp, body_resp = parse_response(response)
    
    if status_code == 201:
        try:
            response_data = json.loads(body_resp.decode('utf-8'))
            if response_data.get('status') == 'success':
                log(f"✓ POST /upload returned 201 Created", GREEN)
                log(f"  File path: {response_data.get('filepath')}", GREEN)
                return True
            else:
                log(f"✗ Unexpected response status: {response_data.get('status')}", RED)
                return False
        except json.JSONDecodeError:
            log(f"✗ Response body is not valid JSON", RED)
            return False
    else:
        log(f"✗ Expected 201, got {status_code}", RED)
        return False


def test_404():
    """Test 404 Not Found"""
    log("TEST: GET /nonexistent.html (404 Not Found)", BLUE)
    
    response = send_request('GET', '/nonexistent.html')
    status_code, headers, body = parse_response(response)
    
    if status_code == 404:
        log(f"✓ Correctly returned 404 Not Found", GREEN)
        return True
    else:
        log(f"✗ Expected 404, got {status_code}", RED)
        return False


def test_405():
    """Test 405 Method Not Allowed"""
    log("TEST: PUT /index.html (405 Method Not Allowed)", BLUE)
    
    response = send_request('PUT', '/index.html')
    status_code, headers, body = parse_response(response)
    
    if status_code == 405:
        log(f"✓ Correctly returned 405 Method Not Allowed", GREEN)
        if 'allow' in headers:
            log(f"  Allow: {headers['allow']}", GREEN)
        return True
    else:
        log(f"✗ Expected 405, got {status_code}", RED)
        return False


def test_path_traversal():
    """Test path traversal protection"""
    log("TEST: Path traversal attack (403 Forbidden)", BLUE)
    
    malicious_paths = [
        '/../etc/passwd',
        '/../../sensitive.txt',
        '//etc/hosts',
        '/./../config'
    ]
    
    all_passed = True
    for path in malicious_paths:
        response = send_request('GET', path)
        status_code, headers, body = parse_response(response)
        
        if status_code == 403:
            log(f"✓ Blocked: {path}", GREEN)
        else:
            log(f"✗ Should block {path}, got {status_code}", RED)
            all_passed = False
    
    return all_passed


def test_host_validation():
    """Test Host header validation"""
    log("TEST: Host header validation", BLUE)
    
    # Test 1: Missing Host header
    response = send_request('GET', '/', headers={}, skip_default_host=True)
    status_code, headers, body = parse_response(response)
    
    if status_code == 400:
        log(f"✓ Missing Host header: 400 Bad Request", GREEN)
        test1 = True
    else:
        log(f"✗ Missing Host header should return 400, got {status_code}", RED)
        test1 = False
    
    # Test 2: Invalid Host header
    response = send_request('GET', '/', headers={'Host': 'evil.com'})
    status_code, headers, body = parse_response(response)
    
    if status_code == 403:
        log(f"✓ Invalid Host header: 403 Forbidden", GREEN)
        test2 = True
    else:
        log(f"✗ Invalid Host header should return 403, got {status_code}", RED)
        test2 = False
    
    return test1 and test2


def test_unsupported_media_type():
    """Test 415 Unsupported Media Type"""
    log("TEST: POST with wrong Content-Type (415)", BLUE)
    
    headers = {
        'Content-Type': 'text/plain'
    }
    body = "This is plain text, not JSON"
    
    response = send_request('POST', '/upload', headers=headers, body=body)
    status_code, headers_resp, body_resp = parse_response(response)
    
    if status_code == 415:
        log(f"✓ Correctly returned 415 Unsupported Media Type", GREEN)
        return True
    else:
        log(f"✗ Expected 415, got {status_code}", RED)
        return False


def test_keep_alive():
    """Test keep-alive connection"""
    log("TEST: Keep-Alive persistent connection", BLUE)
    
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        sock.settimeout(5.0)  # Set timeout to prevent hanging
        
        requests_sent = 0
        max_requests = 3
        
        for i in range(max_requests):
            # Build request with Connection: keep-alive
            request = f"GET / HTTP/1.1\r\n"
            request += f"Host: {HOST}:{PORT}\r\n"
            request += "Connection: keep-alive\r\n"
            request += "\r\n"
            
            # Send request
            sock.sendall(request.encode('utf-8'))
            requests_sent += 1
            
            # Receive response properly
            response = b''
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    
                    # Check if we have complete response
                    if b'\r\n\r\n' in response:
                        header_end = response.find(b'\r\n\r\n')
                        headers_part = response[:header_end].decode('utf-8', errors='replace')
                        
                        # Find Content-Length
                        content_length = None
                        for line in headers_part.split('\r\n'):
                            if line.lower().startswith('content-length:'):
                                content_length = int(line.split(':', 1)[1].strip())
                                break
                        
                        if content_length is not None:
                            body_start = header_end + 4
                            body_received = len(response) - body_start
                            if body_received >= content_length:
                                break
                        else:
                            # No Content-Length, assume complete
                            break
                except socket.timeout:
                    break
            
            if b'200 OK' in response:
                log(f"✓ Request {i+1}/{max_requests} succeeded on same connection", GREEN)
            else:
                log(f"✗ Request {i+1}/{max_requests} failed", RED)
                sock.close()
                return False
            
            time.sleep(0.1)
        
        sock.close()
        log(f"✓ Keep-alive connection handled {requests_sent} requests", GREEN)
        return True
        
    except Exception as e:
        log(f"✗ Keep-alive test failed: {e}", RED)
        return False


def test_concurrent_requests():
    """Test concurrent requests"""
    log("TEST: Concurrent requests (5 simultaneous)", BLUE)
    
    results = []
    threads = []
    
    def make_request(index):
        response = send_request('GET', f'/about.html')
        status_code, headers, body = parse_response(response)
        results.append(status_code == 200)
        if status_code == 200:
            log(f"✓ Concurrent request {index} succeeded", GREEN)
        else:
            log(f"✗ Concurrent request {index} failed: {status_code}", RED)
    
    # Start 5 concurrent requests
    for i in range(5):
        thread = threading.Thread(target=make_request, args=(i+1,))
        thread.start()
        threads.append(thread)
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    if all(results):
        log(f"✓ All 5 concurrent requests succeeded", GREEN)
        return True
    else:
        log(f"✗ Some concurrent requests failed", RED)
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("Multi-threaded HTTP Server - Comprehensive Test Suite")
    print("=" * 70)
    print()
    
    log(f"Testing server at {HOST}:{PORT}", YELLOW)
    print()
    
    # Check if server is running
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        sock.close()
        log("✓ Server is running", GREEN)
    except:
        log("✗ Server is not running. Please start the server first.", RED)
        log(f"  Run: python3 server.py {PORT}", YELLOW)
        return
    
    print()
    
    # Run all tests
    tests = [
        ("GET HTML File", test_get_html),
        ("GET Binary File", test_get_binary),
        ("Binary Integrity", test_binary_integrity),
        ("Large File Transfer", test_large_file),
        ("POST JSON", test_post_json),
        ("404 Not Found", test_404),
        ("405 Method Not Allowed", test_405),
        ("Path Traversal Protection", test_path_traversal),
        ("Host Validation", test_host_validation),
        ("Unsupported Media Type", test_unsupported_media_type),
        ("Keep-Alive Connection", test_keep_alive),
        ("Concurrent Requests", test_concurrent_requests)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            log(f"✗ Test '{test_name}' crashed: {e}", RED)
            results.append((test_name, False))
        
        print()
        time.sleep(0.5)
    
    # Print summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}✓ PASSED{RESET}" if result else f"{RED}✗ FAILED{RESET}"
        print(f"{test_name:.<50} {status}")
    
    print()
    percentage = (passed / total) * 100
    color = GREEN if percentage == 100 else (YELLOW if percentage >= 80 else RED)
    print(f"Total: {color}{passed}/{total} tests passed ({percentage:.1f}%){RESET}")
    print()
    
    if percentage == 100:
        log("🎉 All tests passed! Server implementation is excellent!", GREEN)
    elif percentage >= 80:
        log("👍 Most tests passed. Minor issues to fix.", YELLOW)
    else:
        log("❌ Several tests failed. Please review the implementation.", RED)


if __name__ == '__main__':
    main()

