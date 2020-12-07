# Alunos:       Allann Gois Hoffmann | Artur de Meira Rodrigues | Mateus Cruvinel Cerqueira
# Matricula:         180029789       |        180013688         |        180054368

from player.parser import parse_mpd
from r2a.ir2a import IR2A
import time


class R2ABrabo(IR2A):

    # Atributos da classe.
    def __init__(self, id):
        IR2A.__init__(self, id)
        self.request_time = 0
        self.qualidades = []
        self.buffer = 0
        self.measured_throughput = 0
        self.minimo = 46980
        self.measured = 46980

    # Função para captar o tempo de inicio para a requisição XML.
    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()

        self.send_down(msg)

    #  Função para captar os dados recebidos do XML,
    #  1 - Contem funções para captar as qualidades de video,
    #  2 - Obter a largura de banda da requisição do XML,
    #  3 - E calculo de um valor minimo de qualidade do video,
    #      salva a menor qualidade como sendo o valor retornado da função de numero 2
    def handle_xml_response(self, msg):

        # 1
        parsed = parse_mpd(msg.get_payload())
        self.qualidades = parsed.get_qi()
        self.minimo = self.qualidades[0]
        self.measured = self.qualidades[0]


        # 2
        self.measured_throughput = msg.get_bit_length() / (time.perf_counter() - self.request_time)

        # 3
        for value in self.qualidades:
            if self.measured_throughput >= value:
                self.minimo = value

        print(self.minimo)

        self.send_up(msg)

    #  Função para fazer a requisição do segmento de video,
    #  1 - Captar e armazenar o tamanho do buffer,
    #  2 - Adicionar a qualidade de video escolhida pela função "self.calculo()".
    def handle_segment_size_request(self, msg):
        self.request_time = time.perf_counter()

        # 1
        temp = self.whiteboard.get_playback_buffer_size()
        if len(temp) > 0:
            self.buffer = temp[len(temp)-1][1]
        else:
            self.buffer = 0

        # 2
        msg.add_quality_id(self.calculo())

        self.send_down(msg)

    #  Função para captar a resposta do segmento obtido,
    #  1 - Contem funções para captar a largura de banda obtida na requisição anterior.
    def handle_segment_size_response(self, msg):

        # 1
        self.measured_throughput = msg.get_bit_length() / (time.perf_counter() - self.request_time)

        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

    #  Função para escolher a qualidade de video a ser baixada
    #  por meio de comparações entre tamanho do buffer e pela
    #  largura de banda obtida na requisição de video anterior,
    #  1 - Comparação entre tamanho de buffer e largura de banda.
    def calculo(self):

        if self.buffer < 4:
            for value in self.qualidades:
                if (self.measured_throughput/3) >= value:
                    self.measured = value

        elif self.buffer >= 4 and self.buffer < 6:
            for value in self.qualidades:
                if (self.measured_throughput/(2.5)) >= value:
                    self.measured = value

        elif self.buffer >= 6 and self.buffer < 10:
            for value in self.qualidades:
                if (self.measured_throughput/2) >= value:
                    self.measured = value

        elif self.buffer >= 10 and self.buffer < 12:
            for value in self.qualidades:
                if (self.measured_throughput/1.5) >= value:
                    self.measured = value

        # Caso o buffer esteja "alto", a qualidade escolhida será a maior possivel
        else:
            for value in self.qualidades:
                if self.measured_throughput >= value:
                    self.measured = value

        # Caso a largura de banda seja menor que a qualidade minima,
        # será escolhida a qualidade minima determinada no inicio.
        if self.measured_throughput <= self.qualidades[0]:
            self.measured = self.minimo

        return self.measured
