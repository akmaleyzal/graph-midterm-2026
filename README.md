# UTS Graf Sains Data — Rekomendasi RetailRocket dengan Neo4j

Pengerjaan Ujian Tengah Semester mata kuliah **Graf Sains Data** (S1 Sains Data, FMIPA Universitas
Negeri Surabaya, Gasal 2026/2027), materi *Python Driver untuk Neo4j dan Rekomendasi*.

| | |
|---|---|
| Nama | Akmaley Zal |
| NIM | ‹NIM› |
| Kelas | ‹Kelas› |

Seluruh jawaban dan penjelasan ada di **[`main.ipynb`](main.ipynb)**.

## Isi repositori

| Path | Keterangan |
|---|---|
| `main.ipynb` | Notebook jawaban: Tugas Pendahuluan 1.1–1.3 dan Soal UTS 2.1–2.2 |
| `scripts/import_events.py` | Skrip impor CSV → Neo4j (adaptasi kode soal 1.3), dibuat dari notebook |
| `data/events_filtered.csv` | Data interaksi hasil filter periode P1 + P2 (kolom `fold`) |
| `ecommerce-dataset/` | Dataset asli RetailRocket (`events.csv`, `category_tree.csv`) |
| `pyproject.toml`, `uv.lock`, `requirements.txt` | Dependensi |

## Periode data

| Fold | Rentang (UTC) | Peran |
|---|---|---|
| P1 | 7 Jun 2015 – 18 Jul 2015 | training |
| P2 | 19 Jul 2015 – 1 Agu 2015 | testing |

## Cara menjalankan

1. Python 3.10 + [uv](https://docs.astral.sh/uv/): `uv sync`.
   Alternatif sesuai soal: `uv venv myvenv --python 3.10`, aktifkan, lalu `uv pip install -r requirements.txt`.
2. Neo4j: buat dan jalankan instance lokal di Neo4j Desktop (server 2026.x), lalu buat berkas `.env`:

   ```
   USN=neo4j
   PASSWD=<password>
   DBNAME=midterm-exam
   # URI=neo4j://127.0.0.1:7687   (opsional)
   ```

   Database `DBNAME` dibuat otomatis oleh notebook bila belum ada.
3. Dataset: unduh dari Kaggle lalu ekstrak ke `ecommerce-dataset/`.

   ```
   curl.exe -L -o ecommerce-dataset.zip https://www.kaggle.com/api/v1/datasets/download/retailrocket/ecommerce-dataset
   ```

   `item_properties_part*.csv` (> 100 MB) tidak disertakan di repositori dan tidak dipakai.
4. Buka `main.ipynb` dengan kernel `.venv`, lalu *Run All*. Impor ke Neo4j hanya berjalan bila graf belum lengkap.

Skrip impor juga bisa dipakai langsung dari terminal:

```
uv run python scripts/import_events.py -s data -f events_filtered.csv --reset
```

## Penyesuaian terhadap kode soal

- Driver `neo4j` 4.2.1 → 6.4.1. Kode soal memakai `execute_query`, `RoutingControl`, dan `execute_write`
  yang baru tersedia mulai driver 5, dan driver 4.2.1 tidak bisa terhubung ke server Neo4j 2026.x (protokol Bolt).
- Subquery impor memakai `CALL (v, i, row) { ... }`; bentuk `CALL { WITH ... }` sudah deprecated.
- Skrip impor: argumen tambahan `--database`, `--file`, `--batch-size`, `--reset`; constraint unik untuk
  `Visitor` dan `Item`; properti `fold` pada relasi; `transactionid` dibaca sebagai string.

## Ringkasan hasil

| Bagian | Hasil |
|---|---|
| Data P1 ∪ P2 | 1.193.338 event (P1 872.056 · P2 321.282); 460 baris duplikat dibuang |
| Subgraph Neo4j | 621.168 `Visitor`, 163.295 `Item`; relasi `VIEWED` 1.153.867, `ADDED_TO_CART` 29.615, `BOUGHT` 9.856 |
| VSM user / item | 455.767 × 142.244 / 142.244 × 455.767, density 1,05×10⁻⁵ |
| Proyeksi terpilih | item–item: node 3,2× lebih sedikit dan vektor lebih padat daripada user–user |
| Similarity | cosine + minimal 2 visitor bersama, k = 5 → 77.316 relasi `SIMILAR` |
| User acak (seed 2026) | visitor 1174645 → item iklan 294965, 194958, 244571 |
| Hit@5 / NDCG@5 user tersebut | 0 / 0 |
| Rata-rata 2.034 user eligible (Hit@5 / NDCG@5) | item-KNN 0,0383 / 0,0151 · user-KNN 0,0251 / 0,0105 · popularitas 0,0034 / 0,0012 |
