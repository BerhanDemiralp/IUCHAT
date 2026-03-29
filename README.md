# IÜC Chat Bot

İstanbul Üniversitesi-Cerrahpaşa (IÜC) için geliştirilen **RAG (Retrieval-Augmented Generation)** tabanlı bir sohbet botu uygulamasıdır.

Üniversite belgeleri üzerinden semantic search yaparak kullanıcılara ilgili bilgileri getirir.

## Özellikler

- **Semantic Search**: SentenceTransformer (BAAI/bge-m3) ile vektör araması
- **Hızlı Retrieval**: Supabase pgvector ile cosine similarity search
- **Modern UI**: Streamlit ile kullanıcı dostu arayüz
- **Türkçe Destek**: Türkçe belgeler üzerinde çalışır

## Mimari

```
app/
├── main.py              # Streamlit entry point
├── config.py            # Environment / settings
├── models.py            # Data classes
├── services/
│   ├── embedder.py      # SentenceTransformer wrapper
│   ├── retriever.py     # Supabase RPC call
│   └── supabase_client.py  # Supabase client singleton
└── ui/
    └── components.py    # Streamlit UI widgets

scripts/
├── create_tables.sql    # pgvector extension + tables + index
├── ingest_logic.sql     # Staging → final table insert
└── match_function.sql   # match_chunks RPC function

data/
├── splits/              # CSV data splits for upload
└── chunk-sentence-512_embedded.csv     # main CSV
```

## Gereksinimler

- Python 3.10+
- [Supabase](https://supabase.com) projesi (pgvector etkin)

## Kurulum

### 1. Clone & install

```bash
git clone <repo-url>
cd <repo-dir>
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your Supabase URL and key.

### 3. Run SQL scripts in Supabase

**Supabase → SQL Editor** - scriptleri sırayla çalıştırın:

| Adım | Dosya                        | Açıklama                                                 |
| ---- | ---------------------------- | -------------------------------------------------------- |
| 1    | `scripts/create_tables.sql`  | pgvector extension, staging + final table, IVFFlat index |
| 2    | `scripts/match_function.sql` | `match_chunks` RPC fonksiyonu                            |

### 4. Veri Yükleme

Verileri Supabase'e yüklemek için:

```bash
python upload_to_supabase.py
```

### 5. Uygulamayı Çalıştır

```bash
streamlit run app/main.py
```

Uygulama `http://localhost:8501` adresinde açılır.

## Kullanım

1. Sorunuzu metin kutusuna yazın
2. **top-k** slider'ı ile sonuç sayısını ayarlayın (varsayılan: 10)
3. **Ara** butonuna tıklayın
4. Benzerlik skorları ile birlikte sonuçları görüntüleyin

## Lisans

MIT License
