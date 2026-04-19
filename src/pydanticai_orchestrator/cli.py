from __future__ import annotations

import argparse
import json

from pydanticai_orchestrator.service import OrchestratorService
from pydanticai_orchestrator.settings import get_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='pydanticai-orchestrator')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('doctor')

    worker = sub.add_parser('worker')
    worker.add_argument('backend', choices=['hermes', 'pi', 'codex'])
    worker.add_argument('task')

    stok = sub.add_parser('stokowski')
    stok.add_argument('action', choices=['dry-run', 'status', 'submit'])
    stok.add_argument('task', nargs='?')

    prompt = sub.add_parser('prompt')
    prompt.add_argument('text')

    route = sub.add_parser('route')
    route.add_argument('text')
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = OrchestratorService(get_settings())

    if args.command == 'doctor':
        print(json.dumps(service.doctor(), indent=2))
        return 0
    if args.command == 'worker':
        if args.backend == 'hermes':
            result = service.hermes(args.task)
        elif args.backend == 'codex':
            result = service.codex(args.task)
        else:
            result = service.pi(args.task)
        print(result.model_dump_json(indent=2))
        return 0 if result.ok else 1
    if args.command == 'stokowski':
        if args.action == 'dry-run':
            result = service.stokowski_dry_run()
        elif args.action == 'status':
            result = service.stokowski_status()
        else:
            result = service.stokowski_submit(args.task or '')
        print(result.model_dump_json(indent=2))
        return 0 if result.ok else 1
    if args.command == 'prompt':
        result = service.run_prompt_sync(args.text)
        print(result.model_dump_json(indent=2))
        return 0
    if args.command == 'route':
        result = service.handle_request(args.text)
        print(result.model_dump_json(indent=2))
        return 0
    parser.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
