import argparse
import asyncio
import os

from .config import doctor_report
from .main import create_app
from .security.session import SessionManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="network-assessor", description="Local network and IoT assessment tool"
    )
    subparsers = parser.add_subparsers(dest="command")

    doctor = subparsers.add_parser("doctor", help="Check runtime dependencies")
    doctor.set_defaults(command="doctor")

    storage = subparsers.add_parser(
        "storage", help="Offline JSON audit, retention preview or recovery"
    )
    storage.add_argument("action", choices=("audit", "retention", "recover"))
    storage.add_argument("--data-dir", required=True)
    storage.add_argument("--scan-id")
    storage.add_argument("--older-than-days", type=int, default=90)
    storage.add_argument("--apply", action="store_true")

    serve = subparsers.add_parser("serve", help="Start the local web server")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--no-browser", action="store_true")
    serve.set_defaults(command="serve")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "storage":
        from filelock import Timeout

        from .storage.maintenance import maintain, print_result

        try:
            print_result(
                maintain(
                    args.data_dir,
                    args.action,
                    scan_id=args.scan_id,
                    older_than_days=args.older_than_days,
                    apply=args.apply,
                )
            )
        except Timeout:
            parser.error("Stop the app before running storage maintenance")
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        return 0

    if args.command == "doctor":
        report = doctor_report()
        print(f"Python: {report['python_version']}")
        print(f"OS: {report['os']}")
        print(f"Nmap available: {report['nmap_available']}")
        print(f"Nmap version: {report['nmap_version']}")
        print(f"Data dir: {report['data_dir']}")
        print(f"Provider configured: {report['provider_configured']}")
        return 0

    if args.command == "serve":
        if args.host not in {"127.0.0.1", "localhost"}:
            parser.error("--host must be 127.0.0.1 or localhost")
        os.environ["APP_PORT"] = str(args.port)
        import uvicorn

        session_manager = SessionManager()
        bootstrap_url = session_manager.get_bootstrap_url(args.port)

        class BrowserServer(uvicorn.Server):
            async def startup(self, sockets=None):
                await super().startup(sockets=sockets)
                if not self.started:
                    return
                # Opening before the socket is bound can show "connection refused".
                print(f"Open this local session URL: {bootstrap_url}", flush=True)
                if not args.no_browser:
                    try:
                        import webbrowser

                        await asyncio.to_thread(webbrowser.open, bootstrap_url)
                    except Exception:
                        pass  # The authenticated link remains available in the task log.

        BrowserServer(
            uvicorn.Config(
                create_app(session_manager=session_manager),
                host=args.host,
                port=args.port,
                log_level="info",
            )
        ).run()
        return 0

    parser.print_help()
    return 0
