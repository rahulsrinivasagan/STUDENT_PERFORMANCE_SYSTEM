import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re

class NLPEvaluator:
    def __init__(self):
        """Initialize NLP evaluator with NLTK downloads"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        self.stop_words = set(stopwords.words('english'))
    
    def preprocess_text(self, text):
        """Preprocess text for analysis"""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation and numbers
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\d+', '', text)
        # Tokenize
        tokens = word_tokenize(text)
        # Remove stopwords
        tokens = [token for token in tokens if token not in self.stop_words]
        return set(tokens)
    
    def evaluate_answer(self, answer_text, keywords, max_marks):
        """
        Evaluate descriptive answer using keyword matching
        
        Args:
            answer_text (str): The student's answer text
            keywords (str): Comma-separated keywords
            max_marks (int): Maximum marks for the question
        
        Returns:
            int: Calculated score
        """
        if not answer_text or not keywords:
            return 0
        
        # Preprocess answer
        answer_tokens = self.preprocess_text(answer_text)
        
        # Process keywords
        keyword_list = [kw.strip().lower() for kw in keywords.split(',')]
        keyword_tokens = set()
        for kw in keyword_list:
            keyword_tokens.update(self.preprocess_text(kw))
        
        # Find matches
        matches = answer_tokens.intersection(keyword_tokens)
        
        # Calculate score based on keyword coverage
        if not keyword_tokens:
            return 0
        
        coverage = len(matches) / len(keyword_tokens)
        
        # Assign marks based on coverage
        if coverage >= 0.8:
            score = max_marks
        elif coverage >= 0.6:
            score = int(max_marks * 0.8)
        elif coverage >= 0.4:
            score = int(max_marks * 0.6)
        elif coverage >= 0.2:
            score = int(max_marks * 0.4)
        else:
            score = int(max_marks * 0.2)
        
        return score