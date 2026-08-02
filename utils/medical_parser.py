import re


def clean_parameter_name(name):
    name = name.strip()

    name = re.sub(
        r"^[•\-\*\d\.\)\s]+",
        "",
        name
    )

    name = re.sub(
        r"\s+",
        " ",
        name
    )

    return name.strip()


def is_non_medical_field(parameter):
    ignored_fields = [
        "age",
        "gender",
        "patient id",
        "date",
        "date of admission",
        "hospital name",
        "patient name",
        "admission date"
    ]

    parameter_lower = parameter.lower().strip()

    return parameter_lower in ignored_fields


def extract_medical_values(text):
    extracted = {}

    lines = text.split("\n")

    for line in lines:
        line = line.strip()

        if len(line) < 3:
            continue

        match = re.search(
            r"^([A-Za-z][A-Za-z0-9\s\-/\(\)%]+?)\s*[:\-]?\s+(\d+\.?\d*(?:/\d+\.?\d*)?)",
            line
        )

        if match:
            parameter = clean_parameter_name(
                match.group(1)
            )

            value = match.group(2)

            if is_non_medical_field(parameter):
                continue

            extracted[parameter] = value

    return extracted