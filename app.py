import streamlit as st
import pandas as pd
import requests

# Dicionário para traduzir os nomes da API (em inglês) para os do seu CSV
TRADUCAO_TIMES = {
    "Brazil": "Brasil", "Scotland": "Escócia", "Morocco": "Marrocos", 
    "USA": "Estados Unidos", "Germany": "Alemanha", "Spain": "Espanha",
    "France": "França", "England": "Inglaterra", "Netherlands": "Holanda"
}

@st.cache_data(ttl=300) 
def buscar_jogo_ao_vivo_api():
    # league=1 é o código da Copa do Mundo na API-Football
    url = "https://v3.football.api-sports.io/fixtures?live=all&league=1"
    
    try:
        chave_api = st.secrets["API_KEY"]
    except:
        return None, 0, 0, ""

    headers = {
        'x-apisports-key': chave_api,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    try:
        resposta = requests.get(url, headers=headers)
        dados = resposta.json()
        
        # Confirma se a API retornou a chave 'results' e se é maior que 0
        if dados.get('results', 0) > 0:
            jogo = dados['response'][0] 
            
            time_casa_en = jogo['teams']['home']['name']
            time_fora_en = jogo['teams']['away']['name']
            
            time_casa = TRADUCAO_TIMES.get(time_casa_en, time_casa_en)
            time_fora = TRADUCAO_TIMES.get(time_fora_en, time_fora_en)
            
            nome_jogo = f"{time_casa} x {time_fora}"
            
            # REDE DE SEGURANÇA: Se a API mandar 'None' nos gols, o Python transforma em 0
            gols_casa = jogo['goals']['home']
            gols_casa = 0 if gols_casa is None else int(gols_casa)
            
            gols_fora = jogo['goals']['away']
            gols_fora = 0 if gols_fora is None else int(gols_fora)
            
            # REDE DE SEGURANÇA: Tempo de jogo
            tempo_min = jogo['fixture']['status']['elapsed']
            tempo = f"{tempo_min}'" if tempo_min else "0'"
            
            return nome_jogo, gols_casa, gols_fora, tempo
        else:
            return None, 0, 0, ""
    except Exception as e:
        # Se QUALQUER coisa der errado na internet ou na API, ele esconde o radar silenciosamente
        return None, 0, 0, ""

# 1. Configurando a página
st.set_page_config(page_title="Bolão Copa 2026", page_icon="🏆", layout="centered")

# 2. Lendo os arquivos CSV
df_palpites = pd.read_csv("palpites.csv")
df_resultados = pd.read_csv("resultados.csv")

# 3. FUNÇÃO MÁGICA: Calcula os pontos de cada palpite
def calcular_pontos_do_palpite(row):
    # Procurar o resultado real para o jogo deste palpite
    jogo_real = df_resultados[df_resultados["Jogo"] == row["Jogo"]]
    
    # Se o jogo ainda não aconteceu ou não está no arquivo de resultados, ganha 0 pontos
    if jogo_real.empty:
        return 0
        
    # Pegando os gols reais e os palpites como números inteiros
    g_casa_real = int(jogo_real["Gols_Casa_Real"].values[0])
    g_fora_real = int(jogo_real["Gols_Fora_Real"].values[0])
    
    g_casa_palp = int(row["Gols_Casa_Palpite"])
    g_fora_palp = int(row["Gols_Fora_Palpite"])
    
    # REGRA 1: Acerto Exato do Placar (5 pontos)
    if g_casa_palp == g_casa_real and g_fora_palp == g_fora_real:
        return 5
        
    # Variáveis auxiliares para saber quem venceu (ou se foi empate)
    vencedor_real = "casa" if g_casa_real > g_fora_real else ("fora" if g_fora_real > g_casa_real else "empate")
    vencedor_palp = "casa" if g_casa_palp > g_fora_palp else ("fora" if g_fora_palp > g_casa_palp else "empate")
    
    # Se a pessoa acertou a tendência do jogo (Vencedor ou Empate)
    if vencedor_real == vencedor_palp:
        if vencedor_real == "empate":
            # REGRA 3: Acertou que seria empate, mas errou o placar exato (3 pontos)
            return 3
        else:
            # REGRA 2: Acertou o vencedor, mas errou o placar exato (2 pontos)
            return 2
            
    # Se errou tudo
    return 0

# Aplicando a função em cada linha de palpite para descobrir os pontos daquela aposta
df_palpites["Pontos_Ganhos"] = df_palpites.apply(calcular_pontos_do_palpite, axis=1)

# Agrupando os pontos por participante para criar o ranking geral
df_ranking = df_palpites.groupby("Participante")["Pontos_Ganhos"].sum().reset_index()
df_ranking.columns = ["Participante", "Pontos"]

# --- INTEGRAÇÃO COM AS PÁGINAS DO STREAMLIT ---

st.sidebar.title("Menu do Bolão ⚽")
pagina_selecionada = st.sidebar.radio("Navegue por aqui:", ["🏆 Classificação Geral", "📝 Palpites da Família"])

# Página: CLASSIFICAÇÃO
if pagina_selecionada == "🏆 Classificação Geral":
    st.title("🏆 Classificação da Copa 2026")
    st.write("VISH, GORDIN SAIU DA LANTERNA 🔦")
    
    # Ordenando do maior para o menor
    df_classificacao = df_ranking.sort_values(by="Pontos", ascending=False).reset_index(drop=True)
    df_classificacao.index = df_classificacao.index + 1
    
    st.dataframe(df_classificacao, use_container_width=True)

    # RADAR AO VIVO

    st.divider() 
    st.subheader("🔴 Radar Ao Vivo")

    # Chama a função UMA vez
    jogo_ao_vivo, gols_casa_live, gols_fora_live, tempo = buscar_jogo_ao_vivo_api()

    # O IF controla TUDO. Se for None, ele pula direto pro ELSE lá embaixo.
    if jogo_ao_vivo:
        st.write("Acompanhe como os placares de agora estão afetando o bolão!")
        st.markdown(f"<h3 style='text-align: center; color: #ff4b4b;'>{jogo_ao_vivo} <br> {gols_casa_live} x {gols_fora_live}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'>⏱️ {tempo}</p>", unsafe_allow_html=True)

        palpites_live = df_palpites[df_palpites["Jogo"] == jogo_ao_vivo].copy()

        if not palpites_live.empty:
            condicao_cravar = (palpites_live["Gols_Casa_Palpite"] >= gols_casa_live) & (palpites_live["Gols_Fora_Palpite"] >= gols_fora_live)
            podem_cravar = palpites_live[condicao_cravar]

            vencedor_live = "casa" if gols_casa_live > gols_fora_live else ("fora" if gols_fora_live > gols_casa_live else "empate")
            
            def acertando_tendencia(row):
                vencedor_palp = "casa" if row["Gols_Casa_Palpite"] > row["Gols_Fora_Palpite"] else ("fora" if row["Gols_Fora_Palpite"] > row["Gols_Casa_Palpite"] else "empate")
                return vencedor_palp == vencedor_live

            palpites_live["Acertando_Vencedor"] = palpites_live.apply(acertando_tendencia, axis=1)
            acertando_agora = palpites_live[palpites_live["Acertando_Vencedor"]]

            col1, col2 = st.columns(2)

            with col1:
                st.success("🎯 Podem cravar o placar exato:")
                if not podem_cravar.empty:
                    for index, row in podem_cravar.iterrows():
                        st.write(f"- **{row['Participante']}** ({row['Gols_Casa_Palpite']}x{row['Gols_Fora_Palpite']})")
                else:
                    st.write("Ninguém! Já erraram o placar. ❌")

            with col2:
                st.info("📈 Acertando a tendência atual:")
                if not acertando_agora.empty:
                    for index, row in acertando_agora.iterrows():
                        st.write(f"- **{row['Participante']}**")
                else:
                    st.write("Todo mundo errando! 😱")

        st.write("") 
        if st.button("🔄 Atualizar Radar (A cada 5 min)"):
            st.rerun() 

    # O ELSE tem que estar alinhado com o IF principal
    else:
        st.info("Nenhum jogo da Copa rolando neste exato momento. Fique de olho!")

# Página: PALPITES
elif pagina_selecionada == "📝 Palpites da Família":
    st.title("📝 Palpites da Família")
    st.write("Clique no nome do participante para ver as apostas!")
    
    participantes = df_palpites["Participante"].unique()
    
    for pessoa in participantes:
        # Aqui está a mágica: o 'with st.expander' cria a aba clicável
        with st.expander(f"👤 Palpites de {pessoa}"):
            
            # Filtramos os dados da pessoa
            palpites_da_pessoa = df_palpites[df_palpites["Participante"] == pessoa].copy()
            
            # Formata visualmente o palpite (Ex: "2 x 1")
            palpites_da_pessoa["Palpite"] = palpites_da_pessoa["Gols_Casa_Palpite"].astype(str) + " x " + palpites_da_pessoa["Gols_Fora_Palpite"].astype(str)
            
            # Limpa a tabela para mostrar só o que importa
            tabela_limpa = palpites_da_pessoa[["Jogo", "Palpite", "Pontos_Ganhos"]].reset_index(drop=True)
            tabela_limpa.columns = ["Jogo", "Aposta", "Pontos"]
            
            # st.dataframe permite esconder o índice (aqueles números 0, 1, 2 na lateral)
            st.dataframe(tabela_limpa, hide_index=True, use_container_width=True)