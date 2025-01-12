import regex as re
from bs4 import BeautifulSoup
from datetime import datetime
import calendar
from langchain_openai import OpenAIEmbeddings
import openai
import re
import json
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def fecha_a_letras(fecha_str):
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        dia = fecha.day
        mes = calendar.month_name[fecha.month]  # Nombre completo del mes
        # Formatear la fecha en letras
        fecha_letras = f"{dia} de {mes}"
        return fecha_letras
    except Exception as e:
        return "no hay fecha definida"
def reemplazar_tildes(texto):
    """Reemplaza caracteres acentuados por sus equivalentes sin acento."""
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N'
    }
    for acentuado, sin_acento in reemplazos.items():
        texto = texto.replace(acentuado, sin_acento)
    return texto
def crearVector(cursos,index):
    openai.api_key = OPENAI_API_KEY
    for curso in cursos:
        try:
            curso["Fecha inicio String"]=fecha_a_letras(curso["Fecha inicio"])
            print(curso)
            try:
                curso["Edad mínima"] = int(curso["Edad mínima"])
                curso["Edad mínima"] = 20
            except Exception as e:
                print(e)
                curso["Edad mínima"] = 20
            namespace = "cursos"
            info_vector = f'Titulo: {curso["Titulo"]}, Precio de lista: {curso["Precio de lista"]}, Fecha inicio: {curso["Fecha inicio String"]}, '
            info_vector += f'Edad minima: {str(curso["Edad mínima"])}, '
            info_vector += f'Modalidad: {curso["Modalidad"]}, Componente internacional: {curso["Componente internacional"]}, '
            info_vector += f'Dias y horario de dictado: {curso["Días y horario de dictado"]}, Duracion del programa: {curso["Duración del programa"]}, '
            info_vector += f'Lugar de dictado: {curso["Lugar de dictado"]}, '
            info_vector += f'Certificaciones: {curso["Certificacion"]}'
            info_vector=reemplazar_tildes(info_vector)
            print(info_vector)
            embedding = OpenAIEmbeddings(
                openai_api_key=OPENAI_API_KEY,
                model="text-embedding-3-large"
            )
            metadata = curso
            metadata["infoCrudaWEB"]=len(metadata["infoCrudaWEB"])
            metadata["infoCrudaPDF"]=len(metadata["infoCrudaPDF"])
            del metadata["infoLimpiaPDF"]
            del metadata["infoLimpiaWEB"]
            vector = embedding.embed_documents([info_vector])  # Asegúrate de que `embed_documents` devuelve una lista de vectores
            if isinstance(vector, list) and isinstance(vector[0], list):
                vector = vector[0]  # Extraer el primer (y único) vector de la lista
            metadata = {k: (v if v is not None else "") for k, v in curso.items()}
            index.upsert(vectors=[(curso["codigoCRM"], vector, metadata)], namespace=namespace)
        except Exception as e:
            print(curso)
            print(e)

def eliminarVector(arrEliminar,index):
    namespace="cursos"
    print("Inicio eliminar")
    print(arrEliminar)
    index.delete(ids=arrEliminar, namespace=namespace)
    print("Fin eliminar")
def actualizarVector(cursos,index):
    codigos=[]
    namespace = "cursos"
    for codigo in cursos:
        codigos.append(codigo["codigoCRM"])
    eliminarVector(codigos,index)
    crearVector(cursos,index)
    embedding = OpenAIEmbeddings(
        openai_api_key=OPENAI_API_KEY,
        model="text-embedding-3-large"
    )
def RobotEspecialistaLimpiar(mensaje):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """
                Eres un experto en ordenar informacion.
                Recibiras en tu hyperparametro {texto_largo}
                No resumas informacion(esto es lo mas importante).
                """
            },
            {
                "role": "user",
                "content": mensaje,
            }
        ],
        model="gpt-4o-mini",
        temperature=0.2  # Establece la temperatura en 0
    )
    # Extrae y devuelve el contenido de la respuesta
    return chat_completion.choices[0].message.content

def RobotEspecialistaCompletar(infoLimpia,completar):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""
                Tu objetivo principal es completar la siguiente informacion.
                completar={completar}
                Ten en consideracion que si la modalidad es virtual, entonces
                el lugar de dictado seria Online.
                debes entregar el valor entre llaves
                A continuacion se te pasara la informacion que usaras para completar la informacion faltante
                """
            },
            {
                "role": "user",
                "content": infoLimpia,
            }
        ],
        model="gpt-4o-mini",
        temperature=0.2  # Establece la temperatura en 0
    )
    # Extrae y devuelve el contenido de la respuesta
    return chat_completion.choices[0].message.content

def reemplazar_tildes(texto):
    """Reemplaza caracteres acentuados por sus equivalentes sin acento."""
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N'
    }
    for acentuado, sin_acento in reemplazos.items():
        texto = texto.replace(acentuado, sin_acento)
    return texto
def limpiarInfo(arr):
    if arr:
        cursos=[]
        for curso in arr:
            certificaciones = {
                "MADEN": " certificacion imagister",
                "Maestrias": "certificacion magister",
                "Maestrías": "certificacion magister",
                "Doctorados": "certificacion doctor",
                "MBA": "certificacion magister",
                "Doble Grado": "certificacion double grado magister",
                "Diplomaturas": "certificacion diplomatura",
                "Especializaciones": "certificacion especializacion",
                "Edex": "certificacion edex"
            }
            # Función para asignar certificaciones basadas en el contenido de "Titulo"
            def asignar_certificacion(titulo):
                for clave, valor in certificaciones.items():
                    if clave in titulo:
                        return valor
                return titulo  # Devuelve el título original si no se encuentra ninguna coincidencia

            # Aplicar la función a la columna "Titulo" y crear la columna "Certificacion"
            curso["Certificacion"] = asignar_certificacion(asignar_certificacion(curso["Titulo"]))
            print(curso["Certificacion"])
            curso["infoLimpiaPDF"]=RobotEspecialistaLimpiar(curso["infoCrudaPDF"])
            curso["infoLimpiaPDF"]=reemplazar_tildes(curso["infoLimpiaPDF"])
            curso["infoLimpiaWEB"]=RobotEspecialistaLimpiar(curso["infoCrudaWEB"])
            curso["infoLimpiaWEB"]=reemplazar_tildes(curso["infoLimpiaWEB"])
            curso["infoLimpia"]=RobotEspecialistaLimpiar(curso["infoLimpiaPDF"] + curso["infoLimpiaWEB"])
            curso["infoLimpia"]=reemplazar_tildes(curso["infoLimpia"])
            completar={
                    "Días y horario de dictado":"falta completar",
                    "Modalidad":"falta completar",
                    "Duración del programa":"falta completar",
                    "Lugar de dictado":"falta completar",
            }
            completar=RobotEspecialistaCompletar(curso["infoLimpia"],completar)
            valor=completar
            print(completar)
            completar=extraer_informacion(completar)
            print(completar)
            curso["Días y horario de dictado"]=reemplazar_tildes(completar["Días y horario de dictado"])
            curso["Modalidad"]=reemplazar_tildes(completar["Modalidad"])
            curso["Duración del programa"]=reemplazar_tildes(completar["Duración del programa"])
            curso["Lugar de dictado"]=reemplazar_tildes(completar["Lugar de dictado"])
            cursos.append(curso)
        return cursos


def extraer_informacion(informacionObtenida):
    if isinstance(informacionObtenida, str):
        # Si es una cadena, aplica la expresión regular
        # Asegúrate de que el formato de la cadena sea adecuado para la regex
        matches = re.findall(r'\{(.*?)\}', informacionObtenida, re.DOTALL)
        if matches:
            # Asumiendo que solo hay una coincidencia y está en formato JSON
            json_string = "{" + matches[0] + "}"
            # Reemplaza comillas simples por dobles si es necesario
            json_string = json_string.replace("'", '"')
            try:
                # Intenta convertir la cadena JSON a un diccionario
                info_dict = json.loads(json_string)
                return info_dict
            except json.JSONDecodeError:
                print("Error al decodificar JSON")
                return {}
        else:
            print("No se encontraron coincidencias")
            return {}
    elif isinstance(informacionObtenida, dict):
        # Si ya es un diccionario, simplemente devuélvelo
        return informacionObtenida
    else:
        print("Tipo de dato no soportado")
        return {}

def actualizarIndexTodosCursos(arrCrear,arrActualizar,arrEliminar,index):
    if arrCrear:
        arrCrear=limpiarInfo(arrCrear)
        crearVector(arrCrear,index)
    if arrActualizar:
        arrActualizar=limpiarInfo(arrActualizar)
        actualizarVector(arrActualizar,index)
    if arrEliminar:
        eliminarVector(arrEliminar,index)
    return arrCrear,arrActualizar,arrEliminar