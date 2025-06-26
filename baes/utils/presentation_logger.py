import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

class Colors:
    """ANSI color codes for terminal output"""
    # Basic colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'
    
    # Combined colors for specific purposes
    SUCCESS = GREEN + BOLD
    ERROR = RED + BOLD
    WARNING = YELLOW + BOLD
    INFO = BLUE + BOLD
    PROGRESS = CYAN + BOLD
    REVIEW = MAGENTA + BOLD

class PresentationLogger:
    """
    Presentation-friendly logger for thesis demonstrations
    Features:
    - Clean, simplified output
    - Proper step progression with spacing
    - Color coding following best practices
    - Timing information
    - Retry display
    - TechLead decision logging
    """
    
    def __init__(self, name: str = "BAE_Presentation"):
        self.name = name
        self.step_timings = {}
        self.overall_start_time = None
        
    def start_generation(self, entity: str):
        """Start timing for overall generation process"""
        self.overall_start_time = time.time()
        print(f"\n{Colors.INFO}🚀 Starting {entity.title()} System Generation{Colors.RESET}")
        print("━" * 60)
        
    def step_start(self, step_num: int, total_steps: int, task_name: str, simplified_name: str = None):
        """Log step start with clean formatting"""
        if simplified_name is None:
            # Extract simplified name from technical task name
            if "coordinate_system_generation" in task_name:
                simplified_name = "TechLead Coordination"
            elif "setup_database" in task_name:
                simplified_name = "Database Setup"
            elif "generate_model" in task_name:
                simplified_name = "Model Generation"
            elif "generate_api" in task_name:
                simplified_name = "API Generation"
            elif "generate_ui" in task_name:
                simplified_name = "UI Generation"
            elif "generate_all_tests" in task_name:
                simplified_name = "Test Generation"
            elif "review_and_approve" in task_name:
                simplified_name = "Final Review"
            else:
                simplified_name = task_name.replace("_", " ").title()
        
        self.step_timings[step_num] = time.time()
        
        print(f"\n{Colors.PROGRESS}🎯 Step {step_num}/{total_steps}: {simplified_name}...{Colors.RESET}")
        
    def step_retry(self, step_num: int, retry_count: int, max_retries: int, simplified_name: str):
        """Log step retry attempt"""
        print(f"{Colors.WARNING}🔄 Retry {retry_count}/{max_retries}: {simplified_name}...{Colors.RESET}")
        
    def techlead_review(self, approved: bool, simplified_name: str = None, quality_score: float = None):
        """Log TechLead review decision"""
        if approved:
            quality_info = f" (Quality: {quality_score:.0%})" if quality_score else ""
            print(f"   {Colors.REVIEW}👁️  TechLead Review: {Colors.SUCCESS}✅ APPROVED{quality_info}{Colors.RESET}")
        else:
            print(f"   {Colors.REVIEW}👁️  TechLead Review: {Colors.ERROR}❌ REJECTED{Colors.RESET}")
            
    def step_success(self, step_num: int, simplified_name: str, details: Dict[str, Any] = None):
        """Log successful step completion with timing"""
        if step_num in self.step_timings:
            duration = time.time() - self.step_timings[step_num]
            timing_info = f" ({duration:.1f}s)"
        else:
            timing_info = ""
            
        print(f"   {Colors.SUCCESS}✅ {simplified_name} completed{timing_info}{Colors.RESET}")
        
        # Add simple details if provided
        if details:
            if details.get("database_created"):
                print(f"   {Colors.DIM}   📁 Database ready{Colors.RESET}")
            if details.get("model_lines"):
                print(f"   {Colors.DIM}   💻 Model: {details['model_lines']} lines{Colors.RESET}")
            if details.get("api_endpoints"):
                print(f"   {Colors.DIM}   🔌 API: {details['api_endpoints']} endpoints{Colors.RESET}")
            if details.get("ui_components"):
                print(f"   {Colors.DIM}   🎨 UI: {details['ui_components']} components{Colors.RESET}")
                
    def step_error(self, step_num: int, simplified_name: str, error_msg: str, is_final: bool = False):
        """Log step error"""
        print(f"   {Colors.ERROR}❌ {simplified_name} failed: {error_msg}{Colors.RESET}")
        if is_final:
            print(f"   {Colors.ERROR}🛑 Generation stopped{Colors.RESET}")
            
    def generation_complete(self, entity: str, success: bool, total_tasks: int):
        """Log completion of generation process"""
        if self.overall_start_time:
            total_duration = time.time() - self.overall_start_time
        else:
            total_duration = 0
            
        print("\n" + "━" * 60)
        
        if success:
            print(f"{Colors.SUCCESS}🎉 {entity.title()} System Generated Successfully!{Colors.RESET}")
            print(f"{Colors.INFO}⏱️  Total Time: {total_duration:.1f} seconds{Colors.RESET}")
            print(f"{Colors.INFO}📋 Tasks Completed: {total_tasks}{Colors.RESET}")
            
            print(f"\n{Colors.INFO}🌐 Your system is ready:{Colors.RESET}")
            print(f"   {Colors.CYAN}📊 API Documentation: http://localhost:8100/docs{Colors.RESET}")
            print(f"   {Colors.CYAN}🖥️  Web Interface: http://localhost:8600{Colors.RESET}")
        else:
            print(f"{Colors.ERROR}💥 {entity.title()} System Generation Failed{Colors.RESET}")
            print(f"{Colors.WARNING}⏱️  Time Elapsed: {total_duration:.1f} seconds{Colors.RESET}")
            
    def log_error_for_fixing(self, error_details: Dict[str, Any]):
        """Log detailed error information for debugging/fixing (saved to log file)"""
        # This goes to log file for detailed debugging while keeping console clean
        logger = logging.getLogger("BAE_Error_Details")
        logger.error("Detailed error information: %s", error_details)
        
    def server_restart(self, reason: str = "New entity detected"):
        """Log server restart for auto-restart feature"""
        print(f"\n{Colors.WARNING}🔄 Server Restart: {reason}{Colors.RESET}")
        print(f"{Colors.DIM}💡 Updating web interface...{Colors.RESET}")

# Global instance for easy access
presentation_logger = PresentationLogger()

def get_presentation_logger() -> PresentationLogger:
    """Get the global presentation logger instance"""
    return presentation_logger

def configure_presentation_logging():
    """Configure logging for presentation mode"""
    # Reduce verbosity of other loggers
    logging.getLogger("baes.domain_entities").setLevel(logging.WARNING)
    logging.getLogger("baes.swea_agents").setLevel(logging.WARNING)
    logging.getLogger("baes.core").setLevel(logging.WARNING)
    
    # Only show presentation logs and errors
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.ERROR)
    
    # Create error file handler for debugging details
    error_handler = logging.FileHandler('bae_presentation_errors.log')
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)

def is_debug_mode():
    """Check if debug mode is enabled"""
    return os.getenv("BAE_DEBUG", "0").lower() in ("1", "true", "on", "yes") 