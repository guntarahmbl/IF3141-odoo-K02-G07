# IF3141 Sistem Informasi - Odoo Setup

## Introduction

Odoo merupakan *Enterprise Resource Planning System* yang mampu melakukan implementasi modul modul kustom untuk menyelesaikan permasalahan proses bisnis pada suatu perusahaan.

Odoo memberikan opsi *on-premise solution* sehingga developer dapat melakukan implementasi kustom modul pada local environment.

Repository ini diperuntukkan untuk Tugas Besar IF3141 Sistem Informasi. Untuk memulai silakan melakukan fork dan membuat repository private untuk workspace setiap kelompok.


## Pre-requisites
Odoo diimplementasikan dengan Python environment dan database PostgreSQL. Repository ini sudah membungkus service aplikasi dan database melalui Docker.

Sebelum memulai, pastikan dependency berikut sudah terpasang:

1. Docker Desktop
	- Download: https://www.docker.com/products/docker-desktop/
2. Python 3.11
	- Digunakan untuk virtual environment (venv) pada proses development modul

## Struktur Direktori

- `/config`
	- Untuk menyimpan konfigurasi Odoo
- `/custom_addons`
	- Tempat pengerjaan modul kustom
- `/dump`
	- Database dump yang dapat diakses scripts untuk proses import/export
- `/scripts`
	- Untuk melakukan database migration
- `docker-compose.yml`
	- Orchestration service Odoo dan PostgreSQL

## Step-by-step Installation

1. Jalankan service Odoo dan PostgreSQL:

	```bash
	docker compose up -d
	```

2. Buka aplikasi pada browser:
	- http://localhost:8069

3. Login menggunakan kredensial default:
	- Username: `admin`
	- Password: `admin`

4. Aktifkan mode developer:
	- Masuk ke **Settings**
	- Nyalakan **Developer Mode / Developer Access**

5. Buat Python virtual environment pada workspace:

	```bash
	python3.11 -m venv .venv
	source .venv/bin/activate
	pip install --upgrade pip
	pip install -r requirements.txt
	```

6. Implementasikan modul pada folder:
	- `custom_addons/`

7. Setelah implementasi modul selesai, lakukan update daftar aplikasi:
	- Masuk ke menu **Apps**
	- Pilih **Update Apps List**

8. Jika melakukan perubahan terhadap isi modul (modifying database), jangan lupa lakukan langkah database migration dengan mengikuti step di heading bawah ini.

## Database Migration

Odoo menggunakan local database pada implementasinya. Maka dari itu dibutuhkan migration system yang dapat dilakukan melakukan **dump db** atau **import db**. Sebelum melakukan migration jangan lupa untuk selalu mematikan service odoo & databasenya dengan menjalankan :

```bash 
docker compose down
```

Apabila terdapat perubahan pada database dan perubahan tersebut ingin diteruskan ke anggota tim lain, lakukan export database terlebih dahulu menggunakan script pada folder `scripts`.

- macOS/Linux:

  ```bash
  ./scripts/export_db.sh
  ```

- Windows:

  ```bat
  scripts\export_db.cmd
  ```

Untuk melanjutkan pengerjaan dari hasil perubahan database rekan tim, lakukan import database terlebih dahulu :

- macOS/Linux:

  ```bash
  ./scripts/import_db.sh
  ```

- Windows:

  ```bat
  scripts\import_db.cmd
  ```

## Kontrak Payment Gateway

### Field `Tagihan` yang dipakai 

- `status_lunas`: sumber kebenaran untuk status belum/lunas.
- `link_payment`: URL invoice Xendit yang dikirim ke pelanggan.
- `xendit_invoice_id`: ID invoice yang dikembalikan Xendit.
- `xendit_external_id`: external ID internal untuk mencocokkan callback webhook.
- `pembayaran_ids`: relasi riwayat pembayaran (model `manajemen_piutang.pembayaran`).

### Alur Invoice

1. Pengguna klik `Kirim E-Invoice` pada form Tagihan.
2. Odoo memanggil API Xendit untuk membuat invoice dan menyimpan `link_payment`.
3. Pelanggan membayar melalui link Xendit yang dibuat.
4. Xendit mengirim webhook ke `/xendit/webhook`.
5. Odoo mengubah `status_lunas` menjadi `lunas` dan membuat record `pembayaran`.

### Kontrak Webhook

- Endpoint: `/xendit/webhook`
- Header wajib: `x-callback-token`
- Event yang didukung:
	- `Invoices paid`
	- `Invoices expired`
	- `FVA paid` (jika menggunakan Virtual Account)
	- `E-Wallet Payment Status` (untuk QRIS/OVO/Dana/ShopeePay jika diperlukan)
	- `QR code paid` (jika menampilkan QRIS)

### Pemetaan payload yang dipakai handler

- `id` atau `data.id` → ID invoice Xendit.
- `external_id` atau `data.external_id` → external ID internal untuk pencocokan.
- `status` atau `data.status` → menentukan event `PAID`/`EXPIRED` jika tersedia.
- `paid_amount`, `amount`, atau `data.paid_amount` → jumlah yang diterima.
- `payment_id` → dianggap sinyal pembayaran (sering muncul pada FVA).
- `expired_at` → dianggap sinyal kadaluarsa.


