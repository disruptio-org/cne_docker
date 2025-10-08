from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import os, time

from .extract_pipeline import linearize_document_to_lines, process_document_lines
from .learn.infer import predict_rows
from .csv_writer import write_cne_csv
from .utils_text import sanitize_rows
from .qa import collect_suspect_rows, write_qa_csv
from extractor.pipeline import infer_dtmnfr_from_path
from utils.diff import diff_csvs, validate_csv_schema

APP_DATA = os.environ.get("APP_DATA", "/app/data")
MODEL_PATH = os.environ.get("MODEL_PATH", "/app/models")
STRICT_TEMPLATES = os.environ.get("STRICT_TEMPLATES", "").lower() in {"1", "true", "yes", "on"}

app = FastAPI(title="CNE On-Prem Extractor (Fixed V2)", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MergeRequest(BaseModel):
    csv_a: str
    csv_b: str
    out_path: Optional[str] = None

class ValidateRequest(BaseModel):
    csv_path: str

@app.get("/health")
def health():
    return {"status": "ok", "models_dir": MODEL_PATH}

@app.post("/extract")
async def extract(
    file: UploadFile = File(...),
    operator: str = Form(...),
    orgao: Optional[str] = Form(None),
    ord_reset: bool = Form(True),
    enable_ia: bool = Form(True),
    use_ner: bool = Form(False),
    excel_compat: bool = Query(False),
    encoding: Optional[str] = Query(None),
    qa: bool = Query(False),
):
    if operator not in ("A", "B"):
        raise HTTPException(status_code=400, detail="operator deve ser 'A' ou 'B'")

    os.makedirs(APP_DATA, exist_ok=True)
    ts = int(time.time())
    in_path = os.path.join(APP_DATA, f"upload_{operator}_{ts}_{file.filename}")
    with open(in_path, "wb") as f:
        f.write(await file.read())

    out_csv = os.path.join(APP_DATA, f"extract_{operator}_{ts}.csv")
    csv_encoding = encoding or ("cp1252" if excel_compat else "utf-8-sig")
    lines = linearize_document_to_lines(in_path, enable_ia=enable_ia)

    pipeline_meta = {"needs_review": False}
    if use_ner:
        ner_model_dir = os.path.join(MODEL_PATH, "ner_pt") if MODEL_PATH else "/app/models/ner_pt"
        rows = predict_rows(lines, model_dir=ner_model_dir)
    else:
        rows, pipeline_meta = process_document_lines(lines)
        if enable_ia and not rows:
            fallback_lines = linearize_document_to_lines(in_path, enable_ia=False)
            rows, pipeline_meta = process_document_lines(fallback_lines)

    dtmnfr = infer_dtmnfr_from_path(in_path)

    processed_rows = []
    for row in rows:
        item = dict(row)
        for field in (
            "DTMNFR",
            "ORGAO",
            "TIPO",
            "SIGLA",
            "SIMBOLO",
            "NOME_LISTA",
            "NUM_ORDEM",
            "NOME_CANDIDATO",
            "PARTIDO_PROPONENTE",
            "INDEPENDENTE",
        ):
            item.setdefault(field, "")
        if dtmnfr:
            item["DTMNFR"] = item.get("DTMNFR") or dtmnfr
        if orgao:
            item["ORGAO"] = orgao
        processed_rows.append(item)

    if ord_reset:
        counters = {}
        for item in processed_rows:
            tipo = str(item.get("TIPO", "")).strip()
            if tipo not in {"2", "3"}:
                continue
            key = (
                item.get("DTMNFR", ""),
                item.get("ORGAO", ""),
                item.get("SIGLA", ""),
                item.get("NOME_LISTA", ""),
                tipo,
            )
            counters[key] = counters.get(key, 0) + 1
            item["NUM_ORDEM"] = str(counters[key])

    safe_rows = sanitize_rows(processed_rows)
    suspect_rows = collect_suspect_rows(safe_rows, metadata=pipeline_meta)

    if STRICT_TEMPLATES and (not safe_rows or suspect_rows):
        detail = {
            "error": "classificacao_fraca",
            "rows": len(safe_rows),
            "suspeitos": len(suspect_rows),
        }
        raise HTTPException(status_code=422, detail=detail)

    write_cne_csv(safe_rows, out_csv, encoding=csv_encoding)

    qa_path = None
    if qa:
        qa_path, _ = write_qa_csv(
            safe_rows,
            out_csv,
            metadata=pipeline_meta,
            suspects=suspect_rows,
        )

    orgoes = sorted({row.get("ORGAO", "") for row in safe_rows if row.get("ORGAO")})
    siglas = sorted({row.get("SIGLA", "") for row in safe_rows if row.get("SIGLA")})

    return JSONResponse({
        "input": in_path,
        "output_csv": out_csv,
        "rows": len(safe_rows),
        "orgoes": orgoes,
        "siglas": siglas,
        "qa_csv": qa_path,
        "suspeitos": len(suspect_rows),
    })

@app.post("/merge")
def merge(req: MergeRequest):
    if not os.path.exists(req.csv_a) or not os.path.exists(req.csv_b):
        raise HTTPException(status_code=400, detail="CSV paths inválidos")
    base_out_dir = Path(APP_DATA)
    base_out_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(req.out_path) if req.out_path else base_out_dir / "final_merged.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    diffs, final_df = diff_csvs(req.csv_a, req.csv_b)
    final_df.to_csv(out_path, index=False, sep=";", encoding="utf-8")
    return {"diffs": diffs, "final_csv": str(out_path), "rows": int(final_df.shape[0])}

@app.post("/validate")
def validate(req: ValidateRequest):
    if not os.path.exists(req.csv_path):
        raise HTTPException(status_code=400, detail="CSV inexistente")
    report = validate_csv_schema(req.csv_path)
    return report

@app.get("/download")
def download(path: str):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Ficheiro não encontrado")
    return FileResponse(path, filename=os.path.basename(path))
