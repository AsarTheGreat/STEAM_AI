import os
import re
from colorama import Fore, Style, init
import requests
import time
import socket
import threading
import sys

init(autoreset=True)

KNOWLEDGE_FOLDER = "knowledge";
#KNOWLEDGE_FOLDER = "mystery";

# ASCII art for loading spinner
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

def show_spinner(stop_event):
    """Display an animated spinner while waiting."""
    frame_idx = 0
    while not stop_event.is_set():
        frame = SPINNER_FRAMES[frame_idx % len(SPINNER_FRAMES)]
        sys.stdout.write(f"\r{Fore.CYAN}{frame} Waiting for response from Ollama...{Style.RESET_ALL}")
        sys.stdout.flush()
        frame_idx += 1
        time.sleep(0.1)
    # Clear the spinner line
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()

#calling ollama API
def query_ollama(prompt):
    # Ensure Ollama is reachable before sending the request
    if not wait_for_ollama():
        print(Fore.YELLOW + "Warning: Ollama does not appear ready; attempting request anyway.")

    stop_spinner = threading.Event()
    spinner_thread = threading.Thread(target=show_spinner, args=(stop_spinner,), daemon=True)
    spinner_thread.start()

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "system": "Provide concise answers in no more than 2 sentences.",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 50
                }
            },
            timeout=300
        )

        stop_spinner.set()
        spinner_thread.join()

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            data = None

        # Debugging output
        #print(Fore.CYAN + f"Ollama response: {response.text}")

        if isinstance(data, dict):
            return data.get("response") or data.get("text") or ""
        return response.text

    except requests.exceptions.Timeout:
        stop_spinner.set()
        print(Fore.RED + "Error: Request to Ollama timed out.")
        return ""

    except requests.exceptions.RequestException as e:
        stop_spinner.set()
        print(Fore.RED + f"Error connecting to Ollama API: {e}")
        return ""

    except ValueError as e:
        stop_spinner.set()
        print(Fore.RED + f"Error parsing Ollama response: {e}")
        print(Fore.RED + f"Raw response: {response.text}")
        return ""
    
    finally:
        stop_spinner.set()

def wait_for_ollama(timeout=60, interval=2, model="llama3"):
    """Wait until Ollama is reachable and (optionally) the model responds.

    This will try a TCP connect to the API port, then attempt a small
    generate request to verify the model is responsive. Returns True if
    responsive before timeout, else False.
    """
    end = time.time() + timeout
    while time.time() < end:
        try:
            # Quick TCP check
            with socket.create_connection(("127.0.0.1", 11434), timeout=2):
                pass
        except OSError:
            time.sleep(interval)
            continue

        # If TCP is open, try a light-weight generation to ensure model server
        try:
            resp = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": "hello", "max_tokens": 1},
                timeout=10,
            )
            if resp.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass

        time.sleep(interval)

    return False
    
#Load all text files from the knowledge folder
def load_files():
    data = {};
    for filename in os.listdir(KNOWLEDGE_FOLDER):
        if not filename.endswith(".txt"):
            continue
        # only skip the introduction file when working with the mystery folder
        if KNOWLEDGE_FOLDER == "mystery" and filename == "mystery_introduction.txt":
            continue
        with open(os.path.join(KNOWLEDGE_FOLDER, filename), "r", encoding="utf-8") as f:
            data[filename] = f.read();
    return data;

#List all knowledge files
def list_files(data):
    print(Fore.CYAN + "Knowledge files:");
    for f in data.keys():
        print(" - " + f);

#read a specific file
def read_file(filename, data):
    if filename in data:
        print(Fore.YELLOW + f"\n---{filename}---\n");
        print(data[filename]);
    else:
        print(Fore.RED + f"File '{filename}' not found in knowledge base.");

STOPWORDS = {"a", "an", "the", "is", "are", "was", "were", "in", "on", "at", "of", "for", "to", "and", "or", "that", "this", "it", "what", "who", "when", "where", "why", "how"}

TOPIC_MAP = {
    "science": ["science", "biology", "chemistry", "physics", "earth", "scientist"],
    "technology": ["technology", "tech", "computer", "internet", "ai", "robot", "robotics", "digital", "network", "encryption", "software", "hardware", "programming", "coding"],
    "engineering": ["engineering", "engineer", "build", "design", "bridge", "structure", "machine", "circuit", "prototype", "construction"],
    "arts": ["art", "arts", "music", "drama", "design", "creative", "painting", "story", "literature", "culture", "theater"],
    "mathematics": ["math", "mathematics", "numbers", "algebra", "geometry", "calculus", "statistics", "probability", "pattern", "equation"],
    "greeting": ["hello", "hi", "greetings", "welcome", "hey", "good day", "greeting"]
}

def extract_keywords(text):
    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    return set(words) - STOPWORDS

# Build per-file keyword lists for the current folder
def build_keyword_index(data):
    return {filename: extract_keywords(text) for filename, text in data.items()}

def classify_query_context(query):
    q = query.lower()
    # time-related queries
    if re.search(r"\b(\d{1,2}:\d{2}|\d{1,2}\s?pm|\d{1,2}\s?am|when|time|happened at)\b", q):
        return "timeline"
    # evidence-related
    if any(w in q for w in ["clue", "evidence", "paw", "prints", "glitter", "flashlight", "cookie", "wheel"]):
        return "evidence"
    # location-related
    if any(w in q for w in ["where", "location", "located", "hall", "room", "planetarium", "reading", "gift", "storage"]):
        return "locations"
    # suspect/person-related
    if any(w in q for w in ["who", "suspect", "suspects", "luna", "professor", "janitor", "security", "guard", "director"]):
        return "suspects"
    # default
    return "default"


def best_line_for_query(query, text):
    query_words = [word for word in re.findall(r"\b[a-zA-Z0-9]+\b", query.lower()) if word not in STOPWORDS]
    best_score = 0
    best_line = ""

    for line in text.split("\n"):
        line_words = set(re.findall(r"\b[a-zA-Z0-9]+\b", line.lower())) - STOPWORDS
        score = sum(1 for word in query_words if word in line_words)
        if score > best_score:
            best_score = score
            best_line = line

    return best_line


def infer_topic_files(query, keyword_index, data):
    q = query.lower()
    filename_roots = {fname[:-4]: fname for fname in keyword_index}

    def format_result(fname):
        return (fname, best_line_for_query(query, data[fname]))

    # direct filename match first
    direct_matches = [filename_roots[root] for root in filename_roots if root in q]
    if direct_matches:
        return [format_result(fname) for fname in direct_matches]

    # phrase-based engineering priority
    if "software engineering" in q and "engineering" in filename_roots:
        return [format_result(filename_roots["engineering"])]

    scored = []
    for topic, words in TOPIC_MAP.items():
        if topic not in filename_roots:
            continue
        score = sum(1 for w in words if w in q)
        if score > 0:
            scored.append((score, filename_roots[topic]))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [format_result(filename) for _, filename in scored]


# Context-aware searching: prefer files that match the query category
def context_search(query, keyword_index, data):
    category = classify_query_context(query)

    # map category to filenames present in this folder
    candidate_files = []
    if category != "default":
        for fname in keyword_index.keys():
            if category in fname.lower():
                candidate_files.append((fname, best_line_for_query(query, data[fname])))

    # if no candidate files found for the category, derive topic files from the query
    if not candidate_files:
        candidate_files = infer_topic_files(query, keyword_index, data)

    # if still no candidate files, fall back to all files
    if not candidate_files:
        candidate_files = [(fname, best_line_for_query(query, data[fname])) for fname in keyword_index.keys()]
        fallback_to_all = True
    else:
        fallback_to_all = False

    # score candidate files by keyword overlap
    query_words = re.findall(r"\b[a-zA-Z0-9]+\b", query.lower())
    if not query_words:
        return []
    query_set = set(query_words)

    scored_files = []
    for filename, best_line in candidate_files:
        keywords = keyword_index.get(filename, set())
        score = sum(1 for word in query_set if word in keywords)
        if score > 0:
            scored_files.append((score, filename, best_line))

    if scored_files:
        scored_files.sort(key=lambda item: item[0], reverse=True)
        return [(filename, best_line) for _, filename, best_line in scored_files]

    # if candidate files were selected based on topic inference, return them anyway
    if not fallback_to_all:
        return candidate_files

    return []


# Answering question based on context-aware keyword matching
def answer(query, data, keyword_index):
    matches = context_search(query, keyword_index, data)
    if not matches:
        return Fore.RED + "I don't know that yet."

    query_words = [word for word in re.findall(r"\b[a-zA-Z0-9]+\b", query.lower()) if word not in STOPWORDS]
    results = []

    # check the top matching files and return the best matching line for each file
    for item in matches[:3]:
        if isinstance(item, tuple):
            filename, best_line = item
        else:
            filename, best_line = item, None

        if best_line:
            results.append(Fore.CYAN + f"\n--- {filename} ---")
            results.append(best_line)
            continue

        lines = data[filename].split("\n")
        file_hits = [line for line in lines if any(word in line.lower() for word in query_words)]
        if file_hits:
            best_file_line = best_line_for_query(query, "\n".join(file_hits))
            results.append(Fore.CYAN + f"\n--- {filename} ---")
            results.append(best_file_line)

    if not results:
        best = matches[0]
        if isinstance(best, tuple):
            filename, best_line = best
            return Fore.YELLOW + f"I found something in {filename}.\n" + best_line
        lines = data[best].split("\n")
        snippet = "\n".join(lines[:3])
        return Fore.YELLOW + f"I found something in {best}.\n" + snippet

    return Fore.GREEN + "\n".join(results)

#Help function to show available commands and usage
def print_help():
    print(Fore.MAGENTA + "Available commands:");
    print("  help - Show this help message");
    print("  exit - Exit the assistant");
    print("  list - List all knowledge files");
    print("  read <filename> - Read the contents of a specific knowledge file");
    print("  reload - Reload all knowledge files from disk");
    print("  study - Load STEAM_Study_Buddy");
    print("  back - Exit study mode and return to the default prompt");
    print("Any other input will be treated as a question to answer based on the knowledge files.");



def main():
    if KNOWLEDGE_FOLDER == "mystery":
        try:
            with open(os.path.join(KNOWLEDGE_FOLDER, "mystery_introduction.txt"), "r", encoding="utf-8") as f:
                print(Fore.MAGENTA + f.read());
        except FileNotFoundError:
            print(Fore.RED + "mystery_introduction.txt not found in mystery folder.");
    else:
        print(Fore.CYAN + "Welcome to the STEAM AI assistant!");
        print("Type 'help' for commands.\n");

    data = load_files();
    keyword_index = build_keyword_index(data)
    assistant_name = "STEAM_AI"
    use_ollama = False

    while True:
        user_input = input(Fore.WHITE + f"{assistant_name}> ").strip();

        if user_input.lower() == "":
            continue;
        
        if user_input.lower() == "exit":
            print(Fore.CYAN + "Goodbye!");
            break;

        if user_input.lower() == "help":
            print_help();
            continue;

        if user_input.lower() == "list":
            list_files(data)
            continue
        
        if user_input.lower().startswith("read "):
            filename = user_input.split(" ", 1)[1];
            read_file(filename, data);
            continue;
        
        if user_input.lower() == "reload":
            data = load_files();
            keyword_index = build_keyword_index(data)
            print(Fore.GREEN + "Knowledge files reloaded.");
            continue;

        if user_input.lower() == "study":
            assistant_name = "STEAM_Study_Buddy"
            use_ollama = True
            print(Fore.CYAN + "Study mode enabled. All following queries will be sent to Ollama. Type 'back' to return to the default prompt. ")
            continue;

        if user_input.lower() == "back":
            if use_ollama:
                use_ollama = False
                assistant_name = "STEAM_AI"
                print(Fore.CYAN + "Study mode disabled. Returning to the default prompt.")
            else:
                print(Fore.YELLOW + "You are not currently in study mode.")
            continue;

        if use_ollama:
            print(query_ollama(user_input))
            continue

        #otherwise, treat input as a question
        print(answer(user_input, data, keyword_index));

if __name__ == "__main__":
    main();