# Imports all the necessary python modules and from the csv files
import csv
from pathlib import Path
from .exceptions import DataFileError, InvalidIdentifierError, InvalidRecordError
from .models import Observation, Participant, Session
from .validators import (
    PARTICIPANT_ID_PATTERN,
    SESSION_ID_PATTERN,
    check_identifier,
    check_range,
    is_valid_identifier,
    to_number,
)
# Names of the different values to be in the csv files
PARTICIPANT_COLUMNS = [
    "participant_id",
    "name",
    "baseline_heart_rate",
    "baseline_skin_response",
    "baseline_temperature",
]
# Names of the different values to be in the csv files
SESSION_COLUMNS = [
    "session_id",
    "participant_id",
    "timestamp",
    "heart_rate",
    "skin_response",
    "temperature",
    "activity_level",
    "signal_quality",
]
# If a signal quality is under this it is not usable.
MIN_SIGNAL_QUALITY = 0.5

# This def reads a csv file and gives only the rows with data, skipping everything else.
def read_csv_rows(path, expected_columns):
    # Turn the CSV file into a list of rows, not using empty lines.
    path = Path(path)
    try:
        with open(path, encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
    except FileNotFoundError:
        raise DataFileError(f"File not found: {path}") from None
    except PermissionError:
        raise DataFileError(f"No permission to read: {path}") from None
    except (csv.Error, UnicodeDecodeError) as err:
        raise DataFileError(f"Could not parse {path}: {err}") from None

    # Make sure the header matches the expected.
    if not rows or rows[0] != expected_columns:
        raise DataFileError(f"{path} has an unexpected header (expected {expected_columns})")

    # Ignores the header and returns the rows with data.
    data_rows = []
    for index, row in enumerate(rows[1:], start=2):
        if row:
            data_rows.append((index, row))
    return data_rows

# This store one invalid row in a list of rejected records.
def reject(rejected, path, row_number, error):
    rejected.append({
        "file": Path(path).name,
        "row": row_number,
        "field": error.field,
        "reason": str(error),
    })

# Makes sure one participant row is correct and converts it into an object. 
def parse_participant_row(row):
    if len(row) != len(PARTICIPANT_COLUMNS):
        raise InvalidRecordError(
            f"expected {len(PARTICIPANT_COLUMNS)} columns but found {len(row)}",
            "row_length",
        )
    # Take out the values and validates them.
    participant_id, name, hr, skin, temp = row
    check_identifier(participant_id, PARTICIPANT_ID_PATTERN, "participant_id")

    if name.strip() == "":
        raise InvalidRecordError("missing value", "name")

    hr = check_range(to_number(hr, "baseline_heart_rate", True), "baseline_heart_rate", 35, 205)
    skin = check_range(to_number(skin, "baseline_skin_response"), "baseline_skin_response", 0, 10)
    temp = check_range(to_number(temp, "baseline_temperature"), "baseline_temperature", 25, 42)

    # If everything is done, builds a participant object.
    return Participant(participant_id, name, hr, skin, temp)

# This block puts all the participants from the csv participant file.
def load_participants(path):
    # Read every participant row.
    participants = {}
    rejected = []

    for row_number, row in read_csv_rows(path, PARTICIPANT_COLUMNS):
        try:
            participant = parse_participant_row(row)
            participants[participant.participant_id] = participant
        except (InvalidIdentifierError, InvalidRecordError) as err:
            reject(rejected, path, row_number, err)

    return participants, rejected

# This block validates one session row.
def parse_session_row(row, participants):
    if len(row) != len(SESSION_COLUMNS):
        raise InvalidRecordError(
            f"expected {len(SESSION_COLUMNS)} columns but found {len(row)}",
            "row_length",
        )

    # Each value is read from the row.
    session_id, participant_id, timestamp, heart_rate, skin, temperature, activity, quality = row
    check_identifier(session_id, SESSION_ID_PATTERN, "session_id")
    check_identifier(participant_id, PARTICIPANT_ID_PATTERN, "participant_id")

    # For it to work the participant has to be real.
    try:
        participant = participants[participant_id]
    except KeyError:
        raise InvalidRecordError(f"unknown participant '{participant_id}'", "participant_id") from None

    # Converts the text values to numbers and makes sure it is in the allowed ranges.
    timestamp = check_range(to_number(timestamp, "timestamp", True), "timestamp", 0, 10**6)
    heart_rate = check_range(to_number(heart_rate, "heart_rate", True), "heart_rate", 35, 205)
    skin = check_range(to_number(skin, "skin_response"), "skin_response", 0, 10)
    temperature = check_range(to_number(temperature, "temperature"), "temperature", 25, 42)
    activity = check_range(to_number(activity, "activity_level"), "activity_level", 0, 1)
    quality = check_range(to_number(quality, "signal_quality"), "signal_quality", 0, 1)

    # Reject bad readings.
    if quality < MIN_SIGNAL_QUALITY:
        raise InvalidRecordError(
            f"poor signal quality {quality} (minimum {MIN_SIGNAL_QUALITY})",
            "signal_quality",
        )

    # makee an observation object if the row is valid.
    observation = Observation(timestamp, heart_rate, skin, temperature, activity, quality)
    return session_id, participant, observation

# This def puts all the valid sessions frtom the csv file and puts them by session id.
def load_sessions(path, participants):
    sessions = {}
    rejected = []
    accepted = 0

    for row_number, row in read_csv_rows(path, SESSION_COLUMNS):
        if len(row) >= 2 and is_valid_identifier(row[0], SESSION_ID_PATTERN) and row[1] in participants:
            sessions.setdefault(row[0], Session(row[0], participants[row[1]]))

        try:
            session_id, participant, observation = parse_session_row(row, participants)
            session = sessions.setdefault(session_id, Session(session_id, participant))
            
            if session.participant.participant_id != participant.participant_id:
                raise InvalidRecordError(
                    f"session {session_id} already belongs to {session.participant.participant_id}",
                    "participant_id",
                )
            session.add_observation(observation)
            accepted += 1
        except (InvalidIdentifierError, InvalidRecordError) as err:
            reject(rejected, path, row_number, err)

    return sessions, rejected, accepted
