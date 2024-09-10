import requests
import random
import string
import time
import hashlib
import psutil  # Para monitorar o uso da CPU

class MiningClient:
    
    BASE_URL = 'http://192.168.100.215:8000'

    def __init__(self):
        self.repeated_transmissions_count = 0  # atributo para contagem de transmissões repetidas
        self.miner_address = self.generate_random_miner_address()
        self.miner_name = 'Miner_' + self.miner_address
        self.blocks_mined = 0
        self.errors_count = 0
        self.total_hashes = 0
        self.successful_mining_attempts = 0
        self.start_time = time.time()
        self.hash_rate = 0.0
        self.retransmissions_count = 0  # Adiciona o contador de transmissões repetidas
        self.inicio_time = time.time()  # Tempo de início do minerador
        
    def get_uptime(self):
        """ Calcula o tempo de disponibilidade (uptime) do minerador """
        return time.time() - self.inicio_time    

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

        while True:
            try:
                response = requests.get('{}/chain'.format(self.BASE_URL))
                if response.status_code == 200:
                    data = response.json()
                    last_block = data['chain'][-1]
                    last_proof = last_block['proof']
                else:
                    print('Erro ao obter a cadeia: {}'.format(response.text))
                    return
            except requests.exceptions.RequestException as e:
                print('Erro ao obter a cadeia:', e)
                self.retransmissions_count += 1  # Incrementa o contador de transmissões repetidas 
                return

            difficulty = 5
            hash_prefix = '0' * difficulty
            nonce = 0

            while True:
                nonce += 1
                hash_result = self.calculate_hash('{}{}{}'.format(last_proof, nonce, time.time()))
                self.total_hashes += 1

                if hash_result.startswith(hash_prefix):
                    end_time = time.time()
                    time_elapsed = end_time - self.start_time

                    print('Novo bloco minerado!')
                    print('Hash: {}'.format(hash_result))
                    print('Nonce: {}'.format(nonce))
                    self.blocks_mined += 1
                    self.successful_mining_attempts += 1  # Atualiza tentativas de mineração bem-sucedidas

                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        print('Bloco minerado com sucesso!')
                    else:
                        print('Erro ao minerar bloco: {}'.format(response.text))
                        self.errors_count += 1
                    break

                if self.total_hashes % 1000 == 0:
                    time_elapsed = time.time() - self.start_time
                    if time_elapsed > 0:
                        self.hash_rate = self.total_hashes / time_elapsed

            time_elapsed = time.time() - self.start_time
            if time_elapsed > 0:
                self.hash_rate = self.total_hashes / time_elapsed

            self.hash_rate /= 1000000000  # Converte para GH/s

            # Atualiza a taxa de sucesso
            self.update_success_rate()

            # Espera antes de tentar minerar novamente
            time.sleep(30)

    def update_success_rate(self):
        """ Atualiza a taxa de sucesso de mineração e envia para o servidor """
        total_attempts = self.blocks_mined + self.errors_count
        success_rate = (self.successful_mining_attempts / total_attempts * 100) if total_attempts > 0 else 0
        cpu_usage = self.get_cpu_usage()  # Obter a utilização da CPU
        uptime = self.get_uptime()

        url = '{}/miners/metrics'.format(self.BASE_URL)
        metrics = {
            'miner_address': self.miner_address,
            'miner_name': self.miner_name,
            'blocks_mined': self.blocks_mined,
            'errors_count': self.errors_count,
            'total_hashes': self.total_hashes,
            'hash_rate': self.hash_rate,
            'total_mining_time': time.time() - self.start_time,
            'retransmission_time': self.calculate_retransmission_time(),
            'reward': 0,
            'success_rate': success_rate,  #  taxa de sucesso
            'cpu_usage': cpu_usage,  # utilização da CPU
            'cpu_frequency_ghz': self.get_cpu_frequency(),  # Inclui a frequência da CPU
            'repeat_transaction_miner': self.retransmissions_count,  # Adiciona o contador de transmissões repetidas
            'uptime': uptime  # Adiciona o uptime nas métricas            
        }

        try:
            response = requests.post(url, json=metrics)
            if response.status_code == 201:
                print('Métricas do minerador salvas com sucesso!')
                self.retransmissions_count = 0  # Zera o contador de transmissões repetidas após envio bem-sucedido                
            else:
                print('Erro ao salvar métricas do minerador: {}'.format(response.text))
        except Exception as e:
            print('Erro ao enviar métricas: {}'.format(e))

    def calculate_retransmission_time(self):
        """ Obtém o tempo de retransmissão (RTT) do minerador para o servidor usando HTTP. """
        url = '{}/ping'.format(self.BASE_URL)
        try:
            start_time = time.time()
            response = requests.get(url, timeout=60)
            end_time = time.time()
            rtt = (end_time - start_time) * 1000
            if response.status_code == 200:
                return rtt
            else:
                print('Erro ao testar a conexão com o servidor.')
                return 0
        except requests.exceptions.RequestException as e:
            print('Erro ao calcular o tempo de retransmissão:', e)
            return 0

    def resolve_conflicts(self):
        """ Solicita resolução de conflitos para sincronizar com a cadeia mais longa """
        url = '{}/nodes/resolve'.format(self.BASE_URL)
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(data['message'])
            self.update_success_rate()  # Atualiza as métricas após resolver conflitos
        else:
            print('Erro ao resolver conflitos: {}'.format(response.text))

    def run(self):
        """ Inicia o processo de mineração e resolução de conflitos """
        try:
            while True:
                print('Tentando minerar um novo bloco...')
                self.mine_block()
                self.resolve_conflicts()
        finally:
            print('Concluído')
            # Salva as métricas finais quando o loop é finalizado
            self.update_success_rate()

    def get_cpu_usage(self):
        """ Obtém a utilização atual da CPU em porcentagem """
        return psutil.cpu_percent(interval=1)
    
    def get_cpu_frequency(self):
        """Obtém a frequência máxima da CPU em GHz."""
        freq = psutil.cpu_freq()
        return freq.max / 1000  # Converte MHz para GHz


    

if __name__ == '__main__':
    client = MiningClient()
    client.run()
