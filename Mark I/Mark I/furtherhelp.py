import requests
import nltk
from nltk.tokenize import word_tokenize

# Download NLTK resources (if not done already)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class FurtherHelp:
    def __init__(self):
        # Initialize the NLTK tokenizer
        self.physics_keywords = [
            'gravity', 'force', 'energy', 'mass', 
            'acceleration', 'kinematics', 'dynamics', 
            'thermodynamics', 'quantum', 'momentum', 
            'work', 'power', 'pressure', 'temperature', 
            'entropy', 'electricity', 'magnetism'
        ]

    # Function to check if the question contains any physics keywords
    def contains_physics_keywords(self, question):
        tokens = word_tokenize(question.lower())
        return any(keyword in tokens for keyword in self.physics_keywords)

    # Function to get physics information from Wikipedia
    def ask_physics_ai(self, query):
        base_url = "https://en.wikipedia.org/w/api.php"
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': query,
            'srlimit': 1  # Limit to 1 result for simplicity
        }
        
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if 'query' in data and 'search' in data['query']:
            return data['query']['search'][0]['snippet']  # Return the snippet of the first search result
        else:
            return "I couldn't find any information on that."

    # Main function to get further help based on user input
    def get_further_help(self, user_input):
        if self.contains_physics_keywords(user_input):
            # Extract the first physics keyword for search
            tokens = word_tokenize(user_input.lower())
            for keyword in self.physics_keywords:
                if keyword in tokens:
                    return self.ask_physics_ai(keyword)  # Search Wikipedia for the keyword
        return "I'm sorry, but I don't know about that topic. Please ask about a physics concept."

# Test the class functionality
if __name__ == "__main__":
    further_help = FurtherHelp()
    user_input = input("Ask a physics question: ")
    print(further_help.get_further_help(user_input))
