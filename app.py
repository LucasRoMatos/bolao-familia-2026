import streamlit as st
import pandas as pd

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
    st.write("A pontuação abaixo é calculada automaticamente pelo sistema!")
    
    # Ordenando do maior para o menor
    df_classificacao = df_ranking.sort_values(by="Pontos", ascending=False).reset_index(drop=True)
    df_classificacao.index = df_classificacao.index + 1
    
    st.dataframe(df_classificacao, use_container_width=True)

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