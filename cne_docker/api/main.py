from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os, time

from extractor.pipeline import extract_to_csv
from utils.diff import diff_csvs, validate_csv_schema

APP_DATA = os.environ.get("APP_DATA", "/app/data")
MODEL_PATH = os.environ.get("MODEL_PATH", "/app/models")

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
    enable_ia: bool = Form(True)
):
    if operator not in ("A", "B"):
        raise HTTPException(status_code=400, detail="operator deve ser 'A' ou 'B'")

    os.makedirs(APP_DATA, exist_ok=True)
    ts = int(time.time())
    in_path = os.path.join(APP_DATA, f"upload_{operator}_{ts}_{file.filename}")
    with open(in_path, "wb") as f:
        f.write(await file.read())

    out_csv = os.path.join(APP_DATA, f"extract_{operator}_{ts}.csv")
    result = extract_to_csv(
        in_path, out_csv,
        orgao=orgao, ord_reset=ord_reset, enable_ia=enable_ia, models_dir=MODEL_PATH
    )

    return JSONResponse({
        "input": in_path,
        "output_csv": out_csv,
        "rows": result.get("rows", 0),
        "orgoes": result.get("orgoes", []),
        "siglas": result.get("siglas", [])
    })

@app.post("/merge")
def merge(req: MergeRequest):
    if not os.path.exists(req.csv_a) or not os.path.exists(req.csv_b):
        raise HTTPException(status_code=400, detail="CSV paths inválidos")
    out_path = req.out_path or os.path.join(APP_DATA, "final_merged.csv")
    diffs, final_df = diff_csvs(req.csv_a, req.csv_b)
    final_df.to_csv(out_path, index=False, sep=";", encoding="utf-8")
    return {"diffs": diffs, "final_csv": out_path, "rows": int(final_df.shape[0])}

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
