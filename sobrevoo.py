import PyPDF2
import sys
import re
import json
from tkinter import Tk, Frame, Label, Button, Entry, filedialog
from datetime import datetime, date

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


class ParteData():
    def __init__(self):
        self.trechos = []
        self.anvReservas = []
        self.tripTitular = []
        self.tripReserva = []
        self.aeroportos = dict()
        self.planejamentos = {}
        self.anvTitular = ""

    def __str__(self):
        text = f"Aeronave: {self.anvTitular}\n  \
            Chamada: {self.chamada}\n  \
            Missão: {self.missao}\n  \
            Data de Início: {self.dataInicio}\n \
            Data de Término: {self.dataTermino}\n \
            Aeronaves reservas:\n"
        for anv in self.anvReservas:
            text += f"\t\t{anv}\n"
        text += "Tripulação titular: \n"
        for militar in self.tripTitular:
            text += f"\t{str(militar)}\n"
        text += "Tripulação reserva: \n"
        for militar in self.tripReserva:
            text += f"\t{str(militar)}\n"
        return text

    def extract_text_from_pdf(self, pdfPath):
        with open(pdfPath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
            return text
        

    def get_anv_reservas(self):
        for anv in aeronaves:
            if self.anvTitular != anv:
                self.anvReservas.append(anv)


    def get_parte_data(self, parte_path):
        text_parte_break = self.extract_text_from_pdf(parte_path)
        text_parte = text_parte_break.replace("\n", " ")

        # RECUPERA OS AEROPORTOS
        self.get_aeroportos()

        # ENCONTRAR A MISSÃO NO DOCUMENTO
        start_pattern = "apoio ao MINISTÉRIO "
        end_pattern = ", conforme o cronograma"
        pattern = rf"{start_pattern}(.*){end_pattern}"
        match = re.search(pattern, text_parte)
        if match:
            self.missao = f"TRANSPORTAR O MINISTRO {match.group(1)} (XX PAX)"
        else:
            print("Missão não encontrada")

        # ENCONTRAR QUANTIDADE E TIPO DE AERONAVE
        start_pattern = "Aeronave titular: VC99[A|B|C] "
        tipoAnv = "(E35L|EMB-145|EMB-135)"
        end_pattern = rf" \({tipoAnv}\)\. O"
        pattern = rf"{start_pattern}(.*){end_pattern}"
        match = re.search(pattern, text_parte)
        if match:
            self.anvTitular = match.group(1)
        else:
            print("Aeronave não encontrada")
        
        # RECUPERA AS AERONAVES RESERVAS
        self.get_anv_reservas();

        # ENCONTRAR INDICATIVO DE CHAMADA
        start_pattern = "Chamada será "
        end_pattern = rf"\. 5"
        pattern = rf"{start_pattern}(.*){end_pattern}"
        match = re.search(pattern, text_parte)
        if match:
            self.chamada = match.group(1)
        else:
            print("Indicativo de chamada não encontrado")

        # ENCONTRAR OS TRECHOS
        pattern = rf"\d\d\/\d\d.*\d\d\d\d\n"
        matches = re.findall(pattern, text_parte_break)
        if matches:
            # encontra os dados da linha de cada trecho na parte
            self.dataInicio = date(1900, 1, 31)
            self.dataTermino = date(1900, 1, 31)
            date_flag = True  # quando atribui a data ao dataInicio (só o primeiro trecho), fica False e não atribui mais

            for match in matches:
                trecho = dict()
                trecho['paises'] = []
                with open("airports.json", "r", encoding="utf-8") as arquivo:
                    airports = json.load(arquivo)
                # procura a origem, destino e alternativa
                matches = re.findall(rf"[A-Z][A-Z][A-Z][A-Z]", match)
                trecho['from'] = matches[0]
                trecho['to'] = matches[1]
                trecho['alt'] = matches[2]
                # verifica se a origem e destino estão no Brasil se estiver não entra no sobrevoo
                if airports[trecho['from']]['country'] != airports[trecho['to']]['country']:
                    # pega etd e eta
                    matches = re.findall(rf"\d\d:\d\d", match)
                    trecho['etd'] = matches[0]
                    trecho['eta'] = matches[2]
                    # pega as datas de ida e de retorno e seta as datas de início e término
                    matches = re.findall(rf"\d\d\/\d\d", match)
                    trecho['data_dep'] = matches[0]
                    trecho['data_arr'] = matches[1]
                    year = str(datetime.now().year)
                    self.dataTermino = datetime.strptime(matches[1]+year, "%d/%m%Y")
                    if date_flag == True:
                        self.dataInicio = datetime.strptime(matches[0]+year, "%d/%m%Y")
                        date_flag = False
                    self.trechos.append(trecho)

        # PEGA A TRIPULAÇÃO TITULAR
        start_pattern = r"Pass OM\s"
        end_pattern = r"\s\s\s13"
        pattern = rf"{start_pattern}(.*){end_pattern}"
        tripTitular = re.search(pattern, text_parte)
        if tripTitular:
                # separa os militares conforme seguinte padrão na parte:
                # MJ LEONARDO VASCONCELOS LISBÔA 427.790-203/06/1988SB 149.78403/10/2026 GTE 
                # CP LEANDRO RAPHAEL BORGES DE FREITAS449.412-104/06/1992SB 162.70025/07/2028 GTE
                pattern = r"\b(TC|MJ|CP|1T|2T|SO|1S|2S|3S)\b\s([^0-9]+)\s?(\d{3}\.\d{3}-\d{1})(\d{2}\/\d{2}/\d{4})(SB\s\d{3}\.\d{3})(\d{2}\/\d{2}/\d{4})\s+(\w+)"
                matches = re.findall(pattern, tripTitular.group(1))
                for militar in matches:
                    self.tripTitular.append(militar)
        else:
            print("tripulação titular não encontrada")    

        #PEGA A TRIPULAÇÃO RESERVA
        start_pattern = r"Reserva.*Pass OM\s" ""
        end_pattern = r"\sRespeitosamente"
        pattern = rf"{start_pattern}(.*){end_pattern}"
        tripReserva = re.search(pattern, text_parte)
        tripReservaLimpa = re.sub(r"- \d. RES\s?","", tripReserva.group(1))
        if tripReserva:
                # separa os militares conforme seguinte padrão na parte:
                # CP PAULO RUFFONI NETO - 1° RES 431.082-915/01/1988SB 169.90226/02/2029 GTE 
                # CP GABRIEL LUIZ DA ROCHA FERREIRA - 2° RES438.195-529/10/1990SB 058.44122/03/2028 GTE 
                # SO ALEXANDRE JOSÉ DE MELO COELHO 364.898-220/05/1975SC 003.77229/07/2029 GTE 
                # 3S RONI TOSCANO DE MEDEIROS 656.450-010/10/1995SC 001.00207/05/2029 GTE
                pattern = r"\b(TC|MJ|CP|1T|2T|SO|1S|2S|3S)\b\s([^0-9-]+)[-.]*(\d{3}\.\d{3}-\d{1})(\d{2}\/\d{2}/\d{4})(\w{2}\s\d{3}\.\d{3})(\d{2}\/\d{2}/\d{4})\s+(\w+)"
                matches = re.findall(pattern, tripReservaLimpa)
                for militar in matches:
                    self.tripReserva.append(militar)
        else:
            print("tripulação reserva não encontrada")  


    def get_plan_data(self, plan_path, trecho):
        text_plan_break = self.extract_text_from_pdf(plan_path)
        text_plan = text_plan_break.replace("\n", " ")
        self.planejamentos[trecho] = text_plan
        # print(self.planejamentos[trecho])


    def get_aeroportos(self):
        with open("airports.json", "r", encoding="utf-8") as arquivo:
            airports = json.load(arquivo)
        for trecho in self.trechos:
            # insere o aeroporto de origem
            if not self.aeroportos.get(trecho['from']):
                aeroporto = {
                    trecho['from']: {
                        'nome': airports[trecho['from']]['name'].upper(),
                        'cidade': airports[trecho['from']]['city'].upper(),
                        'pais': airports[trecho['from']]['country'].upper()
                    }
                }
                self.aeroportos.update(aeroporto)

            # insere o aeroporto de destino
            if not self.aeroportos.get(trecho['to']):
                aeroporto = {
                    trecho['to']: {
                        'nome': airports[trecho['to']]['name'].upper(),
                        'cidade': airports[trecho['to']]['city'].upper(),
                        'pais': airports[trecho['to']]['country'].upper()
                    }
                }
                self.aeroportos.update(aeroporto)

            # insere o aeroporto de alternativa se o destino e alternativa forem fora do Brasil
            if not self.aeroportos.get(trecho['alt']) and (airports[trecho['to']]['country'] != 'Brasil' or airports[trecho['alt']]['country'] != 'Brasil'):
                aeroporto = {
                    trecho['alt']: {
                        'nome': airports[trecho['alt']]['name'].upper(),
                        'cidade': airports[trecho['alt']]['city'].upper(),
                        'pais': airports[trecho['alt']]['country'].upper()
                    }
                }
                self.data['aeroportos'].update(aeroporto)
        

class Application:
    def __init__(self, master=None):
        
        self.parteData = ParteData()
        self.ctMaster = Frame(master)
        self.ctMaster["pady"] = 10
        self.ctMaster.pack()

        self.ctParte = Frame(self.ctMaster)
        self.ctParte.pack()

        self.ctTrechos = Frame(self.ctMaster)
        self.ctTrechos.pack()

        self.btUploadParte = Button(self.ctMaster, text="Upload PARTE", command=self.getParte)
        self.btUploadParte.pack()

    def getParte(self):
        self.btCriaSobrevoo = Button(
            self.ctMaster,
            text = "CRIA SOBREVOO",
            command = self.cria_sobrevoo            
        )
        self.btCriaSobrevoo.pack()
        file_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf")],  # somente pdf
            title="Selecione a parte em formato PDF"
        )
        if file_path:
            self.parteData.get_parte_data(file_path) 
            self.btUploadParte.destroy()  
            self.lbTrecho = {} 
            self.ctTrecho = {}
            self.btAddPlan = {}
            self.plan = {}
            self.btAddPais = {}

            # para cada trecho, adiciona um Frame contendo um label, um botão para carregar
            # o planejamento e um botão para adicionar um país e seus pontos de entrada e saída
            for trecho in self.parteData.trechos:
                trechoIndex = trecho['from'] + trecho['to']
                self.ctTrecho[trechoIndex] = Frame(self.ctTrechos, 
                                                      bd=4, pady=5,
                                                      relief='ridge'
                                                      )
                self.ctTrecho[trechoIndex].pack(padx=10, pady=10)
                self.lbTrecho[trechoIndex] = Label(
                    self.ctTrecho[trechoIndex], 
                    text=f"Trecho: {trechoIndex} ({trecho['data_dep']} {trecho['etd']}) - {trecho['to']} ({trecho['data_arr']} {trecho['eta']})",
                    font=('Helvetica', 16, 'bold')
                )
                self.lbTrecho[trechoIndex].pack(pady=10)
                self.btAddPlan[trechoIndex] = Button(
                    self.ctTrecho[trechoIndex], 
                    text = "Upload do Planejamento",
                    command = lambda t=trechoIndex: self.adiciona_plan(t)
                )
                self.btAddPlan[trechoIndex].pack(pady=10)
                self.btAddPais[trechoIndex] = Button(
                    self.ctTrecho[trechoIndex], 
                    text = "Adicionar País",
                    command = lambda t=trechoIndex: self.adiciona_pais(t)
                )
                # self.btAddPais[trechoIndex].pack(pady=10)
    
    # CRIA O SOBREVOO
    def cria_sobrevoo(self):
        for trecho in self.ctTrecho:  # pega cada trecho
            for ctPais in self.ctTrecho[trecho].winfo_children():   #pega cada conteiner que contem pais, ponto de entrada, de saída e rota
                if isinstance(ctPais, Frame):
                    pais = {}
                    index = 0
                    for etPais in ctPais.winfo_children():  # pega os quatro campos do formulário
                        if isinstance(etPais, Entry):
                            if index == 0:
                                pais['pais'] = etPais.get()
                            elif index == 1:
                                pais['ptEntrada'] = etPais.get()
                            elif index == 2:
                                pais['ptSaida'] = etPais.get()
                            else:
                                pais['rota'] = etPais.get()
                                # insere o país, os pontos, as datas e os horários dos pontos
                                self.adiciona_ponto(pais, trecho[:4], trecho[4:])
                            index += 1
        
        # abre o template e adiciona os textos no documento
        

    
    # ADICIONA PONTO EM UM TRECHO ESPECÍFICO
    def adiciona_ponto(self, pais, trechoFrom, trechoTo):
        for trecho in self.parteData.trechos:
            if trecho['from'] == trechoFrom and trecho['to'] == trechoTo:
                trecho['paises'].append(pais)
        # print(self.parteData.trechos)

    # FAZ O UPLOAD DO PLANEJAMENTO QUANDO O USUÁRIO CLICA NO BOTÃO CORRESPONDENTE
    def adiciona_plan(self, trecho):
        file_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf")],  # somente pdf
            title="Selecione o planejamento em formato PDF"
        )
        if file_path:
            self.btAddPlan[trecho].destroy()
            lbPlan = Label(self.ctTrecho[trecho], text=file_path)
            lbPlan.pack(pady=10)
            self.btAddPais[trecho].pack(pady=10)
            self.parteData.get_plan_data(file_path, trecho)
    
    # ADICIONA PONTOS DE PAÍSES NO TRECHO DETERMINADO
    def adiciona_pais(self, trecho):
        ctPais = Frame(self.ctTrecho[trecho])  # frame que contem os dados do país
        ctPais.pack()
        lbPais = Label(ctPais, text = f"País: ")
        lbPais.pack(side='left', anchor='w')
        etPais = Entry(ctPais)
        etPais.pack(side='left', anchor='w')

        # ponto de entrada
        lbPtEntrada = Label(ctPais, text = f"Ponto de entrada: ")
        lbPtEntrada.pack(side='left', anchor='w')
        etPtEntrada = Entry(ctPais)
        etPtEntrada.pack(side='left', anchor='w')

        # ponto de saída
        lbPtSaida = Label(ctPais, text = f"Ponto de saída: ")
        lbPtSaida.pack(side='left', anchor='w')
        etPtSaida = Entry(ctPais)
        etPtSaida.pack(side='left', anchor='w')

        # rota
        lbRota = Label(ctPais, text = f"Rota: ")
        lbRota.pack(side='left', anchor='w')
        etRota = Entry(ctPais)
        etRota.pack(side='left', anchor='w')       
    

root = Tk()
Application(root)
root.mainloop()
