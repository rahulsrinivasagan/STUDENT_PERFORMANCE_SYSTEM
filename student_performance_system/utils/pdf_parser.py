import PyPDF2
import os

class PDFParser:
    def __init__(self):
        """Initialize PDF parser"""
        pass
    
    def extract_text(self, pdf_path):
        """
        Extract text from PDF file
        
        Args:
            pdf_path (str): Path to the PDF file
        
        Returns:
            str: Extracted text from the PDF
        """
        if not os.path.exists(pdf_path):
            return ""
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text.strip()
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""