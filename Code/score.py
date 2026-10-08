"""Scoring utilities for benchmark output evaluation."""

import json
import math
import re

import pandas as pd

FIELD_SPECS = [
    {
        "name": "Genre",
        "path": ("music_features", "genre"),
        "gold_col": "Gold_Genre",
        "metric": "multilabel_f1",
        "allowed": {
            "classical",
            "pop",
            "folk/traditional/world",
            "relaxation music",
            "meditation music",
            "nature sounds",
            "new age",
            "ambient/electronic",
            "religious/spiritual",
            "jazz",
            "rock",
            "country",
            "opera",
            "lullaby/children's music",
            "film/soundtrack",
            "r&b/blues/soul",
            "marching/military music",
            "rap/hip-hop",
            "dance",
            "ballad",
            "chanson",
            "enka",
            "kayōkyoku",
        },
    },
    {
        "name": "BPM/Tempo",
        "path": ("music_features", "bpm_or_tempo"),
        "gold_col": "Gold_BPM",
        "metric": "bpm_mae",
    },
    {
        "name": "Selection Strategy",
        "path": ("music_features", "selection_strategy"),
        "gold_col": "Gold_Music_Selection_Strategy",
        "metric": "accuracy",
        "allowed": {
            "Tailored based on patient assessment",
            "Pre-selected or Designed by researcher",
            "Tailored based on patient assessment; Pre-selected or Designed by researcher",
        },
    },
    {
        "name": "Intervention Theme",
        "path": ("prescription", "intervention_theme"),
        "gold_col": "Gold_Intervention_Theme",
        "metric": "accuracy",
        "allowed": {
            "Music Medicine",
            "Receptive Music Therapy",
            "Active Music Therapy",
            "Active Music Therapy; Receptive Music Therapy",
        },
    },
    {
        "name": "Therapist Requirement",
        "path": ("prescription", "therapist_requirement"),
        "gold_col": "Gold_Therapist_Requirement",
        "metric": "accuracy",
        "allowed": {
            "Certified music therapist required",
            "Can be delivered by a general doctor or nurse",
        },
    },
    {
        "name": "Patient Participation Mode",
        "path": ("prescription", "patient_participation_mode"),
        "gold_col": "Gold_Patient_Participation_Mode",
        "metric": "accuracy",
        "allowed": {
            "Passive listening",
            "Passive listening / guided relaxation",
            "Active participation",
            "Mixed participation",
        },
    },
    {
        "name": "Intervention Type",
        "path": ("prescription", "intervention_type"),
        "gold_col": "Gold_Intervention_Type",
        "metric": "multilabel_f1",
        "allowed": {
            "Listening to Music",
            "Listening to Music(Live Performance)",
            "Singing",
            "Instrument Playing",
            "Improvisation",
            "Dancing/Movement",
            "Music Training",
            "Music Composition",
            "Specialized Music Therapy Techniques",
            "Multimodal Combination (Combining Various Forms of Music Therapy)",
            "Other Methods",
        },
    },
    {
        "name": "Duration",
        "path": ("prescription", "duration"),
        "gold_col": "Gold_Duration",
        "metric": "duration_f1",
    },
    {
        "name": "Frequency",
        "path": ("prescription", "frequency"),
        "gold_col": "Gold_Frequency",
        "metric": "frequency_f1",
    },
    {
        "name": "Study Period",
        "path": ("prescription", "study_period"),
        "gold_col": "Gold_Study_Period",
        "metric": "study_period_f1",
    },
    {
        "name": "Setting",
        "path": ("prescription", "setting"),
        "gold_col": "Gold_Setting",
        "metric": "multilabel_f1",
        "allowed": {
            "hospital",
            "patient's home",
            "nursing home",
            "rehabilitation center",
            "outpatient_or_clinic",
            "community_or_daycare",
            "school_or_university",
            "dental_office",
            "indoor",
            "outdoor",
        },
    },
    {
        "name": "Is Combination Therapy",
        "path": ("prescription", "is_combination_therapy"),
        "gold_col": "Gold_Is_Combination_Therapy",
        "metric": "accuracy",
        "allowed": {"0", "1"},
    },
    {
        "name": "Combination Therapy Type",
        "path": ("prescription", "combination_therapy_type"),
        "gold_col": "Gold_Combination_Therapy_Type",
        "metric": "combination_type_f1",
        "allowed": {
            "Rehabilitation Therapy",
            "Medical Procedure",
            "Surgery / Perioperative Care",
            "Anticancer Treatment",
            "Complementary Non-music Therapy",
            "Pharmacotherapy",
            "Supportive Treatment",
            "Psychotherapy",
            "Speech language therapy",
            "Physiotherapy",
            "Occupational therapy",
            "Other motor therapies",
        },
    },
]


def clean_value(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def result_json(model_value, gold_value, score, reason):
    payload = {
        "model_value": clean_value(model_value),
        "gold_value": clean_value(gold_value),
        "score": round(float(score), 4) if isinstance(score, (int, float)) and math.isfinite(score) else score,
        "error_reason": reason,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def has_model_output(value):
    text = clean_value(value)
    return text not in {"", "Null", "None", "nan"}


def parse_json(text):
    try:
        return json.loads(text), ""
    except Exception as exc:
        return None, f"Model output cannot be parsed as JSON: {exc}"


def nested_get(obj, path):
    cur = obj
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return ""
        cur = cur[key]
    return clean_value(cur)


def split_semicolon(value):
    text = clean_value(value)
    if text in {"", "I don't know", "Null"}:
        return []
    return [part.strip() for part in text.split("; ") if part.strip()]


def f1_from_sets(gold_set, pred_set):
    if not gold_set and not pred_set:
        return 1.0
    if not gold_set or not pred_set:
        return 0.0
    inter = gold_set & pred_set
    if not inter:
        return 0.0
    precision = len(inter) / len(pred_set)
    recall = len(inter) / len(gold_set)
    return 2 * precision * recall / (precision + recall)


def score_accuracy(gold, pred, allowed=None):
    notes = []
    if pred == "I don't know" and gold != "I don't know":
        return 0.0, "Model output is I don't know and does not match the gold value"
    if allowed and pred and pred != "I don't know" and pred not in allowed:
        notes.append(f"Model value is not in the fixed vocabulary: {pred}")
    if clean_value(gold) == clean_value(pred):
        return 1.0, "Exact match" if not notes else "Exact match; " + "; ".join(notes)
    reason = "Mismatch: model value differs from gold value"
    if notes:
        reason += "; " + "; ".join(notes)
    return 0.0, reason


def score_multilabel_f1(gold, pred, allowed):
    gold_items = split_semicolon(gold)
    pred_items = split_semicolon(pred)
    invalid_pred = [item for item in pred_items if item not in allowed]
    invalid_gold = [item for item in gold_items if item not in allowed]
    gold_set = {item for item in gold_items if item in allowed}
    pred_set = {item for item in pred_items if item in allowed}
    score = f1_from_sets(gold_set, pred_set)

    if score == 1.0 and not invalid_pred:
        return score, "Exact match"

    missing = sorted(gold_set - pred_set)
    extra = sorted(pred_set - gold_set)
    reasons = []
    if invalid_pred:
        reasons.append(f"Model output contains labels outside the fixed vocabulary: {invalid_pred}")
    if invalid_gold:
        reasons.append(f"Gold contains labels outside the fixed vocabulary and they were excluded from scoring: {invalid_gold}")
    if missing:
        reasons.append(f"Missing gold labels: {missing}")
    if extra:
        reasons.append(f"Extra model labels: {extra}")
    if not reasons:
        reasons.append("Model labels and gold labels have no overlap")
    return score, "; ".join(reasons)


MULTIMODAL_LABEL = "Multimodal Combination (Combining Various Forms of Music Therapy)"
MULTIMODAL_COMPONENT_LABELS = {
    "Listening to Music",
    "Listening to Music(Live Performance)",
    "Singing",
    "Instrument Playing",
    "Improvisation",
    "Dancing/Movement",
    "Music Training",
    "Music Composition",
    "Specialized Music Therapy Techniques",
}


def score_intervention_type(gold, pred, allowed):
    gold_items = split_semicolon(gold)
    pred_items = split_semicolon(pred)
    invalid_pred = [item for item in pred_items if item not in allowed]
    invalid_gold = [item for item in gold_items if item not in allowed]
    gold_set = {item for item in gold_items if item in allowed}
    pred_set = {item for item in pred_items if item in allowed}

    derived_pred_set = set(pred_set)
    derived_notes = []
    if MULTIMODAL_LABEL in gold_set:
        concrete_pred = pred_set & MULTIMODAL_COMPONENT_LABELS
        if len(concrete_pred) >= 2:
            derived_pred_set -= concrete_pred - gold_set
            derived_pred_set.add(MULTIMODAL_LABEL)
            derived_notes.append(
                "Concrete intervention labels were treated as Multimodal Combination for scoring"
            )

    score = f1_from_sets(gold_set, derived_pred_set)
    if score == 1.0 and not invalid_pred:
        reason = "Exact match"
        if derived_notes:
            reason = "; ".join(derived_notes)
        return score, reason

    missing = sorted(gold_set - derived_pred_set)
    extra = sorted(derived_pred_set - gold_set)
    reasons = []
    reasons.extend(derived_notes)
    if invalid_pred:
        reasons.append(f"Model output contains labels outside the fixed vocabulary: {invalid_pred}")
    if invalid_gold:
        reasons.append(f"Gold contains labels outside the fixed vocabulary and they were excluded from scoring: {invalid_gold}")
    if missing:
        reasons.append(f"Missing gold labels: {missing}")
    if extra:
        reasons.append(f"Extra model labels: {extra}")
    if not reasons:
        reasons.append("Model labels and gold labels have no overlap")
    return score, "; ".join(reasons)


def extract_numbers(value):
    text = clean_value(value)
    if text in {"", "I don't know", "Null"}:
        return []
    return [float(x) for x in re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", text)]


def nearest_mae(source, target):
    return sum(min(abs(x - y) for y in target) for x in source) / len(source)


def score_bpm(gold, pred):
    gold_nums = extract_numbers(gold)
    pred_nums = extract_numbers(pred)
    if not pred_nums:
        return 60.0, "No parseable BPM in model output; 60 BPM penalty applied"
    if not gold_nums:
        return 60.0, "No parseable BPM in gold value; 60 BPM penalty applied"
    p2g = nearest_mae(pred_nums, gold_nums)
    g2p = nearest_mae(gold_nums, pred_nums)
    raw_score = (p2g + g2p) / 2
    score = min(raw_score, 60.0)
    if score == 0:
        return score, "Exact match"
    if raw_score > score:
        return score, f"BPM symmetric MAE is {raw_score:.2f}; capped at 60.00"
    return score, f"BPM symmetric MAE is {score:.2f}"


def normalize_common(text):
    text = clean_value(text).lower()
    text = text.replace("minutes", "min").replace("minute", "min")
    text = text.replace("hours", "hour").replace("hrs", "hour").replace("hr", "hour")
    text = re.sub(r"\bsessions\b", "session", text)
    text = re.sub(r"\bdays\b", "day", text)
    text = re.sub(r"\bweeks\b", "week", text)
    text = re.sub(r"\bmonths\b", "month", text)
    text = re.sub(r"\btimes\b", "time", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_alternative_branches(value):
    text = clean_value(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"\s+\bor\b\s+", text, flags=re.IGNORECASE) if part.strip()]


def split_simple_semicolon_branches(value, unit_pattern):
    text = clean_value(value)
    if ";" not in text:
        return []
    parts = [part.strip() for part in text.split(";") if part.strip()]
    if len(parts) < 2:
        return []
    if all(re.fullmatch(unit_pattern, normalize_common(part)) for part in parts):
        return parts
    return []


def score_best_gold_branch(gold, pred, score_func, branch_label):
    branches = split_alternative_branches(gold)
    if len(branches) < 2:
        return None
    scored = [(score_func(branch, pred), branch) for branch in branches]
    (best_score, best_reason), best_branch = max(scored, key=lambda item: item[0][0])
    if best_score == 1.0:
        return best_score, f"Matched acceptable {branch_label} alternative: {best_branch}"
    return best_score, f"Best {branch_label} alternative was {best_branch}; {best_reason}"


def normalize_procedure_aliases(text):
    procedure_events = [
        "procedure",
        "surgery",
        "operation",
        "labor",
        "chemotherapy infusion",
        "chemotherapy session",
        "mechanical ventilation",
        "ventilation",
        "hemodialysis session",
        "hemodialysis",
        "examination",
        "exam",
    ]
    for phase in ["before", "during", "after"]:
        for event in procedure_events:
            text = re.sub(rf"\b{phase}\s+{re.escape(event)}\b", f"{phase} procedure", text)
    return text


def parse_duration_components(value):
    text = normalize_common(value)
    if text in {"", "i don't know", "null"}:
        return set()
    if text == "random":
        return {"random"}

    components = set()
    text = normalize_procedure_aliases(text)
    has_procedure_context = "procedure" in text
    segments = re.split(r"\s*(?:\+|;|,|\bor\b)\s*", text)
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        phase = None
        for candidate in ["before procedure", "during procedure", "after procedure"]:
            if candidate in segment:
                phase = candidate.replace(" ", "_")
        if phase is None and has_procedure_context:
            for short_phase in ["before", "during", "after"]:
                if re.search(rf"^\s*(?:\d+(?:\.\d+)?\s*(?:min|hour|h)\s+)?{short_phase}\s*$", segment):
                    phase = f"{short_phase}_procedure"
                    break

        break_match = re.search(
            r"(\d+(?:\.\d+)?)\s*-?\s*(min|hour|h)\s+break every\s+(\d+(?:\.\d+)?)\s*(min|hour|h)\b",
            segment,
        )
        if break_match:
            break_num, break_unit, every_num, every_unit = break_match.groups()
            break_minutes = float(break_num) * 60 if break_unit in {"hour", "h"} else float(break_num)
            every_minutes = float(every_num) * 60 if every_unit in {"hour", "h"} else float(every_num)
            components.add(("break_rule", round(break_minutes, 2), round(every_minutes, 2)))
            segment = (segment[: break_match.start()] + " " + segment[break_match.end() :]).strip()

        at_least_match = re.search(r"at least\s*(\d+(?:\.\d+)?)\s*(min|hour|h)\b", segment)
        if at_least_match:
            num, unit = at_least_match.groups()
            minutes = float(num) * 60 if unit in {"hour", "h"} else float(num)
            components.add(("at_least_minutes", round(minutes, 2)))
            segment = (segment[: at_least_match.start()] + " " + segment[at_least_match.end() :]).strip()

        range_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(min|hour|h)\b", segment)
        if range_match:
            low, high, unit = range_match.groups()
            factor = 60 if unit in {"hour", "h"} else 1
            components.add(("range_minutes", round(float(low) * factor, 2), round(float(high) * factor, 2)))
            segment = (segment[: range_match.start()] + " " + segment[range_match.end() :]).strip()

        numeric_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(min|hour|h)\b", segment)
        if phase and not numeric_matches and not break_match:
            components.add(phase)
        for num, unit in numeric_matches:
            minutes = float(num) * 60 if unit in {"hour", "h"} else float(num)
            if phase:
                components.add(("minutes_phase", round(minutes, 2), phase))
            else:
                components.add(("minutes", round(minutes, 2)))
    return components


def component_match_quality(gold_component, pred_component, tolerance=5):
    if gold_component == pred_component:
        return 3
    if isinstance(gold_component, tuple) and isinstance(pred_component, tuple):
        if gold_component[0] == pred_component[0] == "minutes":
            return 2 if abs(gold_component[1] - pred_component[1]) <= tolerance else -1
        if gold_component[0] == pred_component[0] == "minutes_phase":
            return 2 if gold_component[2] == pred_component[2] and abs(gold_component[1] - pred_component[1]) <= tolerance else -1
        if gold_component[0] == "range_minutes" and pred_component[0] == "minutes":
            return 2 if gold_component[1] <= pred_component[1] <= gold_component[2] else -1
        if gold_component[0] == "minutes" and pred_component[0] == "range_minutes":
            pred_midpoint = (pred_component[1] + pred_component[2]) / 2
            return 2 if abs(gold_component[1] - pred_midpoint) <= tolerance else -1
        if gold_component[0] == "at_least_minutes" and pred_component[0] in {"minutes", "minutes_phase"}:
            return 2 if pred_component[1] >= gold_component[1] else -1
        if gold_component[0] == pred_component[0] == "at_least_minutes":
            return 2 if pred_component[1] >= gold_component[1] else -1
    return -1


def component_match(gold_component, pred_component, tolerance=5):
    return component_match_quality(gold_component, pred_component, tolerance=tolerance) >= 0


def f1_with_component_matching(gold_components, pred_components, tolerance=5):
    if not gold_components and not pred_components:
        return 1.0, set(), set()
    matched_gold = set()
    matched_pred = set()
    candidates = []
    for pred_component in pred_components:
        for gold_component in gold_components:
            quality = component_match_quality(gold_component, pred_component, tolerance=tolerance)
            if quality >= 0:
                candidates.append((quality, str(gold_component) == str(pred_component), gold_component, pred_component))
    for _, _, gold_component, pred_component in sorted(candidates, reverse=True, key=lambda item: (item[0], item[1])):
        if gold_component in matched_gold or pred_component in matched_pred:
            continue
        matched_gold.add(gold_component)
        matched_pred.add(pred_component)
    if not pred_components or not gold_components:
        return 0.0, matched_gold, matched_pred
    precision = len(matched_pred) / len(pred_components)
    recall = len(matched_gold) / len(gold_components)
    score = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return score, matched_gold, matched_pred


def score_duration_core(gold, pred):
    if normalize_common(gold) == "random":
        return 1.0, "Gold duration is random; treated as free-arrangement duration"
    gold_components = parse_duration_components(gold)
    pred_components = parse_duration_components(pred)
    score, matched_gold, matched_pred = f1_with_component_matching(gold_components, pred_components, tolerance=5)
    if score == 1.0:
        if normalize_common(gold) != normalize_common(pred):
            has_numeric_match = any(isinstance(component, tuple) and component[0] in {"minutes", "minutes_phase", "range_minutes", "at_least_minutes"} for component in matched_gold | matched_pred)
            if has_numeric_match:
                return score, "Numeric match within duration tolerance"
            return score, "Component match after duration normalization"
        return score, "Exact match"
    return score, component_reason(gold_components, pred_components, matched_gold, matched_pred)


def score_duration(gold, pred):
    branch_result = score_best_gold_branch(gold, pred, score_duration_core, "duration")
    if branch_result is not None:
        return branch_result
    simple_minute_branches = split_simple_semicolon_branches(gold, r"\d+(?:\.\d+)?\s*min")
    if simple_minute_branches:
        scored = [(score_duration_core(branch, pred), branch) for branch in simple_minute_branches]
        (best_score, best_reason), best_branch = max(
            scored,
            key=lambda item: (
                item[0][0],
                normalize_common(item[1]) == normalize_common(pred),
            ),
        )
        if best_score == 1.0:
            return best_score, f"Matched acceptable duration representative point: {best_branch}"
        return best_score, f"Best duration representative point was {best_branch}; {best_reason}"
    return score_duration_core(gold, pred)


def normalize_frequency_text(value):
    text = normalize_common(value)
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*times?\s+per\s+(day|week|month)\b", r"\1 session/\2", text)
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*sessions?\s+per\s+(day|week|month)\b", r"\1 session/\2", text)
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s*times?\s*/\s*(day|week|month)\b", r"\1 session/\2", text)
    text = re.sub(
        r"\b(\d+(?:\.\d+)?)\s*session\s+(?:before|during|after)\s+(exam|examination)\b",
        r"\1 session/procedure",
        text,
    )
    replacements = {
        "once daily": "1 session/day",
        "twice daily": "2 session/day",
        "daily": "1 session/day",
        "1 time/day": "1 session/day",
        "2 time/day": "2 session/day",
        "1 session/chemotherapy infusion": "1 session/procedure",
        "1 session/chemotherapy session": "1 session/procedure",
        "1 session/labor": "1 session/procedure",
        "time": "session",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def parse_frequency_components(value):
    text = normalize_frequency_text(value)
    if text in {"", "i don't know", "null"}:
        return set()
    components = set()
    if "random" in text:
        components.add("random")
    segments = re.split(r"\s*(?:\+|;|,|\bor\b)\s*", text)
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        range_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*session\s*/\s*(day|week|procedure)", segment)
        if range_match:
            low, high, period = range_match.groups()
            components.add(("range", float(low), float(high), period))
            continue
        match = re.search(r"(\d+(?:\.\d+)?)\s*session\s*/\s*(\d+\s*)?(day|week|procedure)", segment)
        if match:
            count, denom, period = match.groups()
            denom_num = float(denom.strip()) if denom and denom.strip() else 1.0
            components.add(("frequency", float(count), denom_num, period))
    return components


def frequency_component_match(gold_component, pred_component):
    if gold_component == pred_component:
        return True
    if isinstance(gold_component, tuple) and isinstance(pred_component, tuple):
        if gold_component[0] == "range" and pred_component[0] == "frequency":
            _, low, high, period = gold_component
            _, count, denom, pred_period = pred_component
            return period == pred_period and denom == 1.0 and low <= count <= high
    return False


def f1_frequency_components(gold_components, pred_components):
    if not gold_components and not pred_components:
        return 1.0, set(), set()
    matched_gold = set()
    matched_pred = set()
    candidates = []
    for pred_component in pred_components:
        for gold_component in gold_components:
            if frequency_component_match(gold_component, pred_component):
                quality = 3 if gold_component == pred_component else 2
                candidates.append((quality, gold_component, pred_component))
    for _, gold_component, pred_component in sorted(candidates, reverse=True, key=lambda item: item[0]):
        if gold_component in matched_gold or pred_component in matched_pred:
            continue
        matched_gold.add(gold_component)
        matched_pred.add(pred_component)
    if not gold_components or not pred_components:
        return 0.0, matched_gold, matched_pred
    precision = len(matched_pred) / len(pred_components)
    recall = len(matched_gold) / len(gold_components)
    score = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return score, matched_gold, matched_pred


def score_frequency_core(gold, pred):
    gold_components = parse_frequency_components(gold)
    pred_components = parse_frequency_components(pred)
    score, matched_gold, matched_pred = f1_frequency_components(gold_components, pred_components)
    if score == 1.0:
        return score, "Exact match"
    return score, component_reason(gold_components, pred_components, matched_gold, matched_pred)


def score_frequency(gold, pred):
    branch_result = score_best_gold_branch(gold, pred, score_frequency_core, "frequency")
    if branch_result is not None:
        return branch_result
    return score_frequency_core(gold, pred)


def parse_study_period_components(value):
    text = normalize_common(value)
    if text in {"", "i don't know", "null"}:
        return set()
    text = text.replace("single session", "1 session")
    components = set()
    if "during hospitalization" in text:
        components.add(("event", "during_hospitalization"))
    if "during operation" in text or "during procedure" in text:
        components.add(("event", "during_procedure"))
    up_to = re.search(r"up to\s*(\d+(?:\.\d+)?)\s*(day|week|month)", text)
    if up_to:
        num, unit = up_to.groups()
        components.add(("upper_day", convert_to_days(float(num), unit)))
    scan_text = re.sub(r"up to\s*\d+(?:\.\d+)?\s*(day|week|month)", " ", text)
    scan_text = re.sub(r"\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*session", " ", scan_text)
    for num, unit in re.findall(r"(\d+(?:\.\d+)?)\s*(session|day|week|month)\b", scan_text):
        num = float(num)
        if unit == "session":
            components.add(("session", num))
        else:
            components.add(("day", convert_to_days(num, unit)))
    range_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*session", text)
    if range_match:
        low, high = range_match.groups()
        components.add(("session_range", float(low), float(high)))
    return components


def convert_to_days(num, unit):
    if unit == "day":
        return num
    if unit == "week":
        return num * 7
    if unit == "month":
        return num * 30
    return num


def study_component_match(gold_component, pred_component):
    if gold_component == pred_component:
        return True
    if isinstance(gold_component, tuple) and isinstance(pred_component, tuple):
        if gold_component[0] == pred_component[0] == "day":
            return abs(gold_component[1] - pred_component[1]) <= 2
        if gold_component[0] == pred_component[0] == "session":
            return gold_component[1] == pred_component[1]
        if gold_component[0] == "session_range" and pred_component[0] == "session":
            return gold_component[1] <= pred_component[1] <= gold_component[2]
        if gold_component[0] == "session_range" and pred_component[0] == "session_range":
            return gold_component[1] <= pred_component[1] and pred_component[2] <= gold_component[2]
        if gold_component[0] == "upper_day" and pred_component[0] == "day":
            return pred_component[1] <= gold_component[1] + 2
        if gold_component[0] == "upper_day" and pred_component[0] == "upper_day":
            return pred_component[1] <= gold_component[1] + 2
    return False


def score_study_period_core(gold, pred):
    gold_text = normalize_common(gold)
    pred_text = normalize_common(pred)
    gold_components = parse_study_period_components(gold)
    pred_components = parse_study_period_components(pred)
    if gold_text and pred_text and gold_text == pred_text:
        return 1.0, "Exact match"
    if not gold_components and not pred_components and (gold_text or pred_text):
        return 0.0, "Unable to parse gold and model values into study-period components"
    if not gold_components and not pred_components:
        return 1.0, "Exact match"
    matched_gold = set()
    matched_pred = set()
    for pred_component in pred_components:
        for gold_component in gold_components:
            if gold_component in matched_gold:
                continue
            if study_component_match(gold_component, pred_component):
                matched_gold.add(gold_component)
                matched_pred.add(pred_component)
                break
    if not gold_components or not pred_components:
        return 0.0, component_reason(gold_components, pred_components, matched_gold, matched_pred)
    precision = len(matched_pred) / len(pred_components)
    recall = len(matched_gold) / len(gold_components)
    score = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    if score == 1.0:
        return score, "Exact match"
    return score, component_reason(gold_components, pred_components, matched_gold, matched_pred)


def score_study_period(gold, pred):
    branch_result = score_best_gold_branch(gold, pred, score_study_period_core, "study-period")
    if branch_result is not None:
        return branch_result
    simple_study_branches = split_simple_semicolon_branches(
        gold, r"\d+(?:\.\d+)?\s*(session|day|week|month)"
    )
    if simple_study_branches:
        scored = [(score_study_period_core(branch, pred), branch) for branch in simple_study_branches]
        (best_score, best_reason), best_branch = max(scored, key=lambda item: item[0][0])
        if best_score == 1.0:
            return best_score, f"Matched acceptable study-period alternative: {best_branch}"
        return best_score, f"Best study-period alternative was {best_branch}; {best_reason}"
    return score_study_period_core(gold, pred)


def component_reason(gold_components, pred_components, matched_gold, matched_pred):
    missing = sorted((gold_components - matched_gold), key=str)
    extra = sorted((pred_components - matched_pred), key=str)
    reasons = []
    if missing:
        reasons.append(f"Missing gold components: {[format_component(x) for x in missing]}")
    if extra:
        reasons.append(f"Extra model components: {[format_component(x) for x in extra]}")
    if not reasons:
        reasons.append("Model components and gold components have no overlap")
    return "; ".join(reasons)


def format_component(component):
    if not isinstance(component, tuple):
        return str(component).replace("_", " ")
    kind = component[0]
    if kind == "minutes":
        return f"{format_number(component[1])} min"
    if kind == "minutes_phase":
        return f"{format_number(component[1])} min {str(component[2]).replace('_', ' ')}"
    if kind == "range_minutes":
        return f"{format_number(component[1])}-{format_number(component[2])} min"
    if kind == "at_least_minutes":
        return f"at least {format_number(component[1])} min"
    if kind == "break_rule":
        return f"{format_number(component[1])} min break every {format_number(component[2])} min"
    if kind == "frequency":
        count = format_number(component[1])
        denom = format_number(component[2])
        period = component[3]
        unit = pluralize_label("session", component[1])
        if denom == "1":
            return f"{count} {unit}/{period}"
        period_unit = pluralize_label(period, component[2])
        return f"{count} {unit}/{denom} {period_unit}"
    if kind == "range":
        return f"{format_number(component[1])}-{format_number(component[2])} sessions/{component[3]}"
    if kind == "session":
        return f"{format_number(component[1])} {pluralize_label('session', component[1])}"
    if kind == "session_range":
        return f"{format_number(component[1])}-{format_number(component[2])} sessions"
    if kind == "day":
        return f"{format_number(component[1])} days"
    if kind == "upper_day":
        return f"up to {format_number(component[1])} days"
    if kind == "event":
        return str(component[1]).replace("_", " ")
    return str(component)


def format_number(value):
    try:
        value = float(value)
    except Exception:
        return str(value)
    if value.is_integer():
        return str(int(value))
    return str(value)


def pluralize_label(label, value):
    try:
        value = float(value)
    except Exception:
        value = 2
    if value == 1:
        return label
    if label == "procedure":
        return label
    return label + "s"


COMBINATION_TYPE_NORMALIZATION = {
    "chemotherapy": "Anticancer Treatment",
    "radiotherapy": "Anticancer Treatment",
    "stem cell transplantation": "Anticancer Treatment",
    "physiotherapy": "Rehabilitation Therapy",
    "occupational therapy": "Rehabilitation Therapy",
    "gait training": "Rehabilitation Therapy",
    "pulmonary rehabilitation": "Rehabilitation Therapy",
    "other motor therapies": "Rehabilitation Therapy",
    "hemodialysis": "Medical Procedure",
    "bronchoscopy": "Medical Procedure",
    "colonoscopy": "Medical Procedure",
    "cardiac catheterization": "Medical Procedure",
    "lumbar puncture": "Medical Procedure",
    "counseling": "Supportive Treatment",
    "education": "Supportive Treatment",
    "supportive care": "Supportive Treatment",
    "aromatherapy": "Complementary Non-music Therapy",
    "progressive muscle relaxation": "Complementary Non-music Therapy",
    "surgery": "Surgery / Perioperative Care",
    "preoperative": "Surgery / Perioperative Care",
    "intraoperative": "Surgery / Perioperative Care",
    "postoperative care": "Surgery / Perioperative Care",
    "midazolam": "Pharmacotherapy",
    "analgesia": "Pharmacotherapy",
    "sedatives": "Pharmacotherapy",
    "drug co-treatment": "Pharmacotherapy",
}


def normalize_combination_type_item(item):
    text = clean_value(item)
    if not text:
        return "", ""
    normalized = COMBINATION_TYPE_NORMALIZATION.get(text.lower())
    if normalized:
        return normalized, f"{text} was normalized to {normalized}"
    return text, ""


def normalize_combination_type_items(items):
    normalized_items = []
    notes = []
    for item in items:
        normalized, note = normalize_combination_type_item(item)
        if normalized:
            normalized_items.append(normalized)
        if note:
            notes.append(note)
    return normalized_items, notes


def score_combination_type_labels(gold, pred, allowed):
    gold_items = split_semicolon(gold)
    pred_items = split_semicolon(pred)
    normalized_gold_items, gold_notes = normalize_combination_type_items(gold_items)
    normalized_pred_items, pred_notes = normalize_combination_type_items(pred_items)
    invalid_pred = [item for item in normalized_pred_items if item not in allowed]
    invalid_gold = [item for item in normalized_gold_items if item not in allowed]
    gold_set = {item for item in normalized_gold_items if item in allowed}
    pred_set = {item for item in normalized_pred_items if item in allowed}
    score = f1_from_sets(gold_set, pred_set)

    reasons = []
    reasons.extend(sorted(set(gold_notes)))
    reasons.extend(sorted(set(pred_notes)))
    if invalid_pred:
        reasons.append(f"Model output contains labels outside the fixed vocabulary: {invalid_pred}")
    if invalid_gold:
        reasons.append(f"Gold contains labels outside the fixed vocabulary and they were excluded from scoring: {invalid_gold}")
    missing = sorted(gold_set - pred_set)
    extra = sorted(pred_set - gold_set)
    if missing:
        reasons.append(f"Missing gold labels: {missing}")
    if extra:
        reasons.append(f"Extra model labels: {extra}")
    if score == 1.0 and not invalid_pred and not invalid_gold:
        return score, "; ".join(reasons) if reasons else "Exact match"
    if not reasons:
        reasons.append("Model labels and gold labels have no overlap")
    return score, "; ".join(reasons)


def score_combination_type(gold_type, pred_type, gold_flag, pred_flag, allowed):
    gold_flag = clean_value(gold_flag)
    pred_flag = clean_value(pred_flag)
    if gold_flag == "0" and pred_flag == "0":
        if clean_value(pred_type) == "Null":
            return 1.0, "Exact match"
        return 0.0, "Gold is not combination therapy, so model combination therapy type should be Null"
    if gold_flag != pred_flag:
        return 0.0, "Combination-therapy flag does not match, so combination therapy type score is 0"
    if gold_flag == "1" and pred_flag == "1":
        return score_combination_type_labels(gold_type, pred_type, allowed)
    return 0.0, "Combination-therapy field cannot be evaluated by the defined rule"


def score_field(spec, gold_row, model_obj):
    gold_value = clean_value(gold_row[spec["gold_col"]])
    pred_value = nested_get(model_obj, spec["path"])
    metric = spec["metric"]
    if metric == "accuracy":
        score, reason = score_accuracy(gold_value, pred_value, spec.get("allowed"))
    elif metric == "multilabel_f1":
        if spec["name"] == "Intervention Type":
            score, reason = score_intervention_type(gold_value, pred_value, spec["allowed"])
        else:
            score, reason = score_multilabel_f1(gold_value, pred_value, spec["allowed"])
    elif metric == "bpm_mae":
        score, reason = score_bpm(gold_value, pred_value)
    elif metric == "duration_f1":
        score, reason = score_duration(gold_value, pred_value)
    elif metric == "frequency_f1":
        score, reason = score_frequency(gold_value, pred_value)
    elif metric == "study_period_f1":
        score, reason = score_study_period(gold_value, pred_value)
    elif metric == "combination_type_f1":
        pred_flag = nested_get(model_obj, ("prescription", "is_combination_therapy"))
        gold_flag = clean_value(gold_row["Gold_Is_Combination_Therapy"])
        score, reason = score_combination_type(gold_value, pred_value, gold_flag, pred_flag, spec["allowed"])
    else:
        raise ValueError(f"Unknown metric: {metric}")
    return result_json(pred_value, gold_value, score, reason)


def failed_field_json(spec, gold_row, reason):
    gold_value = clean_value(gold_row[spec["gold_col"]])
    score = 60.0 if spec["metric"] == "bpm_mae" else 0.0
    return result_json("", gold_value, score, reason)


def extract_score(cell):
    payload = json.loads(clean_value(cell))
    return payload["score"]
