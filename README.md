# API de consultas de dados públicos do SINESP-VDE - Violência Doméstica e Familiar

API REST para consulta de dados de violência doméstica e familiar do Sistema Nacional de Informações de Segurança Pública (SINESP).

## 📋 Sobre o Projeto

Esta API permite consultar dados estruturados sobre violência doméstica no Brasil, oferecendo endpoints para análises estatísticas, rankings e busca avançada por diversos critérios.

## 🏗️ Estrutura do Projeto

```
API-SINESP-VDE/
├── api.py              # Arquivo principal da API FastAPI
├── data_handler.py     # Manipulação e processamento dos dados
├── dados/              # Pasta para arquivos .xlsx (múltiplos anos)
│   ├── sinesp_2020.xlsx
│   ├── sinesp_2021.xlsx
│   ├── sinesp_2022.xlsx
│   └── ...
├── sinesp_vde.xlsx     # Base de dados Excel (compatibilidade)
└── README.md           # Este arquivo
```

## 📊 Estrutura dos Dados

O dataset contém as seguintes colunas:

- **uf**: Unidade Federativa
- **municipio**: Nome do município
- **evento**: Tipo de evento/crime
- **data_referencia**: Data de referência dos dados
- **agente**: Agente causador da violência
- **arma**: Tipo de arma utilizada
- **faixa_etaria**: Faixa etária das vítimas
- **feminino**: Número de vítimas do sexo feminino
- **masculino**: Número de vítimas do sexo masculino
- **nao_informado**: Vítimas com gênero não informado
- **total_vitima**: Total de vítimas
- **total**: Total geral
- **total_peso**: Peso total
- **abrangencia**: Abrangência dos dados
- **formulario**: Tipo de formulário
- **arquivo_origem**: Nome do arquivo de origem (adicionado automaticamente)

## 📁 Configuração dos Dados

### Múltiplos Anos

A API agora suporta múltiplos arquivos Excel na pasta `dados/`. Cada arquivo pode representar um ano diferente:

1. Crie a pasta `dados/` (já criada automaticamente)
2. Adicione seus arquivos .xlsx na pasta:
   - `sinesp_2020.xlsx`
   - `sinesp_2021.xlsx`
   - `sinesp_2022.xlsx`
   - etc.

### Compatibilidade

- Se não houver pasta `dados/`, a API tentará carregar `sinesp_vde.xlsx` da raiz
- Todos os arquivos são combinados automaticamente em um dataset único
- A coluna `arquivo_origem` é adicionada para rastrear a fonte dos dados

## 🚀 Como Executar

### Pré-requisitos

- Python 3.8+
- pip

### Instalação

1. Clone o repositório
2. Instale as dependências:

```bash
pip install fastapi uvicorn pandas openpyxl
```

3. Execute a API:

```bash
python -m uvicorn api:app --reload
```

4. Acesse a documentação interativa em: `http://localhost:8000/docs`

## 📚 Endpoints Disponíveis

### 🔍 Endpoints de Consulta Básica

| Endpoint        | Método | Descrição                                 |
| --------------- | ------ | ----------------------------------------- |
| `/`             | GET    | Informações gerais da API                 |
| `/dados`        | GET    | Preview dos dados (limite: 10 registros)  |
| `/ufs`          | GET    | Lista todas as UFs disponíveis            |
| `/municipios`   | GET    | Lista municípios (filtro opcional por UF) |
| `/eventos`      | GET    | Lista todos os tipos de eventos           |
| `/agentes`      | GET    | Lista todos os agentes causadores         |
| `/armas`        | GET    | Lista todos os tipos de armas             |
| `/faixa-etaria` | GET    | Lista todas as faixas etárias             |
| `/anos`         | GET    | Lista todos os anos disponíveis nos dados |
| `/arquivos`     | GET    | Informações sobre arquivos carregados     |

### 📈 Endpoints de Estatísticas

| Endpoint                   | Método | Descrição                               |
| -------------------------- | ------ | --------------------------------------- |
| `/estatisticas/resumo`     | GET    | Estatísticas gerais do dataset          |
| `/estatisticas/por-uf`     | GET    | Estatísticas agregadas por UF           |
| `/estatisticas/por-evento` | GET    | Estatísticas por tipo de evento         |
| `/estatisticas/genero`     | GET    | Distribuição por gênero com percentuais |

### 🏆 Endpoints de Rankings

| Endpoint                        | Método | Descrição                                       |
| ------------------------------- | ------ | ----------------------------------------------- |
| `/ranking/ufs-violencia`        | GET    | Ranking das UFs com mais violência              |
| `/ranking/municipios-violencia` | GET    | Ranking dos municípios (filtro opcional por UF) |

### 🔎 Endpoints de Busca e Consulta

| Endpoint       | Método | Descrição                                                  |
| -------------- | ------ | ---------------------------------------------------------- |
| `/ocorrencias` | GET    | Busca ocorrências por UF (filtros: município, evento, ano) |
| `/busca`       | GET    | Busca avançada com múltiplos filtros incluindo ano         |

## 📖 Exemplos de Uso

### Listar anos disponíveis

```
GET /anos
```

Resposta:

```json
{
  "anos": [2020, 2021, 2022, 2023, 2024],
  "total_anos": 5
}
```

### Informações sobre arquivos carregados

```
GET /arquivos
```

Resposta:

```json
{
  "arquivos": [
    { "arquivo": "sinesp_2020.xlsx", "registros": 15000 },
    { "arquivo": "sinesp_2021.xlsx", "registros": 18000 },
    { "arquivo": "sinesp_2022.xlsx", "registros": 20000 }
  ],
  "total_arquivos": 3,
  "total_registros": 53000
}
```

### Listar todas as UFs

```
GET /ufs
```

Resposta:

```json
{
  "ufs": ["AC", "AL", "AP", "AM", "BA", "CE", ...]
}
```

### Estatísticas por gênero

```
GET /estatisticas/genero
```

Resposta:

```json
{
  "estatisticas_genero": {
    "feminino": {
      "total": 150000,
      "percentual": 85.5
    },
    "masculino": {
      "total": 25000,
      "percentual": 14.2
    },
    "nao_informado": {
      "total": 500,
      "percentual": 0.3
    },
    "total_geral": 175500
  }
}
```

### Ranking de UFs com mais violência

```
GET /ranking/ufs-violencia?limite=5
```

Resposta:

```json
{
  "ranking_ufs_violencia": [
    { "uf": "SP", "total_vitimas": 45000 },
    { "uf": "RJ", "total_vitimas": 32000 },
    { "uf": "MG", "total_vitimas": 28000 },
    { "uf": "BA", "total_vitimas": 25000 },
    { "uf": "PR", "total_vitimas": 20000 }
  ]
}
```

### Busca avançada com filtro por ano

```
GET /busca?uf=SP&evento=VIOLENCIA_DOMESTICA&agente=CONJUGE&ano=2023&limite=50
```

Resposta:

```json
{
  "filtros_aplicados": ["UF: SP", "Evento: VIOLENCIA_DOMESTICA", "Agente: CONJUGE", "Ano: 2023"],
  "total_encontrados": 1250,
  "total_retornados": 50,
  "dados": [...]
}
```

### Ocorrências específicas por ano

```
GET /ocorrencias?uf=RJ&municipio=Rio de Janeiro&evento=LESAO_CORPORAL&ano=2022
```

## ⚙️ Parâmetros Comuns

- **limite**: Número máximo de registros retornados (padrão: 10-100 dependendo do endpoint)
- **uf**: Filtro por Unidade Federativa
- **municipio**: Filtro por município
- **evento**: Filtro por tipo de evento
- **agente**: Filtro por agente causador
- **arma**: Filtro por tipo de arma
- **faixa_etaria**: Filtro por faixa etária
- **ano**: Filtro por ano (novo parâmetro)

## 🔧 Tecnologias Utilizadas

- **FastAPI**: Framework web para APIs
- **Pandas**: Manipulação e análise de dados
- **Uvicorn**: Servidor ASGI
- **OpenPyXL**: Leitura de arquivos Excel

## 📱 Interface

A API fornece documentação interativa automática através do Swagger UI, acessível em `/docs` quando o servidor está rodando.

## 🤝 Contribuição

Para contribuir com o projeto:

1. Faça um fork
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Faça um push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob licença MIT.

---

**Nota**: Esta API foi desenvolvida para fins educacionais e de análise de dados públicos sobre violência doméstica no Brasil.
