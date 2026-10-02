# the values shown here decides how many usable rows you need to get a valid sesion. 
MIN_USABLE_ROWS = 3

# This defenition is used to get the average of a list for the summary
def average(values):
    """Return the arithmetic mean for a list of numbers."""
    return sum(values) / len(values)

# This def sees the session data and chooses what kind of workout it belongs to. 
def analyze_session(session):
    """Return a summary dictionary for one session."""
    observations = session.observations
    participant = session.participant

    result = {
        "session_id": session.session_id,
        "participant_id": participant.participant_id,
        "usable_rows": len(observations),
        "avg_heart_rate": "",
        "avg_skin_response": "",
        "avg_temperature": "",
        "avg_activity": "",
        "hr_above_baseline": "",
        "classification": "",
        "reasons": [],
    }
    if len(observations) < MIN_USABLE_ROWS:
        result["classification"] = "insufficient_data"
        result["reasons"].append(
            f"only {len(observations)} usable row(s); at least {MIN_USABLE_ROWS} are needed"
        )
        return result
    heart_rates = [obs.heart_rate for obs in observations]
    activities = [obs.activity_level for obs in observations]
    skin_values = [obs.skin_response for obs in observations]
    temps = [obs.temperature for obs in observations]

    avg_heart_rate = average(heart_rates)
    avg_activity = average(activities)
    avg_skin = average(skin_values)
    avg_temperature = average(temps)
    heart_rate_above_baseline = avg_heart_rate - participant.baseline_hr

    result["avg_heart_rate"] = round(avg_heart_rate, 1)
    result["avg_skin_response"] = round(avg_skin, 2)
    result["avg_temperature"] = round(avg_temperature, 2)
    result["avg_activity"] = round(avg_activity, 2)
    result["hr_above_baseline"] = round(heart_rate_above_baseline, 1)

    result["reasons"].append(
        f"Heart rate: {avg_heart_rate:.1f} bpm. Baseline: {participant.baseline_hr} bpm."
    )
    result["reasons"].append(
        f"Skin response: {avg_skin:.2f}. Baseline: {participant.baseline_skin}."
    )
    result["reasons"].append(
        f"Temperature: {avg_temperature:.2f}. Baseline: {participant.baseline_temp}."
    )
    result["reasons"].append(f"Activity level: {avg_activity:.2f}.")

    if avg_activity >= 0.68 or heart_rate_above_baseline >= 45:
        result["classification"] = "high_activity"
        result["reasons"].append("Activity was high or heart rate was much higher than baseline.")
    elif avg_activity >= 0.35 or heart_rate_above_baseline >= 20:
        result["classification"] = "moderate_activity"
        result["reasons"].append("Activity or heart rate was above the usual level.")
    elif heart_rate_above_baseline < 15:
        result["classification"] = "resting"
        result["reasons"].append("Activity was low and heart rate was close to baseline.")
    else:
        result["classification"] = "unusual"
        result["reasons"].append("Heart rate was high even though activity was low.")

    return result
