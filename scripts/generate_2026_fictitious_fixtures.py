from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


def _md5_int(s: str) -> int:
    return int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16)


def _multiplier_for_row(key: str, row_label: str) -> float:
    """
    Fator deterministico (reprodutivel) no intervalo ~[0.9..1.15].
    Serve apenas para tornar os valores de 2026 claramente "de teste".
    """
    seed = _md5_int(f"{key}|{row_label}") % 10_000
    t = seed / 9999.0  # 0..1
    return 0.9 + t * 0.25


def _numeric_year_cols(df: pd.DataFrame) -> list[int]:
    cols: list[int] = []
    for c in df.columns:
        sc = str(c).strip()
        if sc.isdigit():
            cols.append(int(sc))
    return sorted(cols)


def _ensure_year_column(df: pd.DataFrame, *, year: int, source_year: int, growth: float) -> None:
    """
    Garante que `str(year)` exista como coluna e, se criada, deriva de `source_year`.
    """
    ycol = str(year)
    if ycol in df.columns:
        return

    scol = str(source_year)
    if scol not in df.columns:
        raise ValueError(f"Coluna fonte {scol} nao existe para criar {ycol}.")

    df[ycol] = df[scol] * float(growth)


def _ensure_required_lines(df: pd.DataFrame) -> pd.DataFrame:
    """
    O endpoint `/api/upload-historical` valida a presença de algumas linhas
    com rótulos específicos (após normalização simples de espaços/upper).
    Alguns CSVs originais usam abreviações (ex.: "GASTOS C/ PESSOAL").
    Aqui garantimos que as linhas exigidas existam.
    """
    if "linha" not in df.columns:
        return df

    def has(label: str) -> bool:
        return (df["linha"].astype(str).str.strip().str.upper() == label).any()

    def copy_row(src_label: str, dst_label: str) -> None:
        nonlocal df
        mask = df["linha"].astype(str).str.strip().str.upper() == src_label
        if not mask.any():
            return
        row = df.loc[mask].iloc[[0]].copy()
        row.loc[:, "linha"] = dst_label
        df = pd.concat([df, row], ignore_index=True)

    # GASTOS COM PESSOAL
    if not has("GASTOS COM PESSOAL"):
        copy_row("GASTOS C/ PESSOAL", "GASTOS COM PESSOAL")

    return df


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    input_dir = repo_root / "data" / "original"
    out_dir = repo_root / "data" / "test_uploads" / "2026_ficticio"
    out_dir.mkdir(parents=True, exist_ok=True)

    keep_year_end = 2026

    files_map: dict[str, str] = {
        "consolidado": "consolidado_original.csv",
        "fopm": "dre_fopm_original.csv",
        "renovacao": "dre_renovacao_original.csv",
        "ams": "dre_ams_original.csv",
        "venda_sw": "dre_venda_softwares_original.csv",
        "data_science": "dre_data_science_original.csv",
        "administrativa": "dre_administrativa_original.csv",
    }

    for key, filename in files_map.items():
        in_path = input_dir / filename
        if not in_path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {in_path}")

        df = pd.read_csv(in_path, encoding="utf-8")
        if "linha" not in df.columns:
            raise ValueError(f"CSV sem coluna 'linha': {in_path}")

        df = _ensure_required_lines(df)

        year_cols = _numeric_year_cols(df)
        if not year_cols:
            raise ValueError(f"CSV nao possui colunas numericas de ano: {in_path}")

        last_year_present = int(max(year_cols))
        _ensure_year_column(
            df,
            year=keep_year_end,
            source_year=last_year_present,
            growth=1.07,  # leve crescimento só para "fabricar" 2026 quando faltar
        )

        # Mantém só até 2026 (upload detecta 2026 como último ano numérico).
        keep_year_cols = [y for y in year_cols if y <= keep_year_end] + [keep_year_end]
        keep_year_cols = sorted(set(keep_year_cols))

        out_cols = ["linha"] + [str(y) for y in keep_year_cols]
        out_df = df[out_cols].copy()

        # AMS: o motor (base_year_extractor) precisa que algumas linhas operacionais
        # tenham valores numéricos em 2024–2026. Se 2026 vier vazio, copiamos 2025.
        if key == "ams":
            op_lines = {
                "Horas / NF (média hist.)",
                "Ticket Médio / NF (R$)",
                "Custo / Funcionário (R$)",
            }
            for lab in op_lines:
                mask = out_df["linha"].astype(str).str.strip() == lab
                if not mask.any():
                    continue
                v26 = out_df.loc[mask, "2026"].iloc[0] if "2026" in out_df.columns else None
                sv26 = "" if v26 is None or pd.isna(v26) else str(v26).strip()
                if sv26 in {"", "-", "—"}:
                    if "2025" in out_df.columns:
                        out_df.loc[mask, "2026"] = out_df.loc[mask, "2025"].iloc[0]

        # Perturba coluna 2026 para ficar claro que é fixture.
        ycol = str(keep_year_end)
        if ycol not in out_df.columns:
            raise RuntimeError(f"Coluna {ycol} nao foi criada para {key}.")

        for i in range(len(out_df)):
            row_label = out_df.loc[i, "linha"]
            v = out_df.loc[i, ycol]
            if pd.isna(v):
                continue
            sv = str(v).strip()
            if sv in {"", "-", "—"}:
                continue
            out_df.loc[i, ycol] = float(sv) * _multiplier_for_row(key, str(row_label))

        out_path = out_dir / f"{key}_historico_ate_{keep_year_end}_ficticio.csv"
        out_df.to_csv(out_path, index=False, encoding="utf-8")

    print(f"Fixtures geradas em: {out_dir}")
    for p in sorted(out_dir.glob("*_ficticio.csv")):
        print(f"- {p.name}")


if __name__ == "__main__":
    main()

