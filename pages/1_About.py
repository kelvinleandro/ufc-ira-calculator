import streamlit as st
from src.components import render_header

st.set_page_config(page_title="Sobre o IRA", layout="wide", page_icon="📊")

render_header()

st.divider()

st.title("Sobre o Índice de Rendimento Acadêmico (IRA)")

st.markdown(
    """
O Índice de Rendimento Acadêmico (IRA) é a métrica oficial da Universidade Federal do Ceará (UFC) para avaliar o desempenho dos estudantes. Ele é dividido em duas modalidades com propósitos distintos: o **IRA Individual** e o **IRA Geral**.
"""
)

st.header("Qual a diferença entre IRA Individual e Geral?")
st.write(
    """
- **IRA Individual:** Reflete o desempenho acadêmico pessoal de um aluno, considerando suas notas, carga horária e penalidades por trancamento. É o seu histórico transformado em um número.
- **IRA Geral:** É uma nota normalizada que permite uma comparação justa do desempenho de alunos entre diferentes cursos da universidade. Ele ajusta o IRA Individual com base na média e no desvio padrão da turma.
"""
)

st.divider()

st.header("IRA Geral: Comparando entre Cursos")
st.write(
    """
O objetivo do IRA Geral é posicionar o aluno em relação à sua própria turma. A fórmula ajusta o desempenho para uma escala onde a média do curso é sempre **6**. Um IRA Geral de 8, por exemplo, indica que o aluno está um desvio padrão acima da média de seu curso. Os valores são limitados entre 0 e 10.
"""
)
st.latex(
    r"""
IRA_{Geral} = 6 + 2 \left( \frac{IRA_{Individual} - IRA_{m}}{IRA_{dp}} \right)
"""
)
st.markdown(
    """
- **$IRA_{m}$**: Média dos IRAs Individuais dos alunos ativos do curso no semestre.
- **$IRA_{dp}$**: Desvio padrão dos IRAs Individuais dos alunos ativos do curso no semestre.
"""
)

st.divider()

st.header("IRA Individual: Medindo o Desempenho Pessoal")
st.write(
    """
Este índice é a base para o cálculo do IRA Geral e é calculado a partir das notas, cargas horárias das disciplinas cursadas e um fator de penalidade por trancamentos.
"""
)
st.latex(
    r"""
IRA_{Individual} = \left(1 - \frac{0.5 \cdot T}{C}\right) \times \left(\frac{\sum (P_i \cdot C_i \cdot N_i)}{\sum (P_i \cdot C_i)}\right)
"""
)
st.markdown(
    """
Onde os termos da fórmula significam:
- **$T$**: Somatório da carga horária de todas as disciplinas **trancadas**.
- **$C$**: Somatório da carga horária de todas as disciplinas **cursadas ou trancadas**.
- **$N_i$**: Nota final obtida na disciplina "i".
- **$C_i$**: Carga horária da disciplina "i".
- **$P_i$**: Peso referente ao período em que a disciplina "i" foi cursada. Este peso varia de 1 (no primeiro semestre) até um limite máximo de 6.
"""
)

st.divider()

st.markdown(
    """
[Deseja saber mais informações sobre o IRA? Clique aqui para acessar a página oficial da PROGRAD/UFC.](https://prograd.ufc.br/pt/perguntas-frequentes/ira/)
"""
)
