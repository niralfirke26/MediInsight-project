from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

from utils.embedding_model import get_embedding_model


def clean_line(line):
    line = line.strip()
    line = re.sub(r"^[•\-\*\s]+", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def normalize_line(line):
    line = line.lower().strip()
    line = line.replace(":", "")
    line = re.sub(r"\(.*?\)", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def is_noise_line(line):
    normalized = normalize_line(line)
    raw = line.strip()

    if not raw:
        return True

    noise_headings = {
        "complete blood count",
        "cbc",
        "metabolic panel",
        "diabetic profile",
        "lipid profile",
        "renal function test",
        "liver function test",
        "thyroid profile",
        "urine analysis",
        "urinalysis",
        "cardiology findings",
        "radiology notes",
        "radiology report",
        "physician impression",
        "recommendations",
        "chief complaints",
        "vital signs",
        "patient details",
        "report details",
        "laboratory findings",
        "clinical notes"
    }

    metadata_prefixes = (
        "patient name",
        "patient id",
        "age",
        "sex",
        "gender",
        "date",
        "sample",
        "specimen",
        "ref no",
        "report id",
        "department",
        "doctor",
        "consultant",
        "hospital",
        "lab name",
        "laboratory",
        "collected",
        "received",
        "reported"
    )

    if normalized in noise_headings:
        return True

    if any(normalized.startswith(prefix) for prefix in metadata_prefixes):
        return True

    if raw.endswith(":"):
        return True

    if raw.isupper() and len(raw.split()) <= 5:
        return True

    return False


def is_simple_lab_result(line):
    normalized = normalize_line(line)

    lab_result_patterns = [
        r"^[a-zA-Z\s\/\-\(\)]+[:\-]\s*\d+(\.\d+)?",
        r"^[a-zA-Z\s\/\-\(\)]+[:\-]\s*(high|low|normal|positive|negative|present|absent|trace)$",
        r"^[a-zA-Z\s\/\-\(\)]+\s+\d+(\.\d+)?\s*(mg\/dl|g\/dl|mmol\/l|iu\/l|u\/l|%|cells\/.*|ml\/min)?$"
    ]

    for pattern in lab_result_patterns:
        if re.match(pattern, line.strip(), re.IGNORECASE):
            return True

    simple_lab_terms = (
        "proteinuria",
        "albuminuria",
        "ketones",
        "glucose",
        "pus cells",
        "rbc",
        "wbc",
        "epithelial cells",
        "bacteria",
        "casts",
        "crystals",
        "nitrite",
        "bilirubin",
        "urobilinogen"
    )

    if ":" in line and any(term in normalized for term in simple_lab_terms):
        return True

    return False


def is_recommendation_line(line):
    normalized = normalize_line(line)

    recommendation_terms = (
        "advised",
        "recommended",
        "recommend",
        "suggested",
        "consultation",
        "consult",
        "follow up",
        "follow-up",
        "repeat",
        "monitoring",
        "monitor",
        "start",
        "continue",
        "avoid",
        "diet",
        "lifestyle",
        "review",
        "evaluation",
        "refer",
        "referral",
        "admission",
        "urgent care",
        "medical review"
    )

    return any(term in normalized for term in recommendation_terms)


def is_symptom_like_line(line):
    normalized = normalize_line(line)

    symptom_terms = (
        "complains",
        "complaint",
        "reports",
        "history of",
        "fever",
        "pain",
        "cough",
        "breathlessness",
        "shortness of breath",
        "weakness",
        "fatigue",
        "dizziness",
        "nausea",
        "vomiting",
        "burning",
        "swelling",
        "reduced appetite",
        "confusion"
    )

    return any(term in normalized for term in symptom_terms)


def is_clinical_finding_line(line):
    normalized = normalize_line(line)

    finding_terms = (
        "ecg",
        "echo",
        "echocardiography",
        "xray",
        "x-ray",
        "ct",
        "mri",
        "ultrasound",
        "usg",
        "shows",
        "reveals",
        "suggestive of",
        "ejection fraction",
        "pleural effusion",
        "pulmonary edema",
        "lvh",
        "diastolic dysfunction"
    )

    return any(term in normalized for term in finding_terms)


class SemanticMedicalClassifier:

    def __init__(self):

        self.model = get_embedding_model()

        self.section_examples = {
            "symptoms": [
                "patient has fever and chills",
                "patient reports weakness and fatigue",
                "shortness of breath on exertion",
                "pain and swelling in the leg",
                "burning sensation during urination",
                "dizziness nausea loss of appetite",
                "patient complains of cough and breathing difficulty"
            ],

            "clinical_findings": [
                "ecg shows left ventricular hypertrophy",
                "echocardiography shows diastolic dysfunction",
                "ultrasound shows soft tissue edema",
                "mri shows inflammatory changes",
                "chest xray shows infiltrates",
                "imaging reveals abnormal clinical finding",
                "oxygen saturation is reduced",
                "ejection fraction is reduced"
            ],

            "possible_conditions": [
                "poorly controlled diabetes mellitus",
                "chronic kidney disease",
                "bacterial soft tissue infection",
                "cellulitis with abscess formation",
                "urinary tract infection",
                "dyslipidemia",
                "anemia",
                "hypertensive cardiovascular disease",
                "possible heart failure pattern",
                "possible hypothyroid pattern"
            ],

            "recommendations": [
                "surgical evaluation advised",
                "start intravenous antibiotics",
                "strict blood sugar monitoring",
                "nephrology consultation advised",
                "repeat infection markers",
                "hospital admission recommended",
                "low sodium diabetic diet advised",
                "renal friendly diet advised",
                "follow up with physician recommended"
            ]
        }

        self.section_embeddings = {}

        for section, examples in self.section_examples.items():
            embeddings = self.model.encode(
                examples,
                convert_to_numpy=True,
                normalize_embeddings=True
            )

            self.section_embeddings[section] = np.mean(
                embeddings,
                axis=0
            )

    def classify_line(self, line, threshold=0.46):

        cleaned = clean_line(line)

        if len(cleaned) < 5:
            return None, 0

        if is_noise_line(cleaned):
            return None, 0

        if is_simple_lab_result(cleaned):
            return None, 0

        if is_recommendation_line(cleaned):
            return "recommendations", 0.92

        line_embedding = self.model.encode(
            [cleaned],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]

        scores = {}

        for section, section_embedding in self.section_embeddings.items():
            similarity = cosine_similarity(
                [line_embedding],
                [section_embedding]
            )[0][0]

            scores[section] = similarity

        best_section = max(scores, key=scores.get)
        best_score = scores[best_section]

        if is_symptom_like_line(cleaned) and best_score >= 0.40:
            return "symptoms", best_score

        if is_clinical_finding_line(cleaned) and best_score >= 0.40:
            return "clinical_findings", best_score

        if best_score < threshold:
            return None, best_score

        return best_section, best_score

    def classify_report(self, text):

        sections = {
            "symptoms": [],
            "clinical_findings": [],
            "possible_conditions": [],
            "recommendations": []
        }

        seen_lines = set()

        for line in text.split("\n"):
            cleaned = clean_line(line)

            if not cleaned:
                continue

            normalized = normalize_line(cleaned)

            if normalized in seen_lines:
                continue

            section, score = self.classify_line(cleaned)

            if section:
                sections[section].append({
                    "text": cleaned,
                    "confidence": round(float(score), 3)
                })

                seen_lines.add(normalized)

        return sections