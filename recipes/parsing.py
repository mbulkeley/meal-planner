import re


_LABELS = {
    "name": "name",
    "author": "author",
    "description": "description",
    "recipe yield": "recipe_yield",
    "prep time": "prep_time",
    "cook time": "cook_time",
    "total time": "total_time",
    "recipe category": "recipe_category",
}

_DURATION_FIELDS = ("prep_time", "cook_time", "total_time")


def _to_iso8601_duration(text):
    # Ignore trailing notes like "(including overnight cold proof)".
    text = text.split("(")[0].strip()
    hours = re.search(r"(\d+)\s*hour", text, re.IGNORECASE)
    minutes = re.search(r"(\d+)\s*minute", text, re.IGNORECASE)
    if not hours and not minutes:
        return text  # unrecognized — keep the original text rather than losing it
    duration = "PT"
    if hours:
        duration += f"{hours.group(1)}H"
    if minutes:
        duration += f"{minutes.group(1)}M"
    return duration


def parse_recipe_text(text):
    """Parse the labeled plain-text recipe format (Name:, Author:, ...,
    Ingredients:, Instructions:) into a dict of Recipe field values.
    Raises ValueError if no "Name:" line is found.
    """
    section = None
    section_lines = {"ingredients": [], "instructions": []}
    fields = {}

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        lower = stripped.lower()
        if lower.startswith("ingredients:"):
            section = "ingredients"
            continue
        if lower.startswith("instructions:"):
            section = "instructions"
            continue

        if section:
            section_lines[section].append(stripped)
            continue

        if ":" in stripped:
            label, _, value = stripped.partition(":")
            field_name = _LABELS.get(label.strip().lower())
            if field_name:
                fields[field_name] = value.strip()

    if "name" not in fields:
        raise ValueError('Couldn\'t find a "Name:" line in the pasted text.')

    for field_name in _DURATION_FIELDS:
        if field_name in fields:
            fields[field_name] = _to_iso8601_duration(fields[field_name])

    fields["ingredients"] = "\n".join(section_lines["ingredients"])
    fields["instructions"] = "\n".join(section_lines["instructions"])
    return fields
