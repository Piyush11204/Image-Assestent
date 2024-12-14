import os
import logging
from typing import Dict, Any

import numpy as np
import easyocr
from PIL import Image
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuestionOCRAnalyzer:
    def __init__(self, languages: list = ['en']):
        """
        Initialize OCR reader and OpenAI client for question answering
        
        Args:
            languages (list): List of language codes for OCR
        """
        try:
            # Initialize EasyOCR Reader
            self.reader = easyocr.Reader(languages)
            
            # Initialize OpenAI client
            openai.api_key = os.getenv('OPENAI_API_KEY')
            if not openai.api_key:
                raise ValueError("OpenAI API key is required")
        
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise

    def extract_question(self, image_array: np.ndarray) -> str:
        """
        Extract text from image, focusing on identifying the question
        
        Args:
            image_array (np.ndarray): Numpy array of the image
        
        Returns:
            str: Extracted question text
        """
        try:
            # Perform OCR
            results = self.reader.readtext(image_array)
            
            # Extract all text
            full_text = "\n".join([result[1] for result in results])
            
            # Optional: Additional processing to isolate the question
            # This is a simple approach and might need refinement
            question_keywords = ['what', 'who', 'where', 'when', 'why', 'how', 'which']
            
            # Convert full text to lowercase for easier matching
            lower_text = full_text.lower()
            
            # Check for question-like structure
            is_likely_question = any(
                keyword in lower_text.split()[:3] 
                for keyword in question_keywords
            ) or '?' in full_text
            
            return full_text if is_likely_question else ""
        
        except Exception as e:
            logger.error(f"Question extraction failed: {e}")
            return ""

    def answer_question(self, question: str) -> str:
        """
        Use OpenAI to generate an answer to the extracted question
        
        Args:
            question (str): Question text to be answered
        
        Returns:
            str: Generated answer
        """
        try:
            # Prepare messages for OpenAI
            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert question-answering AI. Provide clear, concise, and accurate answers to the given question. If the question is unclear or cannot be answered, explain why."
                },
                {
                    "role": "user", 
                    "content": question
                }
            ]
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # Using the latest affordable model
                messages=messages,
                max_tokens=300,  # Limit response length
                temperature=0.7  # Balanced creativity and accuracy
            )
            
            # Extract and return the answer
            return response['choices'][0]['message']['content']
        
        except Exception as e:
            logger.error(f"Question answering failed: {e}")
            return f"Sorry, I couldn't generate an answer. Error: {str(e)}"

class FlaskQuestionAnswerApp:
    def __init__(self):
        """
        Initialize Flask application for question answering
        """
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Configure upload settings
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
        self.app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', './uploads')
        
        # Ensure upload directory exists
        os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Initialize question OCR analyzer
        self.question_analyzer = QuestionOCRAnalyzer()
        
        # Register routes
        self.register_routes()

    def register_routes(self):
        """
        Register application routes
        """
        self.app.route('/answer-question', methods=['POST'])(self.process_question_image)

    def allowed_file(self, filename: str) -> bool:
        """
        Validate uploaded file type
        """
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def process_question_image(self):
        """
        Process uploaded question image and generate an answer
        """
        try:
            # Validate image upload
            if 'image' not in request.files:
                return jsonify({"error": "No image file provided"}), 400
            
            image_file = request.files['image']
            
            # Additional file validation
            if image_file.filename == '':
                return jsonify({"error": "No selected file"}), 400
            
            if not self.allowed_file(image_file.filename):
                return jsonify({"error": "Invalid file type"}), 400
            
            # Process image
            image_data = Image.open(image_file.stream)
            image_array = np.array(image_data)
            
            # Extract question
            extracted_question = self.question_analyzer.extract_question(image_array)
            
            if not extracted_question:
                return jsonify({
                    "error": "No clear question found in the image",
                    "extracted_text": ""
                }), 400
            
            # Answer the question
            answer = self.question_analyzer.answer_question(extracted_question)
            
            return jsonify({
                "extracted_question": extracted_question,
                "answer": answer
            }), 200
        
        except Exception as e:
            logger.error(f"Question image processing failed: {e}")
            return jsonify({"error": "Internal server error"}), 500

    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = True):
        """
        Run the Flask application
        """
        self.app.run(host=host, port=port, debug=debug)

def main():
    """
    Main entry point for the application
    """
    try:
        question_app = FlaskQuestionAnswerApp()
        logger.info("Question Answering OCR Application initialized successfully")
        question_app.run()
    except Exception as e:
        logger.critical(f"Application startup failed: {e}")

if __name__ == '__main__':
    main()