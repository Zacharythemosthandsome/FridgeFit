# Apple Health import and summary helpers. (You Xuanhe)


import csv
import zipfile   # Unzip and extract ZIP files
from pathlib import Path  # Get file storage path
from typing import IO, Optional, Tuple

from .config import APP_DIR, HEALTH_EXPORT_TAGS


def choose_apple_health_zip() -> Optional[Path]:
    """Open a file picker and return the selected Apple Health export zip."""
    import tkinter as tk
    from tkinter import filedialog
    # Create a file selection window and bring it to the top.
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    file_path = filedialog.askopenfilename(
        title="Choose Apple Health export.zip",
        filetypes=[("ZIP files", "*.zip")],
    )
    root.destroy()

    if not file_path:
        return None
    return Path(file_path)


def process_apple_health_zip(project_folder: Optional[Path] = None) -> Optional[Path]:
    """Convert supported XML records from an Apple Health export zip into CSV files."""
    print("Apple Health Export Tool (Output to Project Folder)")
    project_folder = project_folder or APP_DIR
    # Read the file storage path
    zip_path = choose_apple_health_zip()
    if zip_path is None:
        return None
    
    output_folder = project_folder / zip_path.stem
    if not output_folder.exists():
        output_folder.mkdir(parents=True, exist_ok=True)
        print(f"Created directory in project: {output_folder}")
    # Parse and extract ZIP files
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_file: # Since no modifications are needed when parsing a ZIP file, read-only mode is used.
            xml_files = [name for name in zip_file.namelist() if name.endswith(".xml")] # Find all files in a ZIP archive that end with the .xml extension.

            for xml_name in xml_files:
                if "cda" in xml_name.lower():
                    continue
                _process_xml_file(zip_file, xml_name, output_folder)

        print(f"\nDone! Files are located in: {output_folder}")
        return output_folder
    # If an error is encountered, print the error message.
    except Exception as error:
        print(f"\nError: {error}")
        return None


def _process_xml_file(zip_file: zipfile.ZipFile, xml_name: str, output_folder: Path) -> None:
    file_info = zip_file.getinfo(xml_name)
    total_size = file_info.file_size
    print(f"Analyzing {xml_name}... Please wait.")

    with zip_file.open(xml_name) as scan_stream:
        total_records = _count_records(scan_stream)
    # Analyze the file, pre-read the total entries, and prepare to output a CSV file.
    if total_records == 0:
        print(f"No health record found in {xml_name}, skipping.")
        return

    print(f"Total entries found: {total_records:,}")

    with zip_file.open(xml_name) as xml_stream:
        count, file_count = _write_records_to_csv(xml_stream, output_folder, total_size)

    if count > 0:
        print(f"Success: Generated {file_count} files in /{output_folder.name}/")


def _count_records(xml_stream: IO[bytes]) -> int:
    import lxml.etree as ET

    total_records = 0
    for _, elem in ET.iterparse(xml_stream, events=("end",)):
        if elem.tag in HEALTH_EXPORT_TAGS:
            total_records += 1
        elem.clear()
    return total_records


def _write_records_to_csv(
    xml_stream: IO[bytes], output_folder: Path, total_size: int
) -> Tuple[int, int]:
    import lxml.etree as ET
    from tqdm import tqdm

    outputs = {}
    writers = {}
    count = 0
    # Create a progress bar and begin the conversion.
    try:
        with tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            desc="Converting",
            colour="cyan",
        ) as progress_bar:
            context = ET.iterparse(xml_stream, events=("end",), tag=HEALTH_EXPORT_TAGS)
            for _, elem in context:
                tag_name = elem.tag
                data = dict(elem.attrib)

                if data:
                    if tag_name not in outputs:
                        csv_name = output_folder / f"{tag_name}.csv"  # Create a CSV file in the same folder as the project.
                        output_file = open(csv_name, "w", newline="", encoding="utf-8-sig")  # Use UTF-8-sig encoding with BOM to prevent garbled characters in the converted data.
                        writer = csv.DictWriter(
                            output_file,
                            fieldnames=data.keys(),
                            extrasaction="ignore",
                        )
                        writer.writeheader()
                        outputs[tag_name] = output_file
                        writers[tag_name] = writer

                    writers[tag_name].writerow(data)
                    count += 1

                progress_bar.update(xml_stream.tell() - progress_bar.n)
                _clear_element(elem)

    finally:
        for output_file in outputs.values():
            output_file.close()

    return count, len(outputs)


def _clear_element(elem) -> None:
    elem.clear()
    while elem.getprevious() is not None:
        del elem.getparent()[0]

# Filter Items
def get_health_data_summary(folder_path: Path) -> Optional[str]:
    """Read the exported Record.csv file and summarize the latest activity day."""
    import pandas as pd

    try:
        folder_path = Path(folder_path)
        record_file = folder_path / "Record.csv"

        if not record_file.exists():
            return None

        print("\n[System] Analyzing health data... This might take a few seconds.")
        data_frame = pd.read_csv(record_file, usecols=["type", "startDate", "value"], dtype=str)

        step_data = data_frame[
            data_frame["type"] == "HKQuantityTypeIdentifierStepCount"
        ].copy()
        step_data["startDate"] = pd.to_datetime(step_data["startDate"], errors="coerce")
        step_data["value"] = pd.to_numeric(step_data["value"], errors="coerce")

        energy_data = data_frame[
            data_frame["type"] == "HKQuantityTypeIdentifierActiveEnergyBurned"
        ].copy()
        energy_data["startDate"] = pd.to_datetime(energy_data["startDate"], errors="coerce")
        energy_data["value"] = pd.to_numeric(energy_data["value"], errors="coerce")

        if not step_data.empty:
            latest_date = step_data["startDate"].dt.date.max()
            total_steps = step_data[step_data["startDate"].dt.date == latest_date]["value"].sum()

            total_energy = 0
            if not energy_data.empty:
                total_energy = energy_data[
                    energy_data["startDate"].dt.date == latest_date
                ]["value"].sum()

            return (
                f"Recorded Date: {latest_date}, Total Steps: {int(total_steps)}, "
                f"Active Energy Burned: {int(total_energy)} kcal"
            )

        return "No valid step data found in records."

    except Exception as error:
        print(f"[Warning] Could not parse health data cleanly: {error}")
        return None