from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate

llm = ChatGroq(
    temperature = 0,
    model_name = "llama3-8b-8192"
)

template = """You are a chatbot having a conversation with a human.
You have to Talk with the Human, and ask him questions like his Basic Details or Work Details and etc, so that you can build their Resume/CV. When you feel that you have Adequate Information, polietly end off the conversation and in the end the Message with '===EOF==='

{chat_history}
Human: {human_input}
Chatbot:"""

prompt = PromptTemplate(
    input_variables=["chat_history", "human_input"], template=template
)
memory = ConversationBufferMemory(memory_key="chat_history")

llm_chain = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=True,
    memory=memory,
)
