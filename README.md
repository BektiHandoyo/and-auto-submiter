# 🏴 Flask Flag Submitter API

Sebuah web service sederhana berbasis Flask untuk menyubmit flag ke platform CTF melalui HTTP. Mendukung auto-authentication menggunakan email dan password dari `.env`, serta fallback ke `token.txt`.

---

## 🔧 Fitur

- Kirim flag ke API CTF lewat endpoint HTTP (`/submit`)
- Auto-re-authentication saat token kadaluarsa atau salah
- Token baru akan disimpan otomatis di `token.txt`
- Server akan shutdown otomatis jika kredensial tidak tersedia atau auth gagal
- Mendukung validasi format flag dan timeout

---

## 📁 Struktur File

```
.
├── app.py             # Flask server
├── submiter.py        # Kelas Submitter untuk submit flag
├── token.txt          # Berisi token hasil login
├── .env               # Konfigurasi rahasia (URL, email, password, dll)
├── requirements.txt   # (Opsional) Berisi dependensi
```

---

## 📦 Installasi

### 1. Clone dan install dependensi

```bash
pip install -r requirements.txt
```

Jika belum ada `requirements.txt`, gunakan:

```bash
pip install flask requests python-dotenv
```

---

## ⚙️ Konfigurasi

### 2. Siapkan file `.env`

Buat file `.env` di root folder dan isi:

```env
API_URL=http://example.com
FLAG_FORMAT=LKS{
EMAIL=your@email.com
PASSWORD=your_password
PORT=8900
```

> ⚠️ `EMAIL` dan `PASSWORD` bersifat opsional. Jika tidak disediakan, kamu harus menaruh token di `token.txt` secara manual.

---

### 3. Siapkan token awal (jika tidak pakai auto-auth)

Buat file `token.txt` dan isi dengan JWT token awal:

```txt
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🚀 Menjalankan Server

```bash
python app.py
```

Server akan berjalan di `http://localhost:8900` (default bisa diubah lewat `PORT` di `.env`)

---

## 📮 Mengirim Flag

Gunakan `curl`, Postman, atau tool lain:

```bash
curl -X POST http://localhost:8900/submit      -H "Content-Type: application/json"      -d '{"flag": "LKS{example_flag}"}'
```

### 💡 Response Sukses

```json
{
  "status": "success",
  "verdict": "flag is correct."
}
```

### 💥 Response Gagal (contoh)

```json
{
  "status": "error",
  "message": "Auto-authentication gagal total. Server dihentikan.",
  "detail": "EMAIL atau PASSWORD tidak ditemukan"
}
```

---

## 🔁 Mekanisme Auto-Auth

Jika token yang disimpan di `token.txt` tidak valid:
1. Server akan mencoba login ke endpoint `/api/v2/authenticate` menggunakan `EMAIL` dan `PASSWORD` dari `.env`
2. Jika berhasil, token baru akan disimpan dan request akan diulang sekali.
3. Jika gagal, server akan shutdown otomatis dan error dikembalikan ke klien.

---

## 🧪 Jalankan Submitter secara Manual

```bash
python submiter.py "LKS{example_flag}"
```

---

## 🛑 Catatan Keamanan

- Jangan commit `.env` atau `token.txt` ke repositori publik
- Token bersifat sensitif, simpan hanya di sistem lokal yang aman

---

## 🧩 Credits

Dibuat untuk kebutuhan Capture The Flag (CTF) internal dan integrasi tim otomatisasi flag submission.