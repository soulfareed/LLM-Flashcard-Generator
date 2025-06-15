import io
import PyPDF2
from typing import Optional
import streamlit as st

class FileProcessor:
    def __init__(self):
        pass
    
    def process_file(self, uploaded_file) -> str:
        """Process uploaded file and extract text content"""
        file_type = uploaded_file.type
        content = ""
        
        try:
            if file_type == "text/plain":
                content = self._process_txt_file(uploaded_file)
            elif file_type == "application/pdf":
                content = self._process_pdf_file(uploaded_file)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            return content
            
        except Exception as e:
            raise Exception(f"Error processing file: {str(e)}")
    
    def _process_txt_file(self, uploaded_file) -> str:
        """Process .txt file"""
        try:
            # Read as string
            content = uploaded_file.read().decode('utf-8')
            return content
        except UnicodeDecodeError:
            # Try different encodings
            uploaded_file.seek(0)
            try:
                content = uploaded_file.read().decode('latin-1')
                return content
            except:
                uploaded_file.seek(0)
                content = uploaded_file.read().decode('cp1252')
                return content
    
    def _process_pdf_file(self, uploaded_file) -> str:
        """Process .pdf file"""
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            content = ""
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        content += f"\n--- Page {page_num + 1} ---\n"
                        content += page_text + "\n"
                except Exception as e:
                    print(f"Warning: Could not extract text from page {page_num + 1}: {e}")
                    continue
            
            if not content.strip():
                raise ValueError("No text content could be extracted from the PDF")
            
            return content
            
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def validate_content(self, content: str) -> bool:
        """Validate extracted content"""
        if not content or not content.strip():
            return False
        
        # Check minimum content length
        if len(content.strip()) < 50:
            return False
        
        # Check if content is not just whitespace or special characters
        text_chars = sum(1 for c in content if c.isalnum())
        if text_chars / len(content) < 0.3:  # Less than 30% alphanumeric characters
            return False
        
        return True
    
    def clean_content(self, content: str) -> str:
        """Clean and preprocess extracted content"""
        # Remove excessive whitespace
        content = ' '.join(content.split())
        
        # Remove page headers/footers patterns (common in PDFs)
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip very short lines that might be page numbers or headers
            if len(line) > 5:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)