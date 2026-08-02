import spacy

nlp = spacy.load(
    "en_core_sci_sm"
)


def extract_medical_entities(text):

    doc = nlp(text)

    entities=[]


    for ent in doc.ents:

        cleaned=(
            ent.text
            .strip()
        )


        if len(cleaned)<4:

            continue


        if cleaned.isupper():

            continue


        entities.append(
            cleaned
        )


    entities=list(
        set(
            entities
        )
    )


    return entities