import os
import json
import hashlib
import re
import faiss

from utils.embedding_model import get_embedding_model
from utils.medical_knowledge_base import get_medical_knowledge_chunks


CACHE_DIR = "cache"
FAISS_INDEX_PATH = os.path.join(CACHE_DIR, "medical_faiss.index")
METADATA_PATH = os.path.join(CACHE_DIR, "medical_chunks_metadata.json")
HASH_PATH = os.path.join(CACHE_DIR, "medical_kb_hash.txt")


class FAISSMedicalRetriever:
    def __init__(self):
        self.model = get_embedding_model()
        self.knowledge_chunks = get_medical_knowledge_chunks()

        os.makedirs(CACHE_DIR, exist_ok=True)

        if self._cache_is_valid():
            self._load_cache()
        else:
            self._build_and_save_cache()

    def _knowledge_hash(self):
        kb_text = json.dumps(self.knowledge_chunks, sort_keys=True)
        return hashlib.md5(kb_text.encode("utf-8")).hexdigest()

    def _cache_is_valid(self):
        return (
            os.path.exists(FAISS_INDEX_PATH)
            and os.path.exists(METADATA_PATH)
            and os.path.exists(HASH_PATH)
            and self._saved_hash_matches()
        )

    def _saved_hash_matches(self):
        try:
            with open(HASH_PATH, "r", encoding="utf-8") as file:
                saved_hash = file.read().strip()
            return saved_hash == self._knowledge_hash()
        except Exception:
            return False

    def _build_and_save_cache(self):
        self.chunk_texts = [chunk["text"] for chunk in self.knowledge_chunks]

        self.chunk_embeddings = self.model.encode(
            self.chunk_texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype("float32")

        embedding_dimension = self.chunk_embeddings.shape[1]

        self.index = faiss.IndexFlatIP(embedding_dimension)
        self.index.add(self.chunk_embeddings)

        faiss.write_index(self.index, FAISS_INDEX_PATH)

        with open(METADATA_PATH, "w", encoding="utf-8") as file:
            json.dump(self.knowledge_chunks, file, indent=2)

        with open(HASH_PATH, "w", encoding="utf-8") as file:
            file.write(self._knowledge_hash())

    def _load_cache(self):
        self.index = faiss.read_index(FAISS_INDEX_PATH)

        with open(METADATA_PATH, "r", encoding="utf-8") as file:
            self.knowledge_chunks = json.load(file)

    def normalize_text(self, text):
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s\-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def tokenize(self, text):
        return set(self.normalize_text(text).split())

    def build_query(self, values, severity_results, report_sections):
        query_parts = []

        for parameter, status in severity_results.items():
            value = values.get(parameter, "Not Found")

            if value != "Not Found":
                query_parts.append(f"{parameter} {value} {status}")

        for section_name in [
            "symptoms",
            "clinical_findings",
            "possible_conditions",
            "recommendations"
        ]:
            for item in report_sections.get(section_name, []):
                query_parts.append(item)

        return " ".join(query_parts)

    def calculate_keyword_overlap_score(self, query_text, chunk_text):
        query_tokens = self.tokenize(query_text)
        chunk_tokens = self.tokenize(chunk_text)

        if not query_tokens:
            return 0.0

        overlap = query_tokens.intersection(chunk_tokens)
        overlap_score = len(overlap) / len(query_tokens)

        medical_priority_terms = {
            "glucose", "hba1c", "diabetes", "diabetic", "sugar",
            "creatinine", "egfr", "renal", "kidney", "ckd",
            "infection", "cellulitis", "abscess", "fever", "pus",
            "bacteria", "antibiotics", "urinary", "nitrites",
            "cholesterol", "ldl", "hdl", "triglycerides",
            "ecg", "st-segment", "tachycardia", "hypertrophy",
            "heart", "cardiac", "failure", "ejection",
            "pulmonary", "edema", "fluid", "cardiorenal",
            "alt", "ast", "bilirubin", "fatty", "nafld", "liver",
            "hemoglobin", "anemia", "oxygen", "pleural",
            "thyroid", "tsh", "hypothyroidism"
        }

        priority_bonus = 0.0

        for term in overlap:
            if term in medical_priority_terms:
                priority_bonus += 0.03

        return min(overlap_score + priority_bonus, 1.0)

    def get_report_context_flags(self, values, report_sections):
        report_text = " ".join(
            report_sections.get("symptoms", []) +
            report_sections.get("clinical_findings", []) +
            report_sections.get("possible_conditions", []) +
            report_sections.get("recommendations", [])
        ).lower()

        values_text = " ".join(
            f"{key} {value}"
            for key, value in values.items()
        ).lower()

        full_text = report_text + " " + values_text

        flags = {
            "simple_report": False,
            "complex_multisystem": False,
            "dominant_leg_infection": False,

            "diabetes": any(term in full_text for term in [
                "glucose", "hba1c", "diabetes", "diabetic",
                "blood sugar", "sugar", "polyuria", "nocturia"
            ]),

            "lipid": any(term in full_text for term in [
                "cholesterol", "ldl", "hdl", "triglycerides",
                "dyslipidemia", "statin"
            ]),

            "infection": any(term in full_text for term in [
                "fever", "chills", "infection", "cellulitis",
                "abscess", "soft tissue", "pus", "bacteria",
                "antibiotics", "sepsis", "respiratory tract infection",
                "lower respiratory tract infection", "hospital admission"
            ]),

            "uti": any(term in full_text for term in [
                "urinary tract infection", "burning sensation during urination",
                "burning urination", "burning micturition",
                "pus cells", "bacteria present", "nitrites positive",
                "reduced urine output"
            ]),

            "leg_wound": any(term in full_text for term in [
                "leg swelling", "left lower leg", "left leg",
                "cellulitis", "abscess", "diabetic foot",
                "foot care", "wound", "soft tissue edema",
                "soft tissue infection", "lower limb",
                "calf region", "leg tenderness", "difficulty walking"
            ]),

            "surgical_infection": any(term in full_text for term in [
                "surgical evaluation", "abscess formation",
                "developing abscess", "diabetic foot care",
                "left leg infection", "soft tissue infection",
                "intravenous antibiotics", "broad-spectrum intravenous antibiotics"
            ]),

            "kidney": any(term in full_text for term in [
                "creatinine", "egfr", "renal", "kidney",
                "chronic kidney disease", "blood urea nitrogen",
                "protein in urine", "proteinuria", "microalbuminuria",
                "cortical thinning", "acute-on-chronic kidney disease"
            ]),

            "cardiac_findings": any(term in full_text for term in [
                "ecg", "st-segment", "tachycardia",
                "left ventricular hypertrophy", "diastolic dysfunction",
                "ejection fraction", "cardiac", "heart failure",
                "chest discomfort", "chest tightness",
                "chest heaviness", "echocardiography",
                "premature ventricular complexes",
                "pulmonary artery hypertension"
            ]),

            "heart_failure": any(term in full_text for term in [
                "heart failure", "congestive cardiac failure",
                "pleural effusion", "pulmonary edema",
                "fluid overload", "orthopnea",
                "difficulty sleeping flat",
                "pedal edema", "pitting swelling",
                "swelling in feet", "swelling in feet and ankles",
                "reduced ejection fraction",
                "mildly reduced ejection fraction",
                "ejection fraction of 38",
                "cardiorenal syndrome",
                "vascular congestion",
                "nt-probnp"
            ]),

            "liver": any(term in full_text for term in [
                "alt", "ast", "bilirubin", "fatty", "nafld",
                "liver", "hepatomegaly", "alkaline phosphatase",
                "gamma gt", "ascites"
            ]),

            "thyroid": any(term in full_text for term in [
                "thyroid", "tsh", "hypothyroidism", "t3", "t4"
            ]),

            "anemia": any(term in full_text for term in [
                "hemoglobin", "anemia", "rbc", "hematocrit"
            ]),

            "oxygen": any(term in full_text for term in [
                "oxygen", "shortness of breath", "breathlessness",
                "dyspnea", "pleural effusion", "respiratory distress",
                "oxygen supplementation"
            ]),

            "metabolic": any(term in full_text for term in [
                "metabolic", "fatty liver", "dyslipidemia",
                "high triglycerides", "obesity", "high blood pressure",
                "bmi"
            ])
        }

        flags["dominant_leg_infection"] = (
            flags["infection"]
            and flags["leg_wound"]
            and flags["surgical_infection"]
            and not flags["heart_failure"]
        )

        multisystem_count = sum([
            flags["diabetes"],
            flags["lipid"],
            flags["kidney"],
            flags["cardiac_findings"],
            flags["heart_failure"],
            flags["liver"],
            flags["thyroid"],
            flags["anemia"],
            flags["oxygen"],
            flags["metabolic"]
        ])

        flags["complex_multisystem"] = multisystem_count >= 6

        major_flags = [
            flags["infection"],
            flags["uti"],
            flags["kidney"],
            flags["cardiac_findings"],
            flags["heart_failure"],
            flags["liver"],
            flags["thyroid"],
            flags["oxygen"],
            flags["metabolic"]
        ]

        if (
            flags["diabetes"]
            and flags["lipid"]
            and flags["anemia"]
            and not any(major_flags)
        ):
            flags["simple_report"] = True

        return flags

    def calculate_priority_boost(self, chunk, flags):
        boost = 0.0

        chunk_id = chunk["id"]
        category = chunk["category"]

        if flags["simple_report"]:
            if chunk_id == "poorly_controlled_diabetes":
                boost += 0.34
            elif chunk_id == "cholesterol_cardiac_risk":
                boost += 0.32
            elif chunk_id == "anemia_low_hemoglobin":
                boost += 0.28
            elif chunk_id == "followup_monitoring_context":
                boost += 0.18
            else:
                boost -= 0.35

            return boost

        if flags["infection"]:
            if chunk_id == "diabetes_infection_risk":
                boost += 0.42 if flags["complex_multisystem"] else 0.52
            elif chunk_id == "soft_tissue_infection":
                boost += 0.58 if flags["dominant_leg_infection"] else 0.10
            elif chunk_id == "urgent_surgical_infection_context":
                boost += 0.56 if flags["dominant_leg_infection"] else 0.06
            elif chunk_id == "systemic_inflammation_markers":
                boost += 0.28 if flags["complex_multisystem"] else 0.34
            elif category == "infection":
                boost += 0.14 if flags["complex_multisystem"] else 0.22

        if flags["uti"]:
            if chunk_id == "urinary_tract_infection":
                boost += 0.42

        if flags["diabetes"]:
            if chunk_id == "poorly_controlled_diabetes":
                boost += 0.30
            elif category == "diabetes":
                boost += 0.12

        if flags["diabetes"] and flags["leg_wound"]:
            if chunk_id == "diabetic_foot_care_context":
                boost += 0.30

        if flags["kidney"]:
            if chunk_id == "diabetic_kidney_risk" and flags["diabetes"]:
                boost += 0.40
            elif chunk_id == "kidney_stress_ckd":
                boost += 0.28
            elif category == "kidney":
                boost += 0.14

        if flags["lipid"]:
            if chunk_id == "cholesterol_cardiac_risk":
                boost += 0.26

        if flags["cardiac_findings"]:
            if chunk_id == "cardiac_strain":
                boost += 0.30
            elif chunk_id == "chest_symptoms_cardiac_context":
                boost += 0.20
            elif category == "cardiac":
                boost += 0.14

        if flags["heart_failure"]:
            if chunk_id == "heart_failure_pattern":
                boost += 0.48
            elif chunk_id == "pleural_effusion_context":
                boost += 0.32
            elif chunk_id == "cardiac_strain":
                boost += 0.18

        if flags["liver"]:
            if chunk_id == "fatty_liver_liver_stress":
                boost += 0.26
            elif category == "liver":
                boost += 0.12

        if flags["thyroid"]:
            if chunk_id == "thyroid_imbalance":
                boost += 0.24
            elif chunk_id == "thyroid_cholesterol_link":
                boost += 0.16

        if flags["anemia"]:
            if chunk_id == "anemia_low_hemoglobin":
                boost += 0.24
            elif chunk_id == "anemia_oxygen_heart_stress":
                boost += 0.18

        if flags["oxygen"]:
            if chunk_id == "low_oxygen":
                boost += 0.26
            elif chunk_id == "pleural_effusion_context":
                boost += 0.22

        if flags["metabolic"]:
            if chunk_id == "metabolic_syndrome_context":
                boost += 0.24

        return boost

    def build_required_ids(self, flags):
        required_ids = []

        if flags["simple_report"]:
            return [
                "poorly_controlled_diabetes",
                "cholesterol_cardiac_risk",
                "anemia_low_hemoglobin",
                "followup_monitoring_context"
            ]

        if flags["dominant_leg_infection"]:
            required_ids.extend([
                "soft_tissue_infection",
                "urgent_surgical_infection_context"
            ])

        if flags["heart_failure"]:
            required_ids.append("heart_failure_pattern")

        if flags["lipid"]:
            required_ids.append("cholesterol_cardiac_risk")

        if flags["kidney"]:
            required_ids.append(
                "diabetic_kidney_risk"
                if flags["diabetes"]
                else "kidney_stress_ckd"
            )

        if flags["liver"]:
            required_ids.append("fatty_liver_liver_stress")

        if flags["diabetes"]:
            required_ids.append("poorly_controlled_diabetes")

        if flags["thyroid"]:
            required_ids.append("thyroid_imbalance")

        if flags["anemia"]:
            required_ids.append("anemia_low_hemoglobin")

        if flags["oxygen"]:
            required_ids.append("low_oxygen")

        if flags["uti"]:
            required_ids.append("urinary_tract_infection")

        if flags["infection"]:
            required_ids.append("diabetes_infection_risk")

        if flags["metabolic"]:
            required_ids.append("metabolic_syndrome_context")

        return list(dict.fromkeys(required_ids))

    def get_concept_group(self, chunk_id):
        concept_map = {
            "poorly_controlled_diabetes": "diabetes_control",
            "diabetes_infection_risk": "diabetes_infection",
            "soft_tissue_infection": "soft_tissue_infection",
            "urgent_surgical_infection_context": "urgent_infection",
            "urinary_tract_infection": "uti",
            "diabetic_kidney_risk": "kidney",
            "kidney_stress_ckd": "kidney",
            "cholesterol_cardiac_risk": "cardiac_lipid",
            "cardiac_strain": "cardiac",
            "chest_symptoms_cardiac_context": "cardiac",
            "heart_failure_pattern": "heart_failure",
            "pleural_effusion_context": "pleural_effusion",
            "fatty_liver_liver_stress": "liver",
            "thyroid_imbalance": "thyroid",
            "thyroid_cholesterol_link": "thyroid_lipid",
            "anemia_low_hemoglobin": "anemia",
            "anemia_oxygen_heart_stress": "anemia_oxygen",
            "low_oxygen": "oxygen",
            "metabolic_syndrome_context": "metabolic",
            "systemic_inflammation_markers": "systemic_inflammation",
            "diabetic_foot_care_context": "diabetic_foot",
            "followup_monitoring_context": "followup"
        }

        return concept_map.get(chunk_id, chunk_id)

    def add_retrieval_reason(self, item):
        chunk_id = item["id"]

        reason_map = {
            "poorly_controlled_diabetes":
                "high glucose or HbA1c markers are present",

            "cholesterol_cardiac_risk":
                "cholesterol, LDL, HDL, or triglyceride values are abnormal",

            "anemia_low_hemoglobin":
                "low hemoglobin or anemia is present",

            "followup_monitoring_context":
                "the report recommends monitoring or follow-up",

            "diabetes_infection_risk":
                "diabetes and infection-related findings appear together",

            "soft_tissue_infection":
                "leg swelling, cellulitis, abscess, or soft-tissue infection findings are mentioned",

            "urgent_surgical_infection_context":
                "surgical evaluation, abscess, IV antibiotics, or hospital-level infection management is mentioned",

            "urinary_tract_infection":
                "urinary symptoms, bacteria, pus cells, or nitrites are present",

            "diabetic_kidney_risk":
                "diabetes and kidney markers appear together",

            "kidney_stress_ckd":
                "kidney markers suggest renal stress or chronic kidney disease",

            "cardiac_strain":
                "ECG, echo, chest symptoms, or heart strain findings are present",

            "heart_failure_pattern":
                "breathlessness, swelling, pleural effusion, pulmonary edema, or reduced heart function is present",

            "pleural_effusion_context":
                "pleural effusion, breathlessness, or respiratory fluid-related findings are present",

            "fatty_liver_liver_stress":
                "liver enzymes or fatty liver findings are present",

            "thyroid_imbalance":
                "thyroid markers suggest possible imbalance",

            "low_oxygen":
                "low oxygen saturation or breathlessness is present",

            "metabolic_syndrome_context":
                "diabetes, lipids, obesity, blood pressure, or fatty liver appear together"
        }

        item["retrieval_reason"] = reason_map.get(
            chunk_id,
            "semantic similarity and clinical context matched"
        )

        return item

    def diversify_results(self, results, flags, top_k):
        selected = []
        used_ids = set()
        used_concepts = set()

        required_ids = self.build_required_ids(flags)

        for required_id in required_ids:
            if len(selected) >= top_k:
                break

            for item in results:
                if item["id"] == required_id and item["id"] not in used_ids:
                    selected.append(item)
                    used_ids.add(item["id"])
                    used_concepts.add(self.get_concept_group(item["id"]))
                    break

        for item in results:
            if len(selected) >= top_k:
                break

            if item["id"] in used_ids:
                continue

            concept = self.get_concept_group(item["id"])

            if concept in used_concepts:
                continue

            selected.append(item)
            used_ids.add(item["id"])
            used_concepts.add(concept)

        return sorted(selected[:top_k], key=lambda x: x["score"], reverse=True)

    def retrieve(self, values, severity_results, report_sections, top_k=5, min_score=0.20):
        query = self.build_query(values, severity_results, report_sections)

        if not query.strip():
            return []

        flags = self.get_report_context_flags(values, report_sections)

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype("float32")

        search_k = min(max(top_k * 8, 25), len(self.knowledge_chunks))

        scores, indexes = self.index.search(query_embedding, search_k)

        results = []

        for raw_score, index in zip(scores[0], indexes[0]):
            if index == -1:
                continue

            chunk = self.knowledge_chunks[index]

            keyword_score = self.calculate_keyword_overlap_score(
                query,
                chunk["text"]
            )

            hybrid_score = (
                float(raw_score) * 0.70
                +
                keyword_score * 0.30
            )

            priority_boost = self.calculate_priority_boost(chunk, flags)
            final_score = hybrid_score + priority_boost

            if final_score < min_score:
                continue

            item = {
                "id": chunk["id"],
                "title": chunk["title"],
                "category": chunk["category"],
                "text": chunk["text"],
                "score": round(final_score, 3),
                "semantic_score": round(float(raw_score), 3),
                "keyword_score": round(keyword_score, 3),
                "hybrid_score": round(hybrid_score, 3),
                "priority_boost": round(priority_boost, 3),
                "concept_group": self.get_concept_group(chunk["id"])
            }

            item = self.add_retrieval_reason(item)
            results.append(item)

        results = sorted(
            results,
            key=lambda x: x["score"],
            reverse=True
        )

        adjusted_top_k = top_k

        if flags["simple_report"]:
            adjusted_top_k = 4
        elif flags["complex_multisystem"]:
            adjusted_top_k = 7
        elif flags["dominant_leg_infection"]:
            adjusted_top_k = 7
        elif flags["infection"]:
            adjusted_top_k = 5

        return self.diversify_results(
            results,
            flags,
            adjusted_top_k
        )


def format_faiss_context(retrieved_chunks):
    if not retrieved_chunks:
        return "No FAISS medical context retrieved."

    output = []

    for chunk in retrieved_chunks:
        output.append(
            f"- {chunk['title']} | "
            f"Score: {chunk['score']}\n\n"
            f"Category: {chunk['category']}\n\n"
            f"Concept group: {chunk.get('concept_group', 'N/A')}\n\n"
            f"Semantic score: {chunk.get('semantic_score', 'N/A')}\n\n"
            f"Keyword overlap: {chunk.get('keyword_score', 'N/A')}\n\n"
            f"Hybrid retrieval score: {chunk.get('hybrid_score', 'N/A')}\n\n"
            f"Clinical priority boost: {chunk.get('priority_boost', 'N/A')}\n\n"
            f"Retrieved because: {chunk.get('retrieval_reason', 'N/A')}\n\n"
            f"{chunk['text']}"
        )

    return "\n\n".join(output)