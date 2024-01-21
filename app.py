import re
import streamlit as st
import openai
import os
from dotenv import load_dotenv, find_dotenv
from unidecode import unidecode
from pathlib import Path
import pickle

_ = load_dotenv(find_dotenv())

DIR_MESSAGES = Path(__file__).parent / 'messages'
DIR_MESSAGES.mkdir(exist_ok=True)
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

def retorno_resposta(messages, 
                     openai_key,
                     model='gpt-3.5-turbo',
                     temperature=0,
                     stream=False):
    openai.api_key = openai_key
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=stream
    )
    return response

def convert_message_name(message_name):
    file_name = unidecode(message_name)
    file_name = re.sub('\W+', '', file_name).lower()
    return file_name

def return_message_name(messages):
    for message in messages:
        if message['role'] == 'user':
            message_name = message['content'][:30]
            break
    return message_name

def save_message(messages):
    if len(messages) == 0:
        return False
    message_name = return_message_name(messages)
    file_name = convert_message_name(message_name)
    save_file = {'message_name':message_name,
                 'file_name':file_name,
                 'messages':messages}
    with open(DIR_MESSAGES / file_name, 'wb') as f:
        pickle.dump(save_file, f)
    
def read_message(messages, key='message'):
    if len(messages) == 0:
        return []
    message_name = return_message_name(messages)
    file_name = convert_message_name(message_name)
    with open(DIR_MESSAGES / file_name, 'rb') as f:
        message = pickle.load(f)
    return messages[key]

def pagina_principal():

    if not 'messages' in st.session_state:
        st.session_state.messages = []

    messages =  read_message(st.session_state['messages'])

    st.header('🤖 DoctorDocs', divider=True)
    
    for message in messages:
        chat = st.chat_message(message['role'])
        chat.markdown(message['content'])
    
    prompt = st.chat_input('Pergunte sobre a documentação do proejto')

    if prompt:
        new_message = {'role':'user','content':prompt}
        chat = st.chat_message(new_message['role'])
        
        chat.markdown(new_message['content'])

        messages.append(new_message)
        response_completed = ''
        chat = st.chat_message('assistant')
        placeholder = chat.empty()
        placeholder.markdown(' |')
        answers = retorno_resposta(messages, openai_key=OPENAI_KEY, stream=True)
        for response in answers:
            response_completed += response.choices[0].delta.get('content', '')
            placeholder.markdown(response_completed + ' |')
        new_message = {'role':'assistant', 'content': response_completed}
        messages.append(new_message)
        save_message(messages)




        st.session_state['messages'] = messages
pagina_principal()