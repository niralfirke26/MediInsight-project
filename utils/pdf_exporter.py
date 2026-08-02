from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors


def clean_text(value):
    if value is None:
        return ""

    text = str(value).strip()

    cleaned = ""

    for char in text:
        if ord(char) < 128:
            cleaned += char

    cleaned = " ".join(cleaned.split())

    noise_tokens = [
        "____",
        "----",
        "━━━━",
        "────",
        "■■",
        "■",
        "• •",
    ]

    for token in noise_tokens:
        cleaned = cleaned.replace(token, "")

    return cleaned.strip()


def is_noise_text(text):
    text = clean_text(text)

    if not text:
        return True

    if len(text) < 4:
        return True

    if set(text) <= set("■-_—–=. "):
        return True

    return False


def build_pdf_buffer():
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45,
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="MedTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=26,
            textColor=colors.HexColor("#1E3A8A"),
            spaceAfter=16,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=14,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyTextCustom",
            parent=styles["BodyText"],
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=7,
        )
    )

    return buffer, doc, styles


def add_paragraph(story, text, styles):
    text = clean_text(text)

    if is_noise_text(text):
        return

    safe_text = text.replace("\n", "<br/>")

    story.append(Paragraph(safe_text, styles["BodyTextCustom"]))
    story.append(Spacer(1, 6))


def add_section(story, title, styles):
    title = clean_text(title)

    if not title:
        return

    story.append(Paragraph(title, styles["SectionTitle"]))


def add_bullet_list(story, items, styles, empty_text="No major items detected."):
    cleaned_items = []
    seen = set()

    for item in items or []:
        text = clean_text(item)

        if is_noise_text(text):
            continue

        normalized = text.lower()

        if normalized in seen:
            continue

        seen.add(normalized)
        cleaned_items.append(text)

    if not cleaned_items:
        add_paragraph(story, empty_text, styles)
        return

    for item in cleaned_items:
        add_paragraph(story, f"• {item}", styles)


def add_values_table(story, extracted_values, severity_results, styles):
    rows = [["Medical Value", "Result", "Status"]]

    for parameter, value in extracted_values.items():
        if value in ["Not Found", None, ""]:
            continue

        status = severity_results.get(parameter, "Normal")

        rows.append(
            [
                clean_text(parameter),
                clean_text(value),
                clean_text(status),
            ]
        )

    if len(rows) == 1:
        add_paragraph(story, "No medical values were detected.", styles)
        return

    table = Table(rows, colWidths=[2.1 * inch, 1.4 * inch, 2.0 * inch])

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DBEAFE")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(table)
    story.append(Spacer(1, 12))


def generate_medical_summary_pdf(
    summary,
    extracted_values,
    severity_results,
    report_sections,
    retrieved_context,
):
    buffer, doc, styles = build_pdf_buffer()

    story = []

    story.append(Paragraph("MedExplain Medical Summary", styles["MedTitle"]))

    generated_on = datetime.now().strftime("%d %B %Y, %I:%M %p")

    add_paragraph(story, f"Generated on: {generated_on}", styles)

    add_section(story, "Simplified Explanation", styles)
    add_paragraph(story, summary, styles)

    add_section(story, "Important Medical Values", styles)
    add_values_table(story, extracted_values, severity_results, styles)

    add_section(story, "Clinical Findings", styles)
    add_bullet_list(
        story,
        report_sections.get("clinical_findings", []),
        styles,
    )

    add_section(story, "Possible Conditions", styles)
    add_bullet_list(
        story,
        report_sections.get("possible_conditions", []),
        styles,
    )

    add_section(story, "Symptoms Mentioned", styles)
    add_bullet_list(
        story,
        report_sections.get("symptoms", []),
        styles,
    )

    add_section(story, "Recommendations", styles)
    add_bullet_list(
        story,
        report_sections.get("recommendations", []),
        styles,
    )

    add_section(story, "Retrieved Medical Context", styles)

    retrieved_items = []

    for chunk in retrieved_context or []:
        title = clean_text(chunk.get("title", "Medical Context"))
        text = clean_text(chunk.get("text", ""))

        if is_noise_text(title) and is_noise_text(text):
            continue

        if text:
            retrieved_items.append(f"{title}: {text}")
        elif title:
            retrieved_items.append(title)

    add_bullet_list(
        story,
        retrieved_items,
        styles,
        empty_text="No retrieved medical context available.",
    )

    add_section(story, "Important Disclaimer", styles)

    add_paragraph(
        story,
        "This AI-generated medical summary is intended only for educational "
        "and understanding purposes. It is not a diagnosis, prescription, "
        "or replacement for qualified medical advice.",
        styles,
    )

    doc.build(story)

    buffer.seek(0)

    return buffer