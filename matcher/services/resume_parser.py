import PyPDF2
from docx import Document
import io


class ResumeParser:
    """Parse resume files and extract text content."""
    
    def extract_text(self, file):
        """Extract text from PDF or DOCX file."""
        file_extension = file.name.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            return self._extract_from_pdf(file)
        elif file_extension in ['docx', 'doc']:
            return self._extract_from_docx(file)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def _extract_from_pdf(self, file):
        """Extract text from PDF file."""
        try:
            # Reset file pointer to beginning
            if hasattr(file, 'seek'):
                file.seek(0)
            
            # Read the file content
            file_content = file.read()
            
            # Create a BytesIO object for PyPDF2
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            # Reset file pointer for potential reuse
            if hasattr(file, 'seek'):
                file.seek(0)
            
            if not text.strip():
                raise ValueError("No text could be extracted from the PDF. The file might be image-based or corrupted.")
            
            return text.strip()
        except PyPDF2.errors.PdfReadError as e:
            raise ValueError(f"Error reading PDF file: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing PDF: {str(e)}")
    
    def _extract_from_docx(self, file):
        """Extract text from DOCX file."""
        try:
            # Reset file pointer to beginning
            if hasattr(file, 'seek'):
                file.seek(0)
            
            # Read the file content
            file_content = file.read()
            
            # Create a BytesIO object for python-docx
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            
            text = ""
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text += paragraph.text + "\n"
            
            # Reset file pointer for potential reuse
            if hasattr(file, 'seek'):
                file.seek(0)
            
            if not text.strip():
                raise ValueError("No text could be extracted from the DOCX file.")
            
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error processing DOCX: {str(e)}")

