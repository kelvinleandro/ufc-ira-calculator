# Calculadora de IRA - UFC

Uma aplicação web interativa construída com Streamlit para analisar históricos acadêmicos da Universidade Federal do Ceará (UFC), extraídos do sistema SIGAA. A ferramenta calcula automaticamente o Índice de Rendimento Acadêmico (IRA) Individual e Geral, e apresenta um dashboard com métricas e visualizações sobre o desempenho do aluno.

## ✨ Funcionalidades

- **Upload de Histórico**: Faça o upload do seu histórico escolar em formato PDF diretamente na aplicação.

- **Cálculo Automático de IRA**:

  - **IRA Individual**: Calculado com base nas suas notas, carga horária e penalidades por trancamento.

  - **IRA Geral**: Calculado de forma normalizada, permitindo a comparação do seu desempenho com a média e o desvio padrão do seu curso.

- **Dashboard Interativo**:

  - **Métricas Principais**: Cards com o seu IRA Individual, IRA Geral e a percentagem de conclusão do curso.

  - **Gráfico de Evolução**: Acompanhe a evolução do seu IRA Individual acumulado ao longo dos semestres.

  - **Análises Detalhadas**: Gráficos de distribuição de notas e da carga horária cursada por semestre.

  - **Página Informativa**: Uma página dedicada a explicar as regras e fórmulas por trás do cálculo do IRA.

  - **Contribuição da Comunidade**: Um formulário para que os usuários possam sugerir a adição de novos cursos à base de dados da aplicação.

## Estrutura do Projeto

```
ufc-ira-calculator/
├── .streamlit/
│   ├── config.toml         # Configurações de tema e UI
│   └── secrets.toml        # Credenciais do banco de dados (local)
├── pages/
│   └── 1_About.py          # Código da página "Sobre"
├── src/
│   ├── __init__.py
│   ├── calculations.py     # Lógica dos cálculos matemáticos do IRA
│   ├── components.py       # Componentes de UI reutilizáveis (ex: header)
│   ├── database.py         # Funções de comunicação com o banco de dados
│   └── pdf_parser.py       # Lógica para extrair dados do PDF
├── .gitignore
├── app.py                  # Ponto de entrada e UI da página principal
├── main.py                 # Código simples que roda pelo terminal para mostrar o IRA
└── requirements.txt        # Dependências do projeto
```

## 🚀 Como Executar Localmente

### 1. Configuração do Ambiente

#### a. Clone o repositório:

```sh
git clone https://github.com/kelvinleandro/ufc-ira-calculator.git
cd ufc-ira-calculator
```

#### b. Crie e ative um ambiente virtual:

```sh
# Criar o ambiente
python -m venv .venv

# Ativar no Windows
.\.venv\Scripts\activate

# Ativar no macOS/Linux
source .venv/bin/activate
```

#### c. Instale as dependências:

```sh
pip install -r requirements.txt
```

#### d. Configure os segredos (credenciais):

Crie uma pasta `.streamlit` na raiz do projeto e, dentro dela, um arquivo `secrets.toml`. Adicione as suas credenciais do PostgreSQL:

```
# .streamlit/secrets.toml
[postgres]
host = "seu_host"
port = "5432"
dbname = "seu_banco"
user = "seu_usuario"
password = "sua_senha"
```

### 2. Executando a Aplicação

Com o ambiente virtual ativado, execute o seguinte comando no terminal:

```sh
streamlit run app.py
```

A aplicação será aberta automaticamente no seu navegador padrão.
