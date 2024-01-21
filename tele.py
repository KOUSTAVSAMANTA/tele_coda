import telebot
import random
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import StrOutputParser
import time
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from pymongo import MongoClient

os.environ["GOOGLE_API_KEY"] = "AIzaSyDqKzb2p4ItiEEao-oim5IcGgAifOtv6do"
BOT_TOKEN = "6661992463:AAFMNkZB-ao59C-J0IhryfuTXHpQUDnzdHI"
template = """You are a nice chatbot having a conversation with a human.your name is CODA Powerd by Gemini.you are developed by Koustav Samanta.
Note: if the human ask anything related the human answer from the Previous conversation.  

Previous conversation:
{chat_history}

Human question: {question}
Response:"""

uri = "mongodb+srv://koustav:koustav2003@cluster0.wmnc2.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(uri)
db = client['AUTH']
collection = db['Authentication']

memory_key = "chat_history"
# memory = ConversationBufferMemory(memory_key=memory_key)
# Initialize Telegram bot
bot = telebot.TeleBot(BOT_TOKEN)
bot.delete_webhook()

def load_or_create_memory(user_id, collection):
  """Loads the memory for a user if the user ID exists in the database.
  If the user ID does not exist, creates a new memory.

  Args:
    user_id: The user ID to check for.
    collection: The collection to check in.

  Returns:
    The memory for the user.
  """

  if collection.find_one({"user_id": user_id}) is not None:
    _mem = ConversationBufferMemory(memory_key=memory_key)
    memory = collection.find_one({"user_id": user_id})["memory_key"]
    for i in memory:
        try:
            _mem.chat_memory.add_user_message(i['Human'])
            _mem.chat_memory.add_ai_message(i['AI'])
        except Exception as e:
            pass
    return _mem
  else:
    memory = ConversationBufferMemory(memory_key=memory_key)
    return memory
def check_user(user_id, memory_key, collection):
  """Checks if a user is present in the collection.
  If present, updates the entry.
  If not present, creates a new entry.

  Args:
    user_id: The user ID to check for.
    memory_key: The memory key to update or create.
    collection: The collection to check in.

  Returns:
    True if the user is present, False otherwise.
  """

  if collection.find_one({"user_id": user_id}) is not None:
    collection.update_one(
        {"user_id": user_id}, {"$set": {"memory_key": memory_key}})
    return "updated"
  else:
    collection.insert_one({"user_id": user_id, "memory_key": memory_key})
    return "created"
def delete_entry(user_id, collection):
  """Deletes an entry from a collection where the user ID matches.

  Args:
    user_id: The user ID to match.
    collection: The collection to delete from.
  """

  collection.delete_one({"user_id": user_id})
  return "deleted"
@bot.message_handler(commands=['clear'])
def send_welcome(message):
    userid = message.chat.id
    z = delete_entry(user_id=userid,collection=collection)
    bot.send_message(chat_id=message.chat.id, text="Memory cleared !! "+z)
# Handle incoming messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    prompt = message.text
    userid = message.chat.id
    memory =load_or_create_memory(user_id=userid,collection=collection)
    print(memory)
    llm = ChatGoogleGenerativeAI(model="gemini-pro")
    prompt_t = PromptTemplate.from_template(template)

    # Notice that we need to align the `memory_key`
    conversation = LLMChain(
        llm=llm,
        prompt=prompt_t,
        verbose=True,
        memory=memory,
        output_parser=StrOutputParser()
    )
    z = conversation({"question": prompt})
    assistant_response = z['text']
    try:
        input_text = assistant_response
        code_start = input_text.find("```python")
        code_end = input_text.find("```", code_start + 1)

        if code_start != -1 and code_end != -1:
            print(input_text[code_start + 8:code_end].strip())
    except Exception as e:
        pass
    response_text = assistant_response
    print(prompt)
    bot.send_message(chat_id=message.chat.id, text=response_text)
    print(type(memory))
    z = memory.chat_memory.messages
    mem = []
    for i in range(0,len(z),2):
        mem.append({"Human":z[i].content,"AI":z[i+1].content})
    print(mem)
    # print(userid.id)
    ch =check_user(user_id=userid,memory_key=mem,collection=collection)
    print(ch)



# Run the bot
bot.polling()
