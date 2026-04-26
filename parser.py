from docx import Document
from docx.shared import Pt



def parser_docx(file_path):

    doc = Document(file_path)
    
    last_font = None
    last_size = None
    last_alignment = None
    
    for para in doc.paragraphs:
        for run in para.runs:
            parser = []
            text = run.text
        
            if not text.strip():
                continue

            font_name = run.font.name if run.font.name else 'По умолчанию'
            font_size = run.font.size.pt if run.font.size else 'По умолчанию'     
            
            if font_name != last_font or font_size != last_size:
                parser.append(font_name)
                parser.append(font_size)
                last_font = font_name
                last_size = font_size

            for i, para in enumerate(doc.paragraphs):
                format = para.paragraph_format
                alignment = format.alignment
                
                if alignment != last_alignment:
                    parser.append(alignment)
                    last_alignment = alignment
                    break
            
            parser.append(text)

            print(parser)
    
file_path = r"C:\Users\diff\Downloads\тестовая аналитика.docx"
print(parser_docx(file_path))