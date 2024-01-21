import re
import streamlit as st
import openai
import os
from dotenv import load_dotenv, find_dotenv
from unidecode import unidecode
from pathlib import Path
import pickle

# Load environment variables from .env file
_ = load_dotenv(find_dotenv())

# Define the directory for storing messages
DIR_MESSAGES = Path(__file__).parent / 'messages'
DIR_MESSAGES.mkdir(exist_ok=True)

# Get OpenAI API key from environment variable
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

# SAVE AND READ CHATS ============================

def retorno_resposta(messages: list, 
                     openai_key: str,
                     model: str ='gpt-3.5-turbo',
                     temperature: int = 0,
                     stream: bool = False):
    """
    Get the response from the OpenAI Chat API.

    Parameters:
    - messages (list): List of messages in the conversation.
    - openai_key (str): OpenAI API key.
    - model (str): Model name, default is 'gpt-3.5-turbo'.
    - temperature (int): Controls the randomness of the response, default is 0.
    - stream (bool): Whether to use streaming for API response, default is False.

    Returns:
    - dict: Response from the OpenAI Chat API.
    """
    openai.api_key = openai_key
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=stream
    )
    return response

def convert_message_name(message_name: str) -> str:
    """
    Convert a message name to a valid file name.

    Parameters:
    - message_name (str): The original message name.

    Returns:
    - str: Converted file name.
    """
    file_name = unidecode(message_name)
    file_name = re.sub('\W+', '', file_name).lower()
    return file_name

def return_message_name(messages: list) -> str:
    """
    Return the message name from the user's messages.

    Parameters:
    - messages (list): List of messages in the conversation.

    Returns:
    - str: Message name.
    """
    for message in messages:
        if message['role'] == 'user':
            message_name = message['content'][:30]
            break
    return message_name

def save_message(messages: list) -> None:
    """
    Save the conversation messages to a file.

    Parameters:
    - messages (list): List of messages in the conversation.
    """
    if len(messages) == 0:
        return False
    message_name = return_message_name(messages)
    file_name = convert_message_name(message_name)
    save_file = {'message_name': message_name,
                 'file_name': file_name,
                 'messages': messages}
    with open(DIR_MESSAGES / file_name, 'wb') as f:
        pickle.dump(save_file, f)

def read_message(messages: list, key: str ='messages') -> str:
    """
    Read the conversation messages from a file.

    Parameters:
    - messages (list): List of messages in the conversation.
    - key (str): Key to extract from the saved messages, default is 'messages'.

    Returns:
    - str: Extracted information from the saved messages.
    """
    if len(messages) == 0:
        return []
    message_name = return_message_name(messages)
    file_name = convert_message_name(message_name)
    with open(DIR_MESSAGES / file_name, 'rb') as f:
        messages = pickle.load(f)
    return messages[key]

def talk_list() -> list:
    talks =  list(DIR_MESSAGES.glob('*'))
    talks = sorted(talks, key= lambda item: item.stat().st_mtime_ns, reverse=True)
    return [talk.stem for talk in talks]

# PAGES ===========================================

def pagina_principal():
    """
    Main page for the Streamlit app.
    """
    if not 'messages' in st.session_state:
        st.session_state.messages = []

    messages = read_message(st.session_state['messages'])

    st.header('🤖 DoctorDocs', divider=True)
    
    for message in messages:
        chat = st.chat_message(message['role'])
        chat.markdown(message['content'])
    
    prompt = st.chat_input('Pergunte sobre a documentação do projeto')

    if prompt:
        new_message = {'role':'user', 'content': prompt}
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

def tab_talks(tab: st.tabs) -> st.tabs:
    """
    Placeholder for the talks tab.

    Parameters:
    - tab (st.tabs): The Streamlit tabs object.

    Returns:
    - st.tabs: The modified Streamlit tabs object.
    """
    tab.button('➕ Novo Chat',
               on_click=talk_select,
               args=('',),
               use_container_width=True)
    tab.markdown('')
    talks = talk_list()
    for talk in talks:
        tab.button(talk,
                on_click=talk_select,
                args=(talk,),
                use_container_width=True)     
    


def talk_select(message_name: str):
    if message_name == '':
        st.session_state.messages = []

def main():
    """
    Main function to run the Streamlit app.
    """
    pagina_principal()
    tab1, tab2 = st.sidebar.tabs(['Conversas', 'Configurações'])
    tab_talks(tab1)

if __name__ == '__main__':
    main()
