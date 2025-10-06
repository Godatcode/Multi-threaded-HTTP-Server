# Getting Started - Multi-threaded HTTP Server

## 🚀 Quick Start (3 Steps)

### Step 1: Navigate to Project Directory
```bash
cd /Users/arkaghosh/Desktop/CN_Project
```

### Step 2: Start the Server
```bash
python3 server.py
```

You should see:
```
[2024-10-06 10:30:00] HTTP Server started on http://127.0.0.1:8080
[2024-10-06 10:30:00] Thread pool size: 10
[2024-10-06 10:30:00] Serving files from 'resources' directory
[2024-10-06 10:30:00] Press Ctrl+C to stop the server
```

### Step 3: Test the Server

**Option A: Open in Browser**
```
http://localhost:8080/
```

**Option B: Run Automated Tests (in a new terminal)**
```bash
cd /Users/arkaghosh/Desktop/CN_Project
python3 test_client.py
```

**Option C: Quick Shell Test**
```bash
./quick_test.sh
```

## 📁 Project Structure

```
CN_Project/
│
├── 📄 server.py                      # Main HTTP server (670 lines)
├── 🧪 test_client.py                 # Test suite (550 lines, 12 tests)
├── 🚀 quick_test.sh                  # Quick bash tests
│
├── 📚 Documentation
│   ├── README.md                     # Complete documentation (1500+ lines)
│   ├── SUBMISSION_GUIDE.md           # How to submit
│   ├── PROJECT_SUMMARY.md            # Project overview
│   └── GETTING_STARTED.md            # This file
│
├── ⚙️  Configuration
│   ├── requirements.txt              # Dependencies (standard library only)
│   ├── .gitignore                    # Git ignore rules
│   └── sample_post_data.json         # Sample JSON for testing
│
└── 📂 resources/                     # Static files
    ├── 🌐 HTML Pages (Beautiful UI)
    │   ├── index.html                # Home page
    │   ├── about.html                # Technical details
    │   └── contact.html              # API documentation
    │
    ├── 🖼️  Images (Binary Testing)
    │   ├── logo.png                  # PNG image (3.9 KB)
    │   ├── large_image.png           # Large PNG (26 MB) ⭐
    │   ├── photo.jpg                 # JPEG image (33 KB)
    │   └── landscape.jpg             # JPEG image (43 KB)
    │
    ├── 📄 Text Files (Binary Testing)
    │   ├── sample1.txt               # Test text (1.6 KB)
    │   └── sample2.txt               # Test text (2.3 KB)
    │
    └── 📤 uploads/                   # POST upload directory
        └── .gitkeep                  # Keep directory in git
```

## 📊 File Statistics

| Category | Count | Total Size |
|----------|-------|------------|
| Python Files | 2 | 1220 lines |
| HTML Files | 3 | 1000+ lines |
| Documentation | 4 | 3000+ lines |
| Images | 4 | ~26 MB |
| Text Files | 2 | ~4 KB |
| **Total Files** | **15+** | **~26 MB** |

## 🎯 What to Test

### 1. Basic Server (2 minutes)

```bash
# Start server
python3 server.py

# In browser, visit:
# http://localhost:8080/          → Beautiful home page
# http://localhost:8080/about     → Technical details
# http://localhost:8080/contact   → API documentation
```

### 2. Binary File Downloads (2 minutes)

```bash
# Download images
curl -O http://localhost:8080/logo.png
curl -O http://localhost:8080/photo.jpg

# Download text files
curl -O http://localhost:8080/sample1.txt

# Verify integrity
md5 logo.png
md5 resources/logo.png
# ☝️ These should match!
```

### 3. POST JSON (1 minute)

```bash
curl -X POST http://localhost:8080/upload \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "message": "Hello!"}'
```

Expected response:
```json
{
  "status": "success",
  "message": "File created successfully",
  "filepath": "/uploads/upload_20241006_103000_a7b9.json"
}
```

Check the file was created:
```bash
ls -la resources/uploads/
```

### 4. Security Tests (1 minute)

```bash
# Path traversal (should return 403)
curl http://localhost:8080/../etc/passwd

# Invalid host (should return 403)
curl -H "Host: evil.com" http://localhost:8080/

# Missing host (should return 400)
curl -H "Host:" http://localhost:8080/
```

### 5. Automated Tests (2 minutes)

```bash
python3 test_client.py
```

You should see:
```
Total: 12/12 tests passed (100.0%)
🎉 All tests passed! Server implementation is excellent!
```

## 🔧 Server Configuration Options

### Default Configuration
```bash
python3 server.py
# Host: 127.0.0.1
# Port: 8080
# Threads: 10
```

### Custom Port
```bash
python3 server.py 9000
# Host: 127.0.0.1
# Port: 9000
# Threads: 10
```

### Custom Host and Port
```bash
python3 server.py 9000 0.0.0.0
# Host: 0.0.0.0 (all interfaces)
# Port: 9000
# Threads: 10
```

### Full Configuration
```bash
python3 server.py 9000 0.0.0.0 20
# Host: 0.0.0.0
# Port: 9000
# Threads: 20
```

## 📝 Common Use Cases

### 1. Demo for Professor/TA
```bash
# Terminal 1: Start server with verbose output
python3 server.py

# Terminal 2: Run tests to show everything works
python3 test_client.py

# Terminal 3: Show beautiful UI in browser
open http://localhost:8080/
```

### 2. Testing During Development
```bash
# Start server in background
python3 server.py &
SERVER_PID=$!

# Run tests
python3 test_client.py

# Stop server
kill $SERVER_PID
```

### 3. Stress Testing
```bash
# Terminal 1: Start server
python3 server.py

# Terminal 2: Multiple concurrent requests
for i in {1..10}; do
  curl http://localhost:8080/ &
done
wait

# Check logs in Terminal 1 for thread pool status
```

## 🐛 Troubleshooting

### Problem: Port already in use
```
Error: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or use a different port
python3 server.py 9000
```

### Problem: Permission denied
```
Permission denied: './server.py'
```

**Solution:**
```bash
# Make executable
chmod +x server.py

# Or run with python3
python3 server.py
```

### Problem: Module not found
```
ModuleNotFoundError: No module named 'PIL'
```

**Solution:**
This only affects image generation (already done). The server itself has **zero dependencies** and uses only Python standard library.

### Problem: Tests fail
```
✗ Server is NOT running
```

**Solution:**
```bash
# Make sure server is running first
python3 server.py

# Then run tests in a different terminal
python3 test_client.py
```

## 📖 Next Steps

### 1. Explore the Code
```bash
# Open in your favorite editor
code server.py          # VS Code
vim server.py          # Vim
nano server.py         # Nano
```

### 2. Read Documentation
- **README.md** - Complete technical documentation
- **SUBMISSION_GUIDE.md** - How to submit to GitHub
- **PROJECT_SUMMARY.md** - Project overview and checklist

### 3. Customize
- Modify `DEFAULT_PORT` in server.py
- Add new HTML pages in resources/
- Add new file types in `_handle_get()` method
- Extend test suite in test_client.py

### 4. Submit
Follow the steps in **SUBMISSION_GUIDE.md**:
1. Create GitHub repository
2. Push all files
3. Submit repository link

## 🎓 Learning Resources

### Understanding the Code

**Key Concepts to Study:**
1. **Socket Programming** → Lines 1-50 in server.py
2. **Thread Pool** → Lines 100-200 in server.py
3. **HTTP Parsing** → Lines 50-100 in server.py
4. **Binary Transfer** → Lines 400-500 in server.py
5. **Security** → Lines 350-400 in server.py

**Important Functions:**
- `HTTPServer.start()` - Main server loop
- `ThreadPool._worker()` - Worker thread logic
- `HTTPServer._handle_client()` - Request processing
- `HTTPRequest._parse()` - HTTP parsing
- `HTTPServer._handle_get()` - GET request handler
- `HTTPServer._handle_post()` - POST request handler

## ✅ Quick Checklist

Before submitting, verify:

- [ ] Server starts without errors
- [ ] Can access http://localhost:8080/ in browser
- [ ] All HTML pages load correctly
- [ ] Images download correctly
- [ ] POST /upload creates files
- [ ] All 12 tests pass
- [ ] Security tests block malicious requests
- [ ] Logs show thread pool activity
- [ ] README.md is complete
- [ ] All test files present

## 🎉 Success Criteria

Your setup is working when:

1. ✅ Server starts and shows startup message
2. ✅ Browser displays beautiful home page
3. ✅ `test_client.py` shows 12/12 tests passed
4. ✅ Binary files download without corruption
5. ✅ POST creates JSON files in uploads/
6. ✅ Security tests return 403/400 errors
7. ✅ Logs show thread activity

## 💡 Pro Tips

### 1. Keep Server Running
Use two terminals: one for server, one for testing.

### 2. Check Logs
Server logs show everything happening in real-time.

### 3. Test Often
Run `test_client.py` after any changes.

### 4. Use Browser DevTools
Press F12 to see network requests and responses.

### 5. Read the Logs
Server logs are incredibly detailed and helpful.

## 📞 Need Help?

1. **Check README.md** - Comprehensive documentation
2. **Run tests** - `python3 test_client.py` shows what's working
3. **Check logs** - Server output shows detailed information
4. **Verify files** - Make sure all test files exist

## 🚀 You're Ready!

Everything is set up and ready to go. Just:

1. Start the server: `python3 server.py`
2. Run the tests: `python3 test_client.py`
3. Submit to GitHub (see SUBMISSION_GUIDE.md)

**Expected Result**: Full marks! ✅

---

**Happy Testing! 🎯**

If all tests pass, you're ready to submit with confidence! 🏆

