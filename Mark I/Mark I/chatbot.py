import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from physics_dataset import PhysicsDataset  # Make sure this class is defined as earlier

class Chatbot:
    def __init__(self):
        self.model_name = "microsoft/DialoGPT-medium"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self.chat_history_ids = None  # Initialize chat history
        self.MAX_HISTORY_LENGTH = 10000

        # Initialize the physics dataset
        self.physics_dataset = PhysicsDataset()

        # Initialize memory for past interactions
        self.memory = {}  # This will store key parts of conversations

    def get_bot_response(self, user_input):
        user_input = user_input.lower()  # Normalize input to lower case

        # Check if the user is referring to a previous conversation
        if 'what did we talk about' in user_input:
            if self.memory:
                remembered_info = "\n".join([f"{k}: {v}" for k, v in self.memory.items()])
                return f"Here's what I remember:\n{remembered_info}"
            else:
                return "I don't remember anything specific yet. Let's talk!"

        # Check if there's a physics-related response
        physics_answer = self.physics_dataset.get_physics_answer(user_input)
        if physics_answer is not None:
            # Store the question-answer pair in memory
            self.memory[user_input] = physics_answer
            return physics_answer

        # Proceed with generating a response using DialoGPT
        new_user_input_ids = self.tokenizer.encode(user_input + self.tokenizer.eos_token, return_tensors='pt')

        if self.chat_history_ids is not None:
            bot_input_ids = torch.cat([self.chat_history_ids, new_user_input_ids], dim=-1)
        else:
            bot_input_ids = new_user_input_ids

        if bot_input_ids.shape[1] > self.MAX_HISTORY_LENGTH:
            bot_input_ids = bot_input_ids[:, -self.MAX_HISTORY_LENGTH:]

        self.chat_history_ids = self.model.generate(
            bot_input_ids,
            max_length=10000,
            pad_token_id=self.tokenizer.eos_token_id,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=0.7
        )

        bot_response = self.tokenizer.decode(self.chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
        
        # Store this user input and bot response in memory for later recall
        self.memory[user_input] = bot_response
        return bot_response
