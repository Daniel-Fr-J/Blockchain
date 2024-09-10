from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import hashlib
from time import time
import requests
import pymysql
import os

class Blockchain:
    # Variável de classe
    rec = 0
    ret=0
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.rewards_file = 'miner_rewards.txt'
        self.metrics_file = 'metrics.txt'
        self.start_time = time()
        self.initialize_rewards_file()
        self.initialize_metrics_file()
        self.new_block(previous_hash='1', proof=100)  # Cria o bloco gênesis
        self.db_connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='validado'
        )
        self.db_cursor = self.db_connection.cursor()
        self.create_metrics_table()
        self.start_time = time()  # Define o tempo de início
        
    def create_metrics_table(self):
        """ Cria a tabela de métricas no banco de dados se não existir """
        create_table_query = """
        CREATE TABLE IF NOT EXISTS miner_metrics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            miner_address VARCHAR(255) NOT NULL,
            miner_name VARCHAR(255) NOT NULL,
            blocks_mined INT NOT NULL,
            errors_count INT NOT NULL,
            total_hashes BIGINT NOT NULL,
            hash_rate FLOAT NOT NULL,
            total_mining_time FLOAT NOT NULL,
            retransmission_time FLOAT NOT NULL,
            reward FLOAT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success_rate FLOAT NOT NULL,
            cpu_usage FLOAT NOT NULL,  
            cpu_frequency_ghz FLOAT NOT NULL,
            repeat_transaction_miner FLOAT NOT NULL,
            uptime FLOAT NOT NULL
        )
        """
        try:
            self.db_cursor.execute(create_table_query)
            self.db_connection.commit()
        except pymysql.MySQLError as e:
            print('Erro ao criar tabela de métricas: {}'.format(e))

    def record_miner_metrics(self, miner_address, miner_name, blocks_mined, errors_count, total_hashes, hash_rate, total_mining_time, retransmission_time, reward=None, success_rate=None,cpu_usage=None, cpu_frequency_ghz=None, repeat_transaction_miner=None, uptime=None):
        """ Registra as métricas do minerador no banco de dados """
        reward = Blockchain.rec  # Usa a variável de classe rec se reward não for fornecido
        if reward > 0:            
            insert_query = """
            INSERT INTO miner_metrics (miner_address, miner_name, blocks_mined, errors_count, total_hashes, hash_rate, total_mining_time, retransmission_time, reward,success_rate,cpu_usage, cpu_frequency_ghz, repeat_transaction_miner, uptime)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            try:
                self.db_cursor.execute(insert_query, (miner_address, miner_name, blocks_mined, errors_count, total_hashes, hash_rate, total_mining_time, retransmission_time, reward, success_rate, cpu_usage, cpu_frequency_ghz, repeat_transaction_miner, uptime))
                self.db_connection.commit()
            except Exception as e:
                print('Erro ao registrar métricas no banco de dados: {}'.format(e))

        
    def new_block(self, proof, previous_hash=None, miner_address=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []
        self.chain.append(block)
##        if block['index'] > 1 and miner_address:
##            reward = self.calculate_reward(len(block['transactions']))                            
##            total_mining_time = time() - self.start_time
##            retransmission_time = self.calculate_retransmission_time
##            self.record_reward(miner_address, reward)
##            self.record_miner_metrics(
##                miner_address,
##                'Miner Name',  # Nome fictício, deve ser passado ou calculado
##                1,  # Bloco minerado
##                0,  # Erros
##                0,  # Total de hashes
##                0,  # Taxa de hash
##                total_mining_time,                
##                retransmission_time,
##                reward
##            )
        # Apenas registra métricas e recompensas se não for o bloco gênesis
        if block['index'] > 1 and miner_address:
            reward = self.calculate_reward(len(block['transactions']))
            self.record_reward(miner_address, reward)
            self.save_metrics()
        
        return block
            


##    def new_block(self, proof, previous_hash=None, miner_address=None):
##        block = {
##            'index': len(self.chain) + 1,
##            'timestamp': time(),
##            'transactions': self.current_transactions,
##            'proof': proof,
##            'previous_hash': previous_hash or self.hash(self.chain[-1]),
##        }
##        self.current_transactions = []
##        self.chain.append(block)
##        if block['index'] > 1 and miner_address:
##            reward = self.calculate_reward(len(block['transactions']))
##            self.record_reward(miner_address, reward)
##        self.save_metrics()
##        return block

    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = '{}{}'.format(last_proof, proof).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    @property
    def last_block(self):
        return self.chain[-1]

    def get_chain(self):
        return self.chain

    def replace_chain(self, new_chain):
        if len(new_chain) > len(self.chain):
            self.chain = new_chain
            return True
        return False

    def initialize_rewards_file(self):
        """ Cria o arquivo de recompensas se não existir """
        if not os.path.isfile(self.rewards_file):
            with open(self.rewards_file, mode='w') as file:
                file.write('Miner Address, Amount\n')

    def record_reward(self, miner_address, amount):
        """ Registra a recompensa no arquivo TXT """
        with open(self.rewards_file, mode='a') as file:
            file.write('{}: {}\n'.format(miner_address, amount))

    def calculate_reward(self, num_transactions):
        """ Calcula a recompensa com base no número de transações no bloco """
        if num_transactions > 10:  # Bloco grande
            Blockchain.rec = 1 
            return 1
        elif num_transactions > 5:  # Bloco médio
            Blockchain.rec = 0.5
            return 0.5
        else:  # Bloco pequeno
            Blockchain.rec = 0.2
            return 0.2

    def initialize_metrics_file(self):
        """ Cria o arquivo de métricas se não existir e escreve o cabeçalho """
        if not os.path.isfile(self.metrics_file):
            with open(self.metrics_file, mode='w') as file:
                file.write('Comprimento da Cadeia, Tempo de Geração de Blocos, Número de Transações por Bloco, Taxa de Transações Confirmadas, Recompensas Acumuladas\n')

    def save_metrics(self):
        """ Salva as métricas da blockchain em um arquivo TXT """
        # Calcular as métricas
        current_time = time()
        block_times = [block['timestamp'] for block in self.chain]
        block_generation_time = (block_times[-1] - block_times[0]) / (len(self.chain) - 1) if len(self.chain) > 1 else 0
        num_transactions_per_block = [len(block['transactions']) for block in self.chain]
        avg_num_transactions_per_block = sum(num_transactions_per_block) / len(num_transactions_per_block) if num_transactions_per_block else 0
        total_transactions = sum(num_transactions_per_block)
        elapsed_time = current_time - self.start_time
        confirmed_transactions_per_time = total_transactions / elapsed_time if elapsed_time > 0 else 0

        # Calcular a recompensa total e média
        total_rewards = sum(self.calculate_reward(len(block['transactions'])) for block in self.chain)
        avg_reward_per_block = total_rewards / len(self.chain) if len(self.chain) > 1 else 0

        metrics = (
            len(self.chain),
            block_generation_time,
            avg_num_transactions_per_block,
            confirmed_transactions_per_time,
            total_rewards  # Total de recompensas acumuladas
        )

        # Adicionar métricas ao arquivo
        with open(self.metrics_file, mode='a') as file:
            file.write(', '.join(map(str, metrics)) + '\n')
    def close(self):
       self.db_cursor.close()
       self.db_connection.close()  

class RequestHandler(BaseHTTPRequestHandler):
    blockchain = Blockchain()
    port = 8000  # Porta do servidor, pode ser ajustada conforme necessário

    def _send_response(self, response, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def do_GET(self):
        if self.path == '/chain':
            response = {
                'chain': self.blockchain.get_chain(),
                'length': len(self.blockchain.get_chain())
            }
            self._send_response(response)
        elif self.path == '/mine':
            if not self.blockchain.current_transactions:
                self.send_error(400, 'Nenhuma transação para minerar')
                return

            last_proof = self.blockchain.last_block['proof']
            proof = self.blockchain.proof_of_work(last_proof)
            previous_hash = self.blockchain.hash(self.blockchain.last_block)
            
            # Adiciona o endereço do minerador
            miner_address = self.headers.get('Miner-Address', 'unknown')
            block = self.blockchain.new_block(proof, previous_hash, miner_address)
            
            response = {
                'message': 'Novo bloco minerado!',
                'index': block['index'],
                'transactions': block['transactions'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash']
            }
            self._send_response(response)
        elif self.path == '/nodes/resolve':
            response = self.resolve_conflicts()
            self._send_response(response)
            
        elif self.path == '/ping':
            # Endpoint /ping para verificar latência
            start_time = time()
            response = {'message': 'Pong'}
            end_time = time()
            rtt = (end_time - start_time) * 1000  # Converte para milissegundos
            response['rtt'] = rtt
            Blockchain.ret= rtt
            self._send_response(response)    
        else:
            self.send_error(404, 'Not Found')

    def do_POST(self):
        if self.path == '/transactions/new':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            values = json.loads(post_data.decode())
            required = ['sender', 'recipient', 'amount']
            if not all(k in values for k in required):
                self.send_error(400, 'Faltam parâmetros')
                return
            index = self.blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
            response = {'message': 'Transação adicionada ao bloco {}'.format(index)}
            self._send_response(response, 201)
        elif self.path == '/miners/metrics':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            metrics = json.loads(post_data.decode())
            required = ['miner_address', 'miner_name', 'blocks_mined', 'errors_count', 'total_hashes', 'hash_rate', 'total_mining_time',   'retransmission_time', 'reward', 'success_rate']
            if not all(k in metrics for k in required):
                self.send_error(400, 'Faltam parâmetros')
                return
            self.blockchain.record_miner_metrics(
                metrics['miner_address'],
                metrics['miner_name'],
                metrics['blocks_mined'],
                metrics['errors_count'],
                metrics['total_hashes'],
                metrics['hash_rate'],
                metrics['total_mining_time'],                                
                metrics['retransmission_time'],
                metrics['reward'],
                metrics['success_rate'],
                metrics['cpu_usage'],  # uso da CPU
                metrics['cpu_frequency_ghz'],  # Frequência da CPU
                metrics['repeat_transaction_miner'],# repetições na transmissão de mineração
                metrics['uptime']
            )
            if (Blockchain.rec>0):
                response = {'message': 'Métricas do minerador salvas com sucesso'}
                self._send_response(response, 201)
            else:
                response = {'message': 'Off'}
                self._send_response(response, 200)
        else:
            self.send_error(404, 'Not Found')

    def resolve_conflicts(self):
        neighbours = self.get_neighbours()
        new_chain = None
        max_length = len(self.blockchain.get_chain())

        for neighbour in neighbours:
            try:
                response = requests.get('{}/chain'.format(neighbour))
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
            except requests.RequestException:
                continue

        if new_chain:
            self.blockchain.replace_chain(new_chain)
            return {'message': 'Cadeia substituída com sucesso', 'new_chain': new_chain}
        else:
            return {'message': 'Nenhuma substituição necessária'}

    def valid_chain(self, chain):
        last_block = chain[0]
        index = 1

        while index < len(chain):
            block = chain[index]
            if block['previous_hash'] != self.hash(last_block):
                return False
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            index += 1

        return True

    def get_neighbours(self):
        return [
            'http://localhost:{}'.format(self.port + 1),
            'http://localhost:{}'.format(self.port + 2)
        ]

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Iniciando o servidor na porta {}...'.format(port))
    httpd.serve_forever()

if __name__ == "__main__":
    run(port=RequestHandler.port)
