import re


MEDICAL_KEYWORDS = {
    "patient", "patient name", "age", "gender", "sex",
    "doctor", "physician", "hospital", "clinic",
    "diagnosis", "impression", "clinical", "symptoms",
    "history", "treatment", "recommendation", "follow up",

    # Blood / CBC
    "hemoglobin", "haemoglobin", "hb",
    "wbc", "rbc", "platelet", "platelets",
    "hematocrit", "haematocrit", "pcv",
    "mcv", "mch", "mchc",
    "neutrophils", "lymphocytes", "monocytes",
    "eosinophils", "basophils",

    # Diabetes
    "glucose", "blood sugar", "fasting glucose",
    "postprandial", "hba1c",

    # Lipid profile
    "cholesterol", "ldl", "hdl",
    "triglycerides", "vldl",

    # Kidney
    "creatinine", "urea", "bun", "egfr",
    "uric acid",

    # Liver
    "bilirubin", "albumin", "alt", "ast",
    "sgot", "sgpt", "alkaline phosphatase",

    # Thyroid
    "tsh", "t3", "t4",

    # Vitals
    "blood pressure", "bp", "heart rate",
    "pulse", "spo2", "oxygen saturation",
    "temperature", "bmi",

    # Medical investigations
    "ecg", "echocardiography", "ultrasound",
    "x-ray", "mri", "ct scan", "radiology",
    "pathology", "laboratory",

    # Conditions
    "diabetes", "hypertension", "anemia",
    "infection", "inflammation",
    "kidney disease", "liver disease"
}


MEDICAL_HEADINGS = {
    "complete blood count",
    "blood test",
    "laboratory report",
    "lab report",
    "test results",
    "clinical findings",
    "diagnosis",
    "impression",
    "chief complaints",
    "medical history",
    "recommendations",
    "investigation",
    "radiology report",
    "pathology report",
    "lipid profile",
    "liver function test",
    "kidney function test",
    "thyroid profile",
    "diabetic profile"
}


NON_MEDICAL_KEYWORDS = {
    "invoice",
    "bill no",
    "gst",
    "cgst",
    "sgst",
    "tax invoice",
    "receipt",
    "payment",
    "transaction",
    "account number",
    "bank",
    "marksheet",
    "grade",
    "semester",
    "student",
    "university",
    "college",
    "subject code",
    "roll number",
    "salary",
    "resume",
    "curriculum vitae",
    "purchase order",
    "quotation"
}


MEDICAL_UNIT_PATTERN = re.compile(
    r"\b\d+(\.\d+)?\s*"
    r"(mg/dl|mg/l|g/dl|gm/dl|mmol/l|"
    r"meq/l|u/l|iu/l|miu/l|"
    r"ng/ml|pg/ml|µg/dl|"
    r"cells/cumm|million/cumm|"
    r"lakhs/cumm|mmhg|bpm|%)\b",
    re.IGNORECASE
)


BP_PATTERN = re.compile(
    r"\b\d{2,3}\s*/\s*\d{2,3}\s*(mmhg)?\b",
    re.IGNORECASE
)


def validate_medical_report(text):
    """
    Checks whether uploaded text is likely to be a medical report.

    Returns:
        {
            "valid": bool,
            "score": int,
            "medical_matches": list,
            "reason": str
        }
    """

    if not text or len(text.strip()) < 30:
        return {
            "valid": False,
            "score": 0,
            "medical_matches": [],
            "reason": "The uploaded file does not contain enough readable medical information."
        }

    text_lower = text.lower()

    score = 0
    medical_matches = []

    # -------------------------------------------------
    # 1. Count unique medical keywords
    # -------------------------------------------------

    for keyword in MEDICAL_KEYWORDS:
        if keyword in text_lower:
            medical_matches.append(keyword)
            score += 1

    # -------------------------------------------------
    # 2. Detect medical report headings
    # -------------------------------------------------

    heading_matches = []

    for heading in MEDICAL_HEADINGS:
        if heading in text_lower:
            heading_matches.append(heading)
            score += 2

    # -------------------------------------------------
    # 3. Detect medical units and values
    # -------------------------------------------------

    medical_units = MEDICAL_UNIT_PATTERN.findall(text_lower)

    if medical_units:
        score += min(len(medical_units), 5)

    # -------------------------------------------------
    # 4. Detect blood pressure pattern
    # -------------------------------------------------

    if BP_PATTERN.search(text_lower):
        score += 2

    # -------------------------------------------------
    # 5. Detect non-medical document signals
    # -------------------------------------------------

    non_medical_matches = []

    for keyword in NON_MEDICAL_KEYWORDS:
        if keyword in text_lower:
            non_medical_matches.append(keyword)

    # Strong penalty if document clearly looks non-medical
    score -= min(len(non_medical_matches) * 2, 8)

    # -------------------------------------------------
    # Final validation
    # -------------------------------------------------

    unique_medical_matches = list(set(medical_matches))

    # A valid report should have enough medical evidence
    if score >= 5 and len(unique_medical_matches) >= 2:
        return {
            "valid": True,
            "score": score,
            "medical_matches": unique_medical_matches,
            "reason": "Valid medical report detected."
        }

    return {
        "valid": False,
        "score": score,
        "medical_matches": unique_medical_matches,
        "reason": (
            "This document does not appear to contain sufficient medical "
            "report information. Please upload a valid medical report."
        )
    }