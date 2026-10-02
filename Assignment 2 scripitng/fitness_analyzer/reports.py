import csv
from pathlib import Path
from .exceptions import DataFileError

# These are the columns for the summary.
SUMMARY_FIELDS = [
    "session_id",
    "participant_id",
    "usable_rows",
    "avg_heart_rate",
    "avg_skin_response",
    "avg_temperature",
    "avg_activity",
    "hr_above_baseline",
    "classification",
]

# This def does the writing to the local disk and turns file errors in to exceptationss.
def _write(path, writer_function, **open_kwargs):
    try:
        with open(path, "w", encoding="utf-8", **open_kwargs) as handle:
            writer_function(handle)
    except PermissionError:
        raise DataFileError(f"No permission to write: {path}") from None
    except OSError as err:
        raise DataFileError(f"Could not write {path}: {err}") from None

# This def makes the folder for output and writes the summary
def write_reports(output_dir, results, rejected):
    output_path = Path(output_dir)
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as err:
        raise DataFileError(f"Could not create output folder {output_path}: {err}") from None

    # These files are created to read the output, it shows the rejected data, the report and a csv file of the summary.
    summary_path = output_path / "analysis_summary.csv"
    report_path = output_path / "analysis_report.txt"
    rejected_path = output_path / "rejected_records.txt"

    # This block writes the CSV summary
    def write_summary(handle):
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    # This def writes the report
    def write_report(handle):
        for result in results:
            handle.write(f"Session: {result['participant_id']}\n")
            handle.write(f"Rows used: {result['usable_rows']}\n")
            handle.write(f"Result: {result['classification'].replace('_', ' ')}\n")
            for reason in result["reasons"]:
                handle.write(f"- {reason}\n")
            handle.write("\n")

    # This def writes the list of rejected rows.
    def write_rejected(handle):
        handle.write("Rejected records:\n")
        for entry in rejected:
            handle.write(
                f"File: {entry['file']}, row: {entry['row']}, "
                f"field: {entry['field']}, reason: {entry['reason']}\n"
            )

    # Save all three.
    _write(summary_path, write_summary, newline="")
    _write(report_path, write_report)
    _write(rejected_path, write_rejected)
    return [summary_path, report_path, rejected_path]
