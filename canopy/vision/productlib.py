"""Product library — turn a confirmed project into a reusable, listable SKU.

A *product* is the cycle-time moat: the first unit of a module type produces a profile + wiki +
BOM + known-symptoms bundle keyed by a SKU; every later unit matches it and is near-instant. This
module derives the product fields from a project and builds the SKU/BOM/symptoms.
"""

from __future__ import annotations

import json

from canopy.profiles.generate import infer_module_class
from canopy.profiles.schema import ModuleProfile
from canopy.vision import wiki as wikimod


def sku_for(part_number: str, make: str, model: str, year: str, module_class: str) -> str:
    """Stable key: prefer the OEM part number, else make|model|year|class."""
    pn = (part_number or "").strip()
    if pn:
        return pn.upper()
    return "|".join(x.strip().lower() for x in (make, model, year, module_class) if x.strip())


def build_product_fields(store, vehicle_id: int) -> dict:
    v = store.get_vehicle(vehicle_id)
    tags = store.list_tags(vehicle_id)
    prof_yaml = store.get_profile(vehicle_id) or ""
    module_class, part_number = "", ""
    if prof_yaml:
        try:
            p = ModuleProfile.from_yaml(prof_yaml)
            module_class = p.identity.module_class
            part_number = p.identity.part_number
        except Exception:
            pass
    if not module_class or module_class == "unknown":
        module_class = infer_module_class(v.get("label", ""), tags)
    make, model, year = v.get("make", ""), v.get("model", ""), v.get("year", "")
    bom = [{"ref": c.get("user_label") or c.get("label"), "part": c.get("part", ""),
            "note": c.get("user_note", "")}
           for c in store.list_pcb_components(vehicle_id)
           if c.get("part") or c.get("user_label")]
    symptoms = [m["content"] for m in store.list_memories(vehicle_id)]
    return {
        "sku": sku_for(part_number, make, model, year, module_class),
        "part_number": part_number, "make": make, "model": model, "year": year,
        "module_class": module_class, "label": v.get("label", ""),
        "profile_yaml": prof_yaml, "wiki": wikimod.build(store, vehicle_id),
        "bom": json.dumps(bom), "symptoms": json.dumps(symptoms),
        "source_vehicle_id": vehicle_id,
    }


def hydrate(product: dict) -> dict:
    """Parse the JSON columns for API responses."""
    p = dict(product)
    for k in ("bom", "symptoms"):
        if isinstance(p.get(k), str):
            try:
                p[k] = json.loads(p[k]) if p[k] else []
            except Exception:
                p[k] = []
    return p
