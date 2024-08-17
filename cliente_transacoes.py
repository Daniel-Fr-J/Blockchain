import requests
import random
import time
import string

class TransactionClient:
    BASE_URL = 'http://192.168.100.215:8000'

    def __init__(self):
        self.total_requests = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.start_time = time.time()
        self.client_name = self.generate_random_name()  # Gerar nome aleatório para o cliente

    def generate_random_name(self):
        """ Gera um nome aleatório para o cliente """
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

    def create_transaction(self, sender, recipient, amount):
        """ Adiciona uma nova transação à blockchain """
        url = '{}/transactions/new'.format(self.BASE_URL)
        start_time = time.time()
        response = requests.post(url, json={
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })
        response_time = time.time() - start_time

        self.total_requests += 1
        self.total_response_time += response_time

        if response.status_code == 201:
            print(response.json()['message'])
        else:
            print('Erro ao adicionar transação:', response.text)
            self.error_count += 1

        return response.status_code

    def view_chain(self):
        """ Visualiza a cadeia de blocos atual """
        url = '{}/chain'.format(self.BASE_URL)
        start_time = time.time()
        response = requests.get(url)
        response_time = time.time() - start_time

        self.total_requests += 1
        self.total_response_time += response_time

        if response.status_code == 200:
            data = response.json()
            print('Cadeia de blocos:')
            for block in data['chain']:
                print(block)
            print('Comprimento da cadeia:', data['length'])
        else:
            print('Erro ao visualizar a cadeia:', response.text)
            self.error_count += 1

    def generate_random_transaction(self):
        """ Gera uma transação aleatória """
        sender = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        recipient = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        amount = random.randint(1, 100)  # Quantia aleatória entre 1 e 100
        return sender, recipient, amount

    def save_metrics(self):
        """ Salva as métricas em um arquivo de texto personalizado com o nome do cliente """
        
        filename = 'client_metrics__{}.txt'.format(self.client_name)
        with open(filename, 'w') as file:
            file.write('Tempo Médio de Resposta: {:.4f} segundos\n'.format(
                self.total_response_time / self.total_requests if self.total_requests > 0 else 0))
            file.write('Número Total de Requisições: {}\n'.format(self.total_requests))
            file.write('Número de Erros nas Requisições: {}\n'.format(self.error_count))
            file.flush()

if __name__ == '__main__':
    client = TransactionClient()

    # Envia um número aleatório de transações a cada 30 segundos
    try:
        while True:
            num_transactions = random.randint(1, 20)  # Número aleatório de transações entre 1 e 20
            for _ in range(num_transactions):
                sender, recipient, amount = client.generate_random_transaction()
                print('Enviando transação: Sender={}, Recipient={}, Amount={}'.format(sender, recipient, amount))
                client.create_transaction(sender=sender, recipient=recipient, amount=amount)
            
            # Visualiza a cadeia de blocos após as transações (opcional)
            client.view_chain()
            
            # Pausa por 30 segundos
            time.sleep(30)
    finally:
        client.save_metrics()  # Salva as métricas ao terminar o processo
