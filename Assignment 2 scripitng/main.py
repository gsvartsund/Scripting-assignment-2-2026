"""Run:  python3 main.py --profiles data/participants.csv \
            --sessions data/fitness_sessions.csv data/fitness_sessions_invalid.csv --output output"""

import argparse
import sys
from fitness_analyzer.analysis import analyze_session
from fitness_analyzer.exceptions import DataFileError
from fitness_analyzer.loader import load_participants, load_sessions
from fitness_analyzer.reports import write_reports
# this def starts the program, and runs analysis.
def main(argv=None):
    parser = argparse.ArgumentParser(description="Smart Fitness Session Analyzer")
    parser.add_argument("--profiles", default="data/participants.csv")
    parser.add_argument(
        "--sessions",
        nargs="+",
        default=["data/fitness_sessions.csv", "data/fitness_sessions_invalid.csv"],
    )
    parser.add_argument("--output", default="output")
    args = parser.parse_args(argv)

    # Load the participant data firs
    try:
        participants, rejected = load_participants(args.profiles)
    except DataFileError as err:
        print(f"Fatal: {err}")
        return 1

    # Keep track of all results and how many rows were valid
    results = []
    accepted_rows = 0

    # Each session file is worked on
    for path in args.sessions:
        try:
            sessions, rejected_rows, ok_rows = load_sessions(path, participants)
        except DataFileError as err:
            print(f"Skipping file: {err}")
            continue

        rejected += rejected_rows
        accepted_rows += ok_rows

        for session in sessions.values():
            results.append(analyze_session(session))

    # Save all the generated reports to the output folder.
    try:
        files = write_reports(args.output, results, rejected)
    except DataFileError as err:
        print(f"Fatal: {err}")
        return 1

    # Print a  summary to the terminal
    print(f"Accepted rows: {accepted_rows}")
    print(f"Rejected rows: {len(rejected)}")
    print("Created files:")
    for path in files:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
