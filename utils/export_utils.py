from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def build_packet_zip(files, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as zip_file:
        for file_path in files:
            path = Path(file_path)

            if not path.exists() or not path.is_file():
                continue

            zip_file.write(path, arcname=path.name)

    return output_path
