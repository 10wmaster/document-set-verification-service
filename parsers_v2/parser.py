import fitz

def parser_pdf(file_path):
    doc = fitz.open(file_path)
    result = []

    for page in doc:
        blocks = page.get_text("dict")["blocks"]

        for b in blocks:
            if b["type"] == 0:
                for line in b["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text: continue

                        chunk = {
                            "text": text,
                            "font": span["font"],
                            "size": round(span["size"], 1),
                            "is_bold": bool(span["flags"] & 2 ** 4),
                            "origin": span["origin"],  # [x, y] для проверки отступов
                            "page": page.number + 1,
                            # Размеры страницы в мм
                            "page_width_mm": round(page.rect.width * 25.4 / 72, 1),
                            "page_height_mm": round(page.rect.height * 25.4 / 72, 1)
                        }
                        result.append(chunk)

    doc.close()
    return result


file_path = r'C:\Users\diff\Documents\project\python\document-set-verification-service\uploads\Вопросы к экзамену 1 семестр.pdf'

print(parser_pdf(file_path))