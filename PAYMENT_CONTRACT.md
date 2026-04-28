# PAYMENT CONTRACT — Manajemen Piutang (Xendit)

Dokumen ringkas ini menjelaskan nama-nama field, endpoint webhook, dan contoh curl untuk pengujian lokal.

## Field dan model yang menjadi kontrak

- Model: `manajemen_piutang.tagihan`
  - `status_lunas` — nilai: `belum_lunas` / `lunas`
  - `link_payment` — URL invoice (ditampilkan ke pelanggan)
  - `xendit_invoice_id` — ID invoice dari Xendit
  - `xendit_external_id` — external ID internal untuk mencocokkan callback webhook
  - `pembayaran_ids` — relasi ke model `manajemen_piutang.pembayaran`

- Model: `manajemen_piutang.pembayaran`
  - `id_transaksi` — ID transaksi/gateway
  - `nominal_masuk` — jumlah masuk
  - `waktu_bayar` — timestamp
  - `status_settlement` — teks status settlement

## Endpoint webhook

- URL publik yang digunakan: `/xendit/webhook`
- Header wajib: `x-callback-token: <CALLBACK_TOKEN>`

Contoh payload yang didukung handler (ringkas):
- Invoice paid: JSON berisi `id` atau `external_id` dan `status":"PAID"` serta `paid_amount`.
- FVA paid: JSON berisi `payment_id`, `external_id`, `amount`.

## Nama konfigurasi di Odoo (ir.config_parameter)

- `manajemen_piutang.xendit_secret_api_key` — Xendit secret key (dipakai sebagai HTTP Basic auth username)
- `manajemen_piutang.xendit_webhook_token` — token callback yang harus cocok dengan header `x-callback-token`
- `web.base.url` — base URL Odoo (set ke ngrok saat testing)

## Contoh cara mengisi (via UI)

1. Aktifkan Developer Mode di Odoo.
2. Buka Settings → Manajemen Piutang.
3. Masukkan `Xendit Secret API Key` dan `Xendit Callback Token`, lalu simpan.

## Contoh pengisian cepat (via DB) — GANTI <VALUE> sebelum dijalankan

```bash
docker compose exec db psql -U odoo -d postgres \
  -c "INSERT INTO ir_config_parameter (key, value) VALUES ('manajemen_piutang.xendit_secret_api_key','<XENDIT_KEY>') ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;"

docker compose exec db psql -U odoo -d postgres \
  -c "INSERT INTO ir_config_parameter (key, value) VALUES ('manajemen_piutang.xendit_webhook_token','<CALLBACK_TOKEN>') ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;"
```

## Contoh curl untuk mensimulasikan webhook (ganti `<TOKEN>` dan URL ngrok)

Invoice paid:

```bash
curl -X POST 'https://<YOUR_NGROK>/xendit/webhook' \
  -H 'Content-Type: application/json' \
  -H 'x-callback-token: <TOKEN>' \
  -d '{"id":"579c8d61f23fa4ca35e52da4","external_id":"invoice_123124123","status":"PAID","paid_amount":50000}'
```

FVA paid (contoh payload minimal):

```bash
curl -X POST 'https://<YOUR_NGROK>/xendit/webhook' \
  -H 'Content-Type: application/json' \
  -H 'x-callback-token: <TOKEN>' \
  -d '{"payment_id":"1487156512722","external_id":"fixed-va-1487156410","amount":80000}'
```

