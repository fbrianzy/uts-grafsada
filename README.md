# UTS Graf Sains Data
Rekomendasi item-item Retail Rocket dengan Neo4j dan Python driver.

Yang dibutuhkan:
- Neo4j Desktop (Versi 2026.09.0)
- VSCode

## Setup Neo4j
Buat instance baru di Neo4j Desktop.

Khusus untuk laptop dengan RAM 16 GB, wajib setting file `neo4j.conf` lebih dulu. Tambahkan baris berikut:
```conf
server.memory.heap.initial_size=2G
server.memory.heap.max_size=4G
dbms.memory.transaction.total.max=0
```
Jika sudah, nyalakan instance tersebut.

## Persiapan Project
Buka terminal dan clone repository ini:
```powershell
git clone https://github.com/fbrianzy/uts-grafsada.git
cd uts-grafsada
```

Buat virtual environment:
```powershell
python -m venv grafsada
```

Aktifkan virtual environment:
```powershell
grafsada\Scripts\activate
```

Install semua dependencies yang dibutuhkan:
```powershell
pip install -r requirements.txt
```

## Cara Menjalankan Kode
- Pastikan file `env` sudah diisi. Cek file `.env.example` untuk melihat format pengisiannya.
- Buka file `UTS.ipynb` di VSCode.
- Pastikan kernel Python yang dipilih sudah sesuai dengan venv yang dibuat tadi (`grafsada`).
- Pilih menu Restart > Run All untuk membersihkan sisa output atau cache sebelumnya dan menjalankan seluruh kode.
