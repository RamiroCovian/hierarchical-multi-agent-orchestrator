"""Punto de entrada CLI del orquestador multi-agente."""

import argparse
import sys

from dotenv import load_dotenv

load_dotenv()

from graph import get_graph_mermaid, run_orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Orquestador multi-agente (supervisor + research + analyst)"
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Consulta a procesar. Si se omite, se pide por input.",
    )
    parser.add_argument(
        "--mermaid",
        action="store_true",
        help="Imprime el diagrama Mermaid del grafo y sale.",
    )
    args = parser.parse_args()

    if args.mermaid:
        print(get_graph_mermaid())
        return

    query = " ".join(args.query).strip()
    if not query:
        query = input("Consulta: ").strip()

    if not query:
        print("Error: consulta vacía.", file=sys.stderr)
        sys.exit(1)

    result = run_orchestrator(query)
    final_response = (result.get("final_response") or "").strip()
    if not final_response:
        final_response = (result.get("analysis_result") or "").strip()

    print("\n=== Respuesta final ===\n")
    print(final_response or "Sin respuesta final.")
    print("\n=== Metadatos ===")
    print(f"steps: {result.get('step_count')}")
    print(f"task_completed: {result.get('task_completed')}")
    print(f"validation_passed: {result.get('validation_passed')}")
    print(f"next_agent: {result.get('next_agent')}")


if __name__ == "__main__":
    main()
