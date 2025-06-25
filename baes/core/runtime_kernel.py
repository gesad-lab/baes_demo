import argparse
import logging

from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel

logger = logging.getLogger(__name__)


class RuntimeKernel:
    """
    Legacy wrapper for Enhanced Runtime Kernel to maintain backward compatibility.
    Delegates to EnhancedRuntimeKernel which supports multiple BAEs with entity recognition.
    """

    def __init__(self, context_store_path: str = "database/context_store.json"):
        self.enhanced_kernel = EnhancedRuntimeKernel(context_store_path)
        logger.debug("RuntimeKernel initialized with Enhanced BAE support")

    # ------------------------------------------------------------------
    # Public API - Legacy compatibility methods
    # ------------------------------------------------------------------
    def run(
        self, natural_language_request: str, context: str = "academic", start_servers: bool = True
    ):
        """Legacy compatibility method that delegates to Enhanced Runtime Kernel"""
        logger.debug("📥 Legacy run method - delegating to Enhanced Runtime Kernel")

        result = self.enhanced_kernel.process_natural_language_request(
            natural_language_request, context, start_servers
        )

        if not result.get("success", False):
            logger.error(
                "❌ Enhanced kernel processing failed: %s", result.get("message", "Unknown error")
            )
            return

        logger.debug("✅ Legacy run method completed successfully via Enhanced Runtime Kernel")

    # ------------------------------------------------------------------
    # Legacy Compatibility Properties
    # ------------------------------------------------------------------
    @property
    def context_store(self):
        """Legacy compatibility property"""
        return self.enhanced_kernel.context_store

    @property
    def student_bae(self):
        """Legacy compatibility property for accessing StudentBAE"""
        return self.enhanced_kernel.bae_registry.get_bae("student")

    def get_supported_entities(self):
        """Get information about supported entities"""
        return self.enhanced_kernel.get_supported_entities_info()

    def validate_request(self, request: str):
        """Validate if a request can be handled"""
        return self.enhanced_kernel.validate_entity_request(request)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Runtime Kernel for BAE Academic System – Scenario 1 initial generation",
    )
    parser.add_argument("request", help="Natural-language request from the HBE")
    parser.add_argument(
        "--context", default="academic", help="Business context (default: academic)"
    )
    parser.add_argument(
        "--no-server",
        action="store_true",
        help="Generate artefacts but do not start FastAPI/Streamlit servers",
    )
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    kernel = RuntimeKernel()
    kernel.run(args.request, context=args.context, start_servers=not args.no_server)


if __name__ == "__main__":
    main()
