
import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Invoice to Excel Converter", page_icon="📄", layout="centered")

st.title("📄 Invoice to Excel Converter")
st.write("Upload your PDF invoices below to extract key details into an Excel sheet.")

uploaded_files = st.file_uploader("Upload one or more invoice PDFs", type=["pdf"], accept_multiple_files=True)

def clean(val):
    if not val:
        return ""
    return val.replace(",", "").strip()

def extract_invoice_data(text):
    invoice_no = re.search(r'Invoice\s*No\.?\s*[:\-]?\s*([A-Z0-9\/\-]+)', text, re.IGNORECASE)
    invoice_date = re.search(r'\bDate\b\s*[:\-]?\s*([\d]{1,2}[-\/][\d]{1,2}[-\/][\d]{2,4})', text, re.IGNORECASE)
    party_name = re.search(r'(?i)Name\s*[:\-]?\s*([A-Z\s\.\-&]+)', text)
    gstin = re.search(r'GSTIN\s*[:\-]?\s*([0-9A-Z]{15})', text)
    hsn_codes = re.findall(r'\b\d{4,8}\b', text)
    taxable_value = re.search(r'(?:Taxable\s*Value|Total\s*Amount\s*Before\s*Tax)\s*[:₹]*\s*([\d,]+\.\d{2})', text, re.IGNORECASE)
    cgst_amt = re.search(r'CGST\s*[:₹]*\s*([\d,]+\.\d{2})', text, re.IGNORECASE)
    sgst_amt = re.search(r'SGST\s*[:₹]*\s*([\d,]+\.\d{2})', text, re.IGNORECASE)
    igst_amt = re.search(r'IGST\s*[:₹]*\s*([\d,]+\.\d{2})', text, re.IGNORECASE)
    invoice_total = re.search(r'(?:Invoice\s*Total|Total\s*Amount\s*After\s*Tax)\s*[:₹]*\s*([\d,]+\.\d{2})', text, re.IGNORECASE)

    items = re.findall(r'(?i)([A-Z0-9\s\-\(\)\/]+)\s+(\d+(?:\.\d+)?)\s*(KGS|NOS)?\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)', text)

    rows = []
    if items:
        for item in items:
            rows.append({
                "Invoice No.": invoice_no.group(1) if invoice_no else "",
                "Date": invoice_date.group(1) if invoice_date else "",
                "Party Name": party_name.group(1).strip() if party_name else "",
                "GSTIN": gstin.group(1) if gstin else "",
                "HSN Code": ", ".join(set(hsn_codes)) if hsn_codes else "",
                "Item": item[0].strip(),
                "Quantity": item[1],
                "Unit": item[2],
                "Rate": item[3],
                "Amount": item[4],
                "Taxable Value": clean(taxable_value.group(1)) if taxable_value else "",
                "CGST Amt": clean(cgst_amt.group(1)) if cgst_amt else "",
                "SGST Amt": clean(sgst_amt.group(1)) if sgst_amt else "",
                "IGST Amt": clean(igst_amt.group(1)) if igst_amt else "",
                "Invoice Total": clean(invoice_total.group(1)) if invoice_total else ""
            })
    else:
        rows.append({
            "Invoice No.": invoice_no.group(1) if invoice_no else "",
            "Date": invoice_date.group(1) if invoice_date else "",
            "Party Name": party_name.group(1).strip() if party_name else "",
            "GSTIN": gstin.group(1) if gstin else "",
            "HSN Code": ", ".join(set(hsn_codes)) if hsn_codes else "",
            "Item": "",
            "Quantity": "",
            "Unit": "",
            "Rate": "",
            "Amount": "",
            "Taxable Value": clean(taxable_value.group(1)) if taxable_value else "",
            "CGST Amt": clean(cgst_amt.group(1)) if cgst_amt else "",
            "SGST Amt": clean(sgst_amt.group(1)) if sgst_amt else "",
            "IGST Amt": clean(igst_amt.group(1)) if igst_amt else "",
            "Invoice Total": clean(invoice_total.group(1)) if invoice_total else ""
        })
    return rows

if uploaded_files:
    all_data = []
    with st.spinner("Extracting data from invoices..."):
        for file in uploaded_files:
            with pdfplumber.open(file) as pdf:
                text = ""
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
                data = extract_invoice_data(text)
                all_data.extend(data)

    df = pd.DataFrame(all_data)
    st.success(f"✅ Extracted {len(df)} rows from {len(uploaded_files)} PDF(s).")

    st.dataframe(df)

    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    st.download_button(
        label="⬇️ Download Excel",
        data=output.getvalue(),
        file_name="invoice_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
