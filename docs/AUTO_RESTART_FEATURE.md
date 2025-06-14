# 🔄 Auto-Restart Feature - User Guide

## Overview

The BAE System includes an automatic server restart feature that ensures new entities appear immediately in the web UI without manual intervention. This is particularly useful for PoC demonstrations and multi-entity system development.

---

## 🎯 **Problem Solved**

**Before Auto-Restart:**
```bash
🏢 HBE> add student
✅ Student entity created successfully!
🌐 FastAPI: http://localhost:8100/docs
🎨 Streamlit: http://localhost:8600

🏢 HBE> add course
✅ Course entity created successfully!
# ❌ Course doesn't appear in web UI until manual restart
```

**After Auto-Restart:**
```bash
🏢 HBE> add student
✅ Student entity created successfully!
🌐 FastAPI: http://localhost:8100/docs
🎨 Streamlit: http://localhost:8600

🔄 HBE> add course
🔄 New entity detected! Refreshing servers to update web UI...
💡 For PoC: Auto-restarting servers to show new entity in web interface
🔄 Restarting servers...
✅ Servers restarted successfully!
# ✅ Course now appears immediately in web UI
```

---

## 🚀 **How to Use**

### **Default Behavior (Recommended)**
Auto-restart is **enabled by default** for seamless PoC demonstrations:

```bash
python bae_chat.py

🧠 BAE System - Conversational Interface
🔄 Auto-restart: New entities appear immediately in web UI

🏢 HBE> add student
# System creates student + starts servers

🔄 HBE> add course
🔄 New entity detected! Refreshing servers to update web UI...
# System automatically restarts servers to show course in UI

🔄 HBE> add teacher
🔄 New entity detected! Refreshing servers to update web UI...
# System automatically restarts servers to show teacher in UI
```

### **Configuration Commands**

#### **Check Current Status**
```bash
🔄 HBE> help
🛠️  System Management:
  • toggle auto restart - Auto-restart after entity changes (ON)
```

#### **Disable Auto-Restart**
```bash
🔄 HBE> toggle auto restart
⚠️  Auto-restart DISABLED - You'll need to manually restart servers to see new entities
💡 Use 'restart servers' command after adding entities to refresh the web UI
```

#### **Re-Enable Auto-Restart**
```bash
🔄 HBE> toggle auto restart
✅ Auto-restart ENABLED - Servers will restart automatically after adding new entities
💡 This ensures the web UI shows new entities immediately (recommended for PoC)
```

#### **Manual Server Management**
```bash
# Start servers manually (when auto-restart is disabled)
🔄 HBE> start servers

# Force restart servers manually
🔄 HBE> restart servers
```

---

## 🔧 **Technical Details**

### **When Auto-Restart Triggers**
The system automatically restarts servers when:

1. ✅ **New entity model generated** - A new entity (Student, Course, Teacher) is successfully created
2. ✅ **Servers already running** - Only restarts if servers are currently active
3. ✅ **Auto-restart enabled** - Feature is turned ON (default)
4. ✅ **Successful generation** - Entity creation completed without errors

### **When Auto-Restart Does NOT Trigger**
- ❌ Entity updates/modifications (not new entities)
- ❌ System errors or failed generations
- ❌ Servers not currently running
- ❌ Auto-restart feature disabled
- ❌ Regular operations that don't involve entity generation

### **Smart Detection Logic**
```python
# Check if new entity was actually created/added
execution_results = result.get("execution_results", [])
entity_added = any(
    task.get("success") and "model" in task.get("task", "")
    for task in execution_results
)

if entity_added:
    # Trigger auto-restart
    self._restart_servers()
```

### **Configuration Storage**
```python
# Stored in session state
self.current_system_state = {
    "auto_restart_on_entity_changes": True,  # Default: ON
    # ... other settings
}
```

---

## 🎭 **PoC Demonstration Benefits**

### **Seamless Multi-Entity Demos**
Perfect for demonstrating **Scenario 3: Multi-Entity System & Reusability**:

```bash
# Complete multi-entity system demo without interruption
🏢 HBE> Create a student management system
✅ Student system created!

🔄 HBE> Add course management to the system
🔄 Auto-restart triggered → Course appears in UI immediately

🔄 HBE> Add teacher management to the system
🔄 Auto-restart triggered → Teacher appears in UI immediately

# Result: Complete academic system (Student + Course + Teacher)
# with web UI showing all entities without manual intervention
```

### **Business Expert Experience**
- **Immediate Feedback**: New entities appear instantly in web interface
- **No Technical Interruption**: No need to understand server management
- **Demonstration Flow**: Smooth presentation without manual restarts
- **User Confidence**: Clear feedback about what's happening and why

---

## ⚙️ **Configuration Options**

### **Environment Variable Override**
```bash
# Disable auto-restart via environment variable
export BAE_AUTO_RESTART=false
python bae_chat.py
```

### **Programmatic Configuration**
```python
# In bae_chat.py initialization
self.current_system_state["auto_restart_on_entity_changes"] = False
```

### **Session Persistence**
Auto-restart setting is saved in `bae_session.json` and restored between sessions.

---

## 🔍 **Troubleshooting**

### **Auto-Restart Not Working**
1. **Check setting**: `help` command shows current status
2. **Verify servers running**: Must have active servers to restart
3. **Check entity generation**: Only triggers for successful new entity creation
4. **Review logs**: Look for "New entity detected!" message

### **Disable for Manual Control**
```bash
🔄 HBE> toggle auto restart
⚠️  Auto-restart DISABLED
```

### **Force Manual Restart**
```bash
🔄 HBE> restart servers
🔄 Restarting servers...
✅ Servers restarted successfully!
```

---

## 📊 **Performance Impact**

- **Restart Time**: ~3-5 seconds for server restart
- **Data Preservation**: No data loss during restart
- **Availability**: Brief interruption (~2-3 seconds) during restart
- **Resource Usage**: Minimal - only restarts when necessary

---

## 🎯 **Best Practices**

### **For PoC Demonstrations**
- ✅ **Keep enabled** for seamless demos
- ✅ **Mention to audience** that auto-restart shows new entities immediately
- ✅ **Use for multi-entity scenarios** (Student → Course → Teacher)

### **For Development**
- ✅ **Enable during entity creation** for immediate feedback
- ⚠️ **Consider disabling** if frequently modifying existing entities
- ✅ **Use manual restart** for fine-grained control when needed

### **For Testing**
- ⚠️ **Disable during automated tests** to avoid interference
- ✅ **Test both modes** (auto-restart ON/OFF) for comprehensive validation

---

**🎉 This feature makes the BAE System demonstration flow seamless and professional, ensuring that new entities appear immediately in the web UI for an optimal user experience during PoC validation!**
