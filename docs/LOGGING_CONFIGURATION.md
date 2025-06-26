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
- ✅ **TechLeadSWEA Decision Logs**: Comprehensive decision summaries shown
- ❌ **HTTP request logs**: Suppressed (too verbose for normal use)

**Example normal output:**
```bash
🧠 BAE System - Conversational Interface
INFO:baes.domain_entities.academic.student_bae:StudentBAE initialized
INFO:baes.core.enhanced_runtime_kernel:🧠 Enhanced Runtime Kernel initialized
📊 TechLeadSWEA ARCHITECTURE DECISION SUMMARY:
   🎯 Entity: Student
   🏗️ Architecture Patterns: domain_driven_design, restful_api, mvc_pattern
   💻 Technology Stack: python_fastapi_streamlit
   📋 Decision: ARCHITECTURE APPROVED with technical specifications
```

### **Debug Mode (BAE_DEBUG=1)**
- ✅ **All system logs**: Everything shown including debug level
- ✅ **HTTP request logs**: Full HTTP request/response details
- ✅ **Enhanced debugging**: More verbose output for troubleshooting

**Example debug output:**
```bash
🐛 Debug mode enabled - HTTP request logs will be shown
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
DEBUG:httpx:load_ssl_context verify=True cert=None trust_env=True http2=False
📊 TechLeadSWEA HYBRID COORDINATION DECISION SUMMARY:
   🎯 Entity: Student
   🔧 Execution Type: creation_validation
   📋 Decision: COORDINATION APPROVED with enhanced oversight
```

---

## 📊 **TechLeadSWEA Decision Logging**

### **Overview**
All TechLeadSWEA decisions are automatically logged with comprehensive summaries for full traceability and governance visibility.

### **Decision Types Logged**

#### **🏗️ Architecture Decisions**
```
📊 TechLeadSWEA ARCHITECTURE DECISION SUMMARY:
   🎯 Entity: [EntityName]
   🏗️ Architecture Patterns: [patterns]
   💻 Technology Stack: [stack]
   ⚡ Performance Level: [level]
   🔒 Security Level: [level]
   📋 Business Requirements: [count] analyzed
   🎯 Domain Focus: [enabled/standard]
   📋 Decision: ARCHITECTURE APPROVED with technical specifications
```

#### **🤖 System Coordination Decisions**
```
📊 TechLeadSWEA COORDINATION DECISION SUMMARY:
   🎯 Entity: [EntityName]
   🔧 Execution Type: [type]
   🤖 SWEA Assignments: [assignments]
   ⚖️ Quality Gates: [count] defined
   🎯 Business Focus: [enabled/disabled]
   📋 Decision: COORDINATION APPROVED with [oversight_level] oversight
```

#### **⚔️ Conflict Resolution Decisions**
```
📊 TechLeadSWEA CONFLICT RESOLUTION DECISION SUMMARY:
   🎯 Entity: [EntityName]
   ⚔️ Conflict Type: [type]
   🤖 Involved SWEAs: [list]
   🎯 Resolution Strategy: [strategy]
   ⚖️ Priority Assignments: [assignments]
   🔧 Technical Constraints: [count] defined
   📋 Decision: CONFLICT RESOLVED with technical authority
```

#### **🔍 Test Failure Analysis Decisions**
```
📊 TechLeadSWEA TEST FAILURE ANALYSIS DECISION:
   🎯 Entity: [EntityName]
   🔍 Issue Type: [type]
   🤖 Responsible SWEA: [assignment]
   🔧 Recommended Action: [action]
   ⚖️ Priority: [high/medium/low]
   💡 Technical Rationale: [rationale]
   📋 Decision: FAILURE ANALYSIS COMPLETE with fix assignment
```

#### **📋 Final Review Decisions**
```
📊 TechLeadSWEA FINAL SYSTEM REVIEW SUMMARY:
   🎯 Entity: [EntityName]
   📊 Overall Quality Score: [score]
   🧪 Test Results: [passed/failed]
   🔍 Code Quality: [level]
   🎯 Business Alignment: [score]
   📋 Decision: SYSTEM [APPROVED/REJECTED] for [reason]
```

---

## 🎯 **Usage Examples**

### **Normal Operation (Clean Output)**
```bash
# Run BAE with clean, professional output
python bae_chat.py
```

### **Debug Mode (Full Visibility)**
```bash
# Run BAE with full debugging and HTTP logs
BAE_DEBUG=1 python bae_chat.py
```

### **Environment File Setup**
```bash
# In your .env file
BAE_DEBUG=0  # Normal mode (default)
# BAE_DEBUG=1  # Debug mode
```

---

## 🔧 **Technical Implementation**

### **Suppressed Loggers**
- `httpx` → WARNING level (unless debug mode)
- HTTP request details filtered out by default

### **Enhanced Loggers**
- `baes.swea_agents.techlead_swea` → Comprehensive decision summaries
- All BAE components → Structured, informative messages
- System coordination → Full traceability

### **Configuration Points**
- `bae_chat.py` main CLI
- `enhanced_runtime_kernel.py` CLI interface  
- `openai_client.py` initialization
- All TechLeadSWEA decision methods

---

## 🚀 **Benefits**

### **For Development**
- 🔍 **Full Traceability**: Every TechLeadSWEA decision is logged and explained
- 🐛 **Debugging**: Complete HTTP request visibility when needed
- 📊 **Performance**: Clean output for normal operations

### **For Demonstrations**
- ✨ **Professional Output**: Clean, focused CLI for PoC demos
- 📈 **Decision Transparency**: Clear governance and decision-making visibility
- 🎯 **Technical Authority**: Full TechLeadSWEA decision audit trail

### **For Production**
- 🔒 **Audit Trail**: Complete record of all technical decisions
- 📊 **Quality Assurance**: Comprehensive logging of quality gates and reviews
- 🤖 **Governance**: Full SWEA coordination and conflict resolution tracking

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