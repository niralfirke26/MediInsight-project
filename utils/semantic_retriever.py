import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from utils.medical_knowledge_base import get_medical_knowledge_chunks
from utils.embedding_model import get_embedding_model


class SemanticMedicalRetriever:
    def __init__(self):
        self.model = get_embedding_model()

        self.knowledge_chunks = get_medical_knowledge_chunks()

        self.chunk_texts = [
            chunk["text"]
            for chunk in self.knowledge_chunks
        ]

        self.chunk_embeddings = self.model.encode(
            self.chunk_texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

    def build_query_parts(
        self,
        values,
        severity_results,
        report_sections
    ):
        query_parts = []

        abnormal_values = []

        for parameter, status in severity_results.items():
            value = values.get(parameter, "Not Found")

            if value != "Not Found":
                abnormal_values.append(
                    f"{parameter} {value} {status}"
                )

        symptoms = " ".join(report_sections.get("symptoms", []))
        clinical_findings = " ".join(report_sections.get("clinical_findings", []))
        possible_conditions = " ".join(report_sections.get("possible_conditions", []))
        recommendations = " ".join(report_sections.get("recommendations", []))

        full_context = " ".join(
            abnormal_values +
            [
                symptoms,
                clinical_findings,
                possible_conditions,
                recommendations
            ]
        )

        query_parts.append(full_context)

        infection_context = " ".join(
            [
                symptoms,
                clinical_findings,
                possible_conditions,
                recommendations
            ]
        )

        if any(
            word in infection_context.lower()
            for word in [
                "fever",
                "infection",
                "cellulitis",
                "abscess",
                "pus",
                "bacteria",
                "antibiotics",
                "urinary tract infection",
                "surgical evaluation"
            ]
        ):
            query_parts.append(
                "urgent infection cellulitis abscess soft tissue infection "
                "fever chills swelling pain tenderness antibiotics surgical evaluation "
                "urinary tract infection inflammatory markers wound diabetic infection "
                + infection_context
            )

        diabetes_terms = " ".join(abnormal_values + [possible_conditions])

        if any(
            word in diabetes_terms.lower()
            for word in [
                "glucose",
                "hba1c",
                "diabetes",
                "diabetic"
            ]
        ):
            query_parts.append(
                "high glucose high hba1c uncontrolled diabetes poor sugar control "
                "diabetes complications infection wound healing kidney heart "
                + diabetes_terms
            )

        kidney_terms = " ".join(abnormal_values + [possible_conditions])

        if any(
            word in kidney_terms.lower()
            for word in [
                "creatinine",
                "urea",
                "egfr",
                "kidney",
                "renal",
                "chronic kidney disease"
            ]
        ):
            query_parts.append(
                "high creatinine blood urea low egfr chronic kidney disease kidney stress "
                + kidney_terms
            )

        heart_terms = " ".join(
            abnormal_values +
            [
                clinical_findings,
                possible_conditions
            ]
        )

        if any(
            word in heart_terms.lower()
            for word in [
                "cholesterol",
                "ldl",
                "hdl",
                "triglycerides",
                "ecg",
                "st-segment",
                "hypertrophy",
                "diastolic",
                "cardiac",
                "heart"
            ]
        ):
            query_parts.append(
                "high cholesterol high ldl low hdl triglycerides cardiac risk "
                "ecg left ventricular hypertrophy diastolic dysfunction heart strain "
                + heart_terms
            )

        liver_terms = " ".join(
            abnormal_values +
            [
                clinical_findings,
                possible_conditions
            ]
        )

        if any(
            word in liver_terms.lower()
            for word in [
                "alt",
                "ast",
                "bilirubin",
                "fatty",
                "liver",
                "nafld",
                "hepatomegaly"
            ]
        ):
            query_parts.append(
                "high alt ast bilirubin fatty liver nafld liver stress hepatomegaly "
                + liver_terms
            )

        return query_parts

    def calculate_priority_boost(self, chunk, report_sections):
        boost = 0.0

        report_text = " ".join(
            report_sections.get("symptoms", []) +
            report_sections.get("clinical_findings", []) +
            report_sections.get("possible_conditions", []) +
            report_sections.get("recommendations", [])
        ).lower()

        chunk_id = chunk["id"]
        category = chunk["category"]

        infection_present = any(
            word in report_text
            for word in [
                "fever",
                "infection",
                "cellulitis",
                "abscess",
                "pus",
                "bacteria",
                "antibiotics",
                "urinary tract infection",
                "surgical evaluation"
            ]
        )

        diabetes_present = any(
            word in report_text
            for word in [
                "diabetes",
                "diabetic",
                "glucose",
                "hba1c",
                "sugar"
            ]
        )

        kidney_present = any(
            word in report_text
            for word in [
                "kidney",
                "renal",
                "creatinine",
                "egfr",
                "chronic kidney disease"
            ]
        )

        cardiac_present = any(
            word in report_text
            for word in [
                "ecg",
                "heart",
                "cardiac",
                "hypertrophy",
                "diastolic",
                "cholesterol",
                "ldl",
                "hdl"
            ]
        )

        if infection_present and category == "infection":
            boost += 0.25

        if infection_present and chunk_id == "diabetes_infection_risk":
            boost += 0.18

        if diabetes_present and category == "diabetes":
            boost += 0.12

        if kidney_present and category == "kidney":
            boost += 0.10

        if cardiac_present and category == "cardiac":
            boost += 0.05

        return boost

    def retrieve(
        self,
        values,
        severity_results,
        report_sections,
        top_k=5,
        min_score=0.25
    ):
        query_parts = self.build_query_parts(
            values,
            severity_results,
            report_sections
        )

        if not query_parts:
            return []

        all_results = {}

        for query in query_parts:
            if not query.strip():
                continue

            query_embedding = self.model.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True
            )

            similarities = cosine_similarity(
                query_embedding,
                self.chunk_embeddings
            )[0]

            ranked_indexes = np.argsort(similarities)[::-1]

            for index in ranked_indexes[:4]:
                base_score = float(similarities[index])
                chunk = self.knowledge_chunks[index]

                priority_boost = self.calculate_priority_boost(
                    chunk,
                    report_sections
                )

                final_score = base_score + priority_boost

                if final_score < min_score:
                    continue

                chunk_id = chunk["id"]

                if (
                    chunk_id not in all_results or
                    final_score > all_results[chunk_id]["score"]
                ):
                    all_results[chunk_id] = {
                        "id": chunk["id"],
                        "title": chunk["title"],
                        "category": chunk["category"],
                        "text": chunk["text"],
                        "score": round(final_score, 3),
                        "base_score": round(base_score, 3),
                        "priority_boost": round(priority_boost, 3)
                    }

        ranked_results = sorted(
            all_results.values(),
            key=lambda item: item["score"],
            reverse=True
        )

        return ranked_results[:top_k]


def format_retrieved_context(retrieved_chunks):
    if not retrieved_chunks:
        return "No strong semantic medical context was retrieved."

    output = []

    for chunk in retrieved_chunks:
        output.append(
            f"- {chunk['title']} "
            f"(category: {chunk['category']}, score: {chunk['score']})\n"
            f"  {chunk['text']}"
        )

    return "\n".join(output)