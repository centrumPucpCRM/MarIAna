from langchain.vectorstores import FAISS
import numpy as np
import pinecone
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from servicios import ActualizarCursosScrapeados,ObtenerCursosScrapeados
from obtenerArreglosParaActualizarPinecone import obtenerArreglosParaActualizarPinecone,obtenerIndexTodosCursos
from ActualizarIndexTodosCursos import actualizarIndexTodosCursos,actualizarIndexTodosCursos
from scrapingPrincipal import scrapingPrincipal
import requests
import os
from dotenv import load_dotenv
load_dotenv()

def obtenerIndexDetalleCursos():
    api_key = "78e19e89-ca6f-4057-bc03-0c0ff6330e61"
    pc = pinecone.Pinecone(api_key=api_key)
    index_name = "detalle-cursos"
    index = pc.Index(index_name)
    return index

def chunk_string(text, chunk_size=1000, buffer_size=100):
    words = text.split()
    chunks = []
    current_chunk = ""
    current_size = 0
    for word in words:
        if current_size + len(word) + 1 > chunk_size:
            chunks.append(current_chunk)
            current_chunk = word
            current_size = len(word)
        else:
            if current_chunk:
                current_chunk += " " + word
            else:
                current_chunk = word
            current_size += len(word) + 1  # +1 for the space
    if current_chunk:
        chunks.append(current_chunk)
    final_chunks = []
    for chunk in chunks:
        while len(chunk) > chunk_size:
            split_index = chunk.rfind(' ', 0, chunk_size)
            if split_index == -1:
                split_index = chunk_size
            final_chunks.append(chunk[:split_index])
            chunk = chunk[split_index:].strip()
        if chunk:
            final_chunks.append(chunk)
    return final_chunks

def crearVectores(informacionDelCurso):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    chunks = chunk_string(informacionDelCurso)
    documents = [Document(page_content=chunk) for chunk in chunks]
    embedding = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY,
            model="text-embedding-3-large"  # Specify the model to use
    )
    vector_store = FAISS.from_documents(documents, embedding=embedding)
    metadata_dict = {i: {'chunkInfoLimpia': doc.page_content} for i, doc in enumerate(documents)}
    vectors = []
    for i in range(vector_store.index.ntotal):
        vector = vector_store.index.reconstruct(i)
        if isinstance(vector, np.ndarray):
            vector_list = vector.astype(np.float32).tolist()
            metadata = metadata_dict.get(i, {})
            vectors.append({
                "id": str(i),
                "values": vector_list,
                "metadata": metadata
            })
        else:
            print(f"Error: El vector con ID {i} no es un np.ndarray.")
            print(f"Tipo del vector: {type(vector)}")
            print(f"Contenido del vector: {vector}")
    return vectors

#===============================================================================
try:
    ActualizarCursosScrapeados()
    hijos=ObtenerCursosScrapeados()
    todos_cursos=[]
    contador=0
    index=obtenerIndexTodosCursos()
    for hijo in hijos:
        link=hijo["Link"]
        if link != 'No link found':
            print(link)
            try:
                response = requests.get(link)
                if response.status_code == 404:
                    print(f"Error 404: El link {link} no existe.")
                    continue
            except requests.exceptions.RequestException as e:
                print(f"Error al acceder al link {link}: {e}")
            cursos=scrapingPrincipal(hijo["Titulo"],link)
            if(cursos):
                todos_cursos.extend(cursos)
                contador+=1
        if(contador==200):
            break
    arrCrear,arrActualizar,arrEliminar=obtenerArreglosParaActualizarPinecone(todos_cursos)

    print(len(arrCrear),len(arrActualizar),len(arrEliminar))
    arrCrear,arrActualizar,arrEliminar=actualizarIndexTodosCursos(arrCrear,arrActualizar,arrEliminar,index)
except Exception as e:
    print(e)
