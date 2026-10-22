# Data dummy

Seluruh data di folder ini fiktif. Tidak ada data perusahaan, karyawan, atau proyek bertanda kerahasiaan. NPWP (`tax_id`) di vendor hanya deretan angka acak.

Buat ulang: `python scripts/generate_data.py` (butuh `pandas` dan `numpy`). Seed tetap 42, jadi hasilnya identik setiap kali.

## Tabel di `raw/`

| File | Baris | Keterangan |
|---|---|---|
| items_source.csv | 2.000 | Master barang dari SCM. `uom` memakai satuan lama (PC, BX, KGS, ...). |
| items_erp.csv | 1.990 | Hasil unggah ke ERP, sudah berisi error. `uom` seharusnya satuan baru. |
| vendors_source.csv | 300 | Master vendor dari Finance. |
| vendors_erp.csv | 299 | Hasil unggah ke ERP, sudah berisi error. |
| mapping_codes.csv | 2.000 | Kode lama ke kode baru, satuan lama ke satuan baru. |
| po_lines.csv | 15.000 | Baris PO. 2025-01-01 sampai 2026-06-30. |
| gr_lines.csv | 14.000 | Baris penerimaan barang. 1.000 baris PO belum diterima. |
| invoice_lines.csv | 12.060 | Baris faktur, termasuk 60 baris ganda (E10). |

`error_truth.csv` ada di folder `data/`, 1.620 baris: `record_key`, `error_code`, `table_name`.

## Perbedaan dari Lampiran PRD (bagian 18)

`po_lines`, `gr_lines`, dan `invoice_lines` punya satu kolom tambahan, `batch_id` (B01 sampai B05, berurutan menurut tanggal PO). Kolom ini dibutuhkan untuk slicer batch dan tren error per batch (B3, B8). Hapus kalau tidak dipakai.

Tabel `tracker_items` tidak dibuat. PRD menyebutnya "dibuat dari exception", jadi isinya datang dari sheet Exceptions milikmu (fase 3).

## Jumlah error yang disisipkan

| Kode | Jumlah | Di mana | Cara menyisipkan |
|---|---|---|---|
| E1 | 46 | items_erp 40, vendors_erp 6 | Baris sumber dihapus dari ERP |
| E2 | 35 | items_erp 30, vendors_erp 5 | Baris ERP disalin, diselipkan di posisi acak |
| E3 | 60 | items_erp | `unit_price` berbeda 0,6x sampai 1,4x dari sumber |
| E4 | 707 | items_erp 80, vendors_erp 12 (kode); po 225, gr 210, invoice 180 (tanggal) | Kode: spasi di ujung, huruf kecil, atau nol di depan hilang. Tanggal: `dd/mm/yyyy`, `dd-Mon-yyyy`, atau `yyyy/mm/dd` |
| E5 | 46 | items_erp 40 (`uom` atau `vendor_code` kosong), vendors_erp 6 (`tax_id` atau `payment_term` kosong) | Kolom dikosongkan |
| E6 | 40 | items_erp | `uom` memakai satuan lama atau satuan baru yang salah |
| E7 | 150 | po_lines | `item_code` menunjuk kode yang tidak ada (BRG-9xxxx) |
| E8 | 356 | po_lines | Setengah: nilai faktur beda 10 sampai 30 persen. Setengah: kuantitas diterima kurang dari PO |
| E9 | 120 | invoice_lines | 60 faktur tanpa PO, 60 faktur untuk baris PO yang belum ada penerimaan barang |
| E10 | 60 | invoice_lines | `invoice_id` sama muncul dua kali, keduanya `paid_flag` = Y |

Tingkat dasar memakai angka PRD bagian 7.3. Pengecualian: E4 pada tanggal PO, GR, dan faktur memakai 1,5 persen (bukan 4 persen) supaya E4 tidak menutupi jenis error lain. Catat angka ini di README proyekmu.

Peluang error tidak merata. Batch awal (B01) punya sekitar 2,7 kali peluang batch akhir (B05), jadi tren perbaikan terlihat di dashboard.

## Arti `record_key`

| Error | record_key |
|---|---|
| E1 sampai E6 | Kode bersih dari tabel sumber (`item_code` atau `vendor_code`), bukan kode kotor di ERP |
| E4 pada PO | `po_line_id` |
| E4 pada GR | `gr_id` |
| E4 pada faktur | `invoice_id` |
| E7 | `po_line_id` |
| E8 | `po_line_id` (baris PO yang tiga nilainya tidak cocok) |
| E9, E10 | `invoice_id` |

Satu record hanya kena satu error per tabel, jadi pasangan (`record_key`, `error_code`) unik.

## Aturan yang dipakai generator

- Kolom wajib: barang = `item_code`, `uom`, `unit_price`, `vendor_code`; vendor = `vendor_code`, `payment_term`, `tax_id`.
- Format kode: `BRG-` + 5 digit, `VND-` + 4 digit. Format tanggal standar: ISO `yyyy-mm-dd`.
- Satuan benar di ERP = `uom_new` dari `mapping_codes` untuk kode barang yang sama.
- Toleransi three-way match: Rp 1.000. Sekitar 6 persen faktur sengaja selisih Rp 1 sampai Rp 500 dari nilai PO. Itu bukan error dan harus tetap MATCH. Dengan toleransi 0, baris-baris itu berubah jadi EXCEPTION (cocok untuk uji toleransi di PRD bagian 14).
- Baris PO hanya memakai barang dan vendor yang ada di ERP. Satu-satunya pengecualian adalah E7, jadi E1 tidak menambah temuan R-07.
- Kode di ERP harus distandarkan dulu (trim, huruf besar, nol di depan) sebelum dicocokkan. Tanpa itu, kode kotor akan terbaca HILANG.

## Saat membuka di Excel

Impor lewat Power Query dengan semua kolom bertipe teks, lalu ubah tipe belakangan. Buka CSV langsung di Excel mengubah tanggal campur dan bisa merusak kolom kode.

## Hasil cek mandiri

Aturan R-01 sampai R-10 yang ditulis ulang secara terpisah di Python menangkap 1.620 dari 1.620 error, tanpa temuan tambahan (recall 100 persen, precision 100 persen). Angka ini hanya membuktikan kunci jawaban konsisten dengan datanya. Target recall 95 persen dan precision 90 persen di PRD tetap diuji pada deteksi di workbook-mu.
