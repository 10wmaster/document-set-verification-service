import fitz

def parser_pdf(file_path):
    doc = fitz.open(file_path)
    result = []

    for page in doc:
    # ХАК: Если на странице есть картинки (сканы подписей/печатей), 
    # добавляем искусственный чанк, что графика обнаружена
        if len(page.get_images()) > 0:
            result.append({
                "text": "[графическая_подпись_обнаружена]",
                "font": "System",
                "size": 12.0,
                "page": page.number + 1
            })
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