import os
import re
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler-26.02.0\Library\bin"


MEDICAL_KEYWORDS = {
    "patient", "name", "age", "sex", "gender", "doctor", "hospital", "diagnosis",
    "discharge", "summary", "complaint", "history", "examination", "impression",
    "recommendation", "advice", "follow", "review", "treatment", "medicine",
    "tablet", "tab", "cap", "syrup", "dose", "dosage", "mg", "mcg", "ml",

    "blood", "pressure", "bp", "pulse", "pr", "spo2", "oxygen", "temperature",
    "temp", "heart", "rate", "respiratory", "weight", "height", "bmi",

    "hemoglobin", "haemoglobin", "hb", "hematocrit", "haematocrit", "pcv",
    "rbc", "wbc", "platelet", "platelets", "neutrophils", "lymphocytes",
    "eosinophils", "monocytes", "basophils", "mcv", "mch", "mchc",

    "glucose", "sugar", "fasting", "postprandial", "hba1c", "cholesterol",
    "ldl", "hdl", "triglycerides", "creatinine", "urea", "bun", "egfr",
    "sodium", "potassium", "chloride", "bilirubin", "albumin", "protein",
    "alt", "ast", "alp", "sgot", "sgpt", "tsh", "t3", "t4",

    "ecg", "echo", "ejection", "fraction", "lvef", "lv", "lbbb", "icmp",
    "cad", "cag", "ptca", "stent", "cardiac", "cardiology",

    "infection", "fever", "pain", "swelling", "edema", "oedema", "cough",
    "breathlessness", "shortness", "urine", "kidney", "liver", "thyroid",
    "anemia", "anaemia", "diabetes", "hypertension", "htn"
}


NOISE_KEYWORDS = {
    "gst", "cgst", "sgst", "invoice", "bill no", "bill date", "cash amount",
    "receipt amount", "taxable", "hsn", "batch no", "exp dt", "printed",
    "created", "received sum", "rupees", "pharmacy receipt"
}


def _configure_ocr_paths():
    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def _extract_with_pdfplumber(pdf_path):
    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"

    return text.strip()


def _preprocess_image_for_ocr(image):
    image = image.convert("L")
    image = ImageOps.autocontrast(image)
    image = ImageEnhance.Contrast(image).enhance(1.8)
    image = ImageEnhance.Sharpness(image).enhance(1.5)
    image = image.filter(ImageFilter.MedianFilter(size=3))
    return image


def _has_medical_signal(line):
    lower_line = line.lower()

    if any(keyword in lower_line for keyword in MEDICAL_KEYWORDS):
        return True

    medical_value_pattern = re.search(
        r"\b([A-Za-z][A-Za-z\s()/.-]{2,40})\s*[:\-]?\s*(\d+(\.\d+)?)\s*(mg|mcg|ml|gms|gm|%|mmhg|bpm|cells|lakhs|million)?\b",
        line,
        re.IGNORECASE
    )

    if medical_value_pattern:
        return True

    bp_pattern = re.search(r"\b\d{2,3}\s*/\s*\d{2,3}\b", line)
    if bp_pattern:
        return True

    spo2_pattern = re.search(r"\b(spo2|sp02|oxygen)\s*[:\-]?\s*\d{2,3}", line, re.IGNORECASE)
    if spo2_pattern:
        return True

    return False


def _is_noise_line(line):
    cleaned = line.strip()

    if not cleaned:
        return True

    if len(cleaned) < 3:
        return True

    lower_line = cleaned.lower()

    if any(noise in lower_line for noise in NOISE_KEYWORDS):
        return True

    letters = sum(char.isalpha() for char in cleaned)
    digits = sum(char.isdigit() for char in cleaned)
    spaces = sum(char.isspace() for char in cleaned)
    symbols = len(cleaned) - letters - digits - spaces

    total = max(len(cleaned), 1)

    letter_ratio = letters / total
    digit_ratio = digits / total
    symbol_ratio = symbols / total

    if re.fullmatch(r"[\W_]+", cleaned):
        return True

    if symbol_ratio > 0.35 and letters < 8:
        return True

    if digit_ratio > 0.70 and letters < 5:
        return True

    if len(cleaned) > 120 and letter_ratio < 0.45:
        return True

    repeated_noise = re.search(r"(.)\1{5,}", cleaned)
    if repeated_noise:
        return True

    fake_word_noise = re.findall(r"\b[a-zA-Z]{1,2}\b", cleaned)
    words = re.findall(r"\b[a-zA-Z]{3,}\b", cleaned)

    if len(fake_word_noise) > 8 and len(words) < 3:
        return True

    return False


def _clean_ocr_text(raw_text):
    useful_lines = []
    seen_lines = set()

    for line in raw_text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if _is_noise_line(line):
            continue

        if not _has_medical_signal(line):
            continue

        normalized = line.lower()

        if normalized in seen_lines:
            continue

        seen_lines.add(normalized)
        useful_lines.append(line)

    return "\n".join(useful_lines).strip()


def _extract_with_ocr(pdf_path):
    _configure_ocr_paths()

    images = convert_from_path(
        pdf_path,
        dpi=240,
        poppler_path=POPPLER_PATH if os.path.exists(POPPLER_PATH) else None
    )

    full_text = ""

    ocr_config = "--oem 3 --psm 6"

    for page_number, image in enumerate(images, start=1):
        processed_image = _preprocess_image_for_ocr(image)

        page_text = pytesseract.image_to_string(
            processed_image,
            lang="eng",
            config=ocr_config
        )

        cleaned_page_text = _clean_ocr_text(page_text)

        if cleaned_page_text:
            full_text += f"\n--- OCR Page {page_number} ---\n"
            full_text += cleaned_page_text + "\n"

    return full_text.strip()


def extract_text_from_pdf(pdf_path):
    try:
        text = _extract_with_pdfplumber(pdf_path)

        if text and len(text.strip()) > 50:
            return text.strip()

        ocr_text = _extract_with_ocr(pdf_path)

        if ocr_text and len(ocr_text.strip()) > 20:
            return ocr_text.strip()

        return "PDF Error: No readable medical text found. This file may be handwritten, low-quality scanned, image-heavy, or not a standard medical report."

    except Exception as error:
        return f"PDF Error: {str(error)}"