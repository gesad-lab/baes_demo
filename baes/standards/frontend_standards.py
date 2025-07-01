"""
Frontend Standards for FrontendSWEA Agent

Contains Streamlit-specific patterns and validation rules that FrontendSWEA
should follow and TechLeadSWEA should validate against.

These standards ensure consistency in UI generation and eliminate validation
misalignment for frontend code.
"""

from typing import Any, Dict

from .base_standards import BaseStandards


class FrontendStandards(BaseStandards):
    """
    Frontend-specific standards and validation rules for Streamlit UI generation.
    
    These standards define the exact patterns needed to pass TechLeadSWEA validation,
    particularly addressing UI component structure, form handling, and state management.
    """
    
    # Required imports for Streamlit frontend code
    REQUIRED_IMPORTS = {
        "streamlit": "import streamlit as st",
        "requests": "import requests",
        "typing": "from typing import Dict, List, Optional, Any",
        "json": "import json",
        "logging": "import logging",
        "datetime": "from datetime import datetime",
    }
    
    # UI Component patterns
    UI_PATTERNS = {
        "page_config": {
            "required": True,
            "pattern": "st.set_page_config(page_title=\"Entity Management\", page_icon=\"📊\", layout=\"wide\")",
            "placement": "beginning of file"
        },
        "sidebar": {
            "navigation": "with st.sidebar:",
            "title": "st.sidebar.title(\"Navigation\")",
            "buttons": "if st.sidebar.button(\"Action\"):"
        },
        "main_content": {
            "container": "with st.container():",
            "columns": "col1, col2 = st.columns(2)",
            "tabs": "tab1, tab2 = st.tabs([\"Tab 1\", \"Tab 2\"])"
        },
        "forms": {
            "form_context": "with st.form(\"entity_form\"):",
            "submit_button": "submitted = st.form_submit_button(\"Submit\")",
            "validation": "if submitted and field_value:"
        }
    }
    
    # Form handling patterns (CRITICAL - for data input)
    FORM_PATTERNS = {
        "input_fields": {
            "text_input": "st.text_input(\"Label\", key=\"unique_key\")",
            "number_input": "st.number_input(\"Label\", min_value=0, key=\"unique_key\")",
            "date_input": "st.date_input(\"Label\", key=\"unique_key\")",
            "selectbox": "st.selectbox(\"Label\", options=[], key=\"unique_key\")",
            "email_validation": "if \"@\" not in email_value:"
        },
        "form_structure": [
            "with st.form(\"form_name\"):",
            "# Input fields",
            "submitted = st.form_submit_button(\"Submit\")",
            "if submitted:",
            "# Validation logic",
            "# API call",
            "# Success/error handling"
        ],
        "validation_patterns": [
            "if not field_value:",
            "st.error(\"Field is required\")",
            "return",
            "# Proceed with submission"
        ]
    }
    
    # API integration patterns (CRITICAL - for backend communication)
    API_PATTERNS = {
        "base_url": "API_BASE_URL = \"http://localhost:8000\"",
        "endpoints": {
            "list": "response = requests.get(f\"{API_BASE_URL}/entities\")",
            "create": "response = requests.post(f\"{API_BASE_URL}/entities\", json=data)",
            "update": "response = requests.put(f\"{API_BASE_URL}/entities/{id}\", json=data)",
            "delete": "response = requests.delete(f\"{API_BASE_URL}/entities/{id}\")"
        },
        "error_handling": {
            "try_except": [
                "try:",
                "response = requests.get(url)",
                "response.raise_for_status()",
                "data = response.json()",
                "except requests.exceptions.RequestException as e:",
                "st.error(f\"API Error: {e}\")",
                "return"
            ],
            "status_codes": {
                "success": "if response.status_code == 200:",
                "created": "if response.status_code == 201:", 
                "no_content": "if response.status_code == 204:",
                "error": "if response.status_code >= 400:"
            }
        }
    }
    
    # State management patterns
    STATE_PATTERNS = {
        "session_state": {
            "initialization": "if 'key' not in st.session_state:",
            "setting": "st.session_state.key = value",
            "getting": "value = st.session_state.get('key', default)",
            "clearing": "if st.button('Clear'): st.session_state.clear()"
        },
        "refresh_pattern": [
            "if st.button('Refresh'):",
            "st.rerun()"
        ]
    }
    
    # Display patterns
    DISPLAY_PATTERNS = {
        "data_display": {
            "dataframe": "st.dataframe(data, use_container_width=True)",
            "table": "st.table(data)",
            "metrics": "st.metric(label=\"Label\", value=value)"
        },
        "messages": {
            "success": "st.success(\"Operation successful!\")",
            "error": "st.error(\"Error message\")",
            "warning": "st.warning(\"Warning message\")",
            "info": "st.info(\"Information message\")"
        },
        "layout": {
            "expander": "with st.expander(\"Section Title\"):",
            "tabs": "tab1, tab2 = st.tabs([\"Tab 1\", \"Tab 2\"])",
            "columns": "col1, col2, col3 = st.columns([1, 2, 1])"
        }
    }
    
    # Validation methods specific to frontend code
    @classmethod
    def validate_streamlit_structure(cls, code: str) -> Dict[str, Any]:
        """
        Validate Streamlit application structure and required components.
        """
        issues = []
        suggestions = []
        
        # NOTE: st.set_page_config is NOT required in entity pages as they are imported into main app
        # Entity pages are modules, not standalone Streamlit apps
        
        # Check for main content structure
        if "st.title" not in code and "st.header" not in code:
            issues.append("Missing page title or header")
            suggestions.append("Add st.title() or st.header() for page title")
        
        # Check for proper form structure
        if "st.form" in code:
            if "st.form_submit_button" not in code:
                issues.append("Form missing submit button")
                suggestions.append("Add st.form_submit_button() inside form context")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "priority": "REQUIRED"
        }
    
    @classmethod
    def validate_api_integration(cls, code: str) -> Dict[str, Any]:
        """
        Validate API integration patterns and error handling.
        """
        issues = []
        suggestions = []
        
        # Check for API base URL
        if "requests." in code and "API_BASE_URL" not in code:
            issues.append("Missing API_BASE_URL configuration")
            suggestions.append("Define API_BASE_URL constant for API endpoints")
        
        # Check for proper error handling
        if "requests." in code and "try:" not in code:
            issues.append("Missing error handling for API requests")
            suggestions.append("Add try/except blocks around API calls")
        
        # Check for status code handling
        if "requests." in code and "raise_for_status" not in code:
            issues.append("Missing HTTP status code validation")
            suggestions.append("Add response.raise_for_status() after API calls")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "priority": "CRITICAL"
        }
    
    @classmethod
    def validate_form_handling(cls, code: str) -> Dict[str, Any]:
        """
        Validate form creation and input validation patterns.
        """
        issues = []
        suggestions = []
        
        # Check for form validation
        if "st.text_input" in code or "st.number_input" in code:
            if "if" not in code or "st.error" not in code:
                issues.append("Missing input validation and error messages")
                suggestions.append("Add validation logic with st.error() for user feedback")
        
        # Check for unique keys
        if "key=" not in code and ("st.text_input" in code or "st.number_input" in code):
            issues.append("Missing unique keys for input widgets")
            suggestions.append("Add unique key parameter to all input widgets")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "priority": "REQUIRED"
        }
    
    @classmethod
    def validate_ui_completeness(cls, code: str, entity: str) -> Dict[str, Any]:
        """
        Validate that all required UI components are implemented.
        """
        issues = []
        suggestions = []
        
        required_sections = ["create", "list", "update", "delete"]
        
        # Check for CRUD operations
        entity_lower = entity.lower()
        for operation in required_sections:
            operation_pattern = f"{operation}_{entity_lower}"
            if operation_pattern not in code.lower() and operation not in code.lower():
                issues.append(f"Missing {operation} functionality for {entity}")
                suggestions.append(f"Add {operation} section with proper form and API integration")
                break
        
        # Check for navigation
        if "st.sidebar" not in code and "st.tabs" not in code:
            issues.append("Missing navigation structure")
            suggestions.append("Add sidebar navigation or tabs for different operations")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "priority": "CRITICAL"
        }
    
    @classmethod
    def get_frontend_validation(cls, code: str, entity: str) -> Dict[str, Any]:
        """
        Run comprehensive frontend validation against all standards.
        
        This method performs all the validations that TechLeadSWEA should use
        to ensure consistency between generation and validation.
        
        NOTE: Frontend code does NOT use base standards (backend-specific requirements
        like logger.error(), docstrings, return type hints) as these are not applicable
        to Streamlit frontend applications.
        """
        # Run all frontend-specific validations
        structure_validation = cls.validate_streamlit_structure(code)
        api_validation = cls.validate_api_integration(code)
        form_validation = cls.validate_form_handling(code)
        ui_validation = cls.validate_ui_completeness(code, entity)
        
        # Frontend code does NOT use base standards (backend-specific requirements)
        # Base standards include logger.error(), docstrings, return type hints
        # which are not applicable to Streamlit frontend applications
        
        # Combine all issues and suggestions from frontend-specific validations only
        all_issues = (
            structure_validation["issues"] +
            api_validation["issues"] +
            form_validation["issues"] +
            ui_validation["issues"]
        )
        
        all_suggestions = (
            structure_validation["suggestions"] +
            api_validation["suggestions"] + 
            form_validation["suggestions"] +
            ui_validation["suggestions"]
        )
        
        # Calculate overall validity
        is_valid = len(all_issues) == 0
        quality_score = max(0.0, 1.0 - (len(all_issues) * 0.1))
        
        return {
            "is_valid": is_valid,
            "quality_score": quality_score,
            "issues": all_issues,
            "suggestions": all_suggestions,
            "validation_details": {
                "streamlit_structure": structure_validation,
                "api_integration": api_validation,
                "form_handling": form_validation,
                "ui_completeness": ui_validation,
                "base_standards": "Not applicable to frontend code"
            },
            "entity": entity
        } 