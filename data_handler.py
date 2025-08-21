
import pandas as pd
import os
import glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pickle
import hashlib
from datetime import datetime
import logging
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Detectar se está rodando na Vercel
IS_VERCEL = os.environ.get('VERCEL') == '1' or os.environ.get('NOW_REGION') is not None

DATA_FOLDER = "dados"  # Pasta onde ficam os arquivos .xlsx
CACHE_FOLDER = "/tmp/cache" if IS_VERCEL else "cache"  # Pasta para cache dos dados processados
COLUMN_NAMES = [
    "uf", "municipio", "evento", "data_referencia", "agente", "arma", "faixa_etaria",
    "feminino", "masculino", "nao_informado", "total_vitima", "total", "total_peso",
    "abrangencia", "formulario"
]

# Cache global para evitar recarregar dados em cada request
_global_data_cache = None
_cache_timestamp = None

class SinespDataHandler:
    def __init__(self):
        global _global_data_cache, _cache_timestamp
        
        # Se está na Vercel e já tem cache global, usar ele
        if IS_VERCEL and _global_data_cache is not None:
            self.df = _global_data_cache
            self._cached_values = {}
            logger.info("Usando cache global dos dados (Vercel)")
            return
        
        self._setup_cache_folder()
        self.df = self._load_all_data()
        self._cached_values = {}  # Cache para valores únicos
        
        # Salvar no cache global se está na Vercel
        if IS_VERCEL:
            _global_data_cache = self.df
            _cache_timestamp = datetime.now()
            logger.info("Dados salvos no cache global (Vercel)")
    
    def _setup_cache_folder(self):
        """Cria a pasta de cache se não existir"""
        if not os.path.exists(CACHE_FOLDER):
            try:
                os.makedirs(CACHE_FOLDER)
            except Exception as e:
                if not IS_VERCEL:  # Só reporta erro se não for Vercel
                    logger.warning(f"Erro ao criar pasta de cache: {e}")
                # No Vercel, usar cache em memória apenas
                if IS_VERCEL:
                    logger.info("Cache em disco não disponível, usando apenas cache em memória")
    
    def _get_file_hash(self, file_path):
        """Gera hash do arquivo para verificar se mudou"""
        try:
            stat = os.stat(file_path)
            # Usar tamanho e timestamp de modificação para hash rápido
            return hashlib.md5(f"{stat.st_size}_{stat.st_mtime}".encode()).hexdigest()
        except:
            return None
    
    def _get_cache_path(self, file_path):
        """Retorna o caminho do arquivo de cache"""
        file_name = os.path.basename(file_path).replace('.xlsx', '.pkl')
        return os.path.join(CACHE_FOLDER, file_name)
    
    def _load_single_file(self, file_path):
        """Carrega um único arquivo Excel com cache"""
        try:
            cache_path = self._get_cache_path(file_path)
            file_hash = self._get_file_hash(file_path)
            
            # Verificar se existe cache válido (apenas se não for Vercel ou se a pasta existir)
            if not IS_VERCEL and os.path.exists(cache_path):
                try:
                    with open(cache_path, 'rb') as f:
                        cached_data = pickle.load(f)
                    
                    # Verificar se o hash é o mesmo (arquivo não mudou)
                    if cached_data.get('hash') == file_hash:
                        logger.info(f"Cache hit: {os.path.basename(file_path)}")
                        return cached_data['dataframe']
                except:
                    pass  # Se falhou ao ler cache, reprocessar
            
            # Carregar e processar arquivo
            logger.info(f"Processando: {os.path.basename(file_path)}")
            
            # Otimizações para leitura mais rápida com encoding UTF-8
            df = pd.read_excel(
                file_path,
                engine='openpyxl',  # Engine mais rápida para .xlsx
                dtype='string'  # Ler tudo como string primeiro
            )
            
            # Normalizar colunas
            df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
            
            # Filtrar apenas as colunas especificadas que existem
            available_columns = [col for col in COLUMN_NAMES if col in df.columns]
            df = df[available_columns]
            
            # Limpar dados de string - remover caracteres especiais problemáticos
            string_columns = ['uf', 'municipio', 'evento', 'agente', 'arma', 'faixa_etaria', 'abrangencia', 'formulario']
            for col in string_columns:
                if col in df.columns:
                    # Garantir encoding correto e limpar dados
                    df[col] = df[col].astype(str).str.strip()
                    # Remover valores inválidos
                    df[col] = df[col].replace(['nan', 'None', '', 'null'], pd.NA)
            
            # Otimizar tipos de dados
            df = self._optimize_dtypes(df)
            
            # Adicionar coluna com nome do arquivo/ano
            df["arquivo_origem"] = os.path.basename(file_path)
            
            # Salvar no cache apenas se não for Vercel
            if not IS_VERCEL:
                try:
                    cache_data = {
                        'hash': file_hash,
                        'dataframe': df,
                        'timestamp': datetime.now().isoformat()
                    }
                    with open(cache_path, 'wb') as f:
                        pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
                except Exception as e:
                    logger.warning(f"Erro ao salvar cache para {file_path}: {e}")
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao processar {file_path}: {e}")
            return None
    
    def _optimize_dtypes(self, df):
        """Otimiza os tipos de dados do DataFrame para economia de memória"""
        # Converter colunas numéricas com tratamento mais robusto
        numeric_columns = ['feminino', 'masculino', 'nao_informado', 'total_vitima', 'total', 'total_peso']
        for col in numeric_columns:
            if col in df.columns:
                # Converter para numérico, colocando 0 para valores inválidos
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                # Converter para int se possível
                if df[col].dtype == 'float64' and df[col].notnull().all():
                    df[col] = df[col].astype('int64')
        
        # Converter colunas categóricas para economizar memória
        categorical_columns = ['uf', 'evento', 'agente', 'arma', 'faixa_etaria', 'abrangencia', 'formulario']
        for col in categorical_columns:
            if col in df.columns:
                # Converter para category apenas se não for nulo
                df[col] = df[col].astype('category')
        
        # Tratar municipio separadamente (pode ter muitos valores únicos)
        if 'municipio' in df.columns:
            df['municipio'] = df['municipio'].astype('string')
        
        return df

    def _load_all_data(self):
        """Carrega todos os arquivos .xlsx da pasta de dados usando processamento paralelo"""
        try:
            # Criar pasta de dados se não existir
            if not os.path.exists(DATA_FOLDER):
                os.makedirs(DATA_FOLDER)
                logger.info(f"Pasta '{DATA_FOLDER}' criada. Adicione os arquivos .xlsx nesta pasta.")
                return pd.DataFrame(columns=COLUMN_NAMES)
            
            # Buscar todos os arquivos .xlsx na pasta
            xlsx_files = glob.glob(os.path.join(DATA_FOLDER, "*.xlsx"))
            
            if not xlsx_files:
                # Verificar se existe o arquivo antigo na raiz
                if os.path.exists("sinesp_vde.xlsx"):
                    logger.info("Arquivo 'sinesp_vde.xlsx' encontrado na raiz. Carregando...")
                    df = self._load_single_file("sinesp_vde.xlsx")
                    return df if df is not None else pd.DataFrame(columns=COLUMN_NAMES)
                else:
                    logger.info(f"Nenhum arquivo .xlsx encontrado na pasta '{DATA_FOLDER}'")
                    return pd.DataFrame(columns=COLUMN_NAMES)
            
            logger.info(f"Carregando {len(xlsx_files)} arquivos de dados...")
            start_time = datetime.now()
            
            # Ajustar processamento paralelo para Vercel (menos workers)
            dataframes = []
            max_workers = min(2 if IS_VERCEL else 4, len(xlsx_files))  # Reduzir workers na Vercel
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submeter todas as tarefas
                future_to_file = {
                    executor.submit(self._load_single_file, file_path): file_path 
                    for file_path in xlsx_files
                }
                
                # Coletar resultados conforme completam
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        df = future.result()
                        if df is not None:
                            dataframes.append(df)
                    except Exception as e:
                        logger.error(f"Erro ao processar {file_path}: {e}")
                        continue
            
            if not dataframes:
                raise RuntimeError("Nenhum arquivo foi carregado com sucesso")
            
            # Combinar todos os DataFrames de forma otimizada
            logger.info("Combinando DataFrames...")
            combined_df = pd.concat(dataframes, ignore_index=True, sort=False)
            
            # Otimizar o DataFrame final
            combined_df = self._optimize_dtypes(combined_df)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Dados carregados: {len(combined_df):,} registros de {len(dataframes)} arquivos em {duration:.2f}s")
            
            return combined_df
            
        except Exception as e:
            raise RuntimeError(f"Erro ao carregar os dados: {e}")

    def get_anos_disponiveis(self):
        """Retorna os anos disponíveis extraídos da coluna data_referencia ou arquivo_origem"""
        cache_key = "anos_disponiveis"
        if cache_key in self._cached_values:
            return self._cached_values[cache_key]
        
        anos = set()
        
        # Tentar extrair anos da coluna data_referencia
        if "data_referencia" in self.df.columns:
            try:
                # Usar vectorização para melhor performance
                dates = pd.to_datetime(self.df["data_referencia"], errors='coerce')
                anos_data = dates.dt.year.dropna().unique()
                anos.update(anos_data.astype(int))
            except:
                pass
        
        # Tentar extrair anos dos nomes dos arquivos
        if "arquivo_origem" in self.df.columns:
            import re
            for arquivo in self.df["arquivo_origem"].unique():
                # Procurar por anos de 4 dígitos no nome do arquivo
                matches = re.findall(r'\b(20\d{2})\b', str(arquivo))
                for match in matches:
                    anos.add(int(match))
        
        result = sorted(list(anos))
        self._cached_values[cache_key] = result
        return result

    def get_arquivos_carregados(self):
        """Retorna informações sobre os arquivos carregados"""
        cache_key = "arquivos_carregados"
        if cache_key in self._cached_values:
            return self._cached_values[cache_key]
        
        if "arquivo_origem" not in self.df.columns:
            return []
        
        # Usar value_counts para melhor performance
        arquivo_counts = self.df["arquivo_origem"].value_counts()
        arquivos_info = [
            {"arquivo": arquivo, "registros": int(count)}
            for arquivo, count in arquivo_counts.items()
        ]
        
        result = sorted(arquivos_info, key=lambda x: x["arquivo"])
        self._cached_values[cache_key] = result
        return result

    def preview(self, limite=10):
        return self.df.head(limite).to_dict(orient="records")

    def listar_ufs(self):
        cache_key = "ufs"
        if cache_key in self._cached_values:
            return self._cached_values[cache_key]
        
        if "uf" not in self.df.columns:
            raise ValueError("Coluna 'uf' não encontrada")
        
        result = sorted(self.df["uf"].dropna().unique().tolist())
        self._cached_values[cache_key] = result
        return result

    def listar_municipios(self, uf=None):
        cache_key = f"municipios_{uf}" if uf else "municipios_all"
        if cache_key in self._cached_values:
            return self._cached_values[cache_key]
        
        if "municipio" not in self.df.columns:
            raise ValueError("Coluna 'municipio' não encontrada")
        
        df = self.df
        if uf:
            # Usar query para melhor performance
            df = df[df["uf"].str.upper() == uf.upper()]
        
        result = sorted(df["municipio"].dropna().unique().tolist())
        self._cached_values[cache_key] = result
        return result

    def ocorrencias(self, uf: str, municipio: str = None, evento: str = None, ano: int = None):
        if "uf" not in self.df.columns:
            raise ValueError("Coluna 'uf' não encontrada na planilha")
        
        # Usar máscaras booleanas para melhor performance
        mask = self.df["uf"].str.upper() == uf.upper()
        
        if municipio:
            mask &= self.df["municipio"].str.upper() == municipio.upper()
        
        if evento:
            mask &= self.df["evento"].str.upper() == evento.upper()
        
        if ano:
            # Filtrar por ano na data_referencia
            if "data_referencia" in self.df.columns:
                try:
                    dates = pd.to_datetime(self.df["data_referencia"], errors='coerce')
                    mask &= dates.dt.year == ano
                except:
                    pass
            
            # Ou filtrar por arquivo que contenha o ano (fallback)
            if "arquivo_origem" in self.df.columns:
                mask_arquivo = self.df["arquivo_origem"].str.contains(str(ano), na=False)
                # Usar OR se não encontrou nada na data_referencia
                if not mask.any():
                    mask = mask_arquivo
        
        filtro = self.df[mask]
        
        if filtro.empty:
            return None
        return filtro.to_dict(orient="records")
    
    def clear_cache(self):
        """Limpa o cache em memória"""
        self._cached_values.clear()
        logger.info("Cache em memória limpo")
    
    def get_memory_usage(self):
        """Retorna informações sobre uso de memória"""
        memory_mb = self.df.memory_usage(deep=True).sum() / 1024 / 1024
        return {
            "dataframe_size_mb": round(memory_mb, 2),
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "cached_values": len(self._cached_values)
        }
