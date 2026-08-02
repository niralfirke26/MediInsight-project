def generate_summary(report_text,values):

    summary="PATIENT FRIENDLY REPORT\n\n"

    medical_terms={

        "left ventricular hypertrophy":
        "heart muscle has become thicker",

        "hepatomegaly":
        "liver appears enlarged",

        "dyslipidemia":
        "abnormal cholesterol levels",

        "subclinical hypothyroidism":
        "thyroid may be underactive",

        "diastolic dysfunction":
        "heart relaxation may be weaker",

        "fatty infiltration":
        "fat accumulation inside organs",

        "polyuria":
        "frequent urination",

        "nocturia":
        "waking at night to urinate",

        "dyspnea":
        "difficulty breathing"

    }

    lower=report_text.lower()

    summary+="Medical terms explained:\n\n"

    found=False

    for term,meaning in medical_terms.items():

        if term in lower:

            found=True

            summary+=(
                f"• {term} → {meaning}\n"
            )

    if found==False:

        summary+="No difficult terms detected\n\n"


    summary+="\nHealth Findings:\n\n"


    for key,value in values.items():

        if value=="Not Found":

            continue

        v=float(value)

        if key=="Glucose":

            if v>125:

                summary+=(
                f"• Glucose {v}: Blood sugar is high.\n"
                "Possible diabetes risk.\n\n"
                )

        elif key=="HbA1c":

            if v>6.5:

                summary+=(
                f"• HbA1c {v}: Long-term sugar control is poor.\n\n"
                )

        elif key=="LDL":

            if v>160:

                summary+=(
                f"• LDL {v}: Bad cholesterol is high.\n\n"
                )

        elif key=="HDL":

            if v<40:

                summary+=(
                f"• HDL {v}: Good cholesterol is low.\n\n"
                )

        elif key=="Creatinine":

            if v>1.3:

                summary+=(
                f"• Creatinine {v}: Kidney function may be affected.\n\n"
                )

        elif key=="TSH":

            if v>4:

                summary+=(
                f"• TSH {v}: Thyroid imbalance detected.\n\n"
                )

        elif key=="ALT":

            if v>50:

                summary+=(
                f"• ALT {v}: Liver enzymes elevated.\n\n"
                )

        elif key=="AST":

            if v>50:

                summary+=(
                f"• AST {v}: Possible liver stress.\n\n"
                )

        elif key=="Hemoglobin":

            if v<12:

                summary+=(
                f"• Hemoglobin {v}: Possible anemia.\n\n"
                )


    summary+=(
    "Recommendations:\n"
    "- Consult physician\n"
    "- Follow prescribed treatment\n"
    "- Maintain healthy diet\n"
    "- Regular exercise\n"
    )

    return summary