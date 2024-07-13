import dateparser
import datetime
import json
import pickle
import speech_recognition as sr
import wikipedia
import requests
import sqlite3
import unidecode
import pyttsx3
import webbrowser
import nltk
import numpy as np
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import load_model
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import messagebox
from tkcalendar import Calendar # type: ignore
import matplotlib.pyplot as plt
import pygame # type: ignore
import PyPDF2 # type: ignore

# Constants and Initialization
activationWord = "ordinateur"  # Define the activation word
lemmatizer = WordNetLemmatizer()
intents = json.loads(open("intents.json").read())
words = pickle.load(open("words.pkl","rb"))
classes = pickle.load(open("classes.pkl","rb"))
model = load_model("chatbot_model.model.keras")

firefox_path = r"C:\Program Files\Mozilla Firefox\firefox.exe"
webbrowser.register('firefox', None, webbrowser.BackgroundBrowser(firefox_path))

# Initialize text-to-speech engine
engine = pyttsx3.init()
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)


conn = sqlite3.connect('todo_list.db')
c = conn.cursor()

# Create tasks table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY, 
                task TEXT, 
                due_date TEXT,
                priority INTEGER,
                category TEXT)''')
conn.commit()

# Utility functions to clean input and create bag of words
def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    print(f"Tokenized and lemmatized words: {sentence_words}")

    bag = [0] * len(words)
    for w in sentence_words:
        if w in words:
            index = words.index(w)
            bag[index] = 1
            print(f"Word '{w}' found at index {index}")
        else:
            print(f"Word '{w}' not in vocabulary")

    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    
    ERROR_THRESHOLD = 0.15  # Try reducing to allow more intents to be detected
    
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)

    if not results:
        return [{"intent": "fallback", "probability": 1}]

    return [{"intent": classes[r[0]], "probability": r[1]} for r in results]


# Text-to-speech function
def speak(text, rate=120):
    engine.setProperty("rate", rate)
    print("test")
    engine.say(text)
    print("test")
    engine.runAndWait()
    print("test")

# Strip accents to improve recognition
def strip_accents(text):
    for i in range(0, len(text), 1):
        text[i] = unidecode.unidecode(text[i])
    return text

# Parse voice command and handle errors
def parseCommand():
    recognizer = sr.Recognizer()
    mic_list = sr.Microphone.list_microphone_names()
    mic_name = "Microphone (USB Audio Device)"
    try:
        mic_index = mic_list.index(mic_name)
    except ValueError:
        speak("Microphone non trouvé.")
        return "none"

    try:
        with sr.Microphone(device_index=mic_index) as source:
            recognizer.pause_threshold = 2
            print("Microphone initialized. Listening...")
            input_speech = recognizer.listen(source)
            
        print("Recognizing speech ...")
        query = recognizer.recognize_google(input_speech, language="fr-FR")
        print(f"The input speech was: {query}")
        return query.lower()  # Convert to lowercase for easier parsing
    
    except sr.UnknownValueError:
        speak("Je n'ai pas compris ce que vous avez dit. Pouvez-vous répéter, s'il vous plaît ?")
        return "none"
    except sr.RequestError:
        speak("Le service de reconnaissance vocale est actuellement indisponible.")
        return "none"
    except Exception as e:
        speak("Erreur de reconnaissance vocale.")
        print("Error:", e)
        return "none"

# Wikipedia Search
def search_wikipedia(query=''):
    searchResult = wikipedia.search(query)
    if not searchResult:
        print('No wikipedia result')
        return 'No result received'
    try:
        wikiPage = wikipedia.page(searchResult[0])
    except wikipedia.DisambiguationError as error:
        wikiPage = wikipedia.page(error.options[0])
    print(wikiPage.title)
    wikiSummary = str(wikiPage.summary)
    return wikiSummary

# Joke Telling
def tell_joke():
    joke_url = "https://v2.jokeapi.dev/joke/Any?type=single"
    response = requests.get(joke_url)
    if response.status_code == 200:
        joke = response.json().get("joke", "I couldn't find a joke right now.")
        return joke
    else:
        return "I couldn't fetch a joke."

def parse_date(expression):
    # Utilisation de dateparser pour analyser l'expression de date
    date = dateparser.parse(expression, languages=['fr'])
    if date:
        return date
    else:
        return "Date non reconnue"


# Task Management
def show_tasks():
    c.execute("SELECT * FROM tasks")
    tasks = c.fetchall()
    root = tk.Tk()
    root.title("Liste de Tâches")
    for task in tasks:
        task_str = f"Tâche {task[0]} : {task[1]}, échéance : {task[2] if task[2] else 'aucune'}, priorité : {task[3]}, catégorie : {task[4]}"
        tk.Label(root, text=task_str, pady=5).pack()
    root.mainloop()

def add_task(task, due_date=None, priority=1, category="General"):
    c.execute("INSERT INTO tasks (task, due_date, priority, category) VALUES (?, ?, ?, ?)", 
              (task, due_date, priority, category))
    conn.commit()
    speak(f"Tâche ajoutée : {task}, échéance : {due_date if due_date else 'aucune'}, priorité : {priority}, catégorie : {category}")

def list_tasks():
    c.execute("SELECT * FROM tasks")
    tasks = c.fetchall()
    if tasks:
        speak("Voici votre liste de tâches :")
        for task in tasks:
            speak(f"Tâche {task[0]} : {task[1]}")
    else:
        speak("Votre liste de tâches est vide.")

def update_task(task_id, new_task):
    c.execute("UPDATE tasks SET task = ? WHERE id = ?", (new_task, task_id))
    conn.commit()
    speak(f"Tâche mise à jour : {task_id}")

def delete_task(task_id):
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    speak(f"Tâche supprimée : {task_id}")

def search_tasks(keyword):
    c.execute("SELECT * FROM tasks WHERE task LIKE ?", ('%' + keyword + '%',))
    tasks = c.fetchall()
    if tasks:
        speak(f"Voici les tâches contenant le mot-clé {keyword} :")
        for task in tasks:
            speak(f"Tâche {task[0]} : {task[1]}, échéance : {task[2] if task[2] else 'aucune'}, priorité : {task[3]}, catégorie : {task[4]}")
    else:
        speak(f"Aucune tâche ne contient le mot-clé {keyword}.")

def plot_tasks_by_category():
    c.execute("SELECT category, COUNT(*) FROM tasks GROUP BY category")
    data = c.fetchall()
    categories = [row[0] for row in data]
    counts = [row[1] for row in data]
    
    plt.figure(figsize=(10, 5))
    plt.bar(categories, counts, color='blue')
    plt.xlabel('Catégories')
    plt.ylabel('Nombre de Tâches')
    plt.title('Tâches par Catégorie')
    plt.show()

    pygame.mixer.music.stop()
    speak("Musique arrêtée")

# PDF Reading
def read_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfFileReader(file)
        text = ""
        for page_num in range(reader.numPages):
            page = reader.getPage(page_num)
            text += page.extract_text()
        speak(text)

def readPrediction(predictions, intents):
    relevant_response = []
    list_of_intents = intents["intents"]
    for result in predictions:
        tag = result["intent"]
        probability  = result["probability"]
        print(f"Detected intent : {tag} with probability: {probability}")
        match tag:
            case "Internet":
                try:
                    speak("Que voulez vous ouvrir ?")
                    query = parseCommand.lower()
                    webbrowser.get('firefox').open_new(query)  # Open the website in the default browser
                    speak(f"Opening {query}")
                except Exception as e:
                    speak("I couldn't open the website.")
                    print("Error opening website:", e)
                break
            case "task_add":
                speak("Quel est la tâche ?")
                task = parseCommand().lower()
                speak("Quelle est la date d'échéance ?")
                due_date = parse_date(parseCommand().lower())
                speak("Quel est la priorité ?")
                priorite = parseCommand().lower()
                speak("Quel est la catégorie ?")
                cat = parseCommand.lower()
                add_task(task, due_date, priorite, cat)
                break
            case "task_update":
                try:
                    task_id = int(query[3])
                    new_task = " ".join(query[4:])
                    update_task(task_id, new_task)
                except (ValueError, IndexError):
                    speak("Impossible de modifier la tâche.")
                break
            case "task_delete":
                try:
                    speak("Donnez l'identifiant de la tâche")
                    keyword = parseCommand().lower()
                    task_id = int(keyword)
                    delete_task(task_id)
                except (ValueError, IndexError):
                    speak("Impossible de supprimer la tâche.")
                break
            case "task_view":
                plot_tasks_by_category()
                break
            case "task_tables":
                show_tasks()
                break
            case "task_search":
                speak("Que cherchez-vous : Veuillez donner le mot clé")
                keyword = parseCommand().lower()
                search_tasks(keyword)
                break
            case "joke":
                speak(tell_joke())
                break
            case "pdf_read":
                file_path = " ".join(query[3:])
                read_pdf(file_path)


# Main loop with web browser functionality
if __name__ == "__main__":
    print("Debut")
    speak("All systems nominal.")
    print("parler")
    while True:
        query = parseCommand().lower().split()
        query = strip_accents(query)
        if query == ["none"]:
            continue  # If there's an error, skip to the next loop iteration

        if len(query) > 0 and query[0] == activationWord:
            query.pop(0)  # Remove activation word
            if query[0] == 'exit' or query[0] == 'fin':
                speak('Au revoir')
                break
            query = " ".join(query)
            prediction = predict_class(query)
            response = readPrediction(prediction, intents)