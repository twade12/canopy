# PCB pad, trace, and via repair

> tags: pcb-repair, lifted-pad, trace-repair, via, jumper, epoxy, solder-mask, rework

A pad or trace repair must restore electrical continuity, mechanical strength, insulation, and environmental protection. A jumper that works on the bench but breaks under vibration is not a repair.

## Damage types
- Lifted SMT pad.
- Torn through-hole barrel.
- Burned/open trace.
- Cracked via.
- Delaminated laminate.
- Solder-mask loss exposing adjacent nets.
- Carbonized board material that becomes conductive.

## First decision
- If the damaged material is carbonized, remove it until clean non-conductive material remains.
- If the pad connects only to a short trace, rebuild with a jumper to the next accessible point.
- If the pad anchors a connector or high-force component, mechanical reinforcement matters as much as electrical continuity.
- If the board is multilayer and the via/inner layer is damaged, simple surface repair may not restore all connections.

## Jumper repair rules
- Use wire gauge appropriate to current and environment.
- Route along the board; avoid tall loops that catch or vibrate.
- Anchor with epoxy/UV mask/conformal coating where needed.
- Keep jumpers away from hot parts, sharp shields, moving mechanisms, and high-voltage spacing.
- Do not bridge safety isolation slots or creepage/clearance barriers.

## Pad replacement rules
- Clean the area, expose copper, tin carefully, and use adhesive-backed/replacement pads or formed copper foil when appropriate.
- Provide strain relief for leads and connectors.
- Restore solder mask or coating to prevent corrosion/leakage.

## Via repair
- Verify both sides and any inner-layer connection.
- For simple top-bottom vias, wire through the via and solder both sides if spacing allows.
- For dense boards, prefer alternate accessible net points over drilling or aggressive via work.

## Verification
- Continuity from source to destination.
- Isolation to adjacent nets.
- Load test at expected current.
- Mechanical tug/flex test appropriate to the assembly.
- Recoat/insulate and inspect under magnification.

Sources: [IPC 7711/7721 Revision D](https://shop.electronics.org/ipc-771121/ipc-771121-standard-only/Revision-d/english), [IPC Standards](https://www.electronics.org/ipc-standards), [NASA-STD-8739.3](https://nepp.nasa.gov/docuploads/06AA01BA-FC7E-4094-AE829CE371A7B05D/NASA-STD-8739.3.pdf), [NASA-STD-8739.1](https://standards.nasa.gov/standard/NASA/NASA-STD-87391).
