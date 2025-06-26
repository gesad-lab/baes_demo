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
- ✅ **TechLeadSWEA Decision Logs**: Concise decision summaries shown
- ❌ **HTTP request logs**: Suppressed (too verbose for normal use)

**Example normal output:**
```bash
🧠 BAE System - Conversational Interface
INFO:baes.domain_entities.academic.student_bae:StudentBAE initialized
INFO:baes.core.enhanced_runtime_kernel:Processing student entity generation
🧠 TechLeadSWEA COORDINATION: StudentEntity → APPROVED (4 SWEA tasks scheduled)
   📋 Type: creation
   📋 Attributes: 5
   📋 Quality Gates: 3
```

### **Debug Mode (BAE_DEBUG=1)**
- ✅ **All system logs**: Complete operation visibility
- ✅ **HTTP request logs**: Full OpenAI API request/response logging
- ✅ **Enhanced decision logs**: Detailed TechLeadSWEA decision context

**Example debug output:**
```bash
🐛 Debug mode enabled - HTTP request logs will be shown
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
🧠 TechLeadSWEA ARCHITECTURE: StudentEntity → APPROVED (python_fastapi stack)
   📋 Patterns: mvc, rest
   📋 Performance: high
   📋 Security: standard
```

---

## 🧠 **TechLeadSWEA Decision Logging**

### **Centralized Decision Logging**
All TechLeadSWEA decisions use a centralized `_log_decision()` method that provides:
- **Consistent format**: `🧠 TechLeadSWEA [TYPE]: [Entity] → [Decision] ([Rationale])`
- **Context details**: Key decision factors shown as sub-items
- **DRY principle**: No code duplication across decision types
- **Concise output**: Brief but informative summaries

### **Decision Types Logged**

#### **1. 🏗️ Architecture Decisions**
```
🧠 TechLeadSWEA ARCHITECTURE: ProjectEntity → APPROVED (python_fastapi stack)
   📋 Patterns: mvc, rest
   📋 Performance: high
   📋 Security: standard
```

#### **2. 🤖 System Coordination**
```
🧠 TechLeadSWEA COORDINATION: ProjectEntity → APPROVED (5 SWEA tasks scheduled)
   📋 Type: creation
   📋 Attributes: 4
   📋 Quality Gates: 3
```

#### **3. 📋 Review Decisions**
```
🧠 TechLeadSWEA REVIEW: ProjectEntity → REJECTED (quality score 0.65)
   📋 Component: BackendSWEA.generate_model
   📋 Retry Attempt: 1
   📋 Issues Found: 3
```

#### **4. ⚔️ Conflict Resolution**
```
🧠 TechLeadSWEA CONFLICT_RESOLUTION: ProjectEntity → RESOLVED (priority_based strategy)
   📋 Conflict Type: resource_conflict
   📋 Involved Sweas: BackendSWEA, TestSWEA
   📋 Constraints: 2
```

#### **5. 🔍 Test Failure Analysis**
```
🧠 TechLeadSWEA TEST_FAILURE_ANALYSIS: ProjectEntity → ANALYZED (dependency issue)
   📋 Issue Type: dependency_management
   📋 Responsible Swea: BackendSWEA
   📋 Priority: high
```

#### **6. 🎯 Final System Review**
```
🧠 TechLeadSWEA FINAL_REVIEW: ProjectEntity → PASS (quality score 0.85)
   📋 Components Reviewed: 4
   📋 Successful Components: 4
   📋 Deployment Ready: YES
```

#### **7. 🧠 Hybrid Coordination**
```
🧠 TechLeadSWEA HYBRID_COORDINATION: ProjectEntity → APPROVED (strict validation passed)
   📋 Execution Type: creation_validation
   📋 Artifacts: 4
   📋 Fix Iterations: 0
```

---

## 🎯 **Usage Examples**

### **Normal Operation (Clean Output)**
```bash
python bae_chat.py
# Shows only essential decisions and system messages
```

### **Debug Mode (Verbose Output)**
```bash
BAE_DEBUG=1 python bae_chat.py
# Shows HTTP requests, detailed context, and full decision traces
```

### **Testing with Decision Logs**
```bash
python -m pytest tests/integration/test_techlead_governance.py -s
# See TechLeadSWEA decisions during test execution
```

---

## 🔧 **Implementation Benefits**

### **DRY Principle Applied**
- ✅ **Single method**: `_log_decision()` handles all decision logging
- ✅ **No duplication**: Eliminated 200+ lines of repetitive logging code
- ✅ **Consistent format**: All decisions follow the same pattern
- ✅ **Easy maintenance**: Changes apply to all decision types

### **Improved User Experience**
- ✅ **Concise summaries**: Key information without noise
- ✅ **Structured format**: Easy to scan and understand
- ✅ **Context-aware**: Shows relevant details for each decision type
- ✅ **Debug flexibility**: Full details available when needed

### **Better Code Quality**
- ✅ **Maintainable**: Single point of change for logging format
- ✅ **Testable**: Easy to verify decision logging behavior
- ✅ **Extensible**: Simple to add new decision types
- ✅ **Clean**: Reduced code complexity and duplication

---

## 🚨 **Troubleshooting**

### **No Decision Logs Showing**
```bash
# Check if logging level is set correctly
export BAE_DEBUG=1
python your_script.py
```

### **Too Verbose Output**
```bash
# Disable debug mode for cleaner output
unset BAE_DEBUG
# or
export BAE_DEBUG=0
python your_script.py
```

### **Missing Context in Decisions**
Enable debug mode to see full decision context and HTTP request details.

---

## 📋 **Summary**

The BAE logging system now provides:
- **Clean default output** with essential decision summaries
- **Full debug capability** when needed for troubleshooting
- **Centralized decision logging** following DRY principles
- **Consistent format** across all TechLeadSWEA decisions
- **Context-aware details** for different decision types

This approach eliminates code duplication while providing clear visibility into TechLeadSWEA decision-making processes.

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