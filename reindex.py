from app.services.pdf_processor import index_pdf

pdf_path = "A_Data-Driven_Reinforcement_Learning_Enabled_Battery_Fast_Charging_Optimization_Using_Real-World_Experimental_Data.pdf"

print(f"Re-indexing PDF with larger chunks (5000 chars)...")
count = index_pdf(pdf_path)
print(f"Successfully indexed {count} chunks")
