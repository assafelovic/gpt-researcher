from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredCSVLoader

# # Test PyMuPDFLoader
pdf_loader = PyMuPDFLoader("my-docs/Elisha - Coding Career.pdf")
try:
    pdf_data = pdf_loader.load()
    print("PDF Data:", pdf_data)
except Exception as e:
    print("Failed to load PDF:", e)

# Test UnstructuredCSVLoader
csv_loader = UnstructuredCSVLoader("my-docs/active_braze_protocols_from_bq.csv", mode="elements")
try:
    csv_data = csv_loader.load()
    print("CSV Data:", csv_data)
except Exception as e:
    print("Failed to load CSV:", e)