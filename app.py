from flask import Flask, render_template, request, jsonify
import pywhatkit, time, re, json, os, sqlite3
from datetime import datetime

app = Flask(__name__)

DB_PATH  = os.path.join(os.path.dirname(__file__), "insumos_estrela.db")
LOG_FILE = os.path.join(os.path.dirname(__file__), "disparos.log")

CONTATOS_PADRAO = [
    {"nome": "Aipim Mix",                  "numero": "+557381066474",  "ativo": True},
    {"nome": "Alcione Casa Dos Tempeiros", "numero": "+557399120606",  "ativo": True},
    {"nome": "Alem Do Mar Litoral",        "numero": "+5573825720633", "ativo": True},
    {"nome": "Americanas",                 "numero": "+557381140263",  "ativo": True},
    {"nome": "Ana Paula Mix",              "numero": "+5573916501577", "ativo": True},
    {"nome": "Araujo MATEUS",              "numero": "+5571350736555", "ativo": True},
    {"nome": "Arcom",                      "numero": "+553432184200",  "ativo": True},
    {"nome": "Atacadão Eunapolis",         "numero": "+557335112643",  "ativo": True},
    {"nome": "Antonio Teixeira",           "numero": "+5573998569198", "ativo": True},
    {"nome": "Amenitiz Brasil",            "numero": "+5511953259068", "ativo": False},
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/contatos")
def listar_contatos():
    return jsonify(CONTATOS_PADRAO)

@app.route("/grupos")
def listar_grupos():
    conn = get_db()
    rows = conn.execute("SELECT id, nome FROM grupos ORDER BY nome").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/insumos/<int:grupo_id>")
def listar_insumos(grupo_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT i.codigo, i.nome, u.sigla as unidade, g.nome as grupo,
               COALESCE(s.quantidade, 0) as saldo
        FROM insumos i
        JOIN unidades u ON i.id_unidade = u.id
        JOIN grupos g ON i.id_grupo = g.id
        LEFT JOIN saldos s ON s.codigo_insumo = i.codigo
        WHERE i.id_grupo = ?
        ORDER BY i.nome
    """, (grupo_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/google/status")
def google_status():
    try:
        from google_forms import google_configurado
        return jsonify({"configurado": google_configurado()})
    except:
        return jsonify({"configurado": False})

@app.route("/google/gerar_form", methods=["POST"])
def gerar_form():
    try:
        from google_forms import gerar_form_cotacao
        data   = request.get_json()
        itens  = data.get("itens", [])
        titulo = data.get("titulo", "")
        if not itens:
            return jsonify({"erro": "Nenhum item selecionado."}), 400
        result = gerar_form_cotacao(itens, titulo)
        return jsonify(result)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/logs")
def listar_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:    return jsonify(json.load(f))
            except: return jsonify([])
    return jsonify([])

@app.route("/enviar", methods=["POST"])
def enviar():
    data         = request.get_json()
    mensagem     = data.get("mensagem", "").strip()
    selecionados = data.get("contatos", [])
    intervalo    = int(data.get("intervalo", 12))

    if not mensagem:     return jsonify({"erro": "Mensagem vazia."}), 400
    if not selecionados: return jsonify({"erro": "Nenhum contato selecionado."}), 400

    resultados = []
    for contato in selecionados:
        numero = "+" + re.sub(r"[^\d]", "", contato["numero"])
        nome   = contato["nome"]
        try:
            pywhatkit.sendwhatmsg_instantly(
                phone_no=numero, message=mensagem,
                wait_time=20, tab_close=True, close_time=4
            )
            _log(nome, mensagem, "✅ Enviado")
            resultados.append({"contato": nome, "status": "enviado"})
        except Exception as e:
            _log(nome, mensagem, f"❌ Erro: {e}")
            resultados.append({"contato": nome, "status": "erro", "detalhe": str(e)})
        if len(selecionados) > 1:
            time.sleep(intervalo)

    return jsonify({"resultados": resultados})

def _log(contato, mensagem, status):
    entrada = {"data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
               "contato": contato, "status": status,
               "preview": mensagem[:60] + "..." if len(mensagem) > 60 else mensagem}
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try: logs = json.load(f)
            except: pass
    logs.insert(0, entrada)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs[:100], f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    print("\n" + "="*52)
    print("  Disparador de Cotação — Pousada Estrela d'Água")
    print("="*52)
    print("  Acesse: http://localhost:5050")
    print("  Para encerrar: Ctrl+C")
    print("="*52 + "\n")
    app.run(debug=False, port=5050)
