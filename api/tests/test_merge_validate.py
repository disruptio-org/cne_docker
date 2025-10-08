from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app


HEADER = "DTMNFR;ORGAO;TIPO;SIGLA;SIMBOLO;NOME_LISTA;NUM_ORDEM;NOME_CANDIDATO;PARTIDO_PROPONENTE;INDEPENDENTE"


def write_csv(path: Path, rows):
    lines = [HEADER]
    lines.extend(rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


client = TestClient(app)


def test_validate_endpoint_returns_ok_for_valid_csv(tmp_path):
    csv_path = tmp_path / "valid.csv"
    write_csv(
        csv_path,
        [
            "2024;CM;2;AAA;SYM;Lista A;1;João Silva;Partido A;N",
        ],
    )

    response = client.post("/validate", json={"csv_path": str(csv_path)})
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["rows"] == 1
    assert payload["issues"] == []


def test_merge_endpoint_creates_file_and_reports_rows(tmp_path):
    csv_a = tmp_path / "csv_a.csv"
    csv_b = tmp_path / "csv_b.csv"
    out_path = tmp_path / "merged" / "final.csv"

    write_csv(
        csv_a,
        [
            "2024;CM;2;AAA;SYM;Lista A;1;João Silva;Partido A;N",
        ],
    )
    write_csv(
        csv_b,
        [
            "2024;CM;2;AAA;SYM;Lista A;1;João Silva;Partido A;N",
            "2024;AM;3;BBB;SYM;Lista B;2;Maria Souza;Partido B;S",
        ],
    )

    response = client.post(
        "/merge",
        json={
            "csv_a": str(csv_a),
            "csv_b": str(csv_b),
            "out_path": str(out_path),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["final_csv"] == str(out_path)
    assert payload["rows"] == 2
    assert Path(payload["final_csv"]).exists()

    merged_content = out_path.read_text(encoding="utf-8").strip().splitlines()
    assert merged_content[0] == HEADER
    assert len(merged_content) == 3
