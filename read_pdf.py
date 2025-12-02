import pdfplumber
import os

base_path = r"c:\Users\admin\OneDrive - Institute of Business Administration\Desktop\Sharique\sem 5\CS\Research again\Previous"

# Read all PDFs
pdf_files = [
    "Code base - API Security under OWASP API Security Top 10.pdf",
    "Code Validation - Final (2).pdf",
    "v2.pdf"
]

for pdf_file in pdf_files:
    pdf_path = os.path.join(base_path, pdf_file)
    print("\n" + "=" * 80)
    print(f"FILE: {pdf_file}")
    print("=" * 80)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
            print(text[:8000])  # Print first 8000 chars of each
    except Exception as e:
        print(f"Error reading {pdf_file}: {e}")
