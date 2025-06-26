# 📝 BAE Logging Configuration

## Overview

The BAE System includes configurable logging to help with debugging while keeping normal operation clean and focused. By default, verbose HTTP request logs are suppressed to reduce noise in the CLI output.

---

## 🔧 **Configuration**

### **Environment Variable**
```bash
BAE_DEBUG=0|1|true|false|on|off|yes|no
```

### **Default Behavior (BAE_DEBUG=0 or not set)**
- ✅ **System logs**: Normal BAE operation messages shown
- ✅ **Warning/Error logs**: Important issues displayed  
- ❌ **HTTP request logs**: Suppressed (too verbose for normal use)

**Example normal output:**
```bash
🧠 BAE System - Conversational Interface
INFO:baes.domain_entities.academic.student_bae:StudentBAE initialized
INFO:baes.core.enhanced_runtime_kernel:✅ Executed: DatabaseSWEA.setup_database
✅ System generation completed in 45.2 seconds!
```

### **Debug Mode (BAE_DEBUG=1)**
- ✅ **System logs**: Normal BAE operation messages shown
- ✅ **Warning/Error logs**: Important issues displayed
- ✅ **HTTP request logs**: Full OpenAI API request/response logging
- 🐛 **Debug indicator**: Shows when debug mode is active

**Example debug output:**
```bash
🐛 Debug mode enabled - HTTP request logs will be shown
🧠 BAE System - Conversational Interface
INFO:baes.domain_entities.academic.student_bae:StudentBAE initialized
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
INFO:baes.core.enhanced_runtime_kernel:✅ Executed: DatabaseSWEA.setup_database
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
✅ System generation completed in 45.2 seconds!
```

---

## 🚀 **Usage Examples**

### **Normal Operation (Default)**
```bash
python bae_chat.py
# or
BAE_DEBUG=0 python bae_chat.py
```

### **Debug Mode - Show All HTTP Requests**
```bash
BAE_DEBUG=1 python bae_chat.py
# or
BAE_DEBUG=true python bae_chat.py
# or
BAE_DEBUG=on python bae_chat.py
```

### **Permanent Debug Configuration**
Add to your `.env` file:
```bash
BAE_DEBUG=1
```

---

## 🔍 **What Gets Logged**

### **Always Shown (All Modes)**
- BAE initialization messages
- SWEA task execution status
- System generation progress
- Error messages and warnings
- User interaction feedback

### **Debug Mode Only**
- HTTP requests to OpenAI API
- Full request/response payloads (when needed)
- Detailed timing information
- Low-level system operations

---

## 🛠️ **Technical Details**

### **Implementation**
The logging configuration specifically targets the `httpx` logger used by the OpenAI client:

```python
httpx_logger = logging.getLogger("httpx")
if os.getenv("BAE_DEBUG", "0").lower() in ("1", "true", "on", "yes"):
    httpx_logger.setLevel(logging.DEBUG)  # Show all logs
else:
    httpx_logger.setLevel(logging.WARNING)  # Only warnings/errors
```

### **Applied Locations**
- ✅ `bae_chat.py` main CLI entry point
- ✅ `baes/llm/openai_client.py` OpenAI client initialization
- ✅ `baes/core/enhanced_runtime_kernel.py` CLI interface

### **Log Levels**
- `DEBUG (10)`: All messages including HTTP requests
- `INFO (20)`: Normal operation messages
- `WARNING (30)`: Important warnings (default for httpx in normal mode)
- `ERROR (40)`: Error conditions

---

## 🎯 **When to Use Debug Mode**

### **Enable Debug Mode When:**
- 🐛 Troubleshooting OpenAI API issues
- 🔍 Investigating slow response times
- 📊 Monitoring API usage patterns
- 🛠️ Developing new SWEA agents
- 📝 Creating detailed issue reports

### **Keep Normal Mode When:**
- 👤 Regular user operations
- 🎭 PoC demonstrations
- 📚 Learning the system
- 🚀 Production usage

---

## 📊 **Performance Impact**

### **Normal Mode**
- ✅ **Minimal logging overhead**: Only essential messages
- ✅ **Clean output**: Focus on business operations
- ✅ **Better UX**: Less noise for end users

### **Debug Mode**
- ⚠️ **Higher logging overhead**: All HTTP requests logged
- ⚠️ **Verbose output**: Detailed technical information
- ✅ **Better debugging**: Full context for troubleshooting

---

## ❓ **FAQ**

### **Q: Will debug mode slow down the system?**
A: Minimal impact. Logging is fast, but debug mode may produce more console output.

### **Q: Can I enable debug mode for specific requests only?**
A: Yes, set `BAE_DEBUG=1` for a single command:
```bash
BAE_DEBUG=1 python bae_chat.py
```

### **Q: What if I want to see some HTTP logs but not all?**
A: Currently it's all-or-nothing. Future versions may support granular log levels.

### **Q: Where are logs stored?**
A: Console output only. For persistent logging, redirect output:
```bash
python bae_chat.py > bae_output.log 2>&1
```

---

**🎯 This logging configuration ensures the BAE System provides clean, focused output for normal use while offering comprehensive debugging information when needed.** 