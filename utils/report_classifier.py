import re


def clean_line(line):
    line = line.strip()
    line = re.sub(r"^[•\-\*\s]+", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def normalize_heading(line):
    line = line.lower().strip()
    line = line.replace(":", "")
    line = re.sub(r"\(.*?\)", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def looks_like_heading(line):
    cleaned = line.strip()

    if cleaned.endswith(":"):
        return True

    if cleaned.isupper() and len(cleaned.split()) <= 6:
        return True

    return False


def is_metadata(line):
    lower = line.lower()

    metadata_patterns = [
        r"^patient name",
        r"^age",
        r"^gender",
        r"^patient id",
        r"^hospital",
        r"^hospital name",
        r"^date",
        r"^date of admission"
    ]

    return any(re.search(pattern, lower) for pattern in metadata_patterns)


def is_lab_value(line):
    lower = line.lower()

    lab_patterns = [
        r"^hemoglobin",
        r"^wbc",
        r"^platelets",
        r"^rbc",
        r"^rbc count",
        r"^hematocrit",
        r"^glucose",
        r"^fasting glucose",
        r"^postprandial glucose",
        r"^hba1c",
        r"^cholesterol",
        r"^total cholesterol",
        r"^ldl",
        r"^ldl cholesterol",
        r"^hdl",
        r"^hdl cholesterol",
        r"^triglycerides",
        r"^vldl",
        r"^creatinine",
        r"^blood urea",
        r"^alt",
        r"^ast",
        r"^bilirubin",
        r"^bilirubin total",
        r"^tsh",
        r"^t3",
        r"^t4",
        r"^crp",
        r"^esr",
        r"^egfr",
        r"^albumin",
        r"^uric acid",
        r"^alkaline phosphatase",
        r"^temperature",
        r"^heart rate",
        r"^blood pressure",
        r"^oxygen saturation",
        r"^respiratory rate",
        r"^neutrophils",
        r"^pus cells",
        r"^urine ketones",
        r"^protein",
        r"^bacteria"
    ]

    return any(re.search(pattern, lower) for pattern in lab_patterns)


def classify_report_sections(text):
    sections = {
        "symptoms": [],
        "clinical_findings": [],
        "possible_conditions": [],
        "recommendations": []
    }

    symptom_keywords = [
        "fatigue",
        "pain",
        "dizziness",
        "dyspnea",
        "polyuria",
        "nocturia",
        "chest discomfort",
        "shortness of breath",
        "breathlessness",
        "blurred vision",
        "confusion",
        "swelling",
        "fever",
        "cough",
        "weakness",
        "headache",
        "vomiting",
        "nausea",
        "loss of appetite",
        "burning sensation",
        "difficulty walking",
        "chills",
        "tenderness"
    ]

    clinical_keywords = [
        "hypertrophy",
        "hepatomegaly",
        "dysfunction",
        "infiltration",
        "effusion",
        "cortical thinning",
        "ejection fraction",
        "st-segment",
        "ecg",
        "echocardiography",
        "ultrasound",
        "ct",
        "mri",
        "x-ray",
        "scan",
        "grade",
        "preserved",
        "reduced",
        "enlarged",
        "edema",
        "fluid collection",
        "infiltrates",
        "tachycardia"
    ]

    possible_condition_keywords = [
        "possible",
        "suggestive of",
        "consistent with",
        "likely",
        "suspected",
        "impression",
        "diagnosis",
        "disease",
        "syndrome",
        "disorder",
        "nafld",
        "fatty liver disease",
        "chronic kidney disease",
        "kidney disease",
        "diabetes",
        "diabetic",
        "anemia",
        "hypertension",
        "hypothyroidism",
        "hyperthyroidism",
        "infection",
        "inflammation",
        "cardiac risk",
        "dyslipidemia",
        "cellulitis",
        "abscess",
        "heart failure"
    ]

    recommendation_keywords = [
        "follow-up",
        "follow up",
        "therapy",
        "consultation",
        "consult",
        "advised",
        "recommended",
        "recommend",
        "diet",
        "monitoring",
        "evaluation",
        "restriction",
        "lifestyle",
        "initiate",
        "optimize",
        "start",
        "continue",
        "repeat",
        "review",
        "refer",
        "hospital admission",
        "maintain hydration"
    ]

    section_map = {
        "chief complaints": "symptoms",
        "cardiology findings": "clinical_findings",
        "radiology notes": "clinical_findings",
        "radiology report": "clinical_findings",
        "clinical findings": "clinical_findings",
        "physician impression": "possible_conditions",
        "recommendations": "recommendations"
    }

    reset_headings = {
        "complete blood count",
        "cbc",
        "metabolic panel",
        "diabetic profile",
        "lipid profile",
        "renal function test",
        "liver function test",
        "thyroid profile",
        "urine analysis",
        "vital signs"
    }

    current_section = None

    for raw_line in text.split("\n"):
        cleaned = clean_line(raw_line)

        if len(cleaned) < 4:
            continue

        if is_metadata(cleaned):
            continue

        normalized = normalize_heading(cleaned)

        if normalized in section_map:
            current_section = section_map[normalized]
            continue

        if normalized in reset_headings:
            current_section = None
            continue

        if looks_like_heading(cleaned):
            current_section = None
            continue

        if is_lab_value(cleaned):
            continue

        lower = cleaned.lower()

        is_symptom = any(word in lower for word in symptom_keywords)
        is_clinical = any(word in lower for word in clinical_keywords)
        is_possible_condition = any(word in lower for word in possible_condition_keywords)
        is_recommendation = any(word in lower for word in recommendation_keywords)

        if current_section == "symptoms":
            sections["symptoms"].append(cleaned)

        elif current_section == "clinical_findings":
            if is_possible_condition:
                sections["possible_conditions"].append(cleaned)
            else:
                sections["clinical_findings"].append(cleaned)

        elif current_section == "possible_conditions":
            sections["possible_conditions"].append(cleaned)

        elif current_section == "recommendations":
            sections["recommendations"].append(cleaned)

        elif is_recommendation:
            sections["recommendations"].append(cleaned)

        elif is_possible_condition:
            sections["possible_conditions"].append(cleaned)

        elif is_symptom:
            sections["symptoms"].append(cleaned)

        elif is_clinical:
            sections["clinical_findings"].append(cleaned)

    for key in sections:
        sections[key] = list(dict.fromkeys(sections[key]))

    return sections