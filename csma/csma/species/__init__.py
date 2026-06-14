"""Species agents — thin tool wrappers around bio-inspired libraries.

Each species file exposes ONE LangChain tool that:
1. Accepts structured JSON input
2. Calls the reused library (mealpy / networkx)
3. Wraps output via translator.to_payload()
4. Returns BusMessage(...).to_json()
"""
