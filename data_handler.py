import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Detectar se está rodando na Vercel
IS_VERCEL = os.environ.get("VERCEL") == "1" or os.environ.get("NOW_REGION") is not None

DATA_FOLDER = "dados"  # Pasta onde ficam os arquivos de entrada
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
        import pandas as pd
        from datetime import datetime
        global _global_data_cache, _cache_timestamp

        # Se está na Vercel e já tem cache global, usar ele
        if IS_VERCEL and _global_data_cache is not None:
            self.df = _global_data_cache
            self._cached_values = {}
            logger.info("Usando cache global dos dados (Vercel)")
            return

        self._setup_cache_folder()
        self.df = self._load_all_data()
        self._cached_values = {}

        # Salvar no cache global se está na Vercel
        if IS_VERCEL:
            _global_data_cache = self.df
            _cache_timestamp = datetime.now()
            logger.info("Dados salvos no cache global (Vercel)")

    def _setup_cache_folder(self):
        if not os.path.exists(CACHE_FOLDER):
            try:
                os.makedirs(CACHE_FOLDER)
            except Exception as e:
                if not IS_VERCEL:
                    logger.warning(f"Erro ao criar pasta de cache: {e}")
                else:
                    logger.info("Cache em disco não disponível, usando apenas cache em memória")

    def _get_file_hash(self, file_path):
        import hashlib
        try:
            stat = os.stat(file_path)
            return hashlib.md5(f"{stat.st_size}_{stat.st_mtime}".encode()).hexdigest()
        except:
            return None

    def _get_cache_path(self, file_path):
        base = (
            os.path.basename(file_path)
            .replace(".xlsx", ".parquet")
            .replace(".csv.xz", ".parquet")
            .replace(".csv.gz", ".parquet")
        )
        return os.path.join(CACHE_FOLDER, base)

    def _load_single_file(self, file_path):
        import pandas as pd
        cache_path = self._get_cache_path(file_path)
        file_hash = self._get_file_hash(file_path)

        # Verificar cache
        if not IS_VERCEL and os.path.exists(cache_path):
            try:
                df = pd.read_parquet(cache_path)
                logger.info(f"Cache hit: {os.path.basename(file_path)}")
                return df
            except Exception as e:
                logger.warning(f"Erro lendo cache {cache_path}: {e}")

        logger.info(f"Processando: {os.path.basename(file_path)}")

        # Carregar arquivo
        if file_path.endswith(".csv.xz"):
            df = pd.read_csv(file_path, compression="xz", dtype="string")
        elif file_path.endswith(".csv.gz"):
            df = pd.read_csv(file_path, compression="gzip", dtype="string")
        elif file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path, engine="openpyxl", dtype="string")
        else:
            logger.error(f"Formato de arquivo não suportado: {file_path}")
            return None

        # Normalizar colunas
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        available_columns = [col for col in COLUMN_NAMES if col in df.columns]
        df = df[available_columns]

        # Limpeza básica de strings
        string_columns = ["uf", "municipio", "evento", "agente", "arma", "faixa_etaria", "abrangencia", "formulario"]
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace(["nan", "None", "", "null"], pd.NA)

        # Otimizar dtypes
        df = self._optimize_dtypes(df)

        # Adicionar metadado
        df["arquivo_origem"] = os.path.basename(file_path)

        # Salvar cache em Parquet
        if not IS_VERCEL:
            try:
                df.to_parquet(cache_path, compression="snappy", index=False)
            except Exception as e:
                logger.warning(f"Erro ao salvar cache parquet: {e}")

        return df

    def _optimize_dtypes(self, df):
        import pandas as pd
        numeric_columns = ["feminino", "masculino", "nao_informado", "total_vitima", "total", "total_peso"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
                if df[col].dtype == "float64" and df[col].notnull().all():
                    df[col] = df[col].astype("int64")

        categorical_columns = ["uf", "evento", "agente", "arma", "faixa_etaria", "abrangencia", "formulario"]
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].astype("category")

        if "municipio" in df.columns:
            df["municipio"] = df["municipio"].astype("string")

        return df

    def _load_all_data(self):
        import pandas as pd
        import glob
        from datetime import datetime
        from concurrent.futures import ThreadPoolExecutor, as_completed

        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
            logger.info(f"Pasta '{DATA_FOLDER}' criada. Adicione arquivos nela.")
            return pd.DataFrame(columns=COLUMN_NAMES)

        files = []
        files.extend(glob.glob(os.path.join(DATA_FOLDER, "*.xlsx")))
        files.extend(glob.glob(os.path.join(DATA_FOLDER, "*.csv.xz")))
        files.extend(glob.glob(os.path.join(DATA_FOLDER, "*.csv.gz")))

        if not files:
            logger.info("Nenhum arquivo encontrado em 'dados'")
            return pd.DataFrame(columns=COLUMN_NAMES)

        logger.info(f"Carregando {len(files)} arquivos...")
        start_time = datetime.now()
        dataframes = []

        max_workers = min(2 if IS_VERCEL else 4, len(files))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(self._load_single_file, f): f for f in files}
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    df = future.result()
                    if df is not None:
                        dataframes.append(df)
                except Exception as e:
                    logger.error(f"Erro processando {file_path}: {e}")

        if not dataframes:
            raise RuntimeError("Nenhum arquivo foi carregado com sucesso")

        combined = pd.concat(dataframes, ignore_index=True, sort=False)
        combined = self._optimize_dtypes(combined)

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Dados carregados: {len(combined):,} registros em {duration:.2f}s")
        return combined

    # ==== Métodos de consulta (iguais ao seu código) ====

    def get_anos_disponiveis(self):
        import pandas as pd, re
        cache_key = "anos_disponiveis"
        if cache_key in self._cached_values:
            return self._cached_values[cache_key]

        anos = set()
        if "data_referencia" in self.df.columns:
            try:
                anos.update(pd.to_datetime(self.df["data_referencia"], errors="coerce").dt.year.dropna().astype(int))
            except:
                pass
        if "arquivo_origem" in self.df.columns:
            for arquivo in self.df["arquivo_origem"].unique():
                for match in re.findall(r"\b(20\d{2})\b", str(arquivo)):
                    anos.add(int(match))

        result = sorted(list(anos))
        self._cached_values[cache_key] = result
        return result

    def get_arquivos_carregados(self):
        cache_key = "arquivos_carregados"
        if cache_key in self._cached_values:
            return self._cached_values[cache_key]

        if "arquivo_origem" not in self.df.columns:
            return []
        arquivo_counts = self.df["arquivo_origem"].value_counts()
        result = [{"arquivo": a, "registros": int(c)} for a, c in arquivo_counts.items()]
        result = sorted(result, key=lambda x: x["arquivo"])
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
            df = df[df["uf"].str.upper() == uf.upper()]
        result = sorted(df["municipio"].dropna().unique().tolist())
        self._cached_values[cache_key] = result
        return result

    def ocorrencias(self, uf: str, municipio: str = None, evento: str = None, ano: int = None):
        import pandas as pd
        if "uf" not in self.df.columns:
            raise ValueError("Coluna 'uf' não encontrada")

        mask = self.df["uf"].str.upper() == uf.upper()
        if municipio:
            mask &= self.df["municipio"].str.upper() == municipio.upper()
        if evento:
            mask &= self.df["evento"].str.upper() == evento.upper()
        if ano:
            if "data_referencia" in self.df.columns:
                try:
                    mask &= pd.to_datetime(self.df["data_referencia"], errors="coerce").dt.year == ano
                except:
                    pass
            if "arquivo_origem" in self.df.columns and not mask.any():
                mask = self.df["arquivo_origem"].str.contains(str(ano), na=False)

        filtro = self.df[mask]
        if filtro.empty:
            return None
        return filtro.to_dict(orient="records")

    def clear_cache(self):
        self._cached_values.clear()
        logger.info("Cache em memória limpo")

    def get_memory_usage(self):
        memory_mb = self.df.memory_usage(deep=True).sum() / 1024 / 1024
        return {
            "dataframe_size_mb": round(memory_mb, 2),
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "cached_values": len(self._cached_values),
        }
