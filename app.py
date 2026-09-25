import os
import sys
import webbrowser
from threading import Timer
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file

# --- CORREÇÃO DE CAMINHOS PARA EXECUTÁVEL (.EXE) ---
if getattr(sys, 'frozen', False):
    # Se estiver rodando como .EXE
    BASE_DIR = os.path.dirname(sys.executable)
    TEMPLATE_FOLDER = os.path.join(sys._MEIPASS, 'templates')
    STATIC_FOLDER = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)
else:
    # Se estiver rodando como Script Python normal
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__)

FILE_PATH = os.path.join(BASE_DIR, 'estoque_atual.xlsx')

def carregar_planilha():
    if not os.path.exists(FILE_PATH):
        return None, None
    try:
        df_raw = pd.read_excel(FILE_PATH, header=None)
        header_idx = 0
        for idx, row in df_raw.iterrows():
            row_text = " ".join(row.dropna().astype(str)).lower()
            if 'código' in row_text or 'codigo' in row_text or 'qtd' in row_text:
                header_idx = idx
                break

        df = pd.read_excel(FILE_PATH, header=header_idx)
        return df, header_idx
    except Exception as e:
        print(f"Erro ao ler planilha: {e}")
        return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado.'}), 400
    
    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'success': False, 'message': 'Envie um arquivo Excel (.xlsx ou .xls)'}), 400

    file.save(FILE_PATH)
    return jsonify({'success': True, 'message': 'Planilha carregada com sucesso!'})

@app.route('/api/dados', methods=['GET'])
def get_dados():
    df, _ = carregar_planilha()
    if df is None:
        return jsonify({'has_file': False, 'dados': [], 'colunas': []})

    df_clean = df.fillna('')
    return jsonify({
        'has_file': True,
        'colunas': list(df.columns),
        'dados': df_clean.to_dict(orient='records')
    })

@app.route('/api/incrementar', methods=['POST'])
def incrementar():
    valor_busca = request.json.get('codigo', '').strip()
    
    if not valor_busca:
        return jsonify({'success': False, 'message': 'Digite um código válido.'}), 400

    df, header_idx = carregar_planilha()
    if df is None:
        return jsonify({'success': False, 'message': 'Nenhuma planilha foi carregada ainda.'}), 400

    col_a = df.columns[0] 
    col_b = df.columns[1] 
    col_c = df.columns[2] 
    
    nome_col_d = df.columns[3] if len(df.columns) > 3 else "Coluna D"
    nome_col_g = df.columns[6] if len(df.columns) > 6 else "Coluna G"

    mascara = df[col_a].astype(str).str.strip() == str(valor_busca)

    if not mascara.any():
        return jsonify({'success': False, 'message': f'Código "{valor_busca}" não encontrado na Coluna A.'}), 404

    df[col_b] = pd.to_numeric(df[col_b], errors='coerce').fillna(0)
    df[col_c] = pd.to_numeric(df[col_c], errors='coerce').fillna(0)

    idx = df[mascara].index[0]
    limite_b = df.loc[idx, col_b]
    atual_c = df.loc[idx, col_c]

    proximo_c = atual_c + 1

    if proximo_c >= limite_b:
        novo_c = limite_b
        mensagem = f'⚠️ Código {valor_busca}: Limite máximo da Coluna B atingido ({int(limite_b)})!'
    else:
        novo_c = proximo_c
        mensagem = f'✅ Código {valor_busca} contabilizado ({int(novo_c)} de {int(limite_b)})'

    df.loc[idx, col_c] = novo_c
    df.to_excel(FILE_PATH, index=False, startrow=header_idx)

    linha = df.loc[idx]
    val_d = str(linha.iloc[3]) if len(linha) > 3 and pd.notna(linha.iloc[3]) else "-"
    val_g = str(linha.iloc[6]) if len(linha) > 6 and pd.notna(linha.iloc[6]) else "-"

    return jsonify({
        'success': True,
        'message': mensagem,
        'codigo': valor_busca,
        'coluna_d': {'nome': nome_col_d, 'valor': val_d},
        'coluna_g': {'nome': nome_col_g, 'valor': val_g},
        'qtd_contada': int(novo_c),
        'qtd_maxima': int(limite_b)
    })

@app.route('/api/download', methods=['GET'])
def download():
    if os.path.exists(FILE_PATH):
        return send_file(FILE_PATH, as_attachment=True, download_name='estoque_atualizado.xlsx')
    return jsonify({'success': False, 'message': 'Arquivo não encontrado.'}), 404

def abrir_navegador():
    webbrowser.open_new('http://127.0.0.1:5001/')

if __name__ == '__main__':
    # Abre o navegador automaticamente ao clicar no EXE
    Timer(1.5, abrir_navegador).start()
    # Desativa debug=True obrigatoriamente para não dar erro no PyInstaller
    app.run(port=5001, debug=False)