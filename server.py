#!/usr/bin/env python3
"""
Multi-threaded HTTP Server with Socket Programming
Implements HTTP/1.1 protocol with thread pool, connection management, and security features
"""

import socket
import threading
import queue
import os
import json
import time
import mimetypes
import hashlib
from datetime import datetime
from pathlib import Path
from email.utils import formatdate
import signal
import sys
import re

# Constants
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8080
DEFAULT_THREAD_POOL_SIZE = 10
LISTEN_QUEUE_SIZE = 50
MAX_REQUEST_SIZE = 8192
BUFFER_SIZE = 4096
CONNECTION_TIMEOUT = 30  # seconds
MAX_REQUESTS_PER_CONNECTION = 100
RESOURCES_DIR = 'resources'
UPLOADS_DIR = os.path.join(RESOURCES_DIR, 'uploads')


class HTTPRequest:
    """Parse and store HTTP request data"""
    
    def __init__(self, raw_request):
        self.method = None
        self.path = None
        self.version = None
        self.headers = {}
        self.body = None
        self.valid = False
        
        self._parse(raw_request)
    
    def _parse(self, raw_request):
        """Parse raw HTTP request"""
        try:
            # Split headers and body
            parts = raw_request.split(b'\r\n\r\n', 1)
            header_section = parts[0].decode('utf-8', errors='replace')
            self.body = parts[1] if len(parts) > 1 else b''
            
            # Split into lines
            lines = header_section.split('\r\n')
            if not lines:
                return
            
            # Parse request line
            request_line = lines[0].split(' ')
            if len(request_line) != 3:
                return
            
            self.method = request_line[0].upper()
            self.path = request_line[1]
            self.version = request_line[2]
            
            # Parse headers
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    self.headers[key.strip().lower()] = value.strip()
            
            # Check if we need more body data based on Content-Length
            if 'content-length' in self.headers:
                content_length = int(self.headers['content-length'])
                if len(self.body) < content_length:
                    # Body is incomplete, mark as invalid
                    return
            
            self.valid = True
            
        except Exception as e:
            print(f"Error parsing request: {e}")
            self.valid = False


class HTTPResponse:
    """Build HTTP response"""
    
    def __init__(self, status_code, status_text, body=None, headers=None, binary=False):
        self.status_code = status_code
        self.status_text = status_text
        self.body = body
        self.headers = headers or {}
        self.binary = binary
        
        # Add default headers
        if 'Date' not in self.headers:
            self.headers['Date'] = formatdate(timeval=None, localtime=False, usegmt=True)
        if 'Server' not in self.headers:
            self.headers['Server'] = 'Multi-threaded HTTP Server'
    
    def to_bytes(self):
        """Convert response to bytes for sending"""
        # Status line
        response = f"HTTP/1.1 {self.status_code} {self.status_text}\r\n"
        
        # Add Content-Length if not present
        if self.body is not None and 'Content-Length' not in self.headers:
            if self.binary:
                self.headers['Content-Length'] = str(len(self.body))
            else:
                body_bytes = self.body.encode('utf-8') if isinstance(self.body, str) else self.body
                self.headers['Content-Length'] = str(len(body_bytes))
        
        # Headers
        for key, value in self.headers.items():
            response += f"{key}: {value}\r\n"
        
        response += "\r\n"
        
        # Convert to bytes
        response_bytes = response.encode('utf-8')
        
        # Add body
        if self.body is not None:
            if self.binary:
                response_bytes += self.body
            else:
                body_bytes = self.body.encode('utf-8') if isinstance(self.body, str) else self.body
                response_bytes += body_bytes
        
        return response_bytes


class ConnectionQueue:
    """Thread-safe queue for pending connections"""
    
    def __init__(self):
        self.queue = queue.Queue()
        self.lock = threading.Lock()
    
    def put(self, connection):
        """Add connection to queue"""
        self.queue.put(connection)
    
    def get(self, block=True, timeout=None):
        """Get connection from queue"""
        return self.queue.get(block=block, timeout=timeout)
    
    def size(self):
        """Get current queue size"""
        return self.queue.qsize()


class ThreadPool:
    """Manage worker threads for handling client connections"""
    
    def __init__(self, size, handler):
        self.size = size
        self.handler = handler
        self.threads = []
        self.active_count = 0
        self.lock = threading.Lock()
        self.connection_queue = ConnectionQueue()
        self.running = True
        
        # Start worker threads
        for i in range(size):
            thread = threading.Thread(target=self._worker, args=(i+1,), daemon=True)
            thread.start()
            self.threads.append(thread)
    
    def _worker(self, thread_id):
        """Worker thread that processes connections from queue"""
        thread_name = f"Thread-{thread_id}"
        
        while self.running:
            try:
                # Get connection from queue (with timeout to check running flag)
                connection_data = self.connection_queue.get(block=True, timeout=1.0)
                
                with self.lock:
                    self.active_count += 1
                
                # Handle the connection
                self.handler(connection_data, thread_name)
                
                with self.lock:
                    self.active_count -= 1
                    
            except queue.Empty:
                continue
            except Exception as e:
                log(f"[{thread_name}] Error in worker: {e}")
                with self.lock:
                    self.active_count -= 1
    
    def submit(self, connection_data):
        """Submit a connection to be handled by thread pool"""
        self.connection_queue.put(connection_data)
    
    def get_active_count(self):
        """Get number of active threads"""
        with self.lock:
            return self.active_count
    
    def stop(self):
        """Stop all worker threads"""
        self.running = False
        for thread in self.threads:
            thread.join(timeout=2.0)


class HTTPServer:
    """Multi-threaded HTTP Server"""
    
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, thread_pool_size=DEFAULT_THREAD_POOL_SIZE):
        self.host = host
        self.port = port
        self.thread_pool_size = thread_pool_size
        self.socket = None
        self.thread_pool = None
        self.running = False
        
        # Statistics
        self.total_requests = 0
        self.lock = threading.Lock()
        
        # Ensure directories exist
        os.makedirs(RESOURCES_DIR, exist_ok=True)
        os.makedirs(UPLOADS_DIR, exist_ok=True)
    
    def start(self):
        """Start the HTTP server"""
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind and listen
            self.socket.bind((self.host, self.port))
            self.socket.listen(LISTEN_QUEUE_SIZE)
            
            self.running = True
            
            # Log startup
            log(f"HTTP Server started on http://{self.host}:{self.port}")
            log(f"Thread pool size: {self.thread_pool_size}")
            log(f"Serving files from '{RESOURCES_DIR}' directory")
            log("Press Ctrl+C to stop the server")
            
            # Start thread pool
            self.thread_pool = ThreadPool(self.thread_pool_size, self._handle_client)
            
            # Accept connections
            while self.running:
                try:
                    client_socket, client_address = self.socket.accept()
                    
                    # Check thread pool status
                    active = self.thread_pool.get_active_count()
                    queue_size = self.thread_pool.connection_queue.size()
                    
                    if active >= self.thread_pool_size:
                        log(f"Warning: Thread pool saturated, queuing connection")
                    
                    # Submit to thread pool
                    self.thread_pool.submit((client_socket, client_address))
                    
                    # Periodic status logging
                    if self.total_requests % 10 == 0 and active > 0:
                        log(f"Thread pool status: {active}/{self.thread_pool_size} active")
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        log(f"Error accepting connection: {e}")
                    
        except KeyboardInterrupt:
            log("\nShutting down server...")
        except Exception as e:
            log(f"Server error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the server"""
        self.running = False
        
        if self.thread_pool:
            self.thread_pool.stop()
        
        if self.socket:
            self.socket.close()
        
        log("Server stopped")
    
    def _handle_client(self, connection_data, thread_name):
        """Handle a client connection (called by thread pool worker)"""
        client_socket, client_address = connection_data
        
        log(f"[{thread_name}] Connection from {client_address[0]}:{client_address[1]}")
        
        request_count = 0
        keep_alive = True
        
        try:
            # Set socket timeout for persistent connections
            client_socket.settimeout(CONNECTION_TIMEOUT)
            
            while keep_alive and request_count < MAX_REQUESTS_PER_CONNECTION:
                try:
                    # Receive request
                    raw_request = client_socket.recv(MAX_REQUEST_SIZE)
                    
                    if not raw_request:
                        break
                    
                    request_count += 1
                    
                    with self.lock:
                        self.total_requests += 1
                    
                    # Parse request
                    request = HTTPRequest(raw_request)
                    
                    if not request.valid:
                        response = self._error_response(400, "Bad Request")
                        client_socket.sendall(response.to_bytes())
                        break
                    
                    log(f"[{thread_name}] Request: {request.method} {request.path} {request.version}")
                    
                    # Validate Host header
                    if not self._validate_host(request):
                        if 'host' not in request.headers:
                            log(f"[{thread_name}] Security: Missing Host header")
                            response = self._error_response(400, "Bad Request")
                        else:
                            log(f"[{thread_name}] Security: Host mismatch - {request.headers.get('host')}")
                            response = self._error_response(403, "Forbidden")
                        client_socket.sendall(response.to_bytes())
                        break
                    
                    log(f"[{thread_name}] Host validation: {request.headers.get('host', 'N/A')} ✓")
                    
                    # Validate path for security
                    if not self._validate_path(request.path):
                        log(f"[{thread_name}] Security: Path traversal attempt - {request.path}")
                        response = self._error_response(403, "Forbidden")
                        client_socket.sendall(response.to_bytes())
                        break
                    
                    # Route request
                    if request.method == 'GET':
                        response = self._handle_get(request, thread_name)
                    elif request.method == 'POST':
                        response = self._handle_post(request, thread_name)
                    else:
                        response = self._error_response(405, "Method Not Allowed")
                        response.headers['Allow'] = 'GET, POST'
                    
                    # Determine keep-alive
                    connection_header = request.headers.get('connection', '').lower()
                    
                    if request.version == 'HTTP/1.0':
                        keep_alive = (connection_header == 'keep-alive')
                    else:  # HTTP/1.1
                        keep_alive = (connection_header != 'close')
                    
                    # Set response connection header
                    if keep_alive and request_count < MAX_REQUESTS_PER_CONNECTION:
                        response.headers['Connection'] = 'keep-alive'
                        response.headers['Keep-Alive'] = f'timeout={CONNECTION_TIMEOUT}, max={MAX_REQUESTS_PER_CONNECTION}'
                        log(f"[{thread_name}] Connection: keep-alive")
                    else:
                        response.headers['Connection'] = 'close'
                        keep_alive = False
                        log(f"[{thread_name}] Connection: close")
                    
                    # Send response
                    response_bytes = response.to_bytes()
                    client_socket.sendall(response_bytes)
                    
                    # Log response
                    body_size = len(response.body) if response.body else 0
                    if response.binary:
                        body_size = len(response.body) if response.body else 0
                    log(f"[{thread_name}] Response: {response.status_code} {response.status_text} ({body_size} bytes transferred)")
                    
                except socket.timeout:
                    log(f"[{thread_name}] Connection timeout")
                    break
                except ConnectionResetError:
                    log(f"[{thread_name}] Connection reset by client")
                    break
                except Exception as e:
                    log(f"[{thread_name}] Error handling request: {e}")
                    try:
                        response = self._error_response(500, "Internal Server Error")
                        client_socket.sendall(response.to_bytes())
                    except:
                        pass
                    break
                    
        finally:
            client_socket.close()
            log(f"[{thread_name}] Connection closed ({request_count} requests served)")
    
    def _validate_host(self, request):
        """Validate Host header"""
        if 'host' not in request.headers:
            return False
        
        host = request.headers['host']
        
        # Valid hosts: localhost:port, 127.0.0.1:port, or without port
        valid_hosts = [
            f'localhost:{self.port}',
            f'{self.host}:{self.port}',
            'localhost',
            self.host,
            f'127.0.0.1:{self.port}',
            '127.0.0.1'
        ]
        
        # If host is 0.0.0.0, accept any local address
        if self.host == '0.0.0.0':
            return True
        
        return host in valid_hosts
    
    def _validate_path(self, path):
        """Validate path to prevent directory traversal"""
        # Block obvious traversal attempts
        if '..' in path or path.startswith('//'):
            return False
        
        # Normalize path
        try:
            # Remove leading slash for path joining
            clean_path = path.lstrip('/')
            
            # If root path, it's valid
            if not clean_path or clean_path == '/':
                return True
            
            # Join with resources directory and resolve
            full_path = os.path.join(RESOURCES_DIR, clean_path)
            canonical = os.path.abspath(full_path)
            resources_canonical = os.path.abspath(RESOURCES_DIR)
            
            # Ensure the canonical path is within resources directory
            return canonical.startswith(resources_canonical)
            
        except Exception:
            return False
    
    def _handle_get(self, request, thread_name):
        """Handle GET request"""
        # Get file path
        path = request.path.lstrip('/')
        
        # Default to index.html for root
        if not path or path == '/':
            path = 'index.html'
        
        file_path = os.path.join(RESOURCES_DIR, path)
        
        # Check if file exists
        if not os.path.isfile(file_path):
            return self._error_response(404, "Not Found")
        
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Determine content type and mode
        if ext == '.html':
            # HTML files: render in browser
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                headers = {
                    'Content-Type': 'text/html; charset=utf-8'
                }
                
                log(f"[{thread_name}] Serving HTML file: {path} ({len(content)} bytes)")
                
                return HTTPResponse(200, "OK", body=content, headers=headers, binary=True)
                
            except Exception as e:
                log(f"[{thread_name}] Error reading file: {e}")
                return self._error_response(500, "Internal Server Error")
        
        elif ext in ['.txt', '.png', '.jpg', '.jpeg']:
            # Binary files: send as octet-stream for download
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                filename = os.path.basename(file_path)
                headers = {
                    'Content-Type': 'application/octet-stream',
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
                
                log(f"[{thread_name}] Sending binary file: {filename} ({len(content)} bytes)")
                
                return HTTPResponse(200, "OK", body=content, headers=headers, binary=True)
                
            except Exception as e:
                log(f"[{thread_name}] Error reading file: {e}")
                return self._error_response(500, "Internal Server Error")
        
        else:
            # Unsupported file type
            return self._error_response(415, "Unsupported Media Type")
    
    def _handle_post(self, request, thread_name):
        """Handle POST request"""
        # Check Content-Type
        content_type = request.headers.get('content-type', '')
        
        if 'application/json' not in content_type:
            return self._error_response(415, "Unsupported Media Type")
        
        # Parse JSON
        try:
            json_data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return self._error_response(400, "Bad Request")
        except Exception as e:
            log(f"[{thread_name}] Error parsing JSON: {e}")
            return self._error_response(400, "Bad Request")
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:4]
        filename = f"upload_{timestamp}_{random_id}.json"
        filepath = os.path.join(UPLOADS_DIR, filename)
        
        # Write file
        try:
            with open(filepath, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            log(f"[{thread_name}] Created file: {filepath}")
            
            # Build response
            response_data = {
                "status": "success",
                "message": "File created successfully",
                "filepath": f"/uploads/{filename}"
            }
            
            response_body = json.dumps(response_data)
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            return HTTPResponse(201, "Created", body=response_body, headers=headers)
            
        except Exception as e:
            log(f"[{thread_name}] Error writing file: {e}")
            return self._error_response(500, "Internal Server Error")
    
    def _error_response(self, status_code, status_text):
        """Generate error response"""
        body = f"""<!DOCTYPE html>
<html>
<head>
    <title>{status_code} {status_text}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 50px; }}
        h1 {{ color: #d32f2f; }}
    </style>
</head>
<body>
    <h1>{status_code} {status_text}</h1>
    <p>The server encountered an error processing your request.</p>
    <hr>
    <p><em>Multi-threaded HTTP Server</em></p>
</body>
</html>"""
        
        headers = {
            'Content-Type': 'text/html; charset=utf-8'
        }
        
        return HTTPResponse(status_code, status_text, body=body, headers=headers)


def log(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)


def main():
    """Main entry point"""
    # Parse command line arguments
    host = DEFAULT_HOST
    port = DEFAULT_PORT
    thread_pool_size = DEFAULT_THREAD_POOL_SIZE
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        host = sys.argv[2]
    
    if len(sys.argv) > 3:
        try:
            thread_pool_size = int(sys.argv[3])
        except ValueError:
            print(f"Invalid thread pool size: {sys.argv[3]}")
            sys.exit(1)
    
    # Create and start server
    server = HTTPServer(host, port, thread_pool_size)
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print()  # New line after ^C
        server.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start server
    server.start()


if __name__ == '__main__':
    main()

