import re
import fitz
from docx import Document


def parse_page_range(text, max_page):
    text = (text or "").strip()
    if not text:
        return list(range(1, max_page + 1))

    pages = set()
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-")
            pages.update(range(int(start), int(end) + 1))
        else:
            pages.add(int(part))
    return sorted(p for p in pages if 1 <= p <= max_page)


PAGE_NUMBER_RE = re.compile(r"^\s*(страница\s*)?\d{1,4}\s*\.?\s*$", re.IGNORECASE)


def _find_running_headers(texts, min_pages=3): # Удаление нумерации страниц
    counts = {}
    for text in texts:
        for line in {line.strip() for line in text.split("\n") if line.strip() and len(line) <= 80}:
            counts[line] = counts.get(line, 0) + 1
    return {line for line, count in counts.items() if count >= min_pages}


def _clean_page_text(text, running_headers):
    lines = [line for line in text.split("\n") if line.strip() not in running_headers]
    while lines and PAGE_NUMBER_RE.match(lines[-1].strip()):
        lines.pop()
    return "\n".join(lines).strip()


def extract_pdf(path, page_range_text):
    doc = fitz.open(path)
    pages_to_use = parse_page_range(page_range_text, doc.page_count)

    raw_texts = {page_num: doc[page_num - 1].get_text().strip() for page_num in pages_to_use}
    running_headers = _find_running_headers(raw_texts.values())

    slides = []
    for page_num in pages_to_use:
        page = doc[page_num - 1]
        text = _clean_page_text(raw_texts[page_num], running_headers)

        images = []
        for img in page.get_images(full=True):
            xref = img[0]
            images.append(doc.extract_image(xref)["image"])

        if text or images:
            slides.append({"text": text, "images": images})

    doc.close()
    return slides


PAGE_CHAR_BUDGET = 2200


def extract_docx(path, page_range_text):
    doc = Document(path)

    image_parts = {
        rel.rId: rel.target_part.blob
        for rel in doc.part.rels.values()
        if "image" in rel.reltype
    }

    pages = []
    current_text, current_images, current_chars = [], [], 0

    for para in doc.paragraphs:
        manual_page_break = any('w:type="page"' in run._element.xml for run in para.runs)

        if para.text.strip():
            current_text.append(para.text.strip())
            current_chars += len(para.text)

        for run in para.runs:
            for rid in re.findall(r'r:embed="(rId\d+)"', run._element.xml):
                if rid in image_parts:
                    current_images.append(image_parts[rid])

        if manual_page_break or current_chars >= PAGE_CHAR_BUDGET:
            text = "\n".join(current_text).strip()
            if text or current_images:
                pages.append({"text": text, "images": current_images})
            current_text, current_images, current_chars = [], [], 0

    text = "\n".join(current_text).strip()
    if text or current_images:
        pages.append({"text": text, "images": current_images})

    pages_to_use = parse_page_range(page_range_text, len(pages))
    return [pages[i - 1] for i in pages_to_use]
