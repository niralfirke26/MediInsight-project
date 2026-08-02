import re


try:
    from ctransformers import AutoModelForCausalLM

    llm = AutoModelForCausalLM.from_pretrained(
        "D:/AIModels",
        model_file="mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        model_type="mistral",
        gpu_layers=0,
        threads=4
    )

except Exception:
    llm = None


def get_float_value(values, key):
    value = values.get(key, "Not Found")

    if value == "Not Found":
        return None

    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def get_first_available_value(values, keys):
    for key in keys:
        value = get_float_value(values, key)

        if value is not None:
            return value

    return None


def is_noise_line(text):
    cleaned = text.strip().lower()
    cleaned = cleaned.replace(":", "")
    cleaned = re.sub(r"\(.*?\)", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

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
        "cardiology findings",
        "radiology notes",
        "radiology report",
        "physician impression",
        "recommendations",
        "chief complaints",
        "vital signs"
    }

    return cleaned in noise_headings


def clean_section_items(items):
    cleaned_items = []

    for item in items:
        if not item:
            continue

        if is_noise_line(item):
            continue

        cleaned_items.append(item)

    return cleaned_items


def retrieve_medical_context(
    values,
    severity_results,
    report_sections
):
    try:
        from utils.faiss_retriever import FAISSMedicalRetriever

        retriever = FAISSMedicalRetriever()

        return retriever.retrieve(
            values,
            severity_results,
            report_sections,
            top_k=5,
            min_score=0.20
        )

    except Exception:
        try:
            from utils.semantic_retriever import SemanticMedicalRetriever

            retriever = SemanticMedicalRetriever()

            return retriever.retrieve(
                values,
                severity_results,
                report_sections,
                top_k=5,
                min_score=0.20
            )

        except Exception:
            return []


def build_retrieved_context_text(retrieved_chunks):
    if not retrieved_chunks:
        return "No strong semantic medical context retrieved."

    context_lines = []

    for chunk in retrieved_chunks:
        context_lines.append(
            f"{chunk['title']}:\n{chunk['text']}"
        )

    return "\n\n".join(context_lines)


def build_patient_context_summary(retrieved_chunks):
    if not retrieved_chunks:
        return []

    patient_points = []

    for chunk in retrieved_chunks:
        title = chunk.get("title", "")

        if title == "Poorly controlled diabetes":
            patient_points.append(
                "Diabetes-related knowledge was retrieved because sugar markers are high. This supports explaining possible effects on kidneys, heart, nerves, blood vessels, and wound healing."
            )

        elif title == "Diabetes and infection risk":
            patient_points.append(
                "Diabetes-and-infection knowledge was retrieved because high sugar can make infections more serious and slow healing."
            )

        elif title == "Soft tissue infection and cellulitis":
            patient_points.append(
                "Soft-tissue infection knowledge was retrieved because the report mentions leg swelling, pain, cellulitis, abscess, fever, antibiotics, or infection-related findings."
            )

        elif title == "Urgent surgical infection context":
            patient_points.append(
                "Urgent infection knowledge was retrieved because the report mentions abscess formation, severe soft tissue infection, surgical evaluation, or hospital-level monitoring."
            )

        elif title == "Urinary tract infection":
            patient_points.append(
                "Urinary infection knowledge was retrieved because the report mentions burning urination, UTI, bacteria, pus cells, or urinary symptoms."
            )

        elif title == "Systemic inflammation markers":
            patient_points.append(
                "Inflammation-marker knowledge was retrieved because WBC, neutrophils, CRP, ESR, fever, swelling, or infection-related findings may suggest inflammation or infection."
            )

        elif title == "Kidney stress and chronic kidney disease":
            patient_points.append(
                "Kidney-related knowledge was retrieved because kidney markers or CKD-related findings suggest possible reduced filtering."
            )

        elif title == "Diabetes-related kidney risk":
            patient_points.append(
                "Diabetes-kidney knowledge was retrieved because high sugar and kidney markers appear together, which can increase concern for diabetic kidney stress."
            )

        elif title == "High blood pressure with kidney and heart risk":
            patient_points.append(
                "Blood-pressure risk knowledge was retrieved because high blood pressure can affect both the heart and kidneys, especially when diabetes or CKD is also present."
            )

        elif title == "Cholesterol and heart risk":
            patient_points.append(
                "Heart-risk knowledge was retrieved because cholesterol, LDL, HDL, or triglyceride values are abnormal."
            )

        elif title == "Heart strain and cardiac findings":
            patient_points.append(
                "Heart-strain knowledge was retrieved because ECG, echocardiography, blood pressure, or heart-related findings may need medical review."
            )

        elif title == "Possible heart failure pattern":
            patient_points.append(
                "Heart-failure-pattern knowledge was retrieved because breathlessness, swelling, pleural effusion, reduced ejection fraction, or congestive cardiac findings may suggest heart strain."
            )

        elif title == "Chest symptoms and cardiac context":
            patient_points.append(
                "Chest-symptom knowledge was retrieved because chest discomfort, ECG changes, or heart strain findings need careful medical review."
            )

        elif title == "Fatty liver and liver marker elevation":
            patient_points.append(
                "Liver-related knowledge was retrieved because liver enzymes, bilirubin, fatty liver, hepatomegaly, or NAFLD-related findings are present."
            )

        elif title == "Metabolic syndrome pattern":
            patient_points.append(
                "Metabolic-risk knowledge was retrieved because sugar, cholesterol, blood pressure, fatty liver, and kidney/cardiac risks may be connected."
            )

        elif title == "Possible hypothyroid pattern":
            patient_points.append(
                "Thyroid-related knowledge was retrieved because thyroid markers may suggest an underactive thyroid pattern."
            )

        elif title == "Thyroid and cholesterol relationship":
            patient_points.append(
                "Thyroid-cholesterol knowledge was retrieved because thyroid imbalance can sometimes contribute to fatigue, slow metabolism, and abnormal cholesterol."
            )

        elif title == "Low hemoglobin and anemia":
            patient_points.append(
                "Anemia-related knowledge was retrieved because low hemoglobin can explain tiredness, weakness, dizziness, or breathlessness."
            )

        elif title == "Anemia with oxygen and heart strain":
            patient_points.append(
                "Anemia-oxygen-heart knowledge was retrieved because low hemoglobin, breathlessness, low oxygen, or heart strain may reduce oxygen delivery to the body."
            )

        elif title == "Low oxygen saturation":
            patient_points.append(
                "Oxygen-related knowledge was retrieved because low oxygen saturation may require medical review, especially with breathlessness, anemia, infection, or heart strain."
            )

        elif title == "Pleural effusion context":
            patient_points.append(
                "Pleural-effusion knowledge was retrieved because fluid around the lungs can contribute to breathlessness and may relate to heart, kidney, liver, or infection issues."
            )

        elif title == "Diabetic foot care and wound risk":
            patient_points.append(
                "Diabetic foot-care knowledge was retrieved because diabetes with leg infection, swelling, wounds, or cellulitis can increase the risk of slow healing and complications."
            )

        elif title == "Follow-up and monitoring importance":
            patient_points.append(
                "Follow-up knowledge was retrieved because repeat tests, specialist visits, or monitoring help track whether the condition is improving or worsening."
            )

    return patient_points


def create_findings_text(values, severity_results, report_sections):
    findings = []

    for parameter, status in severity_results.items():
        value = values.get(parameter, "Not Found")

        if value != "Not Found":
            findings.append(f"{parameter}: {value} — {status}")

    for section_name in [
        "symptoms",
        "clinical_findings",
        "possible_conditions",
        "recommendations"
    ]:
        cleaned_items = clean_section_items(
            report_sections.get(section_name, [])
        )

        if cleaned_items:
            findings.append(
                f"{section_name}: " +
                "; ".join(cleaned_items[:5])
            )

    return "\n".join(findings)


def build_grouped_clinical_explanation(
    values,
    report_sections,
    retrieved_chunks
):
    grouped = []

    hemoglobin = get_float_value(values, "Hemoglobin")

    glucose = get_first_available_value(
        values,
        ["Glucose", "Fasting Glucose", "Postprandial Glucose"]
    )

    fasting_glucose = get_float_value(values, "Fasting Glucose")
    postprandial_glucose = get_float_value(values, "Postprandial Glucose")
    hba1c = get_float_value(values, "HbA1c")

    cholesterol = get_first_available_value(
        values,
        ["Cholesterol", "Total Cholesterol"]
    )

    ldl = get_first_available_value(
        values,
        ["LDL", "LDL Cholesterol"]
    )

    hdl = get_first_available_value(
        values,
        ["HDL", "HDL Cholesterol"]
    )

    triglycerides = get_float_value(values, "Triglycerides")
    creatinine = get_float_value(values, "Creatinine")
    alt = get_float_value(values, "ALT")
    ast = get_float_value(values, "AST")

    bilirubin = get_first_available_value(
        values,
        ["Bilirubin", "Bilirubin Total"]
    )

    tsh = get_float_value(values, "TSH")

    possible_conditions_text = " ".join(
        clean_section_items(report_sections.get("possible_conditions", []))
    ).lower()

    clinical_findings_text = " ".join(
        clean_section_items(report_sections.get("clinical_findings", []))
    ).lower()

    symptoms_text = " ".join(
        clean_section_items(report_sections.get("symptoms", []))
    ).lower()

    recommendations_text = " ".join(
        clean_section_items(report_sections.get("recommendations", []))
    ).lower()

    retrieved_titles = {
        chunk.get("title", "")
        for chunk in retrieved_chunks
    }

    has_diabetes = (
        (glucose and glucose >= 200) or
        (fasting_glucose and fasting_glucose >= 126) or
        (postprandial_glucose and postprandial_glucose >= 200) or
        (hba1c and hba1c >= 6.5) or
        "diabetes" in possible_conditions_text
    )

    has_infection = (
        "infection" in possible_conditions_text or
        "cellulitis" in possible_conditions_text or
        "abscess" in possible_conditions_text or
        "urinary tract infection" in possible_conditions_text or
        "fever" in symptoms_text or
        "antibiotics" in recommendations_text or
        "Diabetes and infection risk" in retrieved_titles or
        "Soft tissue infection and cellulitis" in retrieved_titles
    )

    has_kidney = (
        (creatinine and creatinine >= 1.5) or
        "kidney" in possible_conditions_text or
        "renal" in possible_conditions_text or
        "chronic kidney disease" in possible_conditions_text or
        "Diabetes-related kidney risk" in retrieved_titles
    )

    has_lipid = (
        (cholesterol and cholesterol >= 240) or
        (ldl and ldl >= 160) or
        (hdl and hdl < 40) or
        (triglycerides and triglycerides >= 200) or
        "dyslipidemia" in possible_conditions_text
    )

    has_liver = (
        (alt and alt > 50) or
        (ast and ast > 50) or
        (bilirubin and bilirubin > 1.2) or
        "fatty" in clinical_findings_text or
        "nafld" in possible_conditions_text
    )

    has_heart = (
        "st-segment" in clinical_findings_text or
        "left ventricular hypertrophy" in clinical_findings_text or
        "diastolic dysfunction" in clinical_findings_text or
        "cardiac" in possible_conditions_text or
        "heart" in possible_conditions_text or
        "Heart strain and cardiac findings" in retrieved_titles
    )

    has_thyroid = (
        (tsh and tsh > 5) or
        "hypothyroidism" in possible_conditions_text
    )

    has_anemia = (
        (hemoglobin and hemoglobin < 12) or
        "anemia" in possible_conditions_text
    )

    oxygen = get_float_value(values, "Oxygen Saturation")

    if has_diabetes and has_infection:
        grouped.append(
            {
                "title": "Sugar control and infection risk",
                "text": (
                    "The report shows very high sugar markers along with infection-related findings. "
                    "This combination is important because uncontrolled diabetes can make infections more serious, slow wound healing, and increase the need for close medical monitoring."
                )
            }
        )

    elif has_diabetes:
        if fasting_glucose and postprandial_glucose and hba1c:
            text = (
                "Fasting sugar, post-meal sugar, and HbA1c are all high. "
                "This suggests that sugar control has been poor recently and over the past few months."
            )
        else:
            text = (
                "Blood sugar markers are high, which suggests poor sugar control and needs medical attention."
            )

        grouped.append(
            {
                "title": "Blood sugar control",
                "text": text
            }
        )

    if "Urgent surgical infection context" in retrieved_titles:
        grouped.append(
            {
                "title": "Urgent infection review",
                "text": (
                    "The retrieved medical context suggests that abscess formation, severe soft tissue infection, surgical evaluation, or hospital observation may represent a higher-priority infection scenario."
                )
            }
        )

    if "Urinary tract infection" in retrieved_titles:
        grouped.append(
            {
                "title": "Urinary infection context",
                "text": (
                    "Burning urination or urinary infection findings may suggest a urinary tract infection, which needs careful review especially when diabetes or kidney disease is also present."
                )
            }
        )

    if has_lipid and has_heart:
        grouped.append(
            {
                "title": "Heart and cholesterol risk",
                "text": (
                    "Cholesterol-related values are abnormal and the report also contains heart-related findings. "
                    "Together, these suggest increased cardiovascular risk and possible strain on the heart."
                )
            }
        )

    elif has_lipid:
        grouped.append(
            {
                "title": "Cholesterol and blood vessel risk",
                "text": (
                    "High cholesterol, high LDL, high triglycerides, or low HDL can increase the risk of blood vessel blockage, heart disease, and stroke over time."
                )
            }
        )

    elif has_heart:
        grouped.append(
            {
                "title": "Heart-related findings",
                "text": (
                    "The ECG or echocardiography findings suggest that the heart may be under strain and should be reviewed by a doctor."
                )
            }
        )

    if "Possible heart failure pattern" in retrieved_titles:
        grouped.append(
            {
                "title": "Possible heart failure pattern",
                "text": (
                    "Breathlessness, swelling, pleural effusion, reduced ejection fraction, or congestive cardiac findings can point toward increased strain on the heart."
                )
            }
        )

    if has_kidney and has_diabetes:
        grouped.append(
            {
                "title": "Kidney stress linked with diabetes",
                "text": (
                    "Kidney markers are abnormal, and diabetes is also present. Diabetes and high blood pressure are common reasons for kidney stress, so kidney follow-up is important."
                )
            }
        )

    elif has_kidney:
        grouped.append(
            {
                "title": "Kidney function",
                "text": (
                    "Kidney markers suggest the kidneys may not be filtering waste as well as expected."
                )
            }
        )

    if has_liver and has_diabetes:
        grouped.append(
            {
                "title": "Liver stress and metabolic risk",
                "text": (
                    "Liver markers or fatty liver findings are present. These can be linked with diabetes, high triglycerides, fatty liver disease, and lifestyle-related metabolic risk."
                )
            }
        )

    elif has_liver:
        grouped.append(
            {
                "title": "Liver-related findings",
                "text": (
                    "Raised liver markers or fatty liver findings suggest liver stress that should be followed up medically."
                )
            }
        )

    if has_thyroid:
        grouped.append(
            {
                "title": "Thyroid pattern",
                "text": (
                    "TSH is high or hypothyroidism is mentioned. This can suggest an underactive thyroid pattern, which may contribute to fatigue, slow metabolism, and cholesterol changes."
                )
            }
        )

    if has_anemia:
        grouped.append(
            {
                "title": "Low hemoglobin / anemia",
                "text": (
                    "Hemoglobin is low or anemia is mentioned. This may explain tiredness, weakness, dizziness, or breathlessness."
                )
            }
        )

    if oxygen and oxygen < 94:
        grouped.append(
            {
                "title": "Oxygen level",
                "text": (
                    "Oxygen saturation is low. This may be important when breathlessness, infection, anemia, or heart strain is also present."
                )
            }
        )

    return grouped


def clean_ai_output(text):
    text = text.strip()

    text = re.sub(
        r"\b(\w{1,8})(\s+\1\b){2,}",
        "",
        text
    )

    last_period = text.rfind(".")

    if last_period != -1:
        text = text[:last_period + 1]

    return text.strip()


def fast_patient_summary(values, severity_results, report_sections):
    summary = "Your report shows several important health findings:\n\n"

    if severity_results:
        summary += "Important abnormal values:\n"

        for parameter, status in severity_results.items():
            value = values.get(parameter, "Not Found")

            if value != "Not Found":
                summary += f"- {parameter}: {value} ({status})\n"

    retrieved_chunks = retrieve_medical_context(
        values,
        severity_results,
        report_sections
    )

    grouped_explanations = build_grouped_clinical_explanation(
        values,
        report_sections,
        retrieved_chunks
    )

    if grouped_explanations:
        summary += "\nWhat this may mean in simple terms:\n"

        for item in grouped_explanations:
            summary += f"- {item['title']}: {item['text']}\n"

    patient_context_points = build_patient_context_summary(
        retrieved_chunks
    )

    if patient_context_points:
        summary += "\nRelevant medical context used by the system:\n"

        for point in patient_context_points[:5]:
            summary += f"- {point}\n"

    summary += (
        "\nPlease consult a qualified doctor for proper diagnosis and treatment. "
        "This explanation is for understanding only and is not a diagnosis."
    )

    return summary


def mistral_summary(values, severity_results, report_sections):
    if llm is None:
        return fast_patient_summary(
            values,
            severity_results,
            report_sections
        )

    findings_text = create_findings_text(
        values,
        severity_results,
        report_sections
    )

    retrieved_chunks = retrieve_medical_context(
        values,
        severity_results,
        report_sections
    )

    grouped_explanations = build_grouped_clinical_explanation(
        values,
        report_sections,
        retrieved_chunks
    )

    grouped_text = "\n".join(
        f"- {item['title']}: {item['text']}"
        for item in grouped_explanations
    )

    retrieved_context = build_retrieved_context_text(
        retrieved_chunks
    )

    prompt = f"""
[INST]
You are MedExplain, an advanced medical report simplification assistant.

Use ONLY the structured findings, grouped reasoning, and retrieved context below.
Do not invent new diseases.
Do not diagnose.
Explain in simple patient-friendly English.
Use short bullet points.
Connect related findings when medically reasonable.
Mention that the explanation is not a replacement for a doctor.

Structured Report Findings:
{findings_text}

Grouped Clinical Reasoning:
{grouped_text}

Retrieved Medical Knowledge:
{retrieved_context}

Generate the patient-friendly explanation:
[/INST]
"""

    response = llm(
        prompt,
        max_new_tokens=500,
        temperature=0.05,
        repetition_penalty=1.2,
        top_p=0.8,
        stop=["</s>", "[/INST]"]
    )

    return clean_ai_output(response)


def simplify_medical_text(
    values,
    severity_results,
    report_sections,
    use_mistral=False
):
    if use_mistral:
        return mistral_summary(
            values,
            severity_results,
            report_sections
        )

    return fast_patient_summary(
        values,
        severity_results,
        report_sections
    )