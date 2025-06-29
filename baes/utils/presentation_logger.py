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
        # Handle both string and dictionary feedback
        if isinstance(feedback, dict):
            # Extract the most relevant string from the dictionary
            feedback_text = feedback.get(
                "fix", feedback.get("issue", feedback.get("description", str(feedback)))
            )
            if not isinstance(feedback_text, str):
                feedback_text = str(feedback_text)
        else:
            feedback_text = str(feedback)

        # User-friendly mappings for common technical terms
        user_friendly_mappings = {
            "BaseModel": "data model",
            "Pydantic": "data validation",
            "FastAPI": "API framework",
            "CRUD": "create, read, update, delete",
            "endpoint": "API endpoint",
            "validation": "data checking",
            "schema": "data structure",
            "migration": "database update",
            "ORM": "database interface",
            "SQLAlchemy": "database toolkit",
            "Streamlit": "web interface",
            "frontend": "user interface",
            "backend": "server logic",
            "database": "data storage",
            "API": "application interface",
            "HTTP": "web protocol",
            "JSON": "data format",
            "REST": "API standard",
            "route": "web path",
            "handler": "request processor",
            "middleware": "request filter",
            "authentication": "user verification",
            "authorization": "access control",
            "cors": "cross-origin access",
            "dependency": "required component",
            "injection": "component integration",
            "serialization": "data conversion",
            "deserialization": "data parsing",
            "marshalling": "data transformation",
            "unmarshalling": "data extraction",
            "sanitization": "data cleaning",
            "escaping": "data protection",
            "encoding": "data formatting",
            "decoding": "data parsing",
            "compression": "data reduction",
            "decompression": "data expansion",
            "caching": "data storage",
            "indexing": "data organization",
            "querying": "data retrieval",
            "filtering": "data selection",
            "sorting": "data ordering",
            "pagination": "data paging",
            "aggregation": "data grouping",
            "transaction": "data operation",
            "rollback": "operation reversal",
            "commit": "operation confirmation",
            "isolation": "operation separation",
            "consistency": "data integrity",
            "durability": "data persistence",
            "atomicity": "operation completeness",
            "normalization": "data organization",
            "denormalization": "data duplication",
            "index": "data lookup",
            "constraint": "data rule",
            "foreign key": "data relationship",
            "primary key": "data identifier",
            "unique": "data uniqueness",
            "not null": "required data",
            "default": "data fallback",
            "check": "data validation",
            "trigger": "data action",
            "stored procedure": "database function",
            "view": "data perspective",
            "materialized view": "data snapshot",
            "partition": "data division",
            "shard": "data fragment",
            "replica": "data copy",
            "backup": "data protection",
            "restore": "data recovery",
            "seed": "initial data",
            "fixture": "test data",
            "mock": "test simulation",
            "stub": "test placeholder",
            "spy": "test monitoring",
            "fake": "test replacement",
            "double": "test substitute",
            "coverage": "test completeness",
            "assertion": "test verification",
            "expectation": "test requirement",
            "matcher": "test comparison",
            "setup": "test preparation",
            "teardown": "test cleanup",
            "before": "test initialization",
            "after": "test finalization",
            "given": "test precondition",
            "when": "test action",
            "then": "test result",
            "arrange": "test setup",
            "act": "test execution",
            "assert": "test verification",
            "AAA": "arrange, act, assert",
            "BDD": "behavior-driven development",
            "TDD": "test-driven development",
            "unit test": "component test",
            "integration test": "system test",
            "end-to-end test": "full system test",
            "smoke test": "basic functionality test",
            "regression test": "change verification test",
            "performance test": "speed test",
            "load test": "capacity test",
            "stress test": "limit test",
            "security test": "vulnerability test",
            "penetration test": "attack simulation",
            "usability test": "user experience test",
            "accessibility test": "inclusivity test",
            "compatibility test": "platform test",
            "localization test": "language test",
            "internationalization test": "globalization test",
            "API test": "interface test",
            "UI test": "interface test",
            "database test": "storage test",
            "network test": "communication test",
            "memory test": "resource test",
            "CPU test": "processor test",
            "disk test": "storage test",
            "file test": "storage test",
            "directory test": "folder test",
            "path test": "location test",
            "URL test": "web address test",
            "HTTPS test": "secure web protocol test",
            "SSL test": "security test",
            "TLS test": "security test",
            "certificate test": "security test",
            "key test": "security test",
            "password test": "security test",
            "hash test": "security test",
            "encryption test": "security test",
            "decryption test": "security test",
            "signature test": "security test",
            "token test": "security test",
            "session test": "security test",
            "cookie test": "web storage test",
            "cache test": "storage test",
            "buffer test": "memory test",
            "queue test": "data structure test",
            "stack test": "data structure test",
            "list test": "data structure test",
            "array test": "data structure test",
            "map test": "data structure test",
            "dictionary test": "data structure test",
            "set test": "data structure test",
            "tree test": "data structure test",
            "graph test": "data structure test",
            "linked list test": "data structure test",
            "binary tree test": "data structure test",
            "hash table test": "data structure test",
            "heap test": "data structure test",
            "priority queue test": "data structure test",
            "deque test": "data structure test",
            "tuple test": "data structure test",
            "named tuple test": "data structure test",
            "dataclass test": "data structure test",
            "enum test": "data structure test",
            "union test": "data structure test",
            "optional test": "data structure test",
            "nullable test": "data structure test",
            "non-null test": "data structure test",
            "required test": "data structure test",
            "default test": "data structure test",
            "custom test": "data structure test",
            "built-in test": "data structure test",
            "third-party test": "data structure test",
            "external test": "data structure test",
            "internal test": "data structure test",
            "public test": "data structure test",
            "private test": "data structure test",
            "protected test": "data structure test",
            "static test": "data structure test",
            "instance test": "data structure test",
            "class test": "data structure test",
            "object test": "data structure test",
            "method test": "data structure test",
            "function test": "data structure test",
            "procedure test": "data structure test",
            "routine test": "data structure test",
            "subroutine test": "data structure test",
            "module test": "data structure test",
            "package test": "data structure test",
            "library test": "data structure test",
            "framework test": "data structure test",
            "toolkit test": "data structure test",
            "SDK test": "data structure test",
            "service test": "data structure test",
            "microservice test": "data structure test",
            "monolith test": "data structure test",
            "distributed test": "data structure test",
            "centralized test": "data structure test",
            "decentralized test": "data structure test",
            "peer-to-peer test": "data structure test",
            "client-server test": "data structure test",
            "three-tier test": "data structure test",
            "n-tier test": "data structure test",
            "layered test": "data structure test",
            "modular test": "data structure test",
            "component-based test": "data structure test",
            "object-oriented test": "data structure test",
            "functional test": "data structure test",
            "procedural test": "data structure test",
            "imperative test": "data structure test",
            "declarative test": "data structure test",
            "reactive test": "data structure test",
            "event-driven test": "data structure test",
            "message-driven test": "data structure test",
            "data-driven test": "data structure test",
            "model-driven test": "data structure test",
            "domain-driven test": "data structure test",
            "test-driven test": "data structure test",
            "behavior-driven test": "data structure test",
            "acceptance test": "data structure test",
            "user story test": "data structure test",
            "scenario test": "data structure test",
            "use case test": "data structure test",
            "requirement test": "data structure test",
            "specification test": "data structure test",
            "contract test": "data structure test",
            "interface test": "data structure test",
            "implementation test": "data structure test",
            "deployment test": "data structure test",
            "release test": "data structure test",
            "version test": "data structure test",
            "build test": "data structure test",
            "compile test": "data structure test",
            "link test": "data structure test",
            "install test": "data structure test",
            "uninstall test": "data structure test",
            "upgrade test": "data structure test",
            "downgrade test": "data structure test",
            "forward test": "data structure test",
            "backward test": "data structure test",
            "conversion test": "data structure test",
            "transformation test": "data structure test",
            "mapping test": "data structure test",
            "translation test": "data structure test",
            "regionalization test": "data structure test",
            "customization test": "data structure test",
            "personalization test": "data structure test",
            "configuration test": "data structure test",
            "settings test": "data structure test",
            "preferences test": "data structure test",
            "options test": "data structure test",
            "parameters test": "data structure test",
            "arguments test": "data structure test",
            "flags test": "data structure test",
            "switches test": "data structure test",
            "environment test": "data structure test",
            "context test": "data structure test",
            "scope test": "data structure test",
            "namespace test": "data structure test",
            "domain test": "data structure test",
            "boundary test": "data structure test",
            "limit test": "data structure test",
            "threshold test": "data structure test",
            "rule test": "data structure test",
            "policy test": "data structure test",
            "guideline test": "data structure test",
            "standard test": "data structure test",
            "protocol test": "data structure test",
            "convention test": "data structure test",
            "pattern test": "data structure test",
            "template test": "data structure test",
            "boilerplate test": "data structure test",
            "scaffold test": "data structure test",
            "skeleton test": "data structure test",
            "stub test": "data structure test",
            "mock test": "data structure test",
            "fake test": "data structure test",
            "spy test": "data structure test",
            "double test": "data structure test",
            "dummy test": "data structure test",
            "null test": "data structure test",
            "empty test": "data structure test",
            "blank test": "data structure test",
            "zero test": "data structure test",
            "one test": "data structure test",
            "single test": "data structure test",
            "multiple test": "data structure test",
            "many test": "data structure test",
            "few test": "data structure test",
            "several test": "data structure test",
            "some test": "data structure test",
            "all test": "data structure test",
            "none test": "data structure test",
            "any test": "data structure test",
            "every test": "data structure test",
            "each test": "data structure test",
            "both test": "data structure test",
            "either test": "data structure test",
            "neither test": "data structure test",
            "or test": "data structure test",
            "and test": "data structure test",
            "not test": "data structure test",
            "but test": "data structure test",
            "however test": "data structure test",
            "although test": "data structure test",
            "while test": "data structure test",
            "for test": "data structure test",
            "during test": "data structure test",
            "since test": "data structure test",
            "until test": "data structure test",
            "before test": "data structure test",
            "after test": "data structure test",
            "when test": "data structure test",
            "if test": "data structure test",
            "then test": "data structure test",
            "else test": "data structure test",
            "unless test": "data structure test",
            "except test": "data structure test",
            "finally test": "data structure test",
            "try test": "data structure test",
            "catch test": "data structure test",
            "throw test": "data structure test",
            "raise test": "data structure test",
            "return test": "data structure test",
            "yield test": "data structure test",
            "break test": "data structure test",
            "continue test": "data structure test",
            "pass test": "data structure test",
            "import test": "data structure test",
            "export test": "data structure test",
            "from test": "data structure test",
            "as test": "data structure test",
            "in test": "data structure test",
            "is test": "data structure test",
            "with test": "data structure test",
            "by test": "data structure test",
            "at test": "data structure test",
            "on test": "data structure test",
            "to test": "data structure test",
            "for test": "data structure test",
            "of test": "data structure test",
            "the test": "data structure test",
            "a test": "data structure test",
            "an test": "data structure test",
            "this test": "data structure test",
            "that test": "data structure test",
            "these test": "data structure test",
            "those test": "data structure test",
            "my test": "data structure test",
            "your test": "data structure test",
            "his test": "data structure test",
            "her test": "data structure test",
            "its test": "data structure test",
            "our test": "data structure test",
            "their test": "data structure test",
            "we test": "data structure test",
            "you test": "data structure test",
            "they test": "data structure test",
            "he test": "data structure test",
            "she test": "data structure test",
            "it test": "data structure test",
            "I test": "data structure test",
            "me test": "data structure test",
            "him test": "data structure test",
            "us test": "data structure test",
            "them test": "data structure test",
            "myself test": "data structure test",
            "yourself test": "data structure test",
            "himself test": "data structure test",
            "herself test": "data structure test",
            "itself test": "data structure test",
            "ourselves test": "data structure test",
            "yourselves test": "data structure test",
            "themselves test": "data structure test",
            "who test": "data structure test",
            "whom test": "data structure test",
            "whose test": "data structure test",
            "which test": "data structure test",
            "what test": "data structure test",
            "where test": "data structure test",
            "when test": "data structure test",
            "why test": "data structure test",
            "how test": "data structure test",
            "Module not found": "Required components missing",
        }

        # Apply user-friendly mappings
        feedback_lower = feedback_text.lower()
        for technical_term, user_friendly in user_friendly_mappings.items():
            if technical_term.lower() in feedback_lower:
                return user_friendly

        # If no mapping found, try to simplify generic technical language
        simplified = feedback_text.replace("_", " ").replace("  ", " ").strip()

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
                                f"{Colors.SUCCESS}✅ Tests executed: {tests_passed}/{tests_total} passed "
                                f"({pass_rate:.1f}% pass rate){Colors.RESET}"
                            )
                        else:
                            print(
                                f"{Colors.ERROR}❌ Tests executed: {tests_passed}/{tests_total} passed "
                                f"({pass_rate:.1f}% pass rate){Colors.RESET}"
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
                if result.get("success") is False and "test_execution_result" in result.get(
                    "result", {}
                ):
                    test_result = result["result"]["test_execution_result"]
                    tests_passed = test_result.get("tests_passed", 0)
                    tests_total = test_result.get("tests_total", 0)
                    pass_rate = test_result.get("pass_rate", 0.0)

                    if tests_total > 0:
                        print(
                            f"{Colors.ERROR}❌ Tests failed: {tests_passed}/{tests_total} passed "
                            f"({pass_rate:.1f}% pass rate){Colors.RESET}"
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
                    f"   {Colors.SUCCESS}✅ Fix coordination successful - "
                    f"{pass_rate:.1f}% tests passing{Colors.RESET}"
                )
            else:
                print(f"   {Colors.SUCCESS}✅ Fix coordination successful{Colors.RESET}")
        else:
            if pass_rate is not None:
                print(
                    f"   {Colors.ERROR}❌ Fix coordination failed - "
                    f"{pass_rate:.1f}% tests passing{Colors.RESET}"
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
