import requests
import random
import string
import time
import hashlib

class MiningClient:
    BASE_URL = 'http://192.168.100.215:8000'

    def __init__(self):
        self.miner_address = self.generate_random_miner_address()
        self.miner_name = 'Miner_' + self.miner_address
        self.blocks_mined = 0
        self.errors_count = 0
        self.total_hashes = 0
        self.start_time = time.time()
        self.hash_rate = 0.0

    def generate_random_miner_address(self):
        """ Gera um endereço de minerador randômico de 8 dígitos """
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))

    def calculate_hash(self, data):
        """ Calcula o hash SHA-256 de uma string """
        sha256 = hashlib.sha256()
        sha256.update(data.encode('utf-8'))
        return sha256.hexdigest()

    def mine_block(self):
        """ Minerar um novo bloco na blockchain """
        url = '{}/mine'.format(self.BASE_URL)
        headers = {'Miner-Address': self.miner_address}

        start_time = time.time()
        start_hash_count = self.total_hashes

        difficulty = 5  # Número de zeros no início do hash
        hash_prefix = '0' * difficulty
        nonce = 0

        while True:
            nonce += 1
            hash_result = self.calculate_hash('{}'.format(nonce))
            self.total_hashes += 1

            if hash_result.startswith(hash_prefix):
                end_time = time.time()
                time_elapsed = end_time - start_time

                print('Novo bloco minerado!')
                print('Hash:', hash_result)
                print('Nonce:', nonce)
                self.blocks_mined += 1

                # Envia a solicitação para minerar o bloco
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    print('Bloco minerado com sucesso!')
                else:
                    print('Erro ao minerar bloco:', response.text)
                    self.errors_count += 1
                break

            # Atualiza o hash rate a cada 1000 hashes
            if self.total_hashes % 1000 == 0:
                time_elapsed = time.time() - start_time
                if time_elapsed > 0:  # Garante que o tempo não seja zero
                    self.hash_rate = self.total_hashes / time_elapsed

        # Atualiza o hash rate após minerar o bloco
        time_elapsed = time.time() - start_time
        if time_elapsed > 0:  # Garante que o tempo não seja zero
            self.hash_rate = self.total_hashes / time_elapsed

        # Converte H/s para GH/s
        self.hash_rate /= 1000000000  # Divida para obter GH/s

    def save_metrics(self):
        """ Salva as métricas em um arquivo de texto """
        filename = 'miner_metrics_{}.txt'.format(self.miner_address)
        with open(filename, 'a') as file:  # Mude 'w' para 'a'
            file.write('Nome do Minerador: {}\n'.format(self.miner_name))
            file.write('Endereço do Minerador: {}\n'.format(self.miner_address))
            file.write('Blocos Minerados: {}\n'.format(self.blocks_mined))
            file.write('Número de Erros de Mineração: {}\n'.format(self.errors_count))
            file.write('Tempo Médio para Minerar Bloco: {:.2f} segundos\n'.format(
                (time.time() - self.start_time) / self.blocks_mined if self.blocks_mined > 0 else 0))
            file.write('Hashs por Segundo: {:.6f} GH/s\n'.format(self.hash_rate))
            file.write('------------------------------\n')  # Adiciona uma linha separadora para clareza
            file.flush()  # Garante que os dados sejam escritos no disco

    def resolve_conflicts(self):
        """ Solicita resolução de conflitos para sincronizar com a cadeia mais longa """
        url = '{}/nodes/resolve'.format(self.BASE_URL)
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(data['message'])
            self.save_metrics()
        else:
            print('Erro ao resolver conflitos:', response.text)

    def run(self):
        """ Inicia o processo de mineração e resolução de conflitos """
        try:
            while True:
                print('Tentando minerar um novo bloco...')
                self.mine_block()
                self.resolve_conflicts()
                time.sleep(30)  # Tempo de espera entre as tentativas de mineração
        finally:
            print('Concluído')
            # Salva as métricas finais quando o loop é finalizado
            self.save_metrics()

if __name__ == '__main__':
    client = MiningClient()
    client.run()
