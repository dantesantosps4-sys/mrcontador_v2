from fastapi import FastAPI, Form, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import sqlite3, hashlib, secrets
from datetime import datetime
import urllib.request, json

app = FastAPI(title="MR Contador")
app.mount("/static", StaticFiles(directory="static"), name="static")

DB = "database.db"

def conn():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    c = conn()
    cur = c.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        token TEXT UNIQUE NOT NULL,
        criado_em TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS transacoes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        tipo TEXT NOT NULL,
        categoria TEXT NOT NULL,
        mes TEXT NOT NULL,
        criado_em TEXT NOT NULL
    )
    """)

    c.commit()
    c.close()

init_db()

PERGUNTAS = {
1:"Quanto eu gastei esse mês?",2:"Qual foi minha receita total?",3:"Estou no lucro ou prejuízo?",4:"Qual meu saldo atual?",5:"Quanto eu posso gastar hoje?",
6:"Meu saldo está diminuindo ou aumentando?",7:"Qual foi meu maior gasto?",8:"Em que categoria gasto mais?",9:"Quanto sobrou no final do mês passado?",10:"Estou gastando mais do que ganho?",
11:"Onde estou gastando dinheiro à toa?",12:"Quais gastos posso cortar?",13:"Meus gastos são essenciais ou supérfluos?",14:"Quanto gasto com alimentação?",15:"Quanto gasto com lazer?",
16:"Qual gasto mais impacta meu saldo?",17:"Meus gastos estão equilibrados?",18:"Estou gastando muito com coisas desnecessárias?",19:"Quanto gasto por dia em média?",20:"Como reduzir meus gastos?",
21:"Onde posso investir meu dinheiro?",22:"Qual investimento está em alta?",23:"Vale a pena investir agora?",24:"Quanto posso investir sem risco?",25:"Qual melhor investimento para iniciantes?",
26:"Investir ou guardar dinheiro?",27:"Qual rendimento posso esperar?",28:"Quanto devo guardar por mês?",29:"Como começar a investir?",30:"Meu perfil é conservador ou arriscado?",
31:"Estou em risco financeiro?",32:"Meu saldo está acabando?",33:"Preciso economizar urgentemente?",34:"Estou entrando em dívida?",35:"Qual meu nível de segurança financeira?",
36:"Onde devo prestar mais atenção nos meus gastos?",37:"Qual foi meu pior hábito financeiro?",38:"O que estou fazendo certo financeiramente?",39:"O que devo mudar urgentemente?",40:"Como posso melhorar minha vida financeira?",
41:"Qual minha média de gastos semanal?",42:"Quanto economizei este mês?",43:"Estou conseguindo guardar dinheiro?",44:"Qual categoria mais cresceu em gastos?",45:"Estou gastando mais que no mês passado?",
46:"Quanto preciso ganhar para equilibrar minhas contas?",47:"Qual o melhor dia para pagar minhas contas?",48:"Tenho gastos recorrentes desnecessários?",49:"Quanto gasto com assinaturas?",50:"Vale a pena cancelar alguma assinatura?",
51:"Quanto preciso economizar para atingir uma meta?",52:"Em quanto tempo consigo juntar X valor?",53:"Meu dinheiro está rendendo bem?",54:"Qual a melhor estratégia para economizar mais?",55:"Estou preparado para emergências financeiras?",
56:"Quanto deveria ter de reserva de emergência?",57:"Meu padrão de vida está alto demais?",58:"Como organizar melhor minhas finanças?",59:"Estou usando bem meu dinheiro?",60:"O que posso fazer hoje para melhorar minhas finanças?"
}

def dinheiro(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def hash_senha(senha):
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 100000).hex()
    return f"{salt}${h}"

def senha_ok(senha, salvo):
    try:
        salt, h = salvo.split("$")
        teste = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 100000).hex()
        return teste == h
    except:
        return False

def usuario_por_token(token):
    if not token:
        return None
    c = conn()
    cur = c.cursor()
    cur.execute("SELECT id, username FROM usuarios WHERE token=?", (token,))
    user = cur.fetchone()
    c.close()
    return user

def categoria(desc, tipo):
    if tipo == "entrada":
        return "Receita"

    d = desc.lower()
    regras = {
        "Alimentação":["mercado","supermercado","comida","lanche","ifood","pizza","restaurante","padaria","açaí","acai","hamburguer"],
        "Transporte":["uber","99","gasolina","posto","ônibus","onibus","taxi","passagem","moto","carro"],
        "Moradia":["aluguel","energia","luz","água","agua","internet","wifi","casa"],
        "Lazer":["netflix","spotify","cinema","jogo","festa","bar","youtube","prime","disney"],
        "Saúde":["farmácia","farmacia","remédio","remedio","consulta","hospital","dentista"],
        "Educação":["escola","curso","livro","faculdade","material"],
        "Vestuário":["roupa","camisa","calça","calca","tênis","tenis","sapato","bermuda"],
        "Beleza":["corte","barbeiro","perfume","cabelo","salão","salao"],
        "Assinaturas":["assinatura","icloud","hbo","amazon"],
        "Dívidas":["dívida","divida","cartão","cartao","parcela","empréstimo","emprestimo"]
    }

    for cat, palavras in regras.items():
        if any(p in d for p in palavras):
            return cat
    return "Outros"

def resumo(uid, mes=""):
    c = conn()
    cur = c.cursor()

    if mes:
        cur.execute("""
        SELECT id, descricao, valor, tipo, categoria, mes, criado_em
        FROM transacoes
        WHERE usuario_id=? AND mes=?
        ORDER BY id DESC
        """, (uid, mes))
    else:
        cur.execute("""
        SELECT id, descricao, valor, tipo, categoria, mes, criado_em
        FROM transacoes
        WHERE usuario_id=?
        ORDER BY id DESC
        """, (uid,))

    rows = cur.fetchall()
    c.close()

    entradas = sum(float(r[2]) for r in rows if r[3] == "entrada")
    gastos = sum(float(r[2]) for r in rows if r[3] == "gasto")
    saldo = entradas - gastos

    cats = {}
    maior_gasto = 0
    maior_desc = "nenhum gasto"

    for r in rows:
        if r[3] == "gasto":
            cats[r[4]] = cats.get(r[4], 0) + float(r[2])
            if float(r[2]) > maior_gasto:
                maior_gasto = float(r[2])
                maior_desc = r[1]

    maior_cat = max(cats, key=cats.get) if cats else "nenhuma categoria"
    maior_val = cats.get(maior_cat, 0)

    return {
        "saldo": saldo,
        "entradas": entradas,
        "gastos": gastos,
        "cats": cats,
        "maior_cat": maior_cat,
        "maior_val": maior_val,
        "maior_gasto": maior_gasto,
        "maior_desc": maior_desc,
        "media_dia": gastos / 30 if gastos else 0,
        "media_semana": gastos / 4 if gastos else 0,
        "historico": [
            {
                "id": r[0],
                "descricao": r[1],
                "valor": r[2],
                "tipo": r[3],
                "categoria": r[4],
                "mes": r[5],
                "criado_em": r[6]
            } for r in rows
        ]
    }

def gerar_alertas(r):
    alertas = []
    entradas = r["entradas"]
    gastos = r["gastos"]
    saldo = r["saldo"]

    if entradas > 0 and gastos > entradas:
        alertas.append(f"🚨 Você está gastando {dinheiro(gastos - entradas)} a mais do que ganha.")

    if saldo < 0:
        alertas.append("⚠️ Seu saldo está negativo. Evite novos gastos agora.")

    if entradas > 0 and gastos >= entradas * 0.7 and gastos <= entradas:
        alertas.append("⚠️ Seus gastos passaram de 70% da sua receita. Atenção ao ritmo.")

    if gastos > 0 and r["maior_val"] > 0:
        pct = (r["maior_val"] / gastos) * 100
        if pct >= 50:
            alertas.append(f"⚠️ {r['maior_cat']} representa {pct:.1f}% dos seus gastos.")

    if gastos > 0:
        alertas.append(f"💡 Cortar 10% dos gastos economizaria {dinheiro(gastos * 0.10)}.")

    if entradas > gastos and entradas > 0:
        alertas.append(f"✅ Você está no lucro de {dinheiro(entradas - gastos)}.")

    if not alertas:
        alertas.append("📊 Registre mais movimentações para eu gerar alertas melhores.")

    return alertas

def resposta_ia(uid, n, mes=""):
    r = resumo(uid, mes)
    e, g, s = r["entradas"], r["gastos"], r["saldo"]
    lucro = e - g
    mc, mv = r["maior_cat"], r["maior_val"]

    respostas = {
        1:f"Você gastou {dinheiro(g)}.",
        2:f"Sua receita total foi {dinheiro(e)}.",
        3:f"Você está {'no lucro' if lucro >= 0 else 'no prejuízo'} de {dinheiro(abs(lucro))}.",
        4:f"Seu saldo atual é {dinheiro(s)}.",
        5:f"Um limite seguro para gastar hoje seria {dinheiro(max(s / 30, 0))}.",
        6:f"Seu saldo está {'positivo/aumentando' if s >= 0 else 'negativo/diminuindo'}.",
        7:f"Seu maior gasto foi {r['maior_desc']}, no valor de {dinheiro(r['maior_gasto'])}.",
        8:f"A categoria em que você mais gasta é {mc}, com {dinheiro(mv)}.",
        9:"Para comparar com o mês passado, registre dados em mais de um mês e use o filtro mensal.",
        10:f"{'Sim' if g > e else 'Não'}. Gastos: {dinheiro(g)}; receitas: {dinheiro(e)}.",
        11:f"Seu maior ponto de atenção é {mc}. Veja se esses gastos são realmente necessários.",
        12:f"Comece tentando reduzir gastos em {mc}.",
        13:"Essenciais costumam ser moradia, alimentação, saúde e transporte. Supérfluos costumam ser lazer, compras por impulso e assinaturas pouco usadas.",
        14:"Veja no gráfico quanto está indo para Alimentação.",
        15:"Veja no gráfico quanto está indo para Lazer.",
        16:f"O gasto que mais impacta seu saldo é {mc}.",
        17:"Se uma categoria domina muito o gráfico, seus gastos não estão equilibrados.",
        18:f"Pode estar gastando muito se {mc} não for essencial.",
        19:f"Sua média diária de gastos é {dinheiro(r['media_dia'])}.",
        20:f"Para reduzir gastos, tente cortar 10% em {mc}.",
        21:"Antes de investir, monte uma reserva de emergência.",
        22:"Não tenho dados de mercado em tempo real, mas renda fixa costuma ser um bom começo para perfil conservador.",
        23:"Vale investir se você já tem saldo positivo e reserva mínima.",
        24:f"Sem risco alto, invista apenas o que sobra. Seu saldo atual é {dinheiro(s)}.",
        25:"Para iniciantes, o ideal é começar com reserva de emergência e investimentos conservadores.",
        26:"Se ainda não tem reserva, guarde. Se já tem, invista aos poucos.",
        27:"O rendimento depende do investimento, prazo, taxa e imposto.",
        28:"Uma meta boa é guardar de 10% a 20% da receita.",
        29:"Comece controlando gastos, quitando dívidas e montando reserva.",
        30:"Se você evita risco e busca segurança, seu perfil tende a ser conservador.",
        31:f"Seu risco financeiro está {'alto' if s < 0 or g > e else 'controlado'}.",
        32:f"{'Sim' if s < r['media_semana'] else 'Não necessariamente'}. Seu saldo é {dinheiro(s)}.",
        33:"Você precisa economizar urgentemente se seus gastos estiverem maiores que sua receita.",
        34:f"{'Sim, possível' if s < 0 else 'Não parece'} pelo saldo atual.",
        35:f"Seu nível de segurança financeira está {'baixo' if s < 0 else 'moderado'}.",
        36:f"Preste mais atenção em {mc}.",
        37:f"Seu pior hábito financeiro pode estar ligado a {mc}.",
        38:"Você está fazendo certo ao registrar e acompanhar seus gastos.",
        39:f"Mude urgentemente gastos em {mc} se forem desnecessários.",
        40:"Registre tudo, defina limite mensal e acompanhe semanalmente.",
        41:f"Sua média semanal de gastos é {dinheiro(r['media_semana'])}.",
        42:f"Se você cortar 10% dos gastos, economiza {dinheiro(g * 0.10)}.",
        43:f"{'Sim' if s > 0 else 'Ainda não'}. Seu saldo é {dinheiro(s)}.",
        44:"Para saber qual categoria cresceu mais, precisamos comparar meses diferentes.",
        45:"Use o filtro mensal para comparar seus gastos com outros meses.",
        46:f"Para equilibrar, você precisa ter pelo menos {dinheiro(g)} de receita.",
        47:"O melhor dia para pagar contas é logo depois de receber dinheiro.",
        48:"Assinaturas, lazer e compras pequenas repetidas costumam ser gastos recorrentes desnecessários.",
        49:"Registre suas assinaturas com nomes como Netflix, Spotify, Prime ou iCloud para acompanhar melhor.",
        50:"Vale cancelar assinatura que você quase não usa.",
        51:"Divida o valor da meta pelo quanto consegue guardar por mês.",
        52:"Tempo para juntar = valor da meta dividido pela economia mensal.",
        53:"Seu dinheiro rende melhor quando sobra e é investido. Primeiro foque em saldo positivo.",
        54:f"A melhor estratégia agora é reduzir {mc} e guardar parte da receita.",
        55:f"{'Parcialmente' if s > 0 else 'Ainda não'}. Uma reserva ideal cobre 3 a 6 meses de gastos.",
        56:"Reserva de emergência ideal: 3 a 6 meses dos gastos essenciais.",
        57:f"Seu padrão pode estar alto se {mc} for supérfluo.",
        58:"Organize suas finanças por categorias, limite mensal e acompanhamento semanal.",
        59:f"Você está usando melhor seu dinheiro ao acompanhar. Atenção principal: {mc}.",
        60:"Hoje: registre seus gastos, corte um gasto pequeno e defina uma meta."
    }

    return respostas.get(n, "Pergunta não encontrada.") + " " + " ".join(gerar_alertas(r))

@app.get("/", response_class=HTMLResponse)
def home():
    return open("templates/index.html", encoding="utf-8").read()

@app.post("/register")
def register(username: str = Form(...), senha: str = Form(...)):
    username = username.strip()
    token = secrets.token_hex(32)

    try:
        c = conn()
        cur = c.cursor()
        cur.execute(
            "INSERT INTO usuarios(username, senha_hash, token, criado_em) VALUES(?,?,?,?)",
            (username, hash_senha(senha), token, datetime.now().isoformat())
        )
        c.commit()
        c.close()
        return {"ok": True, "token": token, "username": username}
    except Exception:
        return JSONResponse({"ok": False, "erro": "Usuário já existe"}, status_code=400)

@app.post("/login")
def login(username: str = Form(...), senha: str = Form(...)):
    username = username.strip()
    c = conn()
    cur = c.cursor()
    cur.execute("SELECT senha_hash, token FROM usuarios WHERE username=?", (username,))
    row = cur.fetchone()
    c.close()

    if not row or not senha_ok(senha, row[0]):
        return JSONResponse({"ok": False, "erro": "Login inválido"}, status_code=401)

    return {"ok": True, "token": row[1], "username": username}

@app.get("/me")
def me(authorization: str = Header(default="")):
    token = authorization.replace("Bearer ", "")
    user = usuario_por_token(token)
    if not user:
        return JSONResponse({"ok": False}, status_code=401)
    return {"ok": True, "id": user[0], "username": user[1]}

@app.post("/add")
def add(
    descricao: str = Form(...),
    valor: float = Form(...),
    tipo: str = Form(...),
    authorization: str = Header(default="")
):
    token = authorization.replace("Bearer ", "")
    user = usuario_por_token(token)

    if not user:
        return JSONResponse({"ok": False, "erro": "Não autorizado"}, status_code=401)

    uid = user[0]
    cat = categoria(descricao, tipo)
    mes = datetime.now().strftime("%Y-%m")

    c = conn()
    cur = c.cursor()
    cur.execute("""
    INSERT INTO transacoes(usuario_id, descricao, valor, tipo, categoria, mes, criado_em)
    VALUES(?,?,?,?,?,?,?)
    """, (uid, descricao, abs(valor), tipo, cat, mes, datetime.now().isoformat()))
    c.commit()
    c.close()

    return {"ok": True}

@app.get("/dados")
def dados(mes: str = "", authorization: str = Header(default="")):
    token = authorization.replace("Bearer ", "")
    user = usuario_por_token(token)

    if not user:
        return JSONResponse({"ok": False, "erro": "Não autorizado"}, status_code=401)

    r = resumo(user[0], mes)
    r["alertas"] = gerar_alertas(r)
    r["perguntas"] = PERGUNTAS
    return r

@app.delete("/delete/{tid}")
def delete(tid: int, authorization: str = Header(default="")):
    token = authorization.replace("Bearer ", "")
    user = usuario_por_token(token)

    if not user:
        return JSONResponse({"ok": False, "erro": "Não autorizado"}, status_code=401)

    c = conn()
    cur = c.cursor()
    cur.execute("DELETE FROM transacoes WHERE id=? AND usuario_id=?", (tid, user[0]))
    c.commit()
    c.close()

    return {"ok": True}

@app.get("/ia/{pergunta_id}")
def ia(pergunta_id: int, mes: str = "", authorization: str = Header(default="")):
    token = authorization.replace("Bearer ", "")
    user = usuario_por_token(token)

    if not user:
        return JSONResponse({"ok": False, "erro": "Não autorizado"}, status_code=401)

    return {"resposta": resposta_ia(user[0], pergunta_id, mes)}

@app.get("/radar-cripto")
def radar_cripto():
    url = (
        "https://api.coingecko.com/api/v3/coins/markets"
        "?vs_currency=brl"
        "&ids=bitcoin,ethereum,solana,cardano,ripple,dogecoin"
        "&order=market_cap_desc"
        "&per_page=6"
        "&page=1"
        "&sparkline=false"
        "&price_change_percentage=24h,7d"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "MRContador/1.0"}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            moedas = json.loads(response.read().decode("utf-8"))

        resultado = []

        for m in moedas:
            nome = m.get("n/ame", "")
            simbolo = m.get("symbol", "").upper()
            preco = float(m.get("current_price") or 0)
            var24 = float(m.get("price_change_percentage_24h") or 0)
            var7 = float(m.get("price_change_percentage_7d_in_currency") or 0)
            market_cap = float(m.get("market_cap") or 0)

            if var24 > 5 and var7 > 8:
                tendencia = "alta forte"
                risco = "alto"
                explicacao = f"{nome} subiu bem nas últimas 24h e também nos últimos 7 dias. Isso mostra força recente, mas também aumenta o risco de correção."
            elif var24 > 2 and var7 > 0:
                tendencia = "alta moderada"
                risco = "médio"
                explicacao = f"{nome} está em alta moderada. O movimento é positivo, mas ainda precisa ser acompanhado com cuidado."
            elif var24 < -5:
                tendencia = "queda forte"
                risco = "alto"
                explicacao = f"{nome} caiu forte nas últimas 24h. Pode ser oportunidade para alguns perfis, mas o risco está elevado."
            elif var7 < 0:
                tendencia = "fraca"
                risco = "médio/alto"
                explicacao = f"{nome} está com desempenho negativo na semana. Melhor observar antes de qualquer decisão."
            else:
                tendencia = "neutra"
                risco = "médio"
                explicacao = f"{nome} está sem movimento muito forte agora. Pode ser melhor acompanhar antes de agir."

            resultado.append({
                "nome": nome,
                "simbolo": simbolo,
                "preco": preco,
                "var24": var24,
                "var7": var7,
                "market_cap": market_cap,
                "tendencia": tendencia,
                "risco": risco,
                "explicacao": explicacao
            })

        return {"ok": True, "moedas": resultado}

    except Exception as e:
        return JSONResponse({
            "ok": False,
            "erro": "Não consegui buscar os dados de cripto agora.",
            "detalhe": str(e)
        }, status_code=500)
