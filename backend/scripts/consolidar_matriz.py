#!/usr/bin/env python3
"""Consolida resultados de todas las configuraciones de tracker en una tabla Markdown."""
import json
from pathlib import Path

OUT = Path("/tmp/galeria_report")
CONFIGS = [
    "bjj_botsort",
    "bjj_botsort_long",
    "bjj_botsort_reid",
    "bjj_botsort_reid_strict",
    "bjj_fasttrack",
    "bjj_fasttrack_long",
]


def _fmt(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def _fmt_pct(v) -> str:
    if v is None:
        return "null"
    return f"{float(v) * 100:.1f}%"


def main():
    rows = []
    for cfg in CONFIGS:
        path = OUT / f"pares_v3_matrix_{cfg}.json"
        if not path.exists():
            print(f"SKIP {cfg}: {path} no existe")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for entry in data:
            t_alu = entry.get("tracking_alumno") or {}
            t_mae = entry.get("tracking_maestro") or {}
            rows.append(
                {
                    "config": cfg,
                    "tecnica": entry.get("tecnica"),
                    "estado": entry.get("estado"),
                    "score": entry.get("score_similitud"),
                    "idsw_alumno": t_alu.get("id_switches"),
                    "idsw_maestro": t_mae.get("id_switches"),
                    "cobertura_alumno": t_alu.get("cobertura_principal"),
                    "cobertura_maestro": t_mae.get("cobertura_principal"),
                    "perdido_alumno": t_alu.get("perdido_definitivamente_en_frame"),
                    "perdido_maestro": t_mae.get("perdido_definitivamente_en_frame"),
                }
            )

    lines = [
        "# Matriz de Configuraciones de Tracking (6 configs × 5 pares)",
        "",
        "| Config | Técnica | Estado | Score | IDSW Alu | IDSW Mae | Cob Alu | Cob Mae | Perdido Alu | Perdido Mae |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['config']} | {r['tecnica']} | {r['estado']} | {_fmt(r['score'])} | "
            f"{_fmt(r['idsw_alumno'])} | {_fmt(r['idsw_maestro'])} | "
            f"{_fmt_pct(r['cobertura_alumno'])} | {_fmt_pct(r['cobertura_maestro'])} | "
            f"{_fmt(r['perdido_alumno'])} | {_fmt(r['perdido_maestro'])} |"
        )

    # Resumen por configuracion
    lines.extend(["", "## Resumen por Configuración", "", "| Config | Pares Completados | Pares con IDSW <= 2 (ambos) y sin pérdida | Max IDSW |"])
    lines.append("|---|---:|---:|---:|")
    for cfg in CONFIGS:
        cfg_rows = [r for r in rows if r["config"] == cfg]
        if not cfg_rows:
            continue
        comp = sum(1 for r in cfg_rows if r["estado"] == "completado")
        ok_track = sum(
            1
            for r in cfg_rows
            if r["estado"] == "completado"
            and (r["idsw_alumno"] or 0) <= 2
            and (r["idsw_maestro"] or 0) <= 2
            and r["perdido_alumno"] is None
            and r["perdido_maestro"] is None
        )
        max_idsw = max(max((r["idsw_alumno"] or 0), (r["idsw_maestro"] or 0)) for r in cfg_rows)
        lines.append(f"| {cfg} | {comp}/{len(cfg_rows)} | {ok_track}/{len(cfg_rows)} | {max_idsw} |")

    md_text = "\n".join(lines) + "\n"
    out_md = OUT / "matriz_resultados.md"
    out_md.write_text(md_text, encoding="utf-8")
    print(md_text)
    print(f"[OK] {out_md}")


if __name__ == "__main__":
    main()
