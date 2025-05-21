import requests
import json
import csv
import os
import chardet

# URL da API
URL_API = "http://apps.superlogica.net/imobiliaria/api/contratos"

# Diretório de salvamento
diretorio = r"C:\Users\dario\kenlo_files"
os.makedirs(diretorio, exist_ok=True)  # Garante que o diretório exista

# Cabeçalhos da requisição (ajusta conforme necessário)
headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'app_token': 'ab68e956-0ba7-4ae9-8fed-385ee2d64992',
    'access_token': '5f47ca55-ad34-465b-bc58-27cf6f0b4df2'
}

# Faz a requisição GET para a API
response = requests.get(URL_API, headers=headers)

# Verifica se a requisição foi bem-sucedida
if response.status_code != 200:
    print(f"Erro na requisição: {response.status_code} - {response.text}")
    exit()

# Detecta a codificação da resposta
encoding_detectado = chardet.detect(response.content).get('encoding', 'utf-8')
print(f"Codificação detectada: {encoding_detectado}")

# Decodifica o conteúdo usando a codificação detectada
try:
    response_text = response.content.decode(encoding_detectado or "utf-8")
except UnicodeDecodeError:
    print("Erro ao decodificar a resposta, tentando com UTF-8.")
    response_text = response.content.decode("utf-8", errors="replace")

# Converte o texto para JSON
try:
    response_json = json.loads(response_text)
except json.JSONDecodeError:
    print("Erro ao converter resposta para JSON.")
    exit()

# Extrai os dados do campo "data"
data = response_json.get("data", [])

if not isinstance(data, list) or not data:
    print("Campo 'data' não encontrado ou não é uma lista válida.")
    exit()

# 📝 Salvar JSON completo
caminho_json = os.path.join(diretorio, "contratos_oficial.json")
with open(caminho_json, "w", encoding="utf-8", errors='ignore') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
print(f"Arquivo JSON salvo em: {caminho_json}")

# 📊 Criar e salvar CSV
caminho_csv = os.path.join(diretorio, "contratos_oficial.csv")

# Função para extrair todas as chaves de um dicionário (incluindo aninhados)


def extrair_chaves(dicionario, prefixo=""):
    chaves = []
    for chave, valor in dicionario.items():
        chave_completa = f"{prefixo}.{chave}" if prefixo else chave
        if isinstance(valor, dict):
            chaves.extend(extrair_chaves(valor, chave_completa))
        elif isinstance(valor, list) and valor and isinstance(valor[0], dict):
            chaves.extend(extrair_chaves(valor[0], chave_completa))
        else:
            chaves.append(chave_completa)
    return chaves


# Extrai todas as chaves únicas dos dados
chaves_unicas = set()
for registro in data:
    if isinstance(registro, dict):
        chaves_unicas.update(extrair_chaves(registro))

# Ordena as chaves para manter a consistência no CSV
chaves_unicas = sorted(chaves_unicas)

# Função para aplanar um dicionário (transformar aninhados em chaves compostas)


def aplanar_dicionario(dicionario, prefixo=""):
    aplanado = {}
    for chave, valor in dicionario.items():
        chave_completa = f"{prefixo}.{chave}" if prefixo else chave
        if isinstance(valor, dict):
            aplanado.update(aplanar_dicionario(valor, chave_completa))
        elif isinstance(valor, list) and valor and isinstance(valor[0], dict):
            for i, item in enumerate(valor):
                aplanado.update(aplanar_dicionario(
                    item, f"{chave_completa}[{i}]"))
        else:
            aplanado[chave_completa] = valor
    return aplanado


# Escreve o CSV
with open(caminho_csv, "w", newline="", encoding="utf-8", errors='ignore') as f:
    writer = csv.DictWriter(f, fieldnames=chaves_unicas)
    writer.writeheader()

    # Percorre os registros principais
    for registro in data:
        if isinstance(registro, dict):
            registro_aplanado = aplanar_dicionario(registro)
            writer.writerow(registro_aplanado)

print(f"Arquivo CSV salvo em: {caminho_csv}")
