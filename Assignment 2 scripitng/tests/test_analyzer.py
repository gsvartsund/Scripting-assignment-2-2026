import tempfile
import unittest
from pathlib import Path
from fitness_analyzer.analysis import analyze_session
from fitness_analyzer.exceptions import DataFileError, InvalidIdentifierError, InvalidRecordError
from fitness_analyzer.loader import load_participants, load_sessions, parse_session_row
from fitness_analyzer.models import Observation, Participant, Session
from fitness_analyzer.reports import write_reports

# These values are reused by the tests to make  participant and session data.
P = {"P001": Participant("P001", "Test", 68, 1.2, 32.4)}
GOOD = ["FIT-2026-001", "P001", "0", "70", "1.2", "32.4", "0.1", "0.9"]

# This  makes a valid row and changes only the values to test.
def row(**changes):
    names = ["sid", "pid", "ts", "hr", "skin", "temp", "act", "q"]
    r = list(GOOD)
    for k, v in changes.items():
        r[names.index(k)] = v
    return r

# These tests check that session rows are accepted or rejected with the correct errors
class RowValidation(unittest.TestCase):
    # A valid row should be read and its session ID and heart rate should be returned.
    def test_valid_row(self):
        sid, p, obs = parse_session_row(GOOD, P)
        self.assertEqual((sid, obs.heart_rate), ("FIT-2026-001", 70))
    # A session ID with the wrong format should be rejected.
    def test_bad_session_id(self):
        with self.assertRaises(InvalidIdentifierError):
            parse_session_row(row(sid="FIT-26-001"), P)
    # A participant ID with the wrong format should be rejected.
    def test_bad_participant_id_format(self):
        with self.assertRaises(InvalidIdentifierError):
            parse_session_row(row(pid="001"), P)
    # A correctly formatted participant ID that is not in the data should be rejected.
    def test_unknown_participant(self):
        with self.assertRaises(InvalidRecordError):
            parse_session_row(row(pid="P999"), P)
    # A word where a number is expected should be rejected.
    def test_not_a_number(self):
        with self.assertRaises(InvalidRecordError):
            parse_session_row(row(hr="fast"), P)
    # A blank value in a required field should be rejected.
    def test_missing_value(self):
        with self.assertRaises(InvalidRecordError):
            parse_session_row(row(act=""), P)
    # A row with too few columns should be rejected.
    def test_wrong_row_length(self):
        with self.assertRaises(InvalidRecordError):
            parse_session_row(GOOD[:-1], P)
    # Heart rates at the allowed limits should pass, and values outside them should fail.
    def test_heart_rate_boundaries(self):
        parse_session_row(row(hr="35"), P)
        parse_session_row(row(hr="205"), P)
        for bad in ("34", "206"):
            with self.assertRaises(InvalidRecordError):
                parse_session_row(row(hr=bad), P)
    # Signal quality at the minimum should pass, but a lower value should fail.
    def test_signal_quality_boundary(self):
        parse_session_row(row(q="0.5"), P)
        with self.assertRaises(InvalidRecordError):
            parse_session_row(row(q="0.49"), P)

# These tests check how the program handles input files and output.
class Files(unittest.TestCase):
    # Trying to load a file that does not exist should raise an error
    def test_missing_file(self):
        with self.assertRaises(DataFileError):
            load_participants("does_not_exist.csv")
    # The provided data files should load and reject the invalid recorss 
    def test_official_files_load(self):
        participants, rej = load_participants("data/participants.csv")
        self.assertEqual(len(participants), 3)
        self.assertEqual(rej, [])
        _, rejected, accepted = load_sessions("data/fitness_sessions.csv", participants)
        self.assertEqual((len(rejected), accepted), (5, 24))
        _, rejected, _ = load_sessions("data/fitness_sessions_invalid.csv", participants)
        self.assertGreater(len(rejected), 5)
    # Report files should be created and can be written more than once so you can run it more times if you want
    def test_output_created_and_repeatable(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "new" / "output" 
            for _ in range(2): 
                paths = write_reports(out, [], [])
                self.assertTrue(all(p.exists() for p in paths))
# This helper creates a session with the heart rates and activity used
def make_session(hrs, act=0.1):
    s = Session("FIT-2026-001", P["P001"])
    for i, hr in enumerate(hrs):
        s.add_observation(Observation(i, hr, 1.2, 32.4, act, 0.9))
    return s
# These tests check how session measurements are 
class Analysis(unittest.TestCase):
    # A session with too few readings should be marked as insufficient.
    def test_insufficient(self):
        self.assertEqual(analyze_session(make_session([70, 70]))["classification"],
                         "insufficient_data")
    # Three valid readings should be enough for the program to classify a session.
    def test_exactly_three_rows_is_enough(self):
        self.assertEqual(analyze_session(make_session([68, 69, 70]))["classification"], "resting")
    # High activity measurements should produce a high-activity classification.
    def test_high_activity(self):
        self.assertEqual(analyze_session(make_session([130, 128, 132], 0.8))["classification"],
                         "high_activity")
    # A falling heart rate is classified using the session average.
    def test_falling_heart_rate_uses_average_classification(self):
        self.assertEqual(analyze_session(make_session([120, 110, 90, 75]))["classification"],
                         "moderate_activity")
if __name__ == "__main__":
    unittest.main()
