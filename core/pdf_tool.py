"""Document Tool: extracts clean text from an uploaded supplier RFP PDF."""
import pymupdf as fitz


def extract_text(file_like) -> str:
    """file_like: a file path (str) or a bytes-like/BytesIO object (e.g. Streamlit UploadedFile)."""
    if hasattr(file_like, "read"):
        data = file_like.read()
        doc = fitz.open(stream=data, filetype="pdf")
    else:
        doc = fitz.open(file_like)

    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()

    text = "\n".join(pages).strip()
    return text
