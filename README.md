# Multi-threaded HTTP Server

A production-grade HTTP/1.1 server implementation from scratch using low-level socket programming.

## 🚀 Quick Start

```bash
# Start the server
python3 server.py

# Run tests
python3 test_client.py

# Access in browser
http://localhost:8080/
```

## 📁 Project Structure

```
CN_Project/
├── server.py              # Main HTTP server
├── test_client.py         # Comprehensive test suite
├── Documentations/        # Complete documentation
│   ├── README.md          # Full technical documentation
│   ├── GETTING_STARTED.md
│   ├── SUBMISSION_GUIDE.md
│   ├── PROJECT_SUMMARY.md
│   └── REQUIREMENTS_VERIFICATION.md
├── resources/             # Static files
│   ├── *.html            # Web pages
│   ├── *.png, *.jpg      # Images
│   ├── *.txt             # Text files
│   └── uploads/          # POST uploads
└── scripts/              # Test scripts
```

## 📚 Documentation

**Complete documentation is in the `Documentations/` folder:**

- **[Documentations/README.md](Documentations/README.md)** - Complete technical guide (start here!)
- **[Documentations/GETTING_STARTED.md](Documentations/GETTING_STARTED.md)** - Quick 3-step guide
- **[Documentations/SUBMISSION_GUIDE.md](Documentations/SUBMISSION_GUIDE.md)** - How to submit to GitHub
- **[Documentations/PROJECT_SUMMARY.md](Documentations/PROJECT_SUMMARY.md)** - Requirements checklist
- **[Documentations/REQUIREMENTS_VERIFICATION.md](Documentations/REQUIREMENTS_VERIFICATION.md)** - Line-by-line verification

## ✅ Requirements Met

- ✅ Multi-threaded server with thread pool
- ✅ TCP socket programming
- ✅ GET and POST requests
- ✅ Binary file transfer
- ✅ Security (path traversal + host validation)
- ✅ HTTP keep-alive
- ✅ Comprehensive logging
- ✅ 12/12 tests passing

## 🎯 Features

- **Zero dependencies** (Python standard library only)
- **Thread pool** with configurable size
- **Binary file integrity** verified
- **Large file support** (tested with 25MB+)
- **Security features** (path traversal protection, host validation)
- **Beautiful UI** with modern design

## 📊 Test Results

```bash
python3 test_client.py
# Result: 12/12 tests passed (100%)
```

## 📞 Need Help?

See **[Documentations/GETTING_STARTED.md](Documentations/GETTING_STARTED.md)** for detailed instructions.

---

**Built with Python 3 | Socket Programming | Threading**

