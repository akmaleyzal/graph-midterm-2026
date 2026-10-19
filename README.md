# UTS Graf Sains Data: Rekomendasi RetailRocket dengan Neo4j

Pengerjaan Ujian Tengah Semester mata kuliah **Graf Sains Data** (S1 Sains Data, FMIPA Universitas
Negeri Surabaya, Gasal 2026/2027), materi *Python Driver untuk Neo4j dan Rekomendasi*.

| | |
|---|---|
| Nama | Akmal Rizal |
| NIM | 23031554078 |
| Kelas | 2023A |

Seluruh jawaban, kode, dan penjelasan ada di **[`main.ipynb`](main.ipynb)**. Notebook ini satu-satunya yang
perlu dijalankan: mulai dari data mentah, filter periode, impor ke Neo4j, sampai evaluasi rekomendasi.

## Isi repositori

| Path | Keterangan |
|---|---|
| `main.ipynb` | Notebook jawaban: Tugas Pendahuluan 1.1–1.3 dan Soal UTS 2.1–2.2 |
| `data/events_filtered.csv` | Data interaksi hasil filter periode P1 + P2 (kolom `fold`), dibuat ulang oleh notebook |
| `ecommerce-dataset/` | Dataset asli RetailRocket (`events.csv`, `category_tree.csv`) |
| `pyproject.toml`, `uv.lock`, `requirements.txt` | Dependensi |

## Periode data

| Fold | Rentang (UTC) | Peran |
|---|---|---|
| P1 | 7 Jun 2015 – 18 Jul 2015 | training |
| P2 | 19 Jul 2015 – 1 Agu 2015 | testing |

## Cara menjalankan

> **Peringatan:** notebook mengosongkan seluruh isi database `neo4j` (Total Reset pada 1.2) dan database
> `DBNAME` (sebelum impor, bila graf belum lengkap). Gunakan instance Neo4j yang tidak berisi data lain.

1. Python 3.10 + [uv](https://docs.astral.sh/uv/): `uv sync`.
   Alternatif sesuai: `uv venv --python 3.10`, aktifkan di terminal `.venv/Source/activate` atau `(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& ".venv\Scripts\Activate.ps1")`, lalu `uv pip install -r requirements.txt`.
2. Neo4j: buat dan jalankan instance lokal di Neo4j Desktop (server 2026.x), lalu buat berkas `.env`:

   ```
   USN=neo4j
   PASSWD=<password>
   DBNAME=midterm-exam
   # URI=neo4j://127.0.0.1:7687   (opsional)
   ```

   Database `DBNAME` dibuat otomatis oleh notebook bila belum ada.
3. Dataset: `events.csv` dan `category_tree.csv` sudah disertakan di `ecommerce-dataset/`. Untuk mengunduh ulang
   dari Kaggle (opsional), ekstrak hasil perintah berikut ke folder yang sama:

   ```
   curl.exe -L -o ecommerce-dataset.zip https://www.kaggle.com/api/v1/datasets/download/retailrocket/ecommerce-dataset
   ```

   `item_properties_part*.csv` (> 100 MB) tidak disertakan di repositori dan tidak dipakai.

   Cek keaslian data mentah: `events.csv` berisi 2.756.101 baris data dengan SHA-256
   `3745aa83238b1e6d44d8fda209807899f420084398f94ddf745f3cbcfecbf9e7`
   (PowerShell: `Get-FileHash ecommerce-dataset/events.csv`; Linux/Git Bash: `sha256sum ecommerce-dataset/events.csv`).
4. Buka `main.ipynb` dengan kernel `.venv`, lalu *Run All*. Impor ke Neo4j hanya berjalan bila graf belum lengkap.

## Penyesuaian terhadap kode soal

- Driver `neo4j` 4.2.1 → 6.4.1. Kode soal memakai `execute_query`, `RoutingControl`, dan `execute_write`
  yang baru tersedia mulai driver 5, dan driver 4.2.1 tidak bisa terhubung ke server Neo4j 2026.x (protokol Bolt).
- Subquery impor memakai `CALL (v, i, row) { ... }`; bentuk `CALL { WITH ... }` sudah deprecated.
- Kode impor soal 1.3 dijalankan sebagai fungsi di notebook, tanpa berkas skrip dan argparse: constraint unik
  untuk `Visitor` dan `Item`, batch 10.000 baris, properti `fold` pada relasi, `transactionid` dibaca sebagai
  string, dan opsi reset sebelum impor.

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
