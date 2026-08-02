"""
Phase 2 semantic NLP layer for MediInsight  .
Uses BioClinicalBERT if available.
Falls back to TF-IDF if BioClinicalBERT fails.
"""

from functools import lru_cache
from typing import Dict, List, Tuple
import numpy as np


SECTION_PROTOTYPES = {
    "symptoms": [
        "patient complains of fever cough pain fatigue dizziness breathlessness",
        "reported symptoms include weakness swelling chest discomfort frequent urination",
        "clinical history describing what the patient feels or experiences",
    ],
    "clinical_findings": [
        "abnormal laboratory result imaging impression organ enlargement dysfunction infection anemia",
        "doctor observed clinical diagnosis medical finding disease marker elevated reduced count",
        "objective report finding based on scan blood test urine test or examination",
    ],
    "recommendations": [
        "doctor advised follow up consultation medication diet monitoring repeat test treatment",
        "recommendation plan for management evaluation therapy specialist review",
        "next steps the patient should follow after the medical report",
    ],
}

CONDITION_PROTOTYPES = {
    "Possible anemia": [
        "low hemoglobin low red blood cells fatigue weakness pallor anemia",
        "reduced hb value indicates anemia or low oxygen carrying capacity",
    ],
    "Possible diabetes or poor sugar control": [
        "high glucose high hba1c diabetes sugar uncontrolled polyuria nocturia blurred vision",
        "blood sugar markers are elevated suggesting diabetes risk",
    ],
    "Possible infection or inflammation": [
        "high white blood cells fever infection inflammation neutrophils elevated crp pus bacteria",
        "abnormal wbc count with symptoms may suggest infection",
    ],
    "Possible liver stress": [
        "high alt ast bilirubin fatty liver hepatomegaly liver enzyme elevation",
        "liver function markers are abnormal indicating liver stress",
    ],
    "Possible kidney stress": [
        "high creatinine urea reduced egfr kidney function abnormal protein urine",
        "renal markers indicate possible kidney stress or reduced filtration",
    ],
    "Possible thyroid imbalance": [
        "high tsh low t3 t4 hypothyroid thyroid imbalance fatigue weight change",
        "thyroid markers abnormal suggesting thyroid imbalance",
    ],
    "Possible cholesterol/cardiac risk": [
        "high ldl triglycerides cholesterol low hdl cardiac risk dyslipidemia",
        "lipid profile abnormal increasing heart disease risk",
    ],
}


def _clean_lines(text: str) -> List[str]:
    lines = []
    for line in text.split("\n"):
        cleaned = " ".join(line.strip().split())
        if len(cleaned) >= 4:
            lines.append(cleaned)
    return lines


@lru_cache(maxsize=1)
def _load_bioclinicalbert():
    import torch
    from transformers import AutoModel, AutoTokenizer

    model_name = "emilyalsentzer/Bio_ClinicalBERT"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()

    return tokenizer, model, torch


def _bert_embeddings(texts: List[str]) -> np.ndarray:
    tokenizer, model, torch = _load_bioclinicalbert()

    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=128,
        return_tensors="pt",
    )

    with torch.no_grad():
        output = model(**encoded)
        token_embeddings = output.last_hidden_state
        attention_mask = encoded["attention_mask"].unsqueeze(-1)

        masked = token_embeddings * attention_mask
        summed = masked.sum(dim=1)
        counts = attention_mask.sum(dim=1).clamp(min=1)

        sentence_embeddings = summed / counts

    return sentence_embeddings.cpu().numpy()


def _tfidf_embeddings(texts: List[str]) -> np.ndarray:
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words="english"
    )

    return vectorizer.fit_transform(texts).toarray()


def _embed(
    texts: List[str],
    prefer_bioclinicalbert: bool = True
) -> Tuple[np.ndarray, str]:

    if prefer_bioclinicalbert:
        try:
            return _bert_embeddings(texts), "BioClinicalBERT"
        except Exception:
            pass

    return _tfidf_embeddings(texts), "TF-IDF fallback"


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / np.clip(
        np.linalg.norm(a, axis=1, keepdims=True),
        1e-9,
        None
    )

    b_norm = b / np.clip(
        np.linalg.norm(b, axis=1, keepdims=True),
        1e-9,
        None
    )

    return np.matmul(a_norm, b_norm.T)


def semantic_classify_report_sections(
    text: str,
    threshold: float = 0.28,
    prefer_bioclinicalbert: bool = True,
) -> Dict[str, object]:

    lines = _clean_lines(text)

    sections = {
        "symptoms": [],
        "clinical_findings": [],
        "recommendations": []
    }

    if not lines:
        return {
            "sections": sections,
            "engine": "none",
            "matches": []
        }

    prototype_labels = []
    prototype_texts = []

    for label, examples in SECTION_PROTOTYPES.items():
        for example in examples:
            prototype_labels.append(label)
            prototype_texts.append(example)

    embeddings, engine = _embed(
        lines + prototype_texts,
        prefer_bioclinicalbert
    )

    line_embeddings = embeddings[:len(lines)]
    prototype_embeddings = embeddings[len(lines):]

    scores = _cosine_similarity(
        line_embeddings,
        prototype_embeddings
    )

    matches = []

    for index, line in enumerate(lines):
        best_idx = int(np.argmax(scores[index]))
        best_score = float(scores[index][best_idx])
        best_label = prototype_labels[best_idx]

        if best_score >= threshold:
            sections[best_label].append(line)
            matches.append({
                "line": line,
                "section": best_label,
                "score": round(best_score, 3),
            })

    for key in sections:
        sections[key] = list(dict.fromkeys(sections[key]))

    return {
        "sections": sections,
        "engine": engine,
        "matches": matches
    }


def infer_clinical_context(
    values: Dict[str, str],
    severity_results: Dict[str, str],
    report_sections: Dict[str, List[str]],
    prefer_bioclinicalbert: bool = True,
) -> Dict[str, object]:

    evidence_parts = []

    for parameter, status in severity_results.items():
        value = values.get(parameter, "Not Found")
        evidence_parts.append(f"{parameter} {value} {status}")

    for key in ["symptoms", "clinical_findings"]:
        evidence_parts.extend(report_sections.get(key, [])[:5])

    evidence_text = " ; ".join(evidence_parts).strip()

    if not evidence_text:
        return {
            "contexts": [],
            "engine": "none",
            "evidence": ""
        }

    condition_labels = []
    condition_texts = []

    for label, examples in CONDITION_PROTOTYPES.items():
        condition_labels.append(label)
        condition_texts.append(" ; ".join(examples))

    embeddings, engine = _embed(
        [evidence_text] + condition_texts,
        prefer_bioclinicalbert
    )

    evidence_embedding = embeddings[:1]
    condition_embeddings = embeddings[1:]

    scores = _cosine_similarity(
        evidence_embedding,
        condition_embeddings
    )[0]

    ranked = sorted(
        [
            {
                "condition": condition_labels[i],
                "score": round(float(scores[i]), 3)
            }
            for i in range(len(condition_labels))
        ],
        key=lambda item: item["score"],
        reverse=True,
    )

    contexts = [
        item for item in ranked
        if item["score"] >= 0.18
    ][:3]

    return {
        "contexts": contexts,
        "engine": engine,
        "evidence": evidence_text
    }


def build_semantic_patient_insights(
    clinical_context: Dict[str, object]
) -> str:

    contexts = clinical_context.get("contexts", [])

    if not contexts:
        return "No strong semantic disease context was detected from the available findings."

    lines = ["Semantic clinical context detected:"]

    for item in contexts:
        lines.append(
            f"- {item['condition']} — confidence score {item['score']}"
        )

    lines.append(
        "These are context links, not a diagnosis. A doctor must confirm the meaning clinically."
    )

    return "\n".join(lines)