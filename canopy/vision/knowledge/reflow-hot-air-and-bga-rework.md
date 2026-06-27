# Reflow, hot air, QFN, and BGA rework

> tags: reflow, hot-air, qfn, bga, msl, preheat, stencil, reball, x-ray, thermal-profile

Hot air is not a heat gun. Controlled reflow requires preheat, airflow control, flux, nozzle choice, thermal awareness, and moisture handling.

## Before hot-air removal
- Confirm the part is actually bad. Do not remove BGAs/QFNs on suspicion.
- Check whether the component is moisture sensitive. Bake or handle per MSL requirements when needed.
- Photograph orientation and nearby parts.
- Shield plastic connectors, electrolytics, relays, MEMS devices, crystals, and labels.
- Preheat the board when thermal mass is high to reduce top-side dwell and pad damage.

## Hot-air removal sequence
- Apply appropriate flux.
- Preheat the local area or entire board as appropriate.
- Use controlled airflow; too much airflow moves small passives.
- Heat evenly until all joints reflow, then lift vertically with minimal force.
- If the part resists, it is not fully reflowed. Do not pry.

## Pad cleanup
- Wick pads gently with flux.
- Preserve solder mask and pads. Excess pressure and dry braid lift pads.
- Inspect for bridges, missing pads, damaged vias, solder balls, and scorched laminate.
- Clean residue enough to inspect.

## Replacement
- Align carefully; tack corners for gull-wing parts.
- For QFN/BGA, use stencil/paste or controlled solder volume.
- Verify orientation marks.
- Reflow with a profile appropriate to the board and part.
- Inspect all visible joints; use X-ray or boundary scan where BGA/QFN hidden joints matter.

## BGA-specific cautions
- BGA reflow without confirming the fault can convert a diagnostic problem into an unrecoverable board problem.
- Warped boards, underfill, conformal coating, lead-free thermal requirements, and large ground planes raise risk.
- A “reflow fix” for intermittent BGA may be temporary if the underlying cause is board flex, thermal cycling, or package fatigue.

## Post-rework verification
- Check for shorts on adjacent rails before power.
- Verify current draw, rail ripple, clock/reset, and original symptom.
- Heat/cool cycle if the failure was intermittent.

Sources: [IPC 7711/7721 Revision D](https://shop.electronics.org/ipc-771121/ipc-771121-standard-only/Revision-d/english), [IPC/JEDEC J-STD-020](https://shop.electronics.org/ipcjedec-j-std-020/ipcjedec-j-std-020-standard-only?f%5B0%5D=language%3A37), [J-STD-020 preview](https://webstore.ansi.org/preview-pages/IPC/preview_IPC%2BJEDEC%2BJ-STD-020E-2015.pdf), [NASA-STD-8739.3](https://nepp.nasa.gov/docuploads/06AA01BA-FC7E-4094-AE829CE371A7B05D/NASA-STD-8739.3.pdf), [Deep learning solder joint X-ray inspection](https://arxiv.org/abs/2008.02604).
