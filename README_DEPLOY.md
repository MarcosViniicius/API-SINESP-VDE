# Deploy na Vercel - Instruções

## 📦 Preparação para Deploy

### 1. Estrutura de Arquivos Necessários

Certifique-se de que os seguintes arquivos estão presentes:

```
API-SINESP-VDE/
├── main.py              # Ponto de entrada para Vercel
├── api.py               # API FastAPI principal
├── data_handler.py      # Manipulação de dados
├── requirements.txt     # Dependências Python
├── vercel.json          # Configuração da Vercel
├── .vercelignore        # Arquivos a ignorar no deploy
├── dados/               # Pasta com arquivos Excel
│   ├── BancoVDE 2015.xlsx
│   ├── BancoVDE 2016.xlsx
│   └── ...
└── README_DEPLOY.md     # Este arquivo
```

### 2. Configurações Importantes

#### Rate Limiting

- **Local**: 100 requests/minuto
- **Vercel**: 50 requests/minuto (otimizado para serverless)

#### Cache

- **Local**: Cache em disco na pasta `cache/`
- **Vercel**: Cache em memória global + `/tmp` temporário

#### Processamento

- **Local**: 4 workers para processamento paralelo
- **Vercel**: 2 workers (otimizado para limitações de memória)

### 3. Limitações da Vercel

#### Tamanho dos Arquivos

- Limite de 50MB por deployment
- Arquivos Excel grandes podem causar problemas
- Considere compactar ou dividir dados grandes

#### Timeout

- Máximo 30 segundos por request
- Carregamento inicial pode ser lento
- Cache global minimiza recarregamentos

#### Memória

- Limite de 1GB RAM por função
- DataFrames grandes podem causar problemas
- Otimização de tipos de dados implementada

### 4. Deploy na Vercel

#### Opção 1: Vercel CLI

```bash
# Instalar Vercel CLI
npm i -g vercel

# Fazer login
vercel login

# Deploy
vercel

# Deploy para produção
vercel --prod
```

#### Opção 2: GitHub Integration

1. Conecte seu repositório ao GitHub
2. Conecte o GitHub à Vercel
3. Cada push fará deploy automático

### 5. Variáveis de Ambiente

Na Vercel, configure se necessário:

```
VERCEL=1
PYTHONPATH=.
```

### 6. Monitoramento

#### Logs

```bash
# Ver logs da função
vercel logs [deployment-url]
```

#### Performance

- Monitor de uso de recursos na dashboard Vercel
- Análise de tempo de resposta
- Rate limiting automático

### 7. Otimizações Implementadas

#### Cache Global

- Dados são carregados uma vez e mantidos em memória
- Reduz tempo de resposta após first load
- Melhora significativa na performance

#### Tipos de Dados

- Colunas categóricas usam `pd.Categorical`
- Números otimizados para tipos menores
- Redução significativa do uso de memória

#### Rate Limiting Adaptativo

- Diferente entre local e Vercel
- Proteção contra overload do serviço
- Balanceamento de performance

### 8. URLs de Exemplo

Após o deploy, sua API estará disponível em:

```
https://seu-projeto.vercel.app/
https://seu-projeto.vercel.app/docs
https://seu-projeto.vercel.app/status
https://seu-projeto.vercel.app/info
```

### 9. Troubleshooting

#### Erro de Timeout

```
Erro 504: Function timeout
```

**Solução**: Reduzir tamanho dos dados ou implementar paginação

#### Erro de Memória

```
Erro 502: Function crashed
```

**Solução**: Otimizar DataFrames ou reduzir dados carregados

#### Arquivos Muito Grandes

```
Erro de deployment: File too large
```

**Solução**: Mover arquivos Excel para storage externo (AWS S3, etc.)

### 10. Melhorias Futuras

#### Storage Externo

- Mover dados para AWS S3 ou similar
- Carregamento sob demanda
- Redução do tamanho do deployment

#### Redis Cache

- Implementar cache Redis para dados compartilhados
- Persistência entre execuções
- Melhor performance global

#### Fragmentação de Dados

- Carregar apenas dados necessários por request
- Paginação avançada
- Filtros no carregamento

### 11. Comandos Úteis

```bash
# Testar localmente primeiro
python -m uvicorn main:app --reload

# Verificar tamanho do projeto
du -sh .

# Verificar dependências
pip list

# Limpar cache local
rm -rf cache/ __pycache__/
```

### 12. Verificação Pós-Deploy

1. ✅ API responde na URL: `/`
2. ✅ Documentação carrega: `/docs`
3. ✅ Status endpoint: `/status`
4. ✅ Dados carregam: `/ufs`
5. ✅ Busca funciona: `/ocorrencias?uf=SP`

---

**💡 Dica**: Mantenha uma versão local para desenvolvimento e use a Vercel apenas para produção, devido às limitações de recursos.
