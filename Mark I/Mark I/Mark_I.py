from doctest import Example
import torch
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import requests
from fuzzywuzzy import process
from transformers import AutoModelForCausalLM, AutoTokenizer
from rtuphysics1 import PhysicsData
import speech_recognition as sr  
from transformers import pipeline
from tkinter import filedialog
from tkinter import *
import torch
import numpy as np
import easyocr
import re
import google.generativeai as genai
from PIL import Image



class PhysicsDataset:
    
    def list_physics_concepts(self):
        return list(self.data.keys())

    def find_similar_concept(self, user_input):
        user_input = user_input.lower()
        similar_concepts = [concept for concept in self.data if user_input in concept.lower()]
        return similar_concepts if similar_concepts else "No similar concepts found."
   

class Chatbot:
    def __init__(self):
        self.model_name = "microsoft/DialoGPT-medium"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self.chat_history_ids = None  
        self.MAX_HISTORY_LENGTH = 10000

        self.physics_dataset = PhysicsData()
        self.further_help = FurtherHelp(wolfram_alpha_app_id='8UK9X2-PKGXQYTYVX')  

        self.memory = {}
    def update_memory(self, key, value):
        
        self.memory[key] = value

    def recall_memory(self, key):
        return self.memory.get(key, "I don't remember that yet.")
    def summarize_text(self, text, max_length=50):
       
          summarizer = pipeline("summarization")
          summary = summarizer(text, max_length=max_length, min_length=10, do_sample=False)
          return summary[0]['summary_text']
    def get_bot_response(self, user_input):
        user_input = user_input.lower()

    def get_bot_response(self, user_input):
         user_input = user_input.lower() 
        
        
         if 'what did we talk about' in user_input:
            if self.memory:
                remembered_info = "\n".join([f"{k}: {v}" for k, v in self.memory.items()])
                return f"Here's what I remember:\n{remembered_info}"
            else:
                return "I don't remember anything specific yet. Let's talk!"

         if "wikipedia" in user_input or "method" in user_input:
            return self.further_help.get_further_help(user_input)

         physics_answer = self.physics_dataset.get_physics_answer(user_input)
         if physics_answer is not None:
            self.memory[user_input] = physics_answer
            return physics_answer

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
 

         self.memory[user_input] = bot_response
         return bot_response
        
class FurtherHelp:
   
     def __init__(self, wolfram_alpha_app_id):
        self.wolfram_alpha_app_id = wolfram_alpha_app_id
        self.physics_keywords = {
            'gravity': ['weight', 'attraction'],
            'force': ['push', 'pull', 'strength'],
            'mass': ['weight', 'amount'],
            'acceleration': ['speeding up', 'velocity change'],
            'kinematics': ['motion', 'movement'],
            'dynamics': ['forces in motion', 'motion dynamics'],
            'thermodynamics': ['heat', 'energy transfer'],
            'quantum': ['quantum mechanics', 'subatomic'],
            'momentum': ['inertia', 'mass in motion'],
            'work': ['energy transfer'],
            'power': ['energy rate'],
            'pressure': ['force per area'],
            'temperature': ['heat measurement'],
            'entropy': ['disorder', 'randomness'],
            'electricity': ['current', 'voltage'],
            'magnetism': ['magnetic force', 'magnet'],
        }
        self.dataset = PhysicsData()

     def contains_physics_keywords(self, question):
        question = question.lower()
        keywords = list(self.physics_keywords.keys())
        matched_keyword, score = process.extractOne(question, keywords)
        
        return matched_keyword if score > 70 else None

     def search_dataset(self, keyword):
        return self.dataset.get_physics_answer(keyword)
        
     def ask_wolfram_alpha(self, query):
        base_url = "http://api.wolframalpha.com/v2/query"
        params = {
            'input': query,
            'format': 'plaintext',
            'output': 'JSON',
            'appid': self.wolfram_alpha_app_id,
            'podstate': 'Default'
        }

        response = requests.get(base_url, params=params)
        data = response.json()

        try:
            pods = data['queryresult']['pods']
            answers = []
            for pod in pods:
                if 'subpods' in pod and len(pod['subpods']) > 0:
                    answers.append(pod['subpods'][0]['plaintext'])
            return "\n".join(answers) if answers else "I couldn't find any information on that."
        except Exception as e:
            return f"An error occurred while querying Wolfram Alpha: {str(e)}"

     def ask_wikipedia(self, keyword, word_limit=300):
        base_url = "https://en.wikipedia.org/w/api.php"
        params = {
            'action': 'query',
            'format': 'json',
            'titles': keyword,
            'prop': 'extracts',
            'explaintext': True,
            'redirects': 1
        }

        response = requests.get(base_url, params=params)
        data = response.json()

        page = next(iter(data['query']['pages'].values()))

        if 'extract' in page:
            extract = page['extract']
            words = extract.split()  

            if len(words) > word_limit:
                truncated_extract = ' '.join(words[:word_limit]) + '...'
                return truncated_extract
            else:
                return extract
        else:
            return "No information found on Wikipedia."





     def get_further_help(self, user_input):
        matched_keyword = self.contains_physics_keywords(user_input)
        if "reference" in user_input.lower():
            return self.ask_reference()

        if "wikipedia" in user_input.lower():
            if matched_keyword:
                return self.ask_wikipedia(matched_keyword)
            else:
                return "No relevant physics concept found for Wikipedia search."

        if "method" in user_input.lower():
            if matched_keyword:
                definition_or_formula = self.search_dataset(matched_keyword)
                if definition_or_formula:
                    return definition_or_formula 

            return self.ask_wolfram_alpha(matched_keyword)
 



wolfram_alpha_app_id = '8UK9X2-PKGXQYTYVX'  
furtherhelp = FurtherHelp(wolfram_alpha_app_id)
chatbot = Chatbot()
physics_data = PhysicsData()





def get_bot_response(user_input):
    return chatbot.get_bot_response(user_input)


def send_message():
    user_message = user_input_box.get()
    
    if user_message.strip() == "":
        return

    if user_message.lower() == 'quit':
        chat_display.config(state=tk.NORMAL)
        chat_display.insert(tk.END, "\nChatbot: Goodbye! Have a great day!\n", "bot")
        root.after(2000, root.quit)  
        return
    
    if user_message.lower() == 'reset':
        chatbot.chat_history_ids = None 
        chat_display.config(state=tk.NORMAL)
        chat_display.insert(tk.END, "\nChatbot: Conversation reset. Feel free to ask anything!\n", "bot")
        chat_display.config(state=tk.DISABLED)
        user_input_box.delete(0, tk.END)
        return


   
    user_input_box.delete(0, tk.END)
    
    chat_display.config(state=tk.NORMAL)
    
    chat_display.insert(tk.END, "\n", "user_space")
    chat_display.window_create(tk.END, window=tk.Label(chat_display, image=user_icon, bg="#ffffff"))
    chat_display.insert(tk.END, "  " + user_message + "\n", "user")



    try:

     if user_message.lower() == 'summarize':
        chat_display.insert(tk.END, "\nChatbot: Please provide the text you'd like me to summarize.\n", "bot")
        chatbot.expecting_summary = True  
        return

     if hasattr(chatbot, 'expecting_summary') and chatbot.expecting_summary:
        chatbot.expecting_summary = False
        summary = chatbot.summarize_text(user_message)
        print(f"Summarized text: {summary}")  

        if summary is None:
            bot_response = "Sorry, I couldn't summarize the text. Please try again."
        else:
            bot_response = f"Summary: {summary}"
     else:
        bot_response = chatbot.get_bot_response(user_message)
        print(f"Bot response: {bot_response}")  

        if bot_response is None:
            bot_response = "Sorry, I couldn't process your request. Please try again."

    except Exception as e:
     bot_response = f"An error occurred: {str(e)}"
     print(f"Error: {str(e)}")  

    chat_display.insert(tk.END, "\n", "bot_space")
    chat_display.window_create(tk.END, window=tk.Label(chat_display, image=bot_icon, bg="#ffffff", anchor="e"))
    chat_display.insert(tk.END, "  " + bot_response + "\n", "bot")

    chat_display.yview(tk.END)
    chat_display.config(state=tk.DISABLED)


 



wolfram_alpha_app_id = '8UK9X2-PKGXQYTYVX'  
furtherhelp = FurtherHelp(wolfram_alpha_app_id)
chatbot = Chatbot()
physics_data = PhysicsData()


def recognize_speech():
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)  
        audio = recognizer.listen(source) 
    
    try:
        user_message = recognizer.recognize_google(audio)  
        
        chat_display.config(state=tk.NORMAL)
        chat_display.insert(tk.END, f"You: {user_message}\n", "user")


        bot_response = chatbot.get_bot_response(user_message)

        chat_display.insert(tk.END, f"Chatbot: {bot_response}\n", "bot")
        chat_display.yview(tk.END)
        chat_display.config(state=tk.DISABLED)
        
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand the audio.")
    except sr.RequestError:
        print("Sorry, there was an error with the request.")


api_key = "AIzaSyDNWw-hwng1JYhkcICiN78tz3BFf-U_yco" 

def upload_image():
    try:
        image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
        if not image_path:
            print("No image selected.")
            return
        
        
        try:
            reader = easyocr.Reader(['en'])
            result = reader.readtext(image_path)
            extracted_text = " ".join([text[1] for text in result])
        except Exception as e:
            print(f"Error with EasyOCR: {e}")
            return
        
        print(f"Extracted Text: {extracted_text}")
        chat_display.config(state=tk.NORMAL)
        chat_display.insert(tk.END, f"User Message:\n{extracted_text}\n", "user")

        if is_formula(extracted_text):
            print("Detected as a formula.")
            interpretation = physical_interpretation(extracted_text)
        else:
            print("Not a formula. Passing to Google Gemini for analysis.")
            interpretation = analyze(extracted_text)

        combined_text = f"Extracted Text:\n{extracted_text}\n\nInterpretation:\n{interpretation}"
        chat_display.insert(tk.END, f"AI Response:\n{combined_text}\n", "AI")

    except Exception as e:
        print(f"Unexpected Error: {e}")

def is_formula(text):
   
    pattern = r'^[A-Za-z]+\s*=\s*[A-Za-z0-9^*/+\-().\s]+$'
    return bool(re.match(pattern, text))

def physical_interpretation(formula):
    
   
    if "F = ma" in formula:
        return "This formula represents Newton's second law: F = ma, where F is the force acting on an object, m is the object's mass, and a is its acceleration. It quantifies the relationship between the motion of an object and the forces acting upon it."

    elif "E = mc^2" in formula:
        return "This is Einstein's mass-energy equivalence formula: E = mc^2, where E is energy, m is mass, and c is the speed of light in a vacuum. It demonstrates that mass can be converted into energy and vice versa, forming the basis for nuclear energy."

    elif "W = Fd cos(theta)" in formula:
        return "This is the formula for work: W = Fd cos(theta), where W is work, F is the applied force, d is the displacement, and theta is the angle between the force and displacement vectors. It calculates the energy transferred when a force moves an object."

    elif "KE = 1/2 mv^2" in formula:
        return "This formula defines kinetic energy: KE = 1/2 mv^2, where KE is kinetic energy, m is the mass of an object, and v is its velocity. It describes the energy an object possesses due to its motion."

    elif "PE = mgh" in formula:
        return "This formula represents gravitational potential energy: PE = mgh, where PE is potential energy, m is mass, g is the acceleration due to gravity, and h is the height above a reference point. It quantifies energy stored due to an object's position in a gravitational field."

    elif "p = mv" in formula:
        return "This is the formula for linear momentum: p = mv, where p is momentum, m is mass, and v is velocity. Momentum describes the quantity of motion an object has."

    elif "F = G(m1*m2)/r^2" in formula:
        return "This is Newton's law of universal gravitation: F = G(m1*m2)/r^2, where F is the gravitational force, G is the gravitational constant, m1 and m2 are masses, and r is the distance between their centers. It quantifies the attractive force between two masses."

    elif "v = u + at" in formula:
        return "This is one of the equations of motion: v = u + at, where v is the final velocity, u is the initial velocity, a is acceleration, and t is time. It relates an object's motion under constant acceleration."

    elif "s = ut + 1/2 at^2" in formula:
        return "This equation describes displacement under constant acceleration: s = ut + 1/2 at^2, where s is displacement, u is initial velocity, a is acceleration, and t is time."

    elif "v^2 = u^2 + 2as" in formula:
        return "This is another kinematic equation: v^2 = u^2 + 2as, where v is final velocity, u is initial velocity, a is acceleration, and s is displacement. It relates velocity and displacement under constant acceleration."

    elif "P = W/t" in formula:
        return "This is the formula for power: P = W/t, where P is power, W is work, and t is time. It quantifies the rate at which work is done or energy is transferred."

    elif "Q = mcΔT" in formula:
        return "This formula represents heat transfer: Q = mcΔT, where Q is heat, m is mass, c is specific heat capacity, and ΔT is the change in temperature. It calculates the heat energy required to change an object's temperature."

    elif "P = IV" in formula:
        return "This is the formula for electrical power: P = IV, where P is power, I is current, and V is voltage. It calculates the rate of energy consumption in an electrical circuit."

    elif "V = IR" in formula:
        return "This is Ohm's law: V = IR, where V is voltage, I is current, and R is resistance. It describes the relationship between voltage, current, and resistance in an electrical circuit."

    elif "C = Q/V" in formula:
        return "This formula defines capacitance: C = Q/V, where C is capacitance, Q is charge, and V is voltage. It measures a capacitor's ability to store charge per unit voltage."

    elif "E = hf" in formula:
        return "This is Planck's equation: E = hf, where E is energy, h is Planck's constant, and f is frequency. It describes the energy of a photon in terms of its frequency."

    elif "F = q(E + v x B)" in formula:
        return "This is the Lorentz force law: F = q(E + v x B), where F is force, q is charge, E is electric field, v is velocity, and B is magnetic field. It calculates the force on a charged particle moving in electromagnetic fields."

    elif "lambda = h/p" in formula:
        return "This is the de Broglie wavelength formula: lambda = h/p, where lambda is wavelength, h is Planck's constant, and p is momentum. It relates the wave-like properties of particles to their momentum."

    elif "P = F/A" in formula:
        return "This is the formula for pressure: P = F/A, where P is pressure, F is force, and A is area. It calculates the force exerted per unit area."

    elif "T = 2π\sqrt{l/g}" in formula:
        return "This is the formula for the period of a simple pendulum: T = 2π\sqrt{l/g}, where T is the period, l is the length of the pendulum, and g is the acceleration due to gravity. It calculates the time for one complete oscillation."

    elif "R = \rho L/A" in formula:
        return "This is the formula for electrical resistance: R = \rho L/A, where R is resistance, \rho is resistivity, L is the length of the conductor, and A is the cross-sectional area. It quantifies how much a material resists the flow of electric current."

    elif "I = Q/t" in formula:
        return "This formula describes electric current: I = Q/t, where I is current, Q is charge, and t is time. It measures the flow of electric charge over time."

    elif "f = 1/T" in formula:
        return "This is the formula for frequency: f = 1/T, where f is frequency and T is the period of a wave. It represents the number of oscillations or cycles per unit time."

    elif "T = F/A" in formula:
        return "This formula represents tensile stress: T = F/A, where T is stress, F is force, and A is the cross-sectional area. It measures the internal forces in a material under tension."

    elif "\epsilon = \Delta L/L" in formula:
        return "This is the formula for strain: \epsilon = \Delta L/L, where \epsilon is strain, \Delta L is the change in length, and L is the original length. It measures the deformation of a material under stress."

    elif "\sigma = E\epsilon" in formula:
        return "This is Hooke's law for stress and strain: \sigma = E\epsilon, where \sigma is stress, E is Young's modulus, and \epsilon is strain. It relates the deformation of an elastic material to the applied force."

    elif "F = -kx" in formula:
        return "This is Hooke's law for springs: F = -kx, where F is the restoring force, k is the spring constant, and x is the displacement from the equilibrium position. It describes the behavior of elastic materials."

    elif "P = \rho gh" in formula:
        return "This formula represents fluid pressure: P = \rho gh, where P is pressure, \rho is fluid density, g is gravitational acceleration, and h is height. It calculates the pressure exerted by a fluid at a given depth."

    elif "v = \sqrt{2gh}" in formula:
        return "This is the formula for the velocity of an object in free fall: v = \sqrt{2gh}, where v is velocity, g is gravitational acceleration, and h is height. It calculates the final velocity of an object falling from rest."

    elif "F = -dU/dx" in formula:
        return "This formula relates force and potential energy: F = -dU/dx, where F is force, U is potential energy, and x is position. It calculates the force as the negative gradient of potential energy."
    elif "L = I\omega" in formula:
        return "This formula defines angular momentum: L = I\omega, where L is angular momentum, I is moment of inertia, and \omega is angular velocity. It describes rotational motion."

    elif "T = \tau/I" in formula:
        return "This is the formula for angular acceleration: T = \tau/I, where T is angular acceleration, \tau is torque, and I is the moment of inertia. It describes the rotational equivalent of Newton's second law."

    elif "V = \frac{4}{3}\pi r^3" in formula:
        return "This is the formula for the volume of a sphere: V = \frac{4}{3}\pi r^3, where V is volume and r is the radius. It is used in geometry and physics applications."

    elif "a_c = v^2/r" in formula:
        return "This formula describes centripetal acceleration: a_c = v^2/r, where a_c is acceleration, v is velocity, and r is the radius of circular motion. It applies to objects moving in circular paths."

    elif "U = -G(m1*m2)/r" in formula:
        return "This is the formula for gravitational potential energy: U = -G(m1*m2)/r, where U is potential energy, G is the gravitational constant, m1 and m2 are masses, and r is the separation."

    elif "P = \rho v g" in formula:
        return "This formula expresses pressure in a fluid: P = \rho v g, where P is pressure, \rho is density, v is velocity, and g is gravity."

    elif "\epsilon_0 = 1/(\mu_0 c^2)" in formula:
        return "This formula relates the permittivity of free space \epsilon_0 to the permeability \mu_0 and speed of light c: \epsilon_0 = 1/(\mu_0 c^2)."

    elif "\Delta S = Q/T" in formula:
        return "This is the formula for entropy change: \Delta S = Q/T, where \Delta S is entropy, Q is heat energy, and T is temperature."

    elif "V = k_e (q/r)" in formula:
        return "This is the formula for electric potential: V = k_e (q/r), where V is potential, k_e is Coulomb's constant, q is charge, and r is distance."

    elif "R = \Delta V/I" in formula:
        return "Ohm's Law with resistance: R = \Delta V/I. R is resistance, I is current, and \Delta voltage."
   
    else:
        return "Unrecognized formula."

def extract_text_from_response(response):
  
    match = re.search(r'"text": "(.*?)"', response, re.DOTALL)
    if match:
        return match.group(1)
    return "No 'text' field found."

def analyze(text):
    
    try:
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(text)
        response_text = str(response)

        extracted_text = extract_text_from_response(response_text)
        print(f"{extracted_text}")
        return extracted_text

    except Exception as e:
        print(f"Error generating response: {e}")
        return f"Error generating response: {str(e)}"


root = tk.Tk()

root.title("Multimodal conversational AI by balamir demirkan belül")
root.geometry("1000x1000")
root.config(bg="#ffffff")

user_icon_img = Image.open("user_icon.png")
user_icon_img = user_icon_img.resize((40, 40), Image.LANCZOS)

user_icon = ImageTk.PhotoImage(user_icon_img)
bot_icon_img = Image.open("bot_icon.png")
bot_icon_img = bot_icon_img.resize((40, 40), Image.LANCZOS)
bot_icon = ImageTk.PhotoImage(bot_icon_img)

mic_icon_img = Image.open("mic_icon.png")
mic_icon_img = mic_icon_img.resize((40, 40), Image.LANCZOS)
mic_icon = ImageTk.PhotoImage(mic_icon_img)

frame = tk.Frame(root, bg="#ffffff")
frame.grid(row=0, column=0, padx=20, pady=20, sticky="w")


upload_button = tk.Button(root, text="Upload Image", width=20, font=("Helvetica", 14), bg="#000000", fg="#ffffff", command=upload_image)
upload_button.grid(row=1, column=0, padx=0, pady=(0,1000))

chat_frame = tk.Frame(root, bg="#ffffff")
chat_frame.grid(row=0, column=1, padx=20, pady=20)

chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, width=70, height=25, bg="#ffffff", fg="#333333", font=("Helvetica", 14))
chat_display.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
chat_display.config(state=tk.DISABLED)

user_input_box = tk.Entry(chat_frame, width=60, font=("New times roman", 14), bg="#333333", fg="#ffffff", borderwidth=5, relief=tk.FLAT)
user_input_box.grid(row=1, column=0, padx=20, pady=10)

send_button = tk.Button(root, text="Send", width=12, font=("New times roman", 14), bg="#000000", fg="#ffffff", command=send_message)
send_button.grid(row=1, column=1, padx=0, pady=(0, 1000))

mic_button = tk.Button(chat_frame, image=mic_icon, command=recognize_speech, width=50, height=50, relief=tk.FLAT)
mic_button.grid(row=2, column=1, padx=20, pady=10)

chat_display.tag_configure("user", foreground="#ffffff", background="#000000", font=("New times roman", 14, "bold"))
chat_display.tag_configure("bot", foreground="#000000",  font=("New times roman", 14, "bold"))
chat_display.tag_configure("user_space", lmargin1=10, lmargin2=10)
chat_display.tag_configure("bot_space", rmargin=10)

root.mainloop()