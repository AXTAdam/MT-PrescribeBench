MTBENCH_PROMPT = r'''You are a music therapy expert. Based on the given case, design an adjunctive music intervention prescription for the patient.

# General rules:
1. If a field cannot be defensibly determined, output "I don't know".
2. Output only the required JSON object with two top-level fields: "Answer" and "Reasoning". Do not output any extra information outside JSON.
3. For fixed-option fields, use the exact spelling, capitalization, and punctuation of the listed options.
4. For multi-label fields, separate labels using English semicolon plus one space: "; ". Multi-label output is allowed only for music_features.genre, prescription.intervention_type, prescription.setting, and prescription.combination_therapy_type.
5. The integrated_prescription must only restate information contained in the structured fields and case.
6. Use canonical concise formats for duration, frequency, and study_period whenever possible.
   - duration: use forms such as "15 min", "30 min", "20-30 min", "during procedure", or "10 min before procedure + during procedure".
   - frequency: use forms such as "1 session/day", "2 session/week", "1 session/month", or "1 session/procedure".
   - study_period: use forms such as "1 session", "4 weeks", "12 weeks", "during hospitalization", or "during treatment period".
   - For event-based clinical scenarios, use "procedure" instead of naming the event type. For example, write "1 session/procedure" instead of "1 session per chemotherapy session".

# Clinical classification rules:
1. Classify the overall intervention theme as follows:
   - Music Medicine: mainly protocol-based music listening; certified music therapist not required; can be delivered by general clinical staff or researchers.
   - Receptive Music Therapy: certified-music-therapist-led listening, guided relaxation, meditation, imagery, or another receptive therapeutic process.
   - Active Music Therapy: certified-music-therapist-led intervention in which the patient actively participates through singing, instrument playing, improvisation, movement, music training, breathing or music-based training, performance, or composition.
   - Active Music Therapy; Receptive Music Therapy: use only when both active participation and receptive/guided listening components are clearly present.
2. Keep prescription.intervention_theme, prescription.therapist_requirement, and prescription.patient_participation_mode logically consistent:
   - Music Medicine → Can be delivered by a general doctor or nurse → Passive listening
   - Receptive Music Therapy → Certified music therapist required → Passive listening / guided relaxation
   - Active Music Therapy → Certified music therapist required → Active participation
   - Active Music Therapy; Receptive Music Therapy → Certified music therapist required → Mixed participation
3. Use prescription.is_combination_therapy = "1" only when music is explicitly delivered as an adjunct to a named non-music therapy, procedure, treatment, or standard care component.


# Field definitions and options:

music_features.genre
- Meaning: Recommended music genre or style category. Select  best match the patient's condition, treatment goals, and expected outcomes. Unless "relaxing music" is necessary, please choose other genres instead.
[Options: classical | pop | folk/traditional/world | relaxation music | meditation music | nature sounds | new age | ambient/electronic | religious/spiritual | jazz | rock | country | opera | lullaby/children's music | film/soundtrack | r&b/blues/soul | marching/military music | rap/hip-hop | dance | ballad | chanson | enka | kayōkyoku]

music_features.bpm_or_tempo
- Meaning: Recommended music tempo expressed as numeric BPM.Do not provide the range, but the specific values instead. And try to list the possible values as well.Keep one decimal place.
[Options: one or more numeric BPM values]

music_features.selection_strategy
- Meaning: How the music is selected. Use patient-tailored selection when music is adapted to symptoms, condition, preference, mood, culture, age, or treatment context; use pre-selected/designed selection when the intervention is fixed, standardized, protocol-driven, or researcher-selected.
[Options: Tailored based on patient assessment | Pre-selected or Designed by researcher | Tailored based on patient assessment; Pre-selected or Designed by researcher]

prescription.intervention_theme
- Meaning: Overall therapeutic category of the entire intervention plan.
[Options: Music Medicine | Receptive Music Therapy | Active Music Therapy | Active Music Therapy; Receptive Music Therapy]

prescription.therapist_requirement
- Meaning: Whether the intervention requires a certified music therapist or can be delivered by general clinical staff. Keep consistent with prescription.intervention_theme.
[Options: Certified music therapist required | Can be delivered by a general doctor or nurse]

prescription.patient_participation_mode
- Meaning: What the patient does during the intervention. Keep consistent with prescription.intervention_theme.
[Options: Passive listening | Passive listening / guided relaxation | Active participation | Mixed participation]

prescription.intervention_type
- Meaning: Concrete music intervention method or methods actually used.
[Options: Listening to Music | Listening to Music(Live Performance) | Singing | Instrument Playing | Improvisation | Dancing/Movement | Music Training | Music Composition | Specialized Music Therapy Techniques | Multimodal Combination (Combining Various Forms of Music Therapy) | Other Methods]

prescription.duration
- Meaning: Length of each music intervention session. If the intervention is tied to a procedure, surgery, mechanical
  ventilation, labor, or another clinical operation, you may use event-anchored expressions such as "before procedure",
  "during procedure", "after procedure", or combinations such as "10 min before + during procedure".
[Options: concise evaluable duration string]

prescription.frequency
  - Meaning: How often the music intervention is delivered. Use concise canonical forms such as "1 session/day", "2 session/week", "1 session/month", or "1 session/procedure". For event-based clinical scenarios such as surgery, medical procedures, examinations, chemotherapy, radiotherapy, dialysis, labor, dressing change, wound care, or similar clinical events, use "session/procedure" rather than naming the event type.
[Options: concise evaluable frequency string]

prescription.study_period
- Meaning: Total period over which the music intervention is implemented, excluding follow-up-only periods. Examples include "4 weeks", "during hospitalization", "single session".
[Options: concise evaluable intervention-period string]

prescription.setting
- Meaning: Location or clinical setting where the music intervention is delivered. Use the most specific supported option. Use "hospital" for wards, bedside, ICU, operating room, treatment room, examination room, catheterization laboratory, endoscopy unit, radiotherapy room, chemotherapy unit, hemodialysis unit, and other in-hospital settings; "patient's home" for home-based care; "nursing home" for residential, aged-care, assisted-living, or long-term care facilities; "rehabilitation center" for rehabilitation facilities unless hospital-based; "outpatient_or_clinic" for outpatient or ambulatory clinic care; "community_or_daycare" for community centers, daycare, or adult day programs; "school_or_university" for school or university settings; "dental_office" for dental clinics or dental offices; use "indoor" or "outdoor" only when no more specific option fits.
[Options: hospital | patient's home | nursing home | rehabilitation center | outpatient_or_clinic | community_or_daycare | school_or_university | dental_office | indoor | outdoor]

prescription.is_combination_therapy
- Meaning: Whether the music intervention is explicitly combined with a named non-music therapy, procedure, treatment, or standard care component. Use "1" only when explicit; use "0" when the music intervention stands alone in the case framing.
[Options: 1 | 0]

prescription.combination_therapy_type
- Meaning: Type of non-music therapy, procedure, treatment, or care component combined with the music intervention. If prescription.is_combination_therapy is "0", output exactly "Null". If prescription.is_combination_therapy is "1", choose one or more options below. If the type cannot be determined, output "I don't know".
[Options: Rehabilitation Therapy | Medical Procedure | Surgery / Perioperative Care | Anticancer Treatment | Complementary Non-music Therapy | Pharmacotherapy | Supportive Treatment | Psychotherapy | Speech language therapy | Physiotherapy | Occupational therapy | Other motor therapies]

integrated_prescription
- Meaning: One concise natural-language sentence integrating the patient scenario, primary goal, secondary goal if provided, music features, and key prescription parameters. Do not add unsupported clinical details, institutions, article identifiers, evidence sources, or specific song titles.
[Options: concise natural-language sentence]

The "Answer" field must contain the prescription object to be scored.
The "Reasoning" field must explain the reasoning process used to select the music features and prescription fields, including the clinical context, treatment goal, intervention theme, dosage, setting, and combination-therapy judgment.

Output exactly in the following JSON format:
{
  "Answer": {
    "music_features": {
      "genre": "",
      "bpm_or_tempo": "",
      "selection_strategy": ""
    },
    "prescription": {
      "intervention_theme": "",
      "therapist_requirement": "",
      "patient_participation_mode": "",
      "intervention_type": "",
      "duration": "",
      "frequency": "",
      "study_period": "",
      "setting": "",
      "is_combination_therapy": "",
      "combination_therapy_type": ""
    },
    "integrated_prescription": ""
  },
  "Reasoning": ""
}

# Case:
{question}
'''
