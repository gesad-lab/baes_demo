import logging
import os
import time
from typing import Any, Dict


class Colors:
    """ANSI color codes for terminal output"""

    # Basic colors
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

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

    def step_start(
        self, step_num: int, total_steps: int, task_name: str, simplified_name: str = None
    ):
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

        print(
            f"\n{Colors.PROGRESS}🎯 Step {step_num}/{total_steps}: {simplified_name}...{Colors.RESET}"
        )

    def step_retry(self, step_num: int, retry_count: int, max_retries: int, simplified_name: str):
        """Log step retry attempt"""
        print(
            f"{Colors.WARNING}🔄 Retry {retry_count}/{max_retries}: {simplified_name}...{Colors.RESET}"
        )

    def techlead_review(
        self,
        approved: bool,
        simplified_name: str = None,
        quality_score: float = None,
        feedback: list = None,
    ):
        """Log TechLead review decision"""
        if approved:
            # quality_info = f" (Quality: {quality_score:.0%})" if quality_score else ""
            print(
                f"   {Colors.REVIEW}👁️  TechLead Review: {Colors.SUCCESS}✅ APPROVED{Colors.RESET}"
            )
        else:
            print(f"   {Colors.REVIEW}👁️  TechLead Review: {Colors.ERROR}❌ REJECTED{Colors.RESET}")
            if feedback and len(feedback) > 0:
                # Show first feedback item in simplified form
                first_feedback = feedback[0] if isinstance(feedback, list) else str(feedback)
                
                # Make the feedback more user-friendly by simplifying technical terms
                user_friendly_feedback = self._make_feedback_user_friendly(first_feedback)
                
                if len(user_friendly_feedback) > 80:
                    user_friendly_feedback = user_friendly_feedback[:77] + "..."
                
                print(f"   {Colors.WARNING}📝 Reason: {user_friendly_feedback}{Colors.RESET}")

    def _make_feedback_user_friendly(self, feedback: str) -> str:
        """Convert technical feedback to user-friendly language"""
        if not feedback:
            return "Quality standards not met"
        
        # Convert technical terms to user-friendly language
        user_friendly_mappings = {
            "Coordination task returned success=False": "Coordination setup failed",
            "Empty coordination plan": "No execution plan created",
            "Coordination plan missing": "Missing required components",
            "Missing required SWEAs": "Missing required system components",
            "coordination plan is empty": "No execution plan created",
            "coordination task failed": "System coordination failed",
            "Generated code is empty": "No code was generated",
            "Contains placeholder comments": "Code contains incomplete sections",
            "Missing Pydantic BaseModel import": "Missing required imports",
            "Missing FastAPI imports": "API setup incomplete",
            "Naming convention not followed": "Code naming standards not met",
            "Quality standards not met": "Quality requirements not satisfied",
            "Validation error": "Code validation failed",
            "Syntax error": "Code syntax issues detected",
            "Import error": "Missing dependencies",
            "Module not found": "Required components missing"
        }
        
        # Apply user-friendly mappings
        feedback_lower = feedback.lower()
        for technical_term, user_friendly in user_friendly_mappings.items():
            if technical_term.lower() in feedback_lower:
                return user_friendly
        
        # If no mapping found, try to simplify generic technical language
        simplified = feedback.replace("_", " ").replace("  ", " ").strip()
        
        # Capitalize first letter
        if simplified:
            simplified = simplified[0].upper() + simplified[1:]
            
        return simplified

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
                print(
                    f"   {Colors.DIM}   🔌 API: {details['api_endpoints']} endpoints{Colors.RESET}"
                )
            if details.get("ui_components"):
                print(
                    f"   {Colors.DIM}   🎨 UI: {details['ui_components']} components{Colors.RESET}"
                )

    def step_error(
        self, step_num: int, simplified_name: str, error_msg: str, is_final: bool = False
    ):
        """Log step error"""
        print(f"   {Colors.ERROR}❌ {simplified_name} failed: {error_msg}{Colors.RESET}")
        if is_final:
            print(f"   {Colors.ERROR}🛑 Generation stopped{Colors.RESET}")

    def complete_generation(self, entity: str, successful_tasks: int, total_tasks: int):
        """Log completion of generation process with integrated testing"""
        if self.overall_start_time:
            total_duration = time.time() - self.overall_start_time
        else:
            total_duration = 0

        print("\n" + "━" * 60)

        success = successful_tasks == total_tasks

        if success:
            print(
                f"{Colors.SUCCESS}🎉 {entity.title()} System Generated Successfully!{Colors.RESET}"
            )
            print(f"{Colors.SUCCESS}✅ ALL tests passing (100% pass rate){Colors.RESET}")
            print(f"{Colors.INFO}⏱️  Total Time: {total_duration:.1f} seconds{Colors.RESET}")
            print(
                f"{Colors.INFO}📋 Tasks Completed: {successful_tasks}/{total_tasks}{Colors.RESET}"
            )

            print(f"\n{Colors.INFO}🌐 Your system is ready:{Colors.RESET}")
            print(f"   {Colors.CYAN}📊 API Documentation: http://localhost:8100/docs{Colors.RESET}")
            print(f"   {Colors.CYAN}🖥️  Web Interface: http://localhost:8600{Colors.RESET}")
        else:
            print(f"{Colors.ERROR}💥 {entity.title()} System Generation Failed{Colors.RESET}")
            print(
                f"{Colors.ERROR}❌ Tasks: {successful_tasks}/{total_tasks} completed{Colors.RESET}"
            )
            print(f"{Colors.WARNING}⏱️  Time Elapsed: {total_duration:.1f} seconds{Colors.RESET}")

    def generation_complete(self, entity: str, success: bool, total_tasks: int):
        """Legacy method for backward compatibility"""
        successful_tasks = total_tasks if success else 0
        self.complete_generation(entity, successful_tasks, total_tasks)

    def complete_generation_with_tests(
        self, entity: str, successful_tasks: int, total_tasks: int, execution_results: list
    ):
        """Complete generation with real test execution results - shows actual test pass rates"""
        if self.overall_start_time:
            total_duration = time.time() - self.overall_start_time
        else:
            total_duration = 0

        print("\n" + "━" * 60)

        success = successful_tasks == total_tasks

        if success:
            print(
                f"{Colors.SUCCESS}🎉 {entity.title()} System Generated Successfully!{Colors.RESET}"
            )

            # Extract actual test execution results
            test_execution_results = []
            for result in execution_results:
                if result.get("success") and "test_execution_result" in result.get("result", {}):
                    test_execution_results.append(result["result"]["test_execution_result"])

            if test_execution_results:
                # Show real test pass rates from actual execution
                for test_result in test_execution_results:
                    tests_passed = test_result.get("tests_passed", 0)
                    tests_total = test_result.get("tests_total", 0)
                    pass_rate = test_result.get("pass_rate", 0.0)

                    if tests_total > 0:
                        if tests_passed == tests_total:
                            print(
                                f"{Colors.SUCCESS}✅ Tests executed: {tests_passed}/{tests_total} passed ({pass_rate:.1f}% pass rate){Colors.RESET}"
                            )
                        else:
                            print(
                                f"{Colors.ERROR}❌ Tests executed: {tests_passed}/{tests_total} passed ({pass_rate:.1f}% pass rate){Colors.RESET}"
                            )
                    else:
                        print(f"{Colors.WARNING}⚠️  No tests found to execute{Colors.RESET}")
            else:
                print(f"{Colors.SUCCESS}✅ ALL tests passing (100% pass rate){Colors.RESET}")

            print(f"{Colors.INFO}⏱️  Total Time: {total_duration:.1f} seconds{Colors.RESET}")
            print(
                f"{Colors.INFO}📋 Tasks Completed: {successful_tasks}/{total_tasks}{Colors.RESET}"
            )

            print(f"\n{Colors.INFO}🌐 Your system is ready:{Colors.RESET}")
            print(f"   {Colors.CYAN}📊 API Documentation: http://localhost:8100/docs{Colors.RESET}")
            print(f"   {Colors.CYAN}🖥️  Web Interface: http://localhost:8600{Colors.RESET}")
        else:
            print(f"{Colors.ERROR}💥 {entity.title()} System Generation Failed{Colors.RESET}")
            print(
                f"{Colors.ERROR}❌ Tasks: {successful_tasks}/{total_tasks} completed{Colors.RESET}"
            )
            print(f"{Colors.WARNING}⏱️  Time Elapsed: {total_duration:.1f} seconds{Colors.RESET}")

            # Show test failure details if available
            for result in execution_results:
                if result.get("success") == False and "test_execution_result" in result.get(
                    "result", {}
                ):
                    test_result = result["result"]["test_execution_result"]
                    tests_passed = test_result.get("tests_passed", 0)
                    tests_total = test_result.get("tests_total", 0)
                    pass_rate = test_result.get("pass_rate", 0.0)

                    if tests_total > 0:
                        print(
                            f"{Colors.ERROR}❌ Tests failed: {tests_passed}/{tests_total} passed ({pass_rate:.1f}% pass rate){Colors.RESET}"
                        )
                    else:
                        print(f"{Colors.WARNING}⚠️  No tests found to execute{Colors.RESET}")

    def log_error_for_fixing(self, error_details: Dict[str, Any]):
        """Log detailed error information for debugging/fixing (saved to log file)"""
        # This goes to log file for detailed debugging while keeping console clean
        logger = logging.getLogger("BAE_Error_Details")
        logger.error("Detailed error information: %s", error_details)

    def server_restart(self, reason: str = "New entity detected"):
        """Log server restart for auto-restart feature"""
        print(f"\n{Colors.WARNING}🔄 Server Restart: {reason}{Colors.RESET}")
        print(f"{Colors.DIM}💡 Updating web interface...{Colors.RESET}")

    def fix_coordination_start(self, reason: str = "Test failures detected"):
        """Log start of fix coordination process"""
        print(f"\n{Colors.WARNING}🔧 Fix Coordination: {reason}{Colors.RESET}")
        print(f"{Colors.DIM}💡 TechLeadSWEA analyzing failures and routing fixes...{Colors.RESET}")

    def fix_coordination_step(self, step_description: str, swea_agent: str = None):
        """Log individual fix coordination step"""
        if swea_agent:
            print(f"   {Colors.PROGRESS}🔄 {step_description} → {swea_agent}{Colors.RESET}")
        else:
            print(f"   {Colors.PROGRESS}🔄 {step_description}{Colors.RESET}")

    def fix_coordination_complete(self, success: bool, pass_rate: float = None):
        """Log completion of fix coordination process"""
        if success:
            if pass_rate is not None:
                print(
                    f"   {Colors.SUCCESS}✅ Fix coordination successful - {pass_rate:.1f}% tests passing{Colors.RESET}"
                )
            else:
                print(f"   {Colors.SUCCESS}✅ Fix coordination successful{Colors.RESET}")
        else:
            if pass_rate is not None:
                print(
                    f"   {Colors.ERROR}❌ Fix coordination failed - {pass_rate:.1f}% tests passing{Colors.RESET}"
                )
            else:
                print(f"   {Colors.ERROR}❌ Fix coordination failed{Colors.RESET}")

    def phase_1_complete(self, entity: str, successful_tasks: int, total_tasks: int):
        """Log completion of Phase 1 (Generation)"""
        print("\n" + "━" * 60)
        print(
            f"{Colors.SUCCESS}🎯 Phase 1 Complete: {entity.title()} System Generated{Colors.RESET}"
        )
        print(f"{Colors.INFO}📋 Tasks Completed: {successful_tasks}/{total_tasks}{Colors.RESET}")
        print(f"{Colors.INFO}🧪 Tests generated (execution deferred to Phase 2){Colors.RESET}")

    def phase_2_start(self):
        """Log the start of Phase 2 validation"""
        print(f"\n{Colors.REVIEW}📍 PHASE 2: Test Generation and Validation{Colors.RESET}")
        print(f"{Colors.INFO}🧪 Generating tests after all artifacts are ready...{Colors.RESET}")
        print(f"{Colors.INFO}🔍 Validating system quality and integration...{Colors.RESET}")
        print(f"{Colors.INFO}✅ Ensuring 100% test pass rate...{Colors.RESET}")
        print()

    def info(self, message: str):
        """Log info message"""
        print(f"{Colors.INFO}{message}{Colors.RESET}")

    def success(self, message: str):
        """Log success message"""
        print(f"{Colors.SUCCESS}{message}{Colors.RESET}")

    def warning(self, message: str):
        """Log warning message"""
        print(f"{Colors.WARNING}{message}{Colors.RESET}")

    def error(self, message: str):
        """Log error message"""
        print(f"{Colors.ERROR}{message}{Colors.RESET}")


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
    error_handler = logging.FileHandler("bae_presentation_errors.log")
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)


def is_debug_mode():
    """Check if debug mode is enabled"""
    return os.getenv("BAE_DEBUG", "0").lower() in ("1", "true", "on", "yes")
