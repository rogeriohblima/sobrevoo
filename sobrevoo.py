import PyPDF2
import sys
import re
import json

aeronaves = {
    'FAB2526': {
        'modelo': 'EMB-145',
        'codigo': 'VC-99A'
    },
    'FAB2560': {
        'modelo': 'EMB-135',
        'codigo': 'VC-99C'
    },
    'FAB2580': {
        'modelo': 'E-35L',
        'codigo': 'VC-99B'
    }
}
aeronaves['FAB2550'] = aeronaves['FAB2526']
aeronaves['FAB2561'] = aeronaves['FAB2560']
aeronaves['FAB2581'] = aeronaves['FAB2580']
aeronaves['FAB2582'] = aeronaves['FAB2580']
aeronaves['FAB2583'] = aeronaves['FAB2580']
aeronaves['FAB2584'] = aeronaves['FAB2580']
aeronaves['FAB2585'] = aeronaves['FAB2580']




def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        return text
    

def get_anv_reservas(data):
    for anv in aeronaves:
        if data['anvTitular'] != anv:
            data['anvReservas'].append(anv)


def get_parte_data(parte_path, data):
    text_parte_break = extract_text_from_pdf(parte_path)
    text_parte = text_parte_break.replace("\n", " ")

    # ENCONTRAR A MISSÃO NO DOCUMENTO
    start_pattern = "apoio ao MINISTÉRIO "
    end_pattern = ", conforme o cronograma"
    pattern = rf"{start_pattern}(.*){end_pattern}"
    match = re.search(pattern, text_parte)
    if match:
        data['missao'] = f"Transportar o MINISTRO {match.group(1)} (XX PAX)"
    else:
        print("Missão não encontrada")

    # ENCONTRAR QUANTIDADE E TIPO DE AERONAVE
    start_pattern = "Aeronave titular: VC99[A|B|C] "
    tipoAnv = "(E35L|EMB-145|EMB-135)"
    end_pattern = f" \({tipoAnv}\)\. O"
    pattern = rf"{start_pattern}(.*){end_pattern}"
    match = re.search(pattern, text_parte)
    if match:
        data['anvTitular'] = match.group(1)
    else:
        print("Aeronave não encontrada")

    # ENCONTRAR INDICATIVO DE CHAMADA
    start_pattern = "Chamada será "
    end_pattern = f"\. 5"
    pattern = rf"{start_pattern}(.*){end_pattern}"
    match = re.search(pattern, text_parte)
    if match:
        data['chamada'] = match.group(1)
    else:
        print("Indicativo de chamada não encontrado")


def get_plan_data(plan_path, data):
    text_plan = extract_text_from_pdf(plan_path)

    # PEGA A ORIGEM E DESTINO
    start_pattern = "FROM "
    end_pattern = "\n"
    pattern = rf"{start_pattern}(.*){end_pattern}"
    match = re.search(pattern, text_plan)
    if match:
        fromTo = match.group(1).split()
        print(fromTo)
        trecho = {
            'from': fromTo[0].split('/')[0],
            'to': fromTo[3].split('/')[0],
            'etd': fromTo[6].replace(':', ''),
            'eta': fromTo[8].replace(':', '') + 'Z'
        }
        print(trecho)
        data['trechos'].append(trecho)
    else:
        print("Origem e Destino não encontrados")



if len(sys.argv) > 2:
    parte_path = sys.argv[1]
    plan_path = sys.argv[2]
    if not parte_path.endswith(".pdf"):
        print("Erro: Por favor, entre com a parte em formato PDF")
        exit(1)
    if not plan_path.endswith(".pdf"):
        print("Erro: Por favor, entre com o planejamento em formato PDF")
        exit(1)
    
    data = dict()
    data['trechos'] = []
    data['anvReservas'] = []
    get_parte_data(parte_path, data)
    get_plan_data(plan_path, data)
    get_anv_reservas(data)
else:
    print("Erro: Por favor, entre com pelo menos uma parte e um planejamento")
    print("Exemplo: python3 sobrevoo.py parte.pdf planejamento1.pdf planejamento2.pdf sobrevooFinal.pdf")