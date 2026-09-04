const form = document.getElementById("convert-form");
const button = document.getElementById("submit-btn");
const status = document.getElementById("status");

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const sourceFile = form.querySelector('input[type=file]').files[0];
    const suggestedName = (sourceFile ? sourceFile.name.replace(/\.[^.]+$/, "") : "presentation") + ".pptx";

    let fileHandle = null;
    if (window.showSaveFilePicker) {
        try {
            fileHandle = await window.showSaveFilePicker({
                suggestedName,
                types: [{
                    description: "PowerPoint",
                    accept: { "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"] },
                }],
            });
        } catch (err) {
            if (err.name === "AbortError") return;
            throw err;
        }
    }

    button.disabled = true;
    button.textContent = "Обработка...";
    status.className = "";
    status.style.display = "block";
    status.textContent = "Обрабатываю документ, это может занять пару минут...";

    try {
        const response = await fetch("/convert", { method: "POST", body: new FormData(form) });
        if (!response.ok) {
            throw new Error(await response.text());
        }

        const blob = await response.blob();

        if (fileHandle) {
            const writable = await fileHandle.createWritable();
            await writable.write(blob);
            await writable.close();
        } else {
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = suggestedName;
            link.click();
            URL.revokeObjectURL(link.href);
        }

        status.className = "ok";
        status.textContent = "Готово! Файл сформирован и сохранён.";
    } catch (err) {
        status.className = "error";
        status.textContent = "Ошибка при обработке: " + err.message;
    } finally {
        button.disabled = false;
        button.textContent = "Сгенерировать презентацию";
    }
});
