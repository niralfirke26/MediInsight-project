import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from utils.embedding_model import get_embedding_model


class MedicalChatbot:
    def __init__(self):
        self.model = get_embedding_model()

        self.safety_note = (
            "This is an educational explanation of the uploaded report. "
            "It is not a diagnosis, prescription, or replacement for a doctor."
        )

        self.intent_keywords = {
            "kidney": [
                "kidney", "renal", "creatinine", "egfr", "urea", "bun",
                "proteinuria", "microalbuminuria", "urine", "nephrology",
                "acute-on-chronic kidney disease", "ckd", "cardiorenal"
            ],

            "heart": [
                "heart", "cardiac", "cardiology", "ecg", "echo",
                "ejection fraction", "ventricular", "lvh", "st-segment",
                "heart failure", "congestive", "pulmonary edema",
                "pleural effusion", "nt-probnp", "hypertension",
                "blood pressure"
            ],

            "infection": [
                "infection", "fever", "wbc", "crp", "esr", "pus",
                "bacteria", "nitrites", "cellulitis", "abscess",
                "antibiotics", "sepsis", "uti", "urinary tract"
            ],

            "diabetes": [
                "diabetes", "sugar", "glucose", "hba1c",
                "fasting", "postprandial", "insulin"
            ],

            "liver": [
                "liver", "alt", "ast", "bilirubin",
                "fatty liver", "nafld", "hepatomegaly"
            ],
        }

    def clean_text(self, text):
        if text is None:
            return ""

        text = str(text).strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def normalize_text(self, text):
        text = self.clean_text(text).lower()
        text = re.sub(r"[^a-z0-9\s\-]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def detect_intents(self, question):
        normalized_question = self.normalize_text(question)

        intent_scores = {}

        for intent, keywords in self.intent_keywords.items():
            score = 0

            for keyword in keywords:
                keyword = self.normalize_text(keyword)

                if keyword and keyword in normalized_question:
                    score += 1

            if score > 0:
                intent_scores[intent] = score

        if not intent_scores:
            return ["general"]

        sorted_intents = sorted(
            intent_scores.items(),
            key=lambda item: item[1],
            reverse=True
        )

        dominant_intent = sorted_intents[0][0]

        return [dominant_intent]

    def build_context_blocks(
        self,
        values,
        severity_results,
        report_sections,
        retrieved_chunks
    ):
        blocks = []

        for parameter, status in severity_results.items():
            value = values.get(parameter, "Not Found")

            if value == "Not Found":
                continue

            status_text = str(status).lower()

            if status_text not in ["normal", "not found"]:
                blocks.append({
                    "source": "abnormal value",
                    "title": parameter,
                    "text": f"{parameter}: {value} ({status})"
                })

        section_map = {
            "clinical_findings": "clinical finding",
            "possible_conditions": "possible condition",
            "symptoms": "symptom",
            "recommendations": "recommendation"
        }

        for section_name, source_name in section_map.items():
            items = report_sections.get(section_name, [])

            for item in items:
                if isinstance(item, dict):
                    text = item.get("text", "")
                else:
                    text = item

                text = self.clean_text(text)

                if len(text) < 3:
                    continue

                if re.fullmatch(r"[\W_]+", text):
                    continue

                blocks.append({
                    "source": source_name,
                    "title": source_name.title(),
                    "text": text
                })

        for chunk in retrieved_chunks or []:
            title = self.clean_text(chunk.get("title", "Medical Context"))
            text = self.clean_text(chunk.get("text", ""))

            combined = text if text else title

            if len(combined) < 5:
                continue

            blocks.append({
                "source": "retrieved medical knowledge",
                "title": title,
                "text": combined
            })

        unique_blocks = []
        seen = set()

        for block in blocks:
            normalized = self.normalize_text(block["text"])

            if normalized in seen:
                continue

            seen.add(normalized)
            unique_blocks.append(block)

        return unique_blocks

    def embed_texts(self, texts):
        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

    def keyword_score(self, text, keywords):
        normalized_text = self.normalize_text(text)

        score = 0.0

        for keyword in keywords:
            normalized_keyword = self.normalize_text(keyword)

            if normalized_keyword in normalized_text:
                score += 0.18

        return min(score, 1.2)

    def intent_score(self, block, detected_intents):
        block_text = (
            f"{block.get('title', '')} "
            f"{block.get('source', '')} "
            f"{block.get('text', '')}"
        )

        score = 0.0

        for intent in detected_intents:
            keywords = self.intent_keywords.get(intent, [])
            score += self.keyword_score(block_text, keywords)

        return score

    def source_priority_score(self, block, detected_intents):
        text = self.normalize_text(block.get("text", ""))

        score = 0.0

        if "kidney" in detected_intents:
            kidney_terms = [
                "creatinine",
                "egfr",
                "renal",
                "kidney",
                "proteinuria",
                "nephrology"
            ]

            if any(term in text for term in kidney_terms):
                score += 0.45

        if "heart" in detected_intents:
            heart_terms = [
                "heart",
                "cardiac",
                "ecg",
                "echo",
                "ejection",
                "ventricular",
                "pulmonary edema"
            ]

            if any(term in text for term in heart_terms):
                score += 0.45

        if "infection" in detected_intents:
            infection_terms = [
                "infection",
                "cellulitis",
                "abscess",
                "wbc",
                "crp",
                "fever"
            ]

            if any(term in text for term in infection_terms):
                score += 0.45

        return score

    def retrieve_relevant_blocks(
        self,
        question,
        context_blocks,
        top_k=10
    ):
        if not context_blocks:
            return []

        detected_intents = self.detect_intents(question)

        block_texts = [
            f"{block['source']} {block['title']} {block['text']}"
            for block in context_blocks
        ]

        question_embedding = self.embed_texts([question])

        block_embeddings = self.embed_texts(block_texts)

        similarities = cosine_similarity(
            question_embedding,
            block_embeddings
        )[0]

        scored_blocks = []

        for index, block in enumerate(context_blocks):
            semantic_score = float(similarities[index])

            intent_bonus = self.intent_score(
                block,
                detected_intents
            )

            source_bonus = self.source_priority_score(
                block,
                detected_intents
            )

            final_score = (
                semantic_score +
                intent_bonus +
                source_bonus
            )

            block_copy = block.copy()

            block_copy["score"] = final_score
            block_copy["embedding"] = block_embeddings[index]

            scored_blocks.append(block_copy)

        scored_blocks = sorted(
            scored_blocks,
            key=lambda x: x["score"],
            reverse=True
        )

        return scored_blocks[:top_k]

    def cluster_blocks(self, blocks, threshold=0.55):
        clusters = []

        for block in blocks:
            embedding = block["embedding"]

            placed = False

            for cluster in clusters:
                similarity = cosine_similarity(
                    [embedding],
                    [cluster["centroid"]]
                )[0][0]

                if similarity >= threshold:
                    cluster["blocks"].append(block)

                    embeddings = [
                        b["embedding"]
                        for b in cluster["blocks"]
                    ]

                    cluster["centroid"] = np.mean(
                        embeddings,
                        axis=0
                    )

                    placed = True
                    break

            if not placed:
                clusters.append({
                    "centroid": embedding,
                    "blocks": [block]
                })

        return clusters

    def build_intro(self, intents):
        if "heart" in intents:
            return "The heart-related findings in this report are:"

        if "kidney" in intents:
            return "The kidney-related findings in this report are:"

        if "infection" in intents:
            return "The infection-related findings in this report are:"

        if "diabetes" in intents:
            return "The diabetes-related findings in this report are:"

        if "liver" in intents:
            return "The liver-related findings in this report are:"

        return "The main report-based findings are:"

    def build_closing(self, intents):
        if "heart" in intents:
            return (
                "In simple terms, the report shows signs of heart strain "
                "including fluid overload, cardiac dysfunction, and "
                "blood pressure-related stress."
            )

        if "kidney" in intents:
            return (
                "In simple terms, the kidneys appear to be under stress. "
                "High sugar, blood pressure, and reduced filtration "
                "can worsen kidney function."
            )

        if "infection" in intents:
            return (
                "In simple terms, the report suggests infection or "
                "inflammation that may require close medical monitoring."
            )

        return (
            "In simple terms, these findings should be interpreted together."
        )

    def answer_from_blocks(self, question, blocks):
        if not blocks:
            return (
                "I could not find enough relevant information "
                "to answer that question.\n\n"
                + self.safety_note
            )

        intents = self.detect_intents(question)

        clusters = self.cluster_blocks(blocks)

        response = self.build_intro(intents)
        response += "\n\n"

        cluster_index = 1

        for cluster in clusters[:5]:
            cluster_blocks = sorted(
                cluster["blocks"],
                key=lambda x: x["score"],
                reverse=True
            )

            top_block = cluster_blocks[0]

            title = self.clean_text(top_block["title"])

            if title.lower() in [
                "clinical finding",
                "possible condition",
                "recommendation",
                "symptom",
                "abnormal value"
            ]:
                title = self.clean_text(top_block["text"])

            response += f"{cluster_index}. {title}\n"
            response += "Evidence from the report:\n"

            seen = set()

            for block in cluster_blocks[:4]:
                evidence = self.clean_text(block["text"])

                normalized = self.normalize_text(evidence)

                if normalized in seen:
                    continue

                seen.add(normalized)

                if len(evidence) > 180:
                    evidence = (
                        evidence[:180]
                        .rsplit(" ", 1)[0] + "..."
                    )

                response += f"- {evidence}\n"

            response += "\n"

            cluster_index += 1

        response += self.build_closing(intents)
        response += "\n\n"
        response += self.safety_note

        return response

    def answer_question(
        self,
        question,
        values,
        severity_results,
        report_sections,
        retrieved_chunks
    ):
        question = self.clean_text(question)

        context_blocks = self.build_context_blocks(
            values,
            severity_results,
            report_sections,
            retrieved_chunks
        )

        relevant_blocks = self.retrieve_relevant_blocks(
            question,
            context_blocks
        )

        return self.answer_from_blocks(
            question,
            relevant_blocks
        )


def answer_medical_question(
    question,
    values,
    severity_results,
    report_sections,
    retrieved_chunks
):
    chatbot = MedicalChatbot()

    return chatbot.answer_question(
        question,
        values,
        severity_results,
        report_sections,
        retrieved_chunks
    )