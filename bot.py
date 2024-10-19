import requests
from typing import Final, List
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import re
import random
import spacy
import numpy as np
from sentence_transformers import SentenceTransformer, util

# Your bot token and username
# Your bot token and username
TOKEN: Final = '7147905922:AAFPXxcBS3vdWmc0W0BrQ_EP2SsiyxhSzZY'
BOT_USERNAME: Final = '@Iesp0404_bot'


TRUTH_FILE = 'truths.txt'
DARE_FILE = 'dares.txt'
filename = "knwldg.txt"


# Google Custom Search API credentials
GOOGLE_API_KEYS: Final[List[str]] = [
    'AIzaSyDqzvNif6a5kJm_sc4EmJzSk5upzrvHE48',  # First API Key
    'AIzaSyCZjlwdblmT1T6xJrsUi22V9xgw9MZzByw',  # Replace with your second API key
]
GOOGLE_CXS: Final[List[str]] = [
    '92178ceca83294240',  # First CX ID
    '671582ee1a93142c9',  # Replace with your second CX ID
]
ALLOWED_GROUP_ID: Final = -1001817635995  # Replace with your actual group ID
ALLOWED_ADMIN_GROUP_ID: Final = -1002137866227

GIF_IMAGE_PATHS: Final = {
    'bite': 'Image/bite.gif',
    'boom': 'Image/boom.gif',
    'beat': 'Image/beat.gif',
    'call': 'Image/call.gif',
    'care': 'Image/care.gif',
    'chill': 'Image/chill.gif',
    'dance': 'Image/dance.gif',
    'enjoy': 'Image/enjoy.gif',
    'feed': 'Image/feed.gif',
    'fight': 'Image/fight.gif',
    'fry': 'Image/fry.gif',
    'greet': 'Image/greet.gif',
    'go': 'Image/go.gif',
    'hug': 'Image/hug.gif',
    'ignore': 'Image/ignore.gif',
    'kill': 'Image/kill.gif',
    'knock': 'Image/knock.gif',
    'miss': 'Image/miss.gif',
    'move': 'Image/move.gif',
    'patt': 'Image/patt.gif',
    'play': 'Image/play.gif',
    'poison': 'Image/poison.gif',
    'poke': 'Image/poke.gif',
    'praise': 'Image/praise.gif',
    'roast': 'Image/roast.gif',
    'scold': 'Image/scold.gif',
    'silent': 'Image/silent.gif',
    'slap': 'Image/slap.gif',
    'snatch': 'Image/snatch.gif',
    'sorry': 'Image/sorry.gif',
    'spit': 'Image/spit.gif',
    'stab': 'Image/stab.gif',
    'stalk': 'Image/stalk.gif',
    'swing': 'Image/swing.gif',
    'tease': 'Image/tease.gif',
    'teach': 'Image/teach.gif',
    'write': 'Image/write.gif',
    'throw': 'Image/throw.gif'
}

class KnowledgeBase:
    def __init__(self, text):
        # Load the pre-trained model once during initialization
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        
        self.text = text
        self.qa_pairs = self._extract_qa_pairs(text)
        self.questions = [qa[0] for qa in self.qa_pairs]
        self.answers = [qa[1] for qa in self.qa_pairs]
        self.question_embeddings = self._embed_sentences(self.questions)
        self.answer_embeddings = self._embed_sentences(self.answers)

    def _extract_qa_pairs(self, text):
        """Extract question-answer pairs from the provided text."""
        qa_pairs = []
        lines = text.split("\n")
        for i in range(0, len(lines)-1, 2):  # Assuming each question and answer are on consecutive lines
            question = lines[i].replace("User 1:", "").strip()
            answer = lines[i+1].replace("User 2:", "").strip()
            qa_pairs.append((question, answer))
        return qa_pairs

    def _embed_sentences(self, sentences):
        """Embed sentences using the SentenceTransformer model."""
        return self.model.encode(sentences, convert_to_tensor=True)

    def answer_question(self, query, top_k=1):
        """Find the most relevant answer based on the query."""
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        cos_similarities = util.pytorch_cos_sim(query_embedding, self.question_embeddings)
        
        # Ensure similarities are computed on the CPU
        cos_similarities = cos_similarities.cpu()

        # Get the top k most similar questions
        top_results = np.argpartition(-cos_similarities, range(top_k))[0:top_k]
        best_question_idx = top_results[0][0]

        # Get the corresponding answer
        best_answer = self.answers[best_question_idx]

        # Remove "User 1:" or "User 2:" from the response before sending it back
        clean_answer = re.sub(r'(User\s*[12]:\s*)', '', best_answer)

        return self._limit_answer_length(clean_answer)

    def _limit_answer_length(self, answer, max_words=150):
        """Limits the answer to a maximum of max_words words."""
        words = answer.split()
        if len(words) > max_words:
            return ' '.join(words[:max_words]) + "..."
        return answer
 
# Initialize the knowledge base with the content from the file

with open(filename, 'r', encoding='utf-8') as file:
    text = file.read()

kb = KnowledgeBase(text)

def clean_text(text: str) -> str:
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    return text


# Function to get a random line from a file
def get_random_line(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:  # Specify UTF-8 encoding
            lines = file.readlines()
            return random.choice(lines).strip() if lines else 'No content found.'
    except FileNotFoundError:
        return f'{file_path} not found. Please make sure the file exists.'
    except UnicodeDecodeError as e:
        return f'Error reading file {file_path}: {e}'


def add_line_to_file(file_path: str, new_line: str) -> str:
    try:
        with open(file_path, 'a') as file:  # Open file in append mode
            file.write(new_line + '\n')
        return 'Your text has been added!'
    except Exception as e:
        return f'Failed to add text: {e}'


async def add_truth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id == ALLOWED_ADMIN_GROUP_ID:  # Check if the command is used in the allowed group
        user_message = ' '.join(context.args).strip()
        if user_message:
            response = add_line_to_file(TRUTH_FILE, user_message)
            await update.message.reply_text(response)
        else:
            await update.message.reply_text('Please provide a truth question to add.')
    else:
        await update.message.reply_text('This command is not allowed in this group.')


async def add_dare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id == ALLOWED_ADMIN_GROUP_ID:  # Check if the command is used in the allowed group
        user_message = ' '.join(context.args).strip()
        if user_message:
            response = add_line_to_file(DARE_FILE, user_message)
            await update.message.reply_text(response)
        else:
            await update.message.reply_text('Please provide a dare to add.')
    else:
        await update.message.reply_text('This command is not allowed in this place Use in https://t.me/+yVFKtplWZUA0Yzhl admin group.')


async def send_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    command = update.message.text.split()[0][1:]
    file_path = GIF_IMAGE_PATHS.get(command)
    username = update.message.from_user.username
    target_user = re.search(r'@(\w+)', update.message.text)
    target_username = target_user.group(0) if target_user else 'someone'
    custom_message = f'@{username} is {command}ing {target_username}'

    if file_path:
        if file_path.endswith('.gif'):
            await update.message.reply_animation(animation=open(file_path, 'rb'), caption=custom_message)
        else:
            await update.message.reply_photo(photo=open(file_path, 'rb'), caption=custom_message)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! Thanks For Chatting With Me, I am YourBot.')


async def truth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    truth = get_random_line('truths.txt')
    await update.message.reply_text(truth)


# Function to handle the /dare command
async def dare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dare = get_random_line('dares.txt')
    await update.message.reply_text(dare)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('No worries, I will assist you with all kinds of help. For more help, contact @YourContactUsername.')


async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('For a custom command, I will respond in a customized way.')


async def get_google_search_response(query: str) -> str:
    search_url = "https://www.googleapis.com/customsearch/v1"
    for api_key, cx in zip(GOOGLE_API_KEYS, GOOGLE_CXS):
        params = {
            "key": api_key,
            "cx": cx,
            "q": query
        }
        try:
            response = requests.get(search_url, params=params)
            if response.status_code == 429:  # Check for quota exceeded
                continue  # Try the next API key and CX ID
            response.raise_for_status()
            search_results = response.json()
            if 'items' in search_results:
                snippets = [clean_text(item.get('snippet', '')) for item in search_results['items']]
                return ' '.join(snippets)[:400]  # Limit response to 400 characters
            else:
                return 'No results found.'
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 403:  # Forbidden (possibly quota exceeded)
                continue  # Try the next API key and CX ID
            return f"HTTP error occurred: {http_err}"
        except Exception as err:
            return f"Other error occurred: {err}"

    # If all keys are exhausted
    return "I've reached my daily search limit. I'll be able to respond after tomorrow."


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    # Check if the command is being used in the allowed group
    if chat_id == ALLOWED_GROUP_ID:
        user_message = ' '.join(context.args)
        if user_message:
            response = await get_google_search_response(user_message)
            await update.message.reply_text(response)
        else:
            await update.message.reply_text('Please ask a question.')
    else:
        await update.message.reply_text('Sorry, this command is not allowed in this group. Join https://t.me/+yVFKtplWZUA0Yzhl')


def handle_response(text: str) -> str:
    processed: str = text.lower()
    if re.search(r'\bhello\b|\bhi\b|\bhii\b|\bhii\b|\bhlo\b|\bhey\b', processed):
        return 'Hello, hi there! How are you?'
    if re.search(r'\bhow are you\b', processed):
        return 'I am just a bot, but I’m here to help you. How can I assist you?'
    if re.search(r'\bthank you\b|\bthanks\b|\bthank\b', processed):
        return 'You’re welcome! Let me know if you need anything else.'
    if re.search(r'\bbye\b|\bgoodbye\b', processed):
        return 'Goodbye! Have a great day!'
    if re.search(r'\bhelp\b', processed):
        return 'I am here to help! Just let me know what you need assistance with.'
    if re.search(r'\bsamaira\b', processed):
        return 'she is a nyc person'
    if re.search(r'\bpurpose of the group\b', processed):
        return 'To Improve English Speaking ✨Keep Learning Keep Growing✨'
    if re.search(r'\bwho is your owner\b', processed):
        return 'My Owner is Ishi'
    if re.search(r'\bgood (morning|mrng|night|nyt|afternoon|noon)\b|\bgm\b|\bgn\b|\bgd nyt\b', processed):
        return 'Jai Shree Krishna, ask any query with search command'

    

    return None


# Command to list all available commands
async def commands_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands_list = '\n'.join([f'/{cmd}' for cmd in GIF_IMAGE_PATHS.keys()])
    all_commands = f"Available commands:\n{commands_list}\n/search"
    await update.message.reply_text(all_commands)



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    

    words = text.split()
    if len(words) > 2:
        response = kb.answer_question(text)
        print('Bot:', response)
        await update.message.reply_text(response)
    else:
        response = handle_response(text)
        if response:
            print('Bot:', response)
            await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


if __name__ == "__main__":
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    for command in GIF_IMAGE_PATHS.keys():
        app.add_handler(CommandHandler(command, send_media))

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))
    app.add_handler(CommandHandler('search', search_command))
    app.add_handler(CommandHandler('iespcommands', commands_command))
    app.add_handler(CommandHandler('truth', truth_command))
    app.add_handler(CommandHandler('dare', dare_command))
    app.add_handler(CommandHandler('addtruth', add_truth_command))
    app.add_handler(CommandHandler('adddare', add_dare_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error)

    print('Polling the bot...')
    app.run_polling(poll_interval=1)
