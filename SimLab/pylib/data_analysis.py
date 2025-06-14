import json
import re
import pandas as pd
from pathlib import Path


def convert_log_to_csv(log_path: Path, csv_output: Path) -> pd.DataFrame:
    # ------------------------- Expressões Regulares ----------------------------
    json_pattern = re.compile(r'\[Mote:1\].*?(\{.*?\})')

    # ---------------------- Leitura + Extração JSON ----------------------------
    rows = []

    with log_path.open(encoding="utf-8") as f:
        for line in f:
            m = json_pattern.search(line)
            if not m:
                continue
            try:
                rec = json.loads(m.group(1))
            except json.JSONDecodeError:
                continue

            # métricas derivadas
            rec["throughput1"] = rec["server_sent"] - rec["total_received"]
            rec["throughput2"] = (
                rec["server_sent"] + rec["total_sent"] - rec["server_received"]
            )
            rows.append(rec)

    # -------------------------- DataFrame bruto --------------------------------
    df = pd.DataFrame(rows)
    df.sort_values(["node", "root_time_now"], inplace=True)
    df.to_csv(csv_output, index=False)
    return df