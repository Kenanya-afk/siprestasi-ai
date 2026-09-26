import os
from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from dotenv import load_dotenv
from PIL import Image
import pytesseract
import io
 
load_dotenv()

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
INTERNAL_KEY = os.getenv("INTERNAL_KEY", "change_this_secret")
 
app = FastAPI(title="SIPRESTASI AI Service")
 
# Kata kunci yang WAJIB ada di hasil OCR supaya dokumen dianggap valid.
# Dibuat lowercase semua supaya perbandingan tidak peduli huruf besar/kecil.
KEYWORD_JUDUL_DOKUMEN = "kartu rencana studi"
KEYWORD_PRODI_SI = "sistem informasi"
 
 
@app.get("/")
def health_check():
    return {"status": "ok", "service": "SIPRESTASI AI Service (OCR mode)"}
 
 
from fastapi import Form

@app.post("/verify-krs")
async def verify_krs(
    file: UploadFile = File(...),
    nama: str = Form(...),
    nim: str = Form(...),
    x_internal_key: str = Header(default=None),
):
    
    if x_internal_key != INTERNAL_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: internal key tidak valid")
 
    allowed_types = ["image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=422,
            detail=f"Tipe file {file.content_type} tidak didukung. Gunakan JPG atau PNG.",
        )
 
    file_bytes = await file.read()
 
    try:
        # Buka file gambar dari memory (tidak perlu simpan ke disk dulu)
        image = Image.open(io.BytesIO(file_bytes))
 
        # Ini baris utamanya: Tesseract "membaca" gambar dan
        # mengembalikan semua teks yang berhasil dikenali sebagai satu string panjang
        hasil_ocr = pytesseract.image_to_string(image)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gagal membaca gambar: {str(e)}")
 
    # Normalisasi: lowercase semua supaya "Sistem Informasi" dan "SISTEM INFORMASI" dianggap sama
    teks_lower = hasil_ocr.lower()
    nama_lower = nama.strip().lower()
    nim_bersih = nim.strip()

    ada_judul_krs = KEYWORD_JUDUL_DOKUMEN in teks_lower
    ada_prodi_si = KEYWORD_PRODI_SI in teks_lower
    ada_nama_cocok = nama_lower in teks_lower
    ada_nim_cocok = nim_bersih in hasil_ocr  # NIM angka, tidak perlu .lower()

    is_valid = ada_judul_krs and ada_prodi_si and ada_nama_cocok and ada_nim_cocok
 
    return {
    "success": True,
    "is_prodi_si": is_valid,
    "detail_pengecekan": {
        "terdeteksi_sebagai_krs": ada_judul_krs,
        "terdeteksi_prodi_si": ada_prodi_si,
        "nama_cocok": ada_nama_cocok,
    },
    "raw_text_preview": hasil_ocr[:500],
    }