import argparse
import os
import shutil
import sys

from .config import doctor_report, load_config
from .main import create_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="network-assessor", description="Local network and IoT assessment tool")
    subparsers = parser.add_subparsers(dest="command")

    doctor = subparsers.add_parser("doctor", help="Check runtime dependencies")
    doctor.set_defaults(command="doctor")

    serve = subparsers.add_parser("serve", help="Start the local web server")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--no-browser", action="store_true")
    serve.set_defaults(command="serve")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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
        config = load_config()
        config.port = args.port
        os.environ["APP_PORT"] = str(args.port)
        import uvicorn

        if not args.no_browser:
            try:
                import webbrowser

                webbrowser.open(f"http://127.0.0.1:{args.port}/")
            except Exception:
                pass
        uvicorn.run(create_app(), host=args.host, port=args.port, log_level="info")
        return 0

    parser.print_help()
    return 0
