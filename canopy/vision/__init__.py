"""Local AI wiring-diagram tool (CLAUDE.md §7.3).

A self-hosted FastAPI app that ingests an automotive wiring-diagram screenshot or PDF,
uses a local multimodal model served by **Ollama** to extract the connector pinout, and
lets a tech chat about the diagram and save per-vehicle knowledge (keyed by VIN). The
eventual payoff is questions like *"how do I wire this to communicate over CAN?"* — and a
generated, human-confirmed bench connection plan.

Everything runs locally: no diagram or VIN leaves the machine. Server/vision deps live in
the ``vision`` extra (``pip install -e ".[vision]"``) and are imported lazily so the core
package stays light.
"""
