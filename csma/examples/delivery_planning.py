"""End-to-end delivery planning demo.

Reads the problem data from examples/delivery_data.json and invokes CSMA.

Expected behavior:
1. Deep Agent write_todos → 3 subtasks:
   [search] route, [consensus] partner, [reasoning] summary
2. Route + partner subtasks delegated and run in parallel; summary waits
3. ant tool → GraphPayload (ordered path + cost)
   bee tool → RankedOptionsPayload (winner + confidence)
4. Summary subtask runs: LLM consumes both results, writes TextPayload
5. Deep Agent synthesizes → final answer (route + partner + summary)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main():
    # Load problem data from file
    data_path = Path(__file__).parent / "delivery_data.json"
    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}")
        sys.exit(1)

    with open(data_path) as f:
        data = json.load(f)

    cities = data["cities"]
    matrix = data["distance_matrix_km"]
    partners = data["shipping_partners"]
    criteria = data["criteria"]

    # Format the distance matrix as readable text
    matrix_lines = []
    header = f"{'':>12}" + "".join(f"{c:>12}" for c in cities)
    matrix_lines.append(header)
    for i, city in enumerate(cities):
        row = f"{city:>12}" + "".join(f"{matrix[i][j]:>12}" for j in range(len(cities)))
        matrix_lines.append(row)
    matrix_text = "\n".join(matrix_lines)

    # Format partners
    partner_text = "\n".join(
        f"  - {p['name']}: " + ", ".join(f"{k}={v}" for k, v in p["scores"].items())
        for p in partners
    )

    # Format criteria
    criteria_text = ", ".join(f"{c['name']} (weight={c['weight']})" for c in criteria)

    problem = (
        f"Find the optimal delivery route across these {len(cities)} cities, "
        f"choose the best shipping partner, then write a short client-facing "
        f"summary.\n\n"
        f"Cities: {', '.join(cities)}\n\n"
        f"Distance Matrix (km):\n{matrix_text}\n\n"
        f"Shipping Partners:\n{partner_text}\n\n"
        f"Evaluation Criteria: {criteria_text}\n\n"
        f"Requirements:\n"
        f"1. Find the shortest route visiting all cities (starting from Mumbai)\n"
        f"2. Choose the best shipping partner based on the criteria\n"
        f"3. Write a professional client-facing summary combining both results"
    )

    print("=" * 70)
    print("CSMA Delivery Planning Demo")
    print("=" * 70)
    print(f"\nProblem:\n{problem}\n")
    print("=" * 70)
    print("Running CSMA...\n")

    from csma.runtime import run_csma

    answer = run_csma(problem)

    print("\n" + "=" * 70)
    print("FINAL ANSWER")
    print("=" * 70)
    print(answer)


if __name__ == "__main__":
    main()
