import pdfplumber

with pdfplumber.open('example.pdf') as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
