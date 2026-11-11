"""Generate synthetic health PDFs for testing the health-records scripts.

Usage: uv run --with pymupdf==1.26.5 python make_pdfs.py <out-dir>

Every name, value and provider here is made up.
"""

import sys
from pathlib import Path

import pymupdf

LAB_P1 = """<h2>Példa Labor Kft. - Laboratóriumi lelet</h2>
<p>Páciens: Teszt Elek &nbsp; Született: 1990.01.01 &nbsp; Mintavétel: 2025.03.14 07:42</p>
<table border=1 cellpadding=3>
<tr><th>Vizsgálat</th><th>Eredmény</th><th>Egység</th><th>Jelzés</th><th>Referencia</th></tr>
<tr><td>Glükóz</td><td>6,4</td><td>mmol/l</td><td>+</td><td>3,9 - 6,0</td></tr>
<tr><td>Húgysav</td><td>301</td><td>µmol/l</td><td></td><td>208 - 428</td></tr>
<tr><td>Összkoleszterin</td><td>5,1</td><td>mmol/l</td><td></td><td>&lt; 5,2</td></tr>
<tr><td>Ferritin</td><td>18</td><td>ug/l</td><td>-</td><td>20 - 250</td></tr>
<tr><td>Lp(a) frakció</td><td>41</td><td>mg/dl</td><td>+</td><td>&lt; 30</td></tr>
</table>
<p>Ellenőrizte: Dr. Minta Ödön</p>"""

LAB_P2 = """<h3>Vérkép</h3>
<table border=1 cellpadding=3>
<tr><th>Vizsgálat</th><th>Eredmény</th><th>Egység</th><th>Jelzés</th><th>Referencia</th></tr>
<tr><td>Fehérvérsejt</td><td>5,9</td><td>G/l</td><td></td><td>4,4 - 12,4</td></tr>
<tr><td>Hemoglobin</td><td>129</td><td>g/l</td><td>-</td><td>140 - 175</td></tr>
<tr><td>MCV</td><td>78,1</td><td>fl</td><td>-</td><td>80,0 - 95,0</td></tr>
</table>"""

DISCHARGE = """<h2>Riverside General Hospital - Discharge letter</h2>
<p>Patient: Test Person. Admitted 2025-05-02, discharged 2025-05-04.</p>
<p><b>Diagnosis:</b> Community-acquired pneumonia, right lower lobe.</p>
<p><b>Labs on admission:</b> CRP 86 mg/L (ref &lt; 5), WBC 13.2 x10^9/L (ref 4.0-11.0).</p>
<p><b>Plan:</b> Amoxicillin 1 g three times daily for 5 days. Chest X-ray in 6 weeks.</p>
<p>Dr. A. Example, Internal Medicine</p>"""

IMAGING = """<h2>Northside Imaging - Ultrasound report</h2>
<p>Date: 2025-06-10. Abdominal ultrasound.</p>
<p>Findings: liver of normal size with increased echogenicity, consistent with mild steatosis.
Gallbladder without stones. Kidneys normal.</p>"""


def html_page(doc: pymupdf.Document, html: str) -> pymupdf.Page:
    page = doc.new_page()
    page.insert_htmlbox(pymupdf.Rect(40, 40, 555, 800), html)
    return page


def text_pdf(path: Path, pages: list[str]) -> None:
    doc = pymupdf.open()
    for html in pages:
        html_page(doc, html)
    doc.save(path)


def scanned_pdf(path: Path, html: str) -> None:
    """Render a page to a slightly rotated greyscale image and keep only the image."""
    src = pymupdf.open()
    html_page(src, html)
    pix = src[0].get_pixmap(matrix=pymupdf.Matrix(2, 2).prerotate(1.2), colorspace=pymupdf.csGRAY)
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_image(page.rect, stream=pix.tobytes("png"))
    doc.save(path)


def mixed_pdf(path: Path, html: str) -> None:
    """A text layer plus a large picture, like a report with an embedded scan image."""
    doc = pymupdf.open()
    page = html_page(doc, html)
    pic = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 400, 300), 0)
    pic.clear_with(180)
    page.insert_image(pymupdf.Rect(40, 300, 555, 760), pixmap=pic)
    doc.save(path)


def encrypted_pdf(path: Path) -> None:
    doc = pymupdf.open()
    html_page(doc, "<p>Secret results</p>")
    doc.save(path, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="pw", owner_pw="owner")


def make_all(out: Path) -> dict[str, Path]:
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "lab": out / "lelet_2025_03.pdf",
        "scan": out / "scan0001.pdf",
        "mixed": out / "ultrasound.pdf",
        "encrypted": out / "locked.pdf",
        "corrupt": out / "broken.pdf",
        "copy": out / "nested" / "lelet_copy.pdf",
    }
    text_pdf(files["lab"], [LAB_P1, LAB_P2])
    scanned_pdf(files["scan"], DISCHARGE)
    mixed_pdf(files["mixed"], IMAGING)
    encrypted_pdf(files["encrypted"])
    files["corrupt"].write_bytes(b"%PDF-1.7\nthis is not really a pdf\n")
    files["copy"].parent.mkdir(exist_ok=True)
    files["copy"].write_bytes(files["lab"].read_bytes())
    return files


if __name__ == "__main__":
    for kind, path in make_all(Path(sys.argv[1])).items():
        print(f"{kind:10} {path}")
