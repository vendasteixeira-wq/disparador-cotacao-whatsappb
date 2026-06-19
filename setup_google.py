"""
SETUP GOOGLE API — Pousada Estrela d'Água
Executa UMA VEZ para configurar as credenciais Google.
Depois o disparador gera Forms automaticamente.
"""
import subprocess, sys, os, webbrowser

def instalar(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

print("\n" + "="*55)
print("  CONFIGURAÇÃO GOOGLE API — Disparador de Cotação")
print("="*55)

# 1. Instalar dependências
print("\n[1/4] Instalando dependências Google...")
for pkg in ["google-auth", "google-auth-oauthlib", "google-auth-httplib2", "google-api-python-client"]:
    instalar(pkg)
print("      OK")

# 2. Instruções para criar credenciais
print("\n[2/4] Configurando acesso Google...")
print("""
  Você precisa criar as credenciais Google UMA VEZ.
  Siga os passos abaixo:

  1. Acesse: https://console.cloud.google.com/
  2. Crie um projeto (ex: "Disparador Cotacao")
  3. Vá em: APIs e Serviços > Biblioteca
  4. Ative: "Google Forms API" e "Google Drive API"
  5. Vá em: APIs e Serviços > Credenciais
  6. Clique: "+ Criar Credenciais" > "ID do cliente OAuth 2.0"
  7. Tipo: "Aplicativo para computador"
  8. Baixe o arquivo JSON e salve como:
     credentials.json  (na mesma pasta que este script)
  9. Execute este script novamente
""")

cred_path = os.path.join(os.path.dirname(__file__), "credentials.json")
if not os.path.exists(cred_path):
    print("  [!] credentials.json não encontrado.")
    print(f"      Coloque o arquivo em: {os.path.dirname(__file__)}")
    resp = input("\n  Abrir o console Google agora? (s/n): ").strip().lower()
    if resp == 's':
        webbrowser.open("https://console.cloud.google.com/apis/credentials")
    input("\n  Pressione Enter após colocar o credentials.json na pasta...")

# 3. Autenticar
if os.path.exists(cred_path):
    print("\n[3/4] Autenticando com Google...")
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.oauth2.credentials import Credentials
    import json

    SCOPES = [
        'https://www.googleapis.com/auth/forms.body',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]

    token_path = os.path.join(os.path.dirname(__file__), "token.json")
    flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(token_path, 'w') as f:
        f.write(creds.to_json())

    print("      Autenticado com sucesso!")
    print(f"      Token salvo em: {token_path}")

    print("\n[4/4] Testando conexão...")
    from googleapiclient.discovery import build
    drive = build('drive', 'v3', credentials=creds)
    about = drive.about().get(fields="user").execute()
    email = about['user']['emailAddress']
    print(f"      Conectado como: {email}")

    print("\n" + "="*55)
    print("  CONFIGURAÇÃO CONCLUÍDA!")
    print("  Agora inicie o disparador com INICIAR_DISPARADOR.bat")
    print("="*55 + "\n")
else:
    print("\n  [ERRO] credentials.json não encontrado. Tente novamente.")

input("\nPressione Enter para fechar...")
