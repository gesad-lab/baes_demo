import os
import sys
import subprocess
import importlib
from pathlib import Path
from typing import Dict, Type
import argparse
import logging

from bae_academic_system.agents.student_bae import StudentBAE
from bae_academic_system.agents.programmer_swea import ProgrammerSWEA
from bae_academic_system.agents.database_swea import DatabaseSWEA
from bae_academic_system.agents.frontend_swea import FrontendSWEA
from bae_academic_system.core.context_store import ContextStore
try:
    from bae_academic_system.config import Config
except ModuleNotFoundError:
    from config import Config

logger = logging.getLogger(__name__)

# Mapping of SWEA agent names to their classes
SWEA_REGISTRY: Dict[str, Type] = {
    "ProgrammerSWEA": ProgrammerSWEA,
    "DatabaseSWEA": DatabaseSWEA,
    "FrontendSWEA": FrontendSWEA,
}


class RuntimeKernel:
    """Simple sequential runtime kernel for Scenario 1.

    Flow:
    1. Interpret NL request with Student BAE.
    2. Execute coordination plan sequentially via SWEA agents.
    3. Persist domain knowledge & evolution to ContextStore.
    4. Reload API/UI loaders so artefacts are live.
    5. Start (or restart) FastAPI + Streamlit servers (optional).

    Note: steps 2 & 5 are clear extension points for concurrency or
    more advanced orchestration. See TODO markers below.
    """

    def __init__(self, context_store_path: str = "database/context_store.json"):
        self.context_store = ContextStore(context_store_path)
        self.student_bae = StudentBAE()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, natural_language_request: str, context: str = "academic", start_servers: bool = True):
        logger.info("📥 Received request: %s", natural_language_request)

        # 1. Business interpretation
        interpretation = self.student_bae.handle_task(
            "interpret_business_request",
            {"request": natural_language_request, "context": context},
        )
        coordination_plan = interpretation.get("coordination_plan", [])
        attributes = interpretation.get("domain_attributes", [])
        business_vocab = interpretation.get("business_vocabulary", [])

        # 2. Execute coordination plan sequentially (future: parallelise here)
        for task in coordination_plan:
            agent_name = task.get("swea_agent") or task.get("agent")
            task_type = task.get("task_type")
            AgentCls = SWEA_REGISTRY.get(agent_name)
            if AgentCls is None:
                logger.warning("Unknown SWEA agent in plan: %s", agent_name)
                continue
            agent = AgentCls()
            payload = {
                "entity": "Student",  # Scenario 1 focus
                "attributes": attributes,
                "context": context,
            }
            logger.info("⚙️  Executing %s.%s", agent_name, task_type)
            agent.handle_task(task_type, payload)

        # 3. Persist domain knowledge & vocab
        self.context_store.preserve_domain_knowledge("Student", {
            "entity": "Student",
            "core_attributes": attributes,
            "business_rules": interpretation.get("business_rules", []),
            "context": context,
        })
        self.context_store.store_business_vocabulary(context, business_vocab, "Student")

        # 4. Reload loaders so new artefacts are available
        self._reload_api_loader()
        self._reload_ui_loader()

        # 5. Optionally start servers (skipped in test mode)
        if start_servers and not os.getenv("SKIP_SERVER_START"):
            self._start_servers()

        logger.info("✅ Scenario 1 generation completed.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _reload_api_loader(self):
        try:
            from api import main as api_main
        except ImportError:
            logger.debug("FastAPI not installed or api.main unavailable; skipping reload.")
            return
        importlib.reload(api_main)
        logger.info("🔄 API routes reloaded")

    def _reload_ui_loader(self):
        try:
            from ui import app as ui_app
        except ImportError:
            logger.debug("Streamlit not installed or ui.app unavailable; skipping reload.")
            return
        importlib.reload(ui_app)
        logger.info("🔄 UI modules reloaded")

    def _start_servers(self):
        # Simple subprocess calls; could be replaced by supervisor/async logic.
        # NOTE: In production we may run these under a process manager.
        project_root = Path(__file__).resolve().parents[2]

        # Start/reload FastAPI server
        api_cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            Config.API_HOST,
            "--port",
            str(Config.API_PORT),
            "--reload",
        ]
        # Restart if already running? For now, we spawn a new one.
        subprocess.Popen(api_cmd, cwd=project_root)  # pylint: disable=subprocess-popen-preexec-fn
        logger.info("🚀 FastAPI server started at http://%s:%s", Config.API_HOST, Config.API_PORT)

        # Start Streamlit UI
        ui_file = project_root / "bae_academic_system" / "ui" / "app.py"
        ui_cmd = ["streamlit", "run", str(ui_file), "--server.port", str(Config.UI_PORT)]
        subprocess.Popen(ui_cmd, cwd=project_root)
        logger.info("🎨 Streamlit UI started at http://%s:%s", Config.UI_HOST, Config.UI_PORT)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Runtime Kernel for BAE Academic System – Scenario 1 initial generation",
    )
    parser.add_argument("request", help="Natural-language request from the HBE")
    parser.add_argument("--context", default="academic", help="Business context (default: academic)")
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