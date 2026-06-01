import os
import re
from pathlib import Path
import numpy as np
import pandas as pd
import PyPDF2

# Production Security Rule: Fetch base directory from environment variable or default safely
BASE_DIR = Path(os.getenv("VFD_SHARE_PATH", r"C:\Share")).resolve()


def read_pdf(base_dir: Path, relative_path: Path, patterns: dict) -> pd.DataFrame:
    """Parses Veterans Affairs authorization PDFs dynamically and structures metadata

    into a unified production-grade pandas DataFrame.
    """
    full_path = (base_dir / relative_path).resolve()
    if not str(full_path).startswith(str(base_dir)):
        raise ValueError("Security Violation: Path traversal detected")

    records = []

    for file in full_path.glob("*.pdf"):
        try:
            with open(file, "rb") as f:
                pdf = PyPDF2.PdfReader(f)
                text = "".join([page.extract_text() for page in pdf.pages])

                # Core data extraction framework (isolated per file execution context)
                patient_info = {"file": file.name}

                for key, pattern in patterns.items():
                    matches = re.findall(pattern, text, re.MULTILINE)

                    if not matches:
                        patient_info[key] = None
                        continue

                    # Specialized validation and cleanup filters
                    if key == "Address":
                        cleaned_addresses = [re.sub(r"[\n\r]+", " ", m).strip() for m in matches]
                        patient_info[key] = " | ".join(cleaned_addresses)

                    elif key == "Authorized_Procedures":
                        cleaned_procedures = []
                        seen_codes = set()
                        for match in matches:
                            clean_match = re.sub(r"\[X\}\s*", "", match).strip()
                            code_match = re.match(r"D\d{4}", clean_match)
                            if code_match:
                                code = code_match.group(0)
                                if code not in seen_codes:
                                    seen_codes.add(code)
                                    cleaned_procedures.append(clean_match)
                        patient_info[key] = (
                            ", ".join(cleaned_procedures) if cleaned_procedures else None
                        )

                    else:
                        patient_info[key] = matches[0].strip() if matches else None

                records.append(patient_info)

        except Exception as e:
            print(f"[ERROR] Telemetry disruption processing file {file.name}: {str(e)}")
            continue

    if not records:
        return pd.DataFrame()

    # Structural dataframe normalization & alignment
    df = pd.DataFrame(records)
    df.replace("", np.nan, inplace=True)
    df.dropna(how="all", axis=0, inplace=True)

    return df


if __name__ == "__main__":
    # Robust regular expression patterns for dynamic telemetry extraction
    VA_PATTERNS = {
        "Name": r"^Veteran Name:\s*(.*)(?=\sReferral)",
        "DOB": r"Veteran Date of Birth:\s*(.*)(?=\sExpiration)",
        "Last_4_SSN": r"^SSN:\s*.*[?!\D](\d+)",
        "Address": r"^Veteran Address:\s*(.*(?:\r?\n*).*)",
        "Authorization #": r"[A-Z]+-Referral Number:\s*(VA\d+)",
        "Priority": r"Priority:\s*(.*)",
        "Referral_Issue_Date": r"Referral Issue Date:\s*(.*)",
        "Referral_Expiration_Date": r"Expiration Date:\s*(.*(?=\s\(SEE BELOW))",
        "Email_Address": r"Email Address \(If Known\):\s*(.*)",
        "Office": r"Initial Community Care Provider/Facility:\s*(.*)",
        "Provisional_Diagnosis": r"Provisional Diagnosis:\s*(K\d+.*)",
        "Authorized_Procedures": r"\s+((?:\[X\}\s+)?D\d{4}\s+.+(?=\n\s+\[X\}|\s+.))",
    }

    print("[INFO] Launching Patient Referral Automation Stream...")
    relative_target = Path(".")
    df = read_pdf(BASE_DIR, relative_target, VA_PATTERNS)

    if not df.empty:
        print(df)
        # df.to_excel('VA_Auth_PatData.xlsx', index=False, header=True)
    else:
        print("[WARN] No data aggregated or extracted from localized PDF formats.")
