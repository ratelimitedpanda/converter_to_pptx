import os
import sys
import tempfile

from flask import Flask, render_template, request, send_file

from .build_pptx import build_presentation
from .extract import extract_docx, extract_pdf
from .llm import make_slide_content

sys.stdout.reconfigure(encoding="utf-8")

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    file = request.files["document"]
    pages_text = request.form.get("pages", "")
    model_name = request.form.get("model", "local-model")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".docx"):
        return "Поддерживаются только файлы .pdf и .docx", 400

    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, file.filename)
    file.save(input_path)

    if ext == ".pdf":
        raw_slides = extract_pdf(input_path, pages_text)
    else:
        raw_slides = extract_docx(input_path, pages_text)

    print(f"Найдено фрагментов для обработки: {len(raw_slides)}")

    slides_content = []
    for i, raw in enumerate(raw_slides, start=1):
        print(f"[{i}/{len(raw_slides)}] Передано модели.")
        content = make_slide_content(raw["text"], model=model_name)
        content["images"] = raw["images"]
        slides_content.append(content)
        print(f"[{i}/{len(raw_slides)}] Модель обработала страницу и вернула ответ.")

    output_path = os.path.join(tmp_dir, "presentation.pptx")
    build_presentation(slides_content, output_path)

    return send_file(output_path, as_attachment=True, download_name="presentation.pptx")
