"""Generator data dummy untuk proyek ERP Data Check & Tracker.
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

N_ITEMS, N_VENDORS = 2000, 300
N_PO, N_GR, N_INV_BASE = 15000, 14000, 11880
N_BATCH = 5

# Peluang error dikalikan angka ini per batch. Batch awal lebih buruk,
# supaya pertanyaan B8 (kualitas membaik?) punya tren untuk dilihat.
BATCH_W = np.array([1.6, 1.3, 1.0, 0.8, 0.6])

# Tingkat dasar dari PRD bagian 7.3. E4 untuk kolom tanggal transaksi
# dibuat lebih rendah supaya E4 tidak menutupi jenis error lain.
RATE = {"E1": 0.02, "E2": 0.015, "E3": 0.03, "E4": 0.04, "E5": 0.02,
        "E6": 0.02, "E7": 0.01, "E8": 0.03, "E9": 0.01, "E10": 0.005}
RATE_E4_TX = 0.015
INV_BASE_FOR_RATE = 12000  # E9 dan E10 dihitung dari jumlah faktur sekitar 12.000

# Selisih nilai faktur di bawah angka ini sah (pembulatan). Toleransi default
# di sheet Rules adalah Rp 1.000, jadi baris ini harus tetap MATCH.
NOISE_MAX = 500
NOISE_SHARE = 0.06

UOM_MAP = {"PC": "PCS", "BX": "BOX", "KGS": "KG", "LTR": "L",
           "MTR": "M", "ST": "SET", "RL": "ROLL", "DZ": "DZN"}
DATE_FMTS = ["%d/%m/%Y", "%d-%b-%Y", "%Y/%m/%d"]

CATS = {
    "Fastener": (["Baut Hex", "Mur", "Ring Plat", "Sekrup Kayu", "Baut Angkur"],
                 ["M6", "M8", "M10", "M12", "M16"],
                 ["Galvanis", "Stainless", "Hitam"], ["PC", "BX"]),
    "Electrical": (["Kabel NYM", "Saklar", "MCB", "Stop Kontak", "Lampu LED"],
                   ["2x1.5mm", "16A", "10W", "20W", "3x2.5mm"],
                   ["Standar", "Heavy Duty"], ["PC", "RL", "MTR"]),
    "Plumbing": (["Pipa PVC", "Knie", "Sambungan T", "Keran", "Seal Tape"],
                 ["1/2 inch", "3/4 inch", "1 inch", "2 inch"],
                 ["Putih", "Kuningan", "PVC"], ["MTR", "PC", "RL"]),
    "Packaging": (["Kardus", "Lakban", "Bubble Wrap", "Plastik PE", "Stretch Film"],
                  ["30x20", "40x30", "50x50", "60cm", "5cm"],
                  ["Putih", "Bening", "Coklat"], ["PC", "RL", "BX"]),
    "Chemical": (["Cat Besi", "Thinner", "Pelumas", "Lem Epoxy", "Pembersih Industri"],
                 ["1L", "5L", "20L", "500ml"], ["Standar", "Food Grade"],
                 ["LTR", "KGS"]),
    "Safety": (["Sarung Tangan", "Helm Proyek", "Masker", "Kacamata", "Sepatu Safety"],
               ["Size M", "Size L", "Size 42", "All Size"],
               ["Karet", "Kulit", "Katun"], ["PC", "DZ", "ST"]),
    "Stationery": (["Kertas A4", "Bolpoin", "Map Folder", "Spidol", "Staples"],
                   ["80gsm", "0.5mm", "F4", "Hitam", "No.10"],
                   ["Standar", "Premium"], ["BX", "DZ", "PC"]),
    "Tools": (["Obeng", "Kunci Pas", "Tang", "Palu", "Meteran"],
              ["6mm", "12mm", "8 inch", "5m", "Set 8"],
              ["Chrome Vanadium", "Baja", "Fiber"], ["PC", "ST", "MTR"]),
}
VENDOR_W1 = ["Maju", "Jaya", "Sinar", "Karya", "Mitra", "Sentosa", "Abadi", "Prima",
             "Bumi", "Cipta", "Global", "Nusantara", "Tekno", "Mandiri", "Surya",
             "Graha", "Indo", "Lestari", "Makmur", "Sejahtera", "Utama", "Wahana"]
VENDOR_W2 = ["Logam", "Elektrik", "Pack", "Kimia", "Teknik", "Pratama", "Industri",
             "Perkasa", "Sarana", "Niaga", "Supplier", "Trading"]
CITIES = ["Jakarta", "Bekasi", "Tangerang", "Bandung", "Surabaya", "Semarang",
          "Medan", "Cikarang", "Sidoarjo", "Bogor", "Depok", "Karawang"]


def n_of(rate, base):
    return int(rate * base + 0.5)


def bcode(idx):
    return [f"B{int(i) + 1:02d}" for i in idx]


class Pool:
    """Pilih record untuk disisipi error. Satu record hanya kena satu error."""

    def __init__(self, rng, batch_idx, mask=None):
        self.rng = rng
        self.b = np.asarray(batch_idx)
        self.free = np.ones(len(self.b), bool) if mask is None else np.asarray(mask).copy()

    def take(self, n):
        cand = np.flatnonzero(self.free)
        w = BATCH_W[self.b[cand]]
        got = np.sort(self.rng.choice(cand, size=n, replace=False, p=w / w.sum()))
        self.free[got] = False
        return got


def messy_dates(rng, dates):
    fmts = rng.integers(0, len(DATE_FMTS), len(dates))
    return [pd.Timestamp(d).strftime(DATE_FMTS[f]) for d, f in zip(dates, fmts)]


def truth_rows(keys, code, table):
    return pd.DataFrame({"record_key": list(keys), "error_code": code, "table_name": table})


def make_vendors(rng):
    names, rows = set(), []
    while len(rows) < N_VENDORS:
        pre = rng.choice(["PT", "CV"], p=[0.7, 0.3])
        nm = f"{pre} {rng.choice(VENDOR_W1)} {rng.choice(VENDOR_W2)}"
        if nm in names:
            continue
        names.add(nm)
        i = len(rows)
        tax = (f"{rng.integers(1, 100):02d}.{rng.integers(0, 1000):03d}."
               f"{rng.integers(0, 1000):03d}.{rng.integers(0, 10)}-"
               f"{rng.integers(0, 1000):03d}.{rng.integers(0, 1000):03d}")
        rows.append({
            "vendor_code": f"VND-{i + 1:04d}", "vendor_name": nm,
            "city": rng.choice(CITIES),
            "payment_term": rng.choice(["NET14", "NET30", "NET45", "NET60", "COD"],
                                       p=[0.1, 0.45, 0.2, 0.15, 0.1]),
            "tax_id": tax, "batch_idx": i * N_BATCH // N_VENDORS,
        })
    return pd.DataFrame(rows)


def make_items(rng, vend_w):
    cats = list(CATS)
    vend = np.concatenate([np.arange(N_VENDORS),
                           rng.choice(N_VENDORS, N_ITEMS - N_VENDORS, p=vend_w)])
    rng.shuffle(vend)
    rows = []
    for i in range(N_ITEMS):
        cat = cats[rng.integers(len(cats))]
        base, spec, fin, uoms = CATS[cat]
        price = int(np.clip(rng.lognormal(np.log(60000), 1.1), 5000, 5_000_000) // 500 * 500)
        rows.append({
            "item_code": f"BRG-{i + 1:05d}",
            "item_name": f"{rng.choice(base)} {rng.choice(spec)} {rng.choice(fin)}",
            "category": cat, "uom_old": rng.choice(uoms), "unit_price": price,
            "vendor_idx": vend[i], "batch_idx": i * N_BATCH // N_ITEMS,
        })
    return pd.DataFrame(rows)


def inject_vendors(rng, src):
    erp = src.copy()
    pool = Pool(rng, src["batch_idx"])
    e1 = pool.take(n_of(RATE["E1"], N_VENDORS))
    e2 = pool.take(n_of(RATE["E2"], N_VENDORS))
    e4 = pool.take(n_of(RATE["E4"], N_VENDORS))
    e5 = pool.take(n_of(RATE["E5"], N_VENDORS))
    for k, i in enumerate(e4):
        c = src.at[i, "vendor_code"]
        erp.at[i, "vendor_code"] = [c + " ", c.lower(), "VND-" + str(int(c[4:]))][k % 3]
    for k, i in enumerate(e5):
        erp.at[i, "tax_id" if k % 2 == 0 else "payment_term"] = ""
    erp["_k"] = np.arange(len(erp), dtype=float)
    dup = erp.loc[e2].copy()
    dup["_k"] = rng.uniform(0, len(erp), len(dup))
    erp = pd.concat([erp.drop(index=e1), dup]).sort_values("_k").drop(columns="_k")
    code = src["vendor_code"]
    truth = pd.concat([
        truth_rows(code[e1], "E1", "vendors_erp"), truth_rows(code[e2], "E2", "vendors_erp"),
        truth_rows(code[e4], "E4", "vendors_erp"), truth_rows(code[e5], "E5", "vendors_erp"),
    ])
    return erp, truth, set(e1.tolist())


def inject_items(rng, src):
    erp = src.copy()
    erp["uom"] = erp["uom_old"].map(UOM_MAP)
    pool = Pool(rng, src["batch_idx"])
    e1 = pool.take(n_of(RATE["E1"], N_ITEMS))
    e2 = pool.take(n_of(RATE["E2"], N_ITEMS))
    e3 = pool.take(n_of(RATE["E3"], N_ITEMS))
    e4 = pool.take(n_of(RATE["E4"], N_ITEMS))
    e5 = pool.take(n_of(RATE["E5"], N_ITEMS))
    e6 = pool.take(n_of(RATE["E6"], N_ITEMS))
    for i in e3:
        old = src.at[i, "unit_price"]
        new = old
        while new == old:
            new = max(500, int(round(old * rng.uniform(0.6, 1.4) / 500) * 500))
        erp.at[i, "unit_price"] = new
    for k, i in enumerate(e4):
        c = src.at[i, "item_code"]
        erp.at[i, "item_code"] = [c + " ", c.lower(), "BRG-" + str(int(c[4:]))][k % 3]
    for k, i in enumerate(e5):
        erp.at[i, "uom" if k % 2 == 0 else "vendor_code"] = ""
    all_uom = sorted(set(UOM_MAP.values()))
    for k, i in enumerate(e6):
        right = erp.at[i, "uom"]
        wrong = src.at[i, "uom_old"] if k % 2 == 0 else rng.choice([u for u in all_uom if u != right])
        erp.at[i, "uom"] = wrong
    erp["_k"] = np.arange(len(erp), dtype=float)
    dup = erp.loc[e2].copy()
    dup["_k"] = rng.uniform(0, len(erp), len(dup))
    erp = pd.concat([erp.drop(index=e1), dup]).sort_values("_k").drop(columns="_k")
    code = src["item_code"]
    truth = pd.concat([truth_rows(code[ix], c, "items_erp")
                       for c, ix in [("E1", e1), ("E2", e2), ("E3", e3),
                                     ("E4", e4), ("E5", e5), ("E6", e6)]])
    return erp, truth, set(e1.tolist())


def build_po(rng, items, vend_w, bad_items, bad_vendors):
    vidx = items["vendor_idx"].values
    valid = np.array([i not in bad_items and v not in bad_vendors
                      for i, v in zip(items.index, vidx)])
    vitems = {v: np.flatnonzero(valid & (vidx == v)) for v in range(N_VENDORS)}
    avail = np.array([v for v in range(N_VENDORS) if len(vitems[v]) > 0])
    pw = vend_w[avail] / vend_w[avail].sum()
    start = pd.Timestamp("2025-01-01")
    lines, po_no = [], 0
    while len(lines) < N_PO:
        po_no += 1
        v = rng.choice(avail, p=pw)
        k = min(int(rng.integers(1, 6)), len(vitems[v]))
        its = rng.choice(vitems[v], size=k, replace=False)
        d = start + pd.Timedelta(days=int(rng.integers(0, 546)))
        for j, it in enumerate(its):
            lines.append({"po_no": po_no, "line": j + 1, "item_idx": it,
                          "vendor_idx": v, "po_date": d})
    po = pd.DataFrame(lines[:N_PO]).sort_values(["po_date", "po_no", "line"], kind="stable")
    po = po.reset_index(drop=True)
    seq = {n: i + 1 for i, n in enumerate(dict.fromkeys(po["po_no"]))}
    po["po_id"] = [f"PO-{seq[n]:06d}" for n in po["po_no"]]
    po["po_line_id"] = [f"{p}-{l * 10}" for p, l in zip(po["po_id"], po["line"])]
    po["quantity"] = np.clip(rng.lognormal(np.log(20), 0.9, N_PO), 1, 500).astype(int)
    po["unit_price"] = items["unit_price"].values[po["item_idx"].values]
    po["po_value"] = po["quantity"] * po["unit_price"]
    po["batch_idx"] = np.arange(N_PO) * N_BATCH // N_PO
    return po


def main():
    rng = np.random.default_rng(SEED)
    RAW.mkdir(parents=True, exist_ok=True)
    vend_w = rng.lognormal(0, 1.0, N_VENDORS)
    vend_w /= vend_w.sum()

    vsrc = make_vendors(rng)
    items = make_items(rng, vend_w)
    items["vendor_code"] = vsrc["vendor_code"].values[items["vendor_idx"].values]
    items["uom"] = items["uom_old"]
    mapping = pd.DataFrame({
        "old_code": [f"{c[:2].upper()}-{1000 + i * 7 + rng.integers(0, 7)}"
                     for i, c in enumerate(items["category"])],
        "new_code": items["item_code"], "uom_old": items["uom_old"],
        "uom_new": items["uom_old"].map(UOM_MAP),
    })

    verp, t_ven, ven_missing = inject_vendors(rng, vsrc)
    ierp, t_itm, itm_missing = inject_items(rng, items)

    po = build_po(rng, items, vend_w, itm_missing, ven_missing)
    po["item_code"] = items["item_code"].values[po["item_idx"].values]
    po["vendor_code"] = vsrc["vendor_code"].values[po["vendor_idx"].values]

    # PO: E7 (item tidak ada) lalu E4 (format tanggal)
    po_pool = Pool(rng, po["batch_idx"])
    e7 = po_pool.take(n_of(RATE["E7"], N_PO))
    e4_po = po_pool.take(n_of(RATE_E4_TX, N_PO))
    po.loc[e7, "item_code"] = [f"BRG-{90000 + rng.integers(1, 9000):05d}" for _ in e7]
    po["po_date_s"] = po["po_date"].dt.strftime("%Y-%m-%d")
    po.loc[e4_po, "po_date_s"] = messy_dates(rng, po.loc[e4_po, "po_date"])
    t_po = pd.concat([truth_rows(po.loc[e7, "po_line_id"], "E7", "po_lines"),
                      truth_rows(po.loc[e4_po, "po_line_id"], "E4", "po_lines")])

    # GR: sebagian baris PO belum diterima
    no_gr = np.zeros(N_PO, bool)
    no_gr[rng.choice(N_PO, N_PO - N_GR, replace=False)] = True
    gr = po.loc[~no_gr, ["po_line_id", "quantity", "unit_price", "po_date", "batch_idx"]]
    gr = gr.reset_index(drop=True)
    gr["quantity_received"] = gr["quantity"]
    gr["gr_date"] = gr["po_date"] + pd.to_timedelta(rng.integers(3, 31, len(gr)), unit="D")

    # Faktur dasar: dari baris yang sudah diterima
    base_pos = np.sort(rng.choice(len(gr), N_INV_BASE, replace=False))
    inv = pd.DataFrame({
        "po_line_id": gr.loc[base_pos, "po_line_id"].values,
        "gr_pos": base_pos,
        "quantity": gr.loc[base_pos, "quantity"].values,
        "unit_price": gr.loc[base_pos, "unit_price"].values,
        "batch_idx": gr.loc[base_pos, "batch_idx"].values,
        "invoice_date": (gr.loc[base_pos, "gr_date"].values
                         + pd.to_timedelta(rng.integers(1, 22, N_INV_BASE), unit="D")),
    })
    inv["invoice_value"] = inv["quantity"] * inv["unit_price"]
    inv["e8"] = inv["e9"] = inv["e10"] = False

    # E8: tiga nilai tidak cocok. Setengah lewat faktur, setengah lewat GR kurang.
    big = ((inv["quantity"] >= 10) & (inv["unit_price"] >= 20000)).values
    e8 = Pool(rng, inv["batch_idx"], big).take(n_of(RATE["E8"], N_INV_BASE))
    rng.shuffle(e8)
    e8a, e8b = e8[: len(e8) // 2], e8[len(e8) // 2:]
    for i in e8a:
        sign = rng.choice([-1, 1])
        inv.at[i, "invoice_value"] = int(round(inv.at[i, "invoice_value"]
                                               * (1 + sign * rng.uniform(0.10, 0.30))))
    for i in e8b:
        q = inv.at[i, "quantity"]
        short = max(1, int(round(q * rng.uniform(0.10, 0.50))))
        gr.at[inv.at[i, "gr_pos"], "quantity_received"] = q - short
    inv.loc[e8, "e8"] = True
    gr["gr_value"] = gr["quantity_received"] * gr["unit_price"]

    # Selisih kecil di bawah toleransi: bukan error, harus tetap MATCH
    rest = np.setdiff1d(np.arange(N_INV_BASE), e8)
    noisy = rng.choice(rest, n_of(NOISE_SHARE, N_INV_BASE), replace=False)
    delta = rng.integers(1, NOISE_MAX + 1, len(noisy)) * rng.choice([-1, 1], len(noisy))
    inv.loc[noisy, "invoice_value"] += delta

    # E10: faktur sama terbayar dua kali
    e10 = Pool(rng, inv["batch_idx"], ~inv["e8"].values).take(
        n_of(RATE["E10"], INV_BASE_FOR_RATE))
    inv.loc[e10, "e10"] = True

    # E9b: faktur untuk baris PO yang belum punya GR
    n9 = n_of(RATE["E9"], INV_BASE_FOR_RATE)
    pos9b = Pool(rng, po["batch_idx"], no_gr).take(n9 // 2)
    b9 = po.loc[pos9b]
    inv9b = pd.DataFrame({
        "po_line_id": b9["po_line_id"].values, "gr_pos": -1,
        "quantity": b9["quantity"].values, "unit_price": b9["unit_price"].values,
        "batch_idx": b9["batch_idx"].values,
        "invoice_date": b9["po_date"].values
        + pd.to_timedelta(rng.integers(5, 41, len(b9)), unit="D"),
        "invoice_value": b9["po_value"].values, "e8": False, "e9": True, "e10": False})
    # E9a: faktur dengan nomor PO yang tidak ada
    n9a = n9 - n9 // 2
    w = BATCH_W / BATCH_W.sum()
    inv9a = pd.DataFrame({
        "po_line_id": [f"PO-9{rng.integers(0, 100000):05d}-10" for _ in range(n9a)],
        "gr_pos": -1, "quantity": 0, "unit_price": 0,
        "batch_idx": rng.choice(N_BATCH, n9a, p=w),
        "invoice_date": pd.Timestamp("2025-02-01")
        + pd.to_timedelta(rng.integers(0, 545, n9a), unit="D"),
        "invoice_value": rng.integers(50, 20000, n9a) * 1000,
        "e8": False, "e9": True, "e10": False})
    inv = pd.concat([inv, inv9b, inv9a], ignore_index=True)
    inv["paid_flag"] = np.where(rng.random(len(inv)) < 0.8, "Y", "N")
    inv.loc[inv["e10"], "paid_flag"] = "Y"
    inv = inv.sort_values("invoice_date", kind="stable").reset_index(drop=True)
    inv["invoice_id"] = [f"INV-{i + 1:06d}" for i in range(len(inv))]

    # GR: urut tanggal, beri nomor, lalu E4
    gr = gr.sort_values("gr_date", kind="stable").reset_index(drop=True)
    gr["gr_id"] = [f"GR-{i + 1:06d}" for i in range(len(gr))]
    gr["gr_date_s"] = gr["gr_date"].dt.strftime("%Y-%m-%d")
    e4_gr = Pool(rng, gr["batch_idx"]).take(n_of(RATE_E4_TX, len(gr)))
    gr.loc[e4_gr, "gr_date_s"] = messy_dates(rng, gr.loc[e4_gr, "gr_date"])

    # Faktur: E4 pada baris non-ganda, lalu salin baris E10 (nomor faktur sama)
    inv["invoice_date_s"] = inv["invoice_date"].dt.strftime("%Y-%m-%d")
    e4_inv = Pool(rng, inv["batch_idx"], ~inv["e10"].values).take(
        n_of(RATE_E4_TX, len(inv)))
    inv.loc[e4_inv, "invoice_date_s"] = messy_dates(rng, inv.loc[e4_inv, "invoice_date"])
    inv["_ord"] = np.arange(len(inv), dtype=float)
    dup = inv[inv["e10"]].copy()
    dup["_ord"] += 0.5
    inv_out = pd.concat([inv, dup]).sort_values("_ord")

    t_inv = pd.concat([
        truth_rows(inv.loc[inv["e8"], "po_line_id"], "E8", "po_lines"),
        truth_rows(inv.loc[inv["e9"], "invoice_id"], "E9", "invoice_lines"),
        truth_rows(inv.loc[inv["e10"], "invoice_id"], "E10", "invoice_lines"),
        truth_rows(inv.loc[e4_inv, "invoice_id"], "E4", "invoice_lines"),
        truth_rows(gr.loc[e4_gr, "gr_id"], "E4", "gr_lines"),
    ])

    truth = pd.concat([t_itm, t_ven, t_po, t_inv], ignore_index=True)
    assert not truth.duplicated(["record_key", "error_code"]).any()

    def out(df, cols, name, rename=None):
        d = df[cols].copy()
        if rename:
            d = d.rename(columns=rename)
        if "batch_idx" in d:
            d["batch_idx"] = bcode(d["batch_idx"])
            d = d.rename(columns={"batch_idx": "batch_id"})
        d.to_csv(RAW / name, index=False)
        return len(d)

    sizes = {
        "items_source": out(items, ["item_code", "item_name", "category", "uom",
                                    "unit_price", "vendor_code", "batch_idx"],
                            "items_source.csv"),
        "items_erp": out(ierp, ["item_code", "item_name", "category", "uom",
                                "unit_price", "vendor_code", "batch_idx"], "items_erp.csv"),
        "vendors_source": out(vsrc, ["vendor_code", "vendor_name", "city", "payment_term",
                                     "tax_id", "batch_idx"], "vendors_source.csv"),
        "vendors_erp": out(verp, ["vendor_code", "vendor_name", "city", "payment_term",
                                  "tax_id", "batch_idx"], "vendors_erp.csv"),
        "mapping_codes": out(mapping, ["old_code", "new_code", "uom_old", "uom_new"],
                             "mapping_codes.csv"),
        "po_lines": out(po, ["po_id", "po_line_id", "item_code", "vendor_code", "quantity",
                             "unit_price", "po_value", "po_date_s", "batch_idx"],
                        "po_lines.csv", {"po_date_s": "po_date"}),
        "gr_lines": out(gr, ["gr_id", "po_line_id", "quantity_received", "gr_value",
                             "gr_date_s", "batch_idx"], "gr_lines.csv",
                        {"gr_date_s": "gr_date"}),
        "invoice_lines": out(inv_out, ["invoice_id", "po_line_id", "invoice_value",
                                       "invoice_date_s", "paid_flag", "batch_idx"],
                             "invoice_lines.csv", {"invoice_date_s": "invoice_date"}),
    }
    truth.to_csv(ROOT / "data" / "error_truth.csv", index=False)

    print("Jumlah baris:")
    for k, v in sizes.items():
        print(f"  {k:15s}{v:>7,}")
    print(f"  {'error_truth':15s}{len(truth):>7,}")
    print("Error per jenis:")
    print(truth.groupby("error_code").size()
          .reindex([f"E{i}" for i in range(1, 11)]).to_string())


if __name__ == "__main__":
    main()
