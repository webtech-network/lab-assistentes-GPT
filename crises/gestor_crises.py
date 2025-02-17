# pip install langchain langchain_chroma langchain_core langchain_text_splitters langchain_openai langchain_community pypdf rapidocr_onnxruntime
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.chains import create_history_aware_retriever
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI

# Caso não seja possivel colocar a chave nas variaveis de ambiente incira manualmente aqui
# Senao deixe vazio
openai_api_key=""

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7, # A temperatura varia de 0 ate 1
    max_tokens=None,
    api_key=openai_api_key,
    # timeout=None,
    # max_retries=2
    )

# criação de vetor de documentos

path_vetorDb = "crises/vetorDB"
vectorstore = Chroma(persist_directory=path_vetorDb, embedding_function=OpenAIEmbeddings(api_key=openai_api_key))
retriever = vectorstore.as_retriever()

system_prompt = (
    "Você é uma assistente para auxiliar funcionariso do setor de gestao de crise de uma empresa."
    "o funcionario ira te chamer quando estiver para ocorrer uma crise ou quando um crise ja esta ocorrendo, por isso DEVE se saber com qual situação esta lidando para procegrir com o atendimento."
    "Por ser uma situação de crise, é importante que você mantenha a calma e siga os procedimentos de segurança, É de suma importancea que lembre o usuario disso"
    "Caso o usuario não saiba o que fazer, você deve instrui-lo a seguir os protocolos de segurança da empresa."
    "Deve-se assumir uma posição amigavel, pois ajuda a acalmar o usuario e a manter a calma, por isso deve perguntar o nome do usuario qual setor ele trabalha."
    "Você deve apenas ser acionado em tempos de crise por isso qualquer pergunta fora do escopo deve ser ignorada e repudiada."
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

contextualize_q_system_prompt = (
"Você é uma assistente para auxiliar funcionariso do setor de gestao de crise de uma empresa."
"o funcionario ira te chamer quando estiver para ocorrer uma crise ou quando um crise ja esta ocorrendo, por isso DEVE se saber com qual situação esta lidando para procegrir com o atendimento."
"Por ser uma situação de crise, é importante que você mantenha a calma e siga os procedimentos de segurança, É de suma importancea que lembre o usuario disso"
)

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)


# Vetor do chat
chat_history = []

while True:
  # Pergunta ao usuário
  question = input("Digite sua pergunta: ")

  # Processa a pergunta e gera a resposta da IA
  ai_msg = rag_chain.invoke({"input": question, "chat_history": chat_history})
  chat_history.extend([HumanMessage(content=question), AIMessage(content=ai_msg["answer"])])

  # Imprime a resposta da IA
  print(ai_msg["answer"] + "\n")