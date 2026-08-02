def normalize_name(name):

    return name.lower().strip()


def check_severity(values):

    results = {}

    for parameter, raw_value in values.items():

        try:
            value = float(
                str(raw_value).split("/")[0]
            )

        except:
            continue

        name = normalize_name(parameter)

        interpretation = None


        # Blood Pressure
        if "blood pressure" in name:

            if value >= 140:
                interpretation = "High"

            elif value >= 120:
                interpretation = "Borderline"

            else:
                interpretation = "Normal"


        # Oxygen Saturation
        elif (
            "oxygen" in name
            or "spo2" in name
        ):

            if value < 95:
                interpretation = "Low"

            else:
                interpretation = "Normal"


        # Hemoglobin
        elif (
            "hemoglobin" in name
            or name == "hb"
        ):

            if value < 12:
                interpretation = "Low"

            else:
                interpretation = "Normal"


        # Glucose
        elif "glucose" in name:

            if value >= 200:
                interpretation = "Very High"

            elif value >= 126:
                interpretation = "High"

            elif value >= 100:
                interpretation = "Borderline"

            else:
                interpretation = "Normal"


        # HbA1c
        elif (
            "hba1c" in name
            or "a1c" in name
        ):

            if value >= 6.5:
                interpretation = "Very High"

            elif value >= 5.7:
                interpretation = "Borderline"

            else:
                interpretation = "Normal"


        # Total Cholesterol
        elif (
            "total cholesterol" in name
            or (
                "cholesterol" in name
                and "hdl" not in name
                and "ldl" not in name
            )
        ):

            if value >= 240:
                interpretation = "Very High"

            elif value >= 200:
                interpretation = "Borderline"

            else:
                interpretation = "Normal"


        # LDL
        elif "ldl" in name:

            if value >= 190:
                interpretation = "Very High"

            elif value >= 130:
                interpretation = "High"

            else:
                interpretation = "Normal"


        # HDL
        elif "hdl" in name:

            if value < 40:
                interpretation = "Low"

            else:
                interpretation = "Good"


        # Triglycerides
        elif "triglyceride" in name:

            if value >= 200:
                interpretation = "Very High"

            elif value >= 150:
                interpretation = "High"

            else:
                interpretation = "Normal"


        # VLDL
        elif "vldl" in name:

            if value > 40:
                interpretation = "High"

            else:
                interpretation = "Normal"


        # Creatinine
        elif "creatinine" in name:

            if value > 1.3:
                interpretation = "High"

            else:
                interpretation = "Normal"


        # Liver
        elif (
            "alt" in name
            or "ast" in name
        ):

            if value > 50:
                interpretation = "High"

            else:
                interpretation = "Normal"


        # Bilirubin
        elif "bilirubin" in name:

            if value > 1.2:
                interpretation = "High"

            else:
                interpretation = "Normal"


        # Thyroid
        elif "tsh" in name:

            if value > 4.5:
                interpretation = "High"

            else:
                interpretation = "Normal"


        if interpretation:

            results[parameter] = interpretation

    return results