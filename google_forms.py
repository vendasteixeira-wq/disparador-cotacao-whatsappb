"""
Módulo de geração de Google Forms para cotações.
Usado pelo app.py do disparador.
"""
import os, json, sqlite3
from datetime import datetime

SCOPES = [
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

BASE_DIR   = os.path.dirname(__file__)
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")
DB_PATH    = os.path.join(BASE_DIR, "insumos_estrela.db")

def get_creds():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    if not os.path.exists(TOKEN_PATH):
        return None
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    return creds

def google_configurado():
    return os.path.exists(TOKEN_PATH)

def gerar_form_cotacao(itens_selecionados, titulo_extra=""):
    """
    itens_selecionados: lista de dicts {codigo, nome, unidade, qtd}
    Retorna: {form_url, edit_url, sheet_url, form_id}
    """
    from googleapiclient.discovery import build

    creds = get_creds()
    if not creds:
        raise Exception("Google não configurado. Execute setup_google.py primeiro.")

    forms_svc = build('forms', 'v1', credentials=creds)
    drive_svc = build('drive', 'v3', credentials=creds)

    hoje   = datetime.now().strftime("%d/%m/%Y")
    titulo = f"Cotação Estrela d'Água — {hoje}{' — '+titulo_extra if titulo_extra else ''}"

    # ── Criar formulário base ──────────────────────────────────────
    form_body = {
        "info": {
            "title": titulo,
            "documentTitle": titulo
        }
    }
    form = forms_svc.forms().create(body=form_body).execute()
    form_id = form['formId']

    # ── Montar perguntas ───────────────────────────────────────────
    requests = []
    idx = 0

    # Descrição inicial
    requests.append({
        "createItem": {
            "item": {
                "title": "INSTRUÇÕES",
                "description": (
                    f"Preencha os preços unitários dos itens abaixo.\n"
                    f"Deixe em branco os itens que você não fornece.\n"
                    f"Data da solicitação: {hoje}\n"
                    f"Empresa: Pousada Estrela d'Água — Porto Seguro/BA\n"
                    f"E-mail para dúvidas: controladoria1@estreladagua.tur.br"
                ),
                "textItem": {}
            },
            "location": {"index": idx}
        }
    })
    idx += 1

    # Dados do fornecedor
    for label in ["Nome da empresa / Fornecedor", "Telefone / WhatsApp", "E-mail para contato"]:
        requests.append({
            "createItem": {
                "item": {
                    "title": label,
                    "questionItem": {
                        "question": {
                            "required": label == "Nome da empresa / Fornecedor",
                            "textQuestion": {"paragraph": False}
                        }
                    }
                },
                "location": {"index": idx}
            }
        })
        idx += 1

    # Separador por grupo
    grupos_vistos = []
    for item in itens_selecionados:
        grupo = item.get('grupo', '')
        if grupo and grupo not in grupos_vistos:
            grupos_vistos.append(grupo)
            requests.append({
                "createItem": {
                    "item": {
                        "title": f"━━━ {grupo} ━━━",
                        "textItem": {}
                    },
                    "location": {"index": idx}
                }
            })
            idx += 1

        qtd_str = f"{item['qtd']} {item['unidade']}" if item.get('qtd') else f"_____ {item['unidade']}"
        label_preco = f"{item['nome']}  |  Qtd: {qtd_str}  |  Unid: {item['unidade']}"

        # Preço unitário
        requests.append({
            "createItem": {
                "item": {
                    "title": f"Preço unitário (R$) — {label_preco}",
                    "questionItem": {
                        "question": {
                            "required": False,
                            "textQuestion": {"paragraph": False}
                        }
                    }
                },
                "location": {"index": idx}
            }
        })
        idx += 1

        # Observação
        requests.append({
            "createItem": {
                "item": {
                    "title": f"Obs/Marca/Validade — {item['nome']}",
                    "questionItem": {
                        "question": {
                            "required": False,
                            "textQuestion": {"paragraph": False}
                        }
                    }
                },
                "location": {"index": idx}
            }
        })
        idx += 1

    # Prazo de validade da cotação
    requests.append({
        "createItem": {
            "item": {
                "title": "Validade desta cotação (em dias)",
                "questionItem": {
                    "question": {
                        "required": False,
                        "textQuestion": {"paragraph": False}
                    }
                }
            },
            "location": {"index": idx}
        }
    })
    idx += 1

    # Condições de pagamento
    requests.append({
        "createItem": {
            "item": {
                "title": "Condições de pagamento oferecidas",
                "questionItem": {
                    "question": {
                        "required": False,
                        "choiceQuestion": {
                            "type": "CHECKBOX",
                            "options": [
                                {"value": "À vista"},
                                {"value": "7 dias"},
                                {"value": "14 dias"},
                                {"value": "21 dias"},
                                {"value": "30 dias"},
                                {"value": "45 dias"},
                                {"value": "60 dias"},
                                {"value": "Boleto"},
                                {"value": "PIX"},
                                {"value": "Cartão"},
                            ]
                        }
                    }
                }
            },
            "location": {"index": idx}
        }
    })
    idx += 1

    # Aplicar todas as perguntas
    forms_svc.forms().batchUpdate(
        formId=form_id,
        body={"requests": requests}
    ).execute()

    # ── Ativar coleta de respostas em Sheets ──────────────────────
    forms_svc.forms().batchUpdate(
        formId=form_id,
        body={
            "requests": [{
                "updateSettings": {
                    "settings": {"quizSettings": {"isQuiz": False}},
                    "updateMask": "quizSettings"
                }
            }]
        }
    ).execute()

    # Pegar URL pública do form
    form_info  = forms_svc.forms().get(formId=form_id).execute()
    form_url   = form_info.get('responderUri', f"https://docs.google.com/forms/d/{form_id}/viewform")
    edit_url   = f"https://docs.google.com/forms/d/{form_id}/edit"

    # Criar planilha de respostas vinculada
    sheet_id   = None
    sheet_url  = None
    try:
        sheets_svc = build('sheets', 'v4', credentials=creds)
        sheet_name = f"Respostas — {titulo[:50]}"
        spreadsheet = sheets_svc.spreadsheets().create(body={
            "properties": {"title": sheet_name}
        }).execute()
        sheet_id  = spreadsheet['spreadsheetId']
        sheet_url = spreadsheet['spreadsheetUrl']

        # Vincular form à planilha
        forms_svc.forms().batchUpdate(
            formId=form_id,
            body={
                "requests": [{
                    "createResponsePart": {
                        "responseDestination": {
                            "spreadsheetId": sheet_id
                        }
                    }
                }]
            }
        ).execute()
    except Exception as e:
        print(f"Aviso: não foi possível vincular planilha: {e}")

    return {
        "form_id":  form_id,
        "form_url": form_url,
        "edit_url": edit_url,
        "sheet_id": sheet_id,
        "sheet_url": sheet_url,
        "titulo":   titulo
    }
