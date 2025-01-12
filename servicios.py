from bs4 import BeautifulSoup
import requests
import json
# Función para obtener cursos
def ActualizarCursosScrapeados():
    url = "https://fcz3yiiezk.execute-api.us-east-1.amazonaws.com/Centrum/Chatbot/ActualizarCursosScrapeados"
    headers = {
        "authorizationToken": "allow"
    }
    response = requests.post(url, headers=headers)
    return response.json()


# Función para obtener cursos
def ObtenerCursosScrapeados():
    url = "https://fcz3yiiezk.execute-api.us-east-1.amazonaws.com/Centrum/Chatbot/ObtenerCursosYLinksPorCategoria"
    headers = {
        "authorizationToken": "allow"
    }
    data = {
        "Categoria": "Otros"
    }
    response = requests.post(url, headers=headers, json=data)
    curso_link = json.loads(response.json()["body"])["Cursos"]
    return curso_link
def ScrapearInfoLinksHijos(link):
    url = "https://fcz3yiiezk.execute-api.us-east-1.amazonaws.com/Centrum/Chatbot/ScrapearInfoLinksHijos"
    headers = {
        "authorizationToken": "allow"
    }
    data = {
        "link": link
    }
    response = requests.post(url, headers=headers, json=data)
    return json.loads(response.json()["body"])

def obtenerInfoProgramaCRM(codigoCRM):
    url = "https://cang.fa.us2.oraclecloud.com:443/crmRestApi/resources/11.13.18.05/catalogProductGroups"
    params = {
            "q":"ProductGroupId=" + codigoCRM,#Columna del excel : Número de producto
            'fields': 'CTRComponenteInternacional_c,RangoDeEdad_c,CTRFechadeinicio_c,CTRPrecioLista_c,CTRMoneda_c',
            'onlyData': 'true',
        }
    headers = {
            'Authorization': 'Basic QUNUVUFMSVpBREFUT1M6UXNsdGExMjM=',
            'Content-Type': 'application/json'
    }
    response = requests.get(url, params=params, headers=headers)
    print(response)
    print(response.json())
    if response.json()["items"]:
        temp=response.json()["items"][0]
        if temp["CTRMoneda_c"]=="PEN":
            temp["Precio de lista"]= str(temp["CTRPrecioLista_c"]) +" soles."
        if temp["CTRMoneda_c"]=="USD":
            temp["Precio de lista"]= str(temp["CTRPrecioLista_c"]) +" dolares."
        temp["Días y horario de dictado"]=""
        temp["Modalidad"]=""
        temp["Duración del programa"]=""
        temp["Lugar de dictado"]=""
        del temp["CTRPrecioLista_c"]
        del temp["CTRMoneda_c"]
        print(temp)
        return temp
    else:
        temp={}
        temp["CTRComponenteInternacional_c"]= ""
        temp["CTRFechadeinicio_c"]= ""
        temp["CTRComponenteInternacional_c"]= ""
        temp["CTRComponenteInternacional_c"]= ""
        temp["Precio de lista"]= ""
        temp["Días y horario de dictado"]=""
        temp["Modalidad"]=""
        temp["Duración del programa"]=""
        temp["Lugar de dictado"]=""
        return temp


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

def ScrapearInformacionCursosCategoria(url):
    """Realiza el scraping de información de cursos desde la URL proporcionada."""
    cursos = []
    try:
        # Realizar la solicitud HTTP para obtener el contenido de la página
        response = requests.get(url)
        response.raise_for_status()  # Lanza un error si la solicitud falla
        # Parsear el contenido HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        # Encontrar todos los div con la clase específica
        divs = soup.find_all('div', class_='quater_content_item_data_info')
        divs2 = soup.find_all('div', class_='quater_content_item_data_fecha')
        # Recorrer cada div y extraer la información
        for div, div2 in zip(divs, divs2):
            curso = {}
            # Obtener el título h4
            title = div.find('h4').text.strip() if div.find('h4') else 'No title found'
            title = reemplazar_tildes(title)
            # Obtener el enlace del botón
            button = div.find('a', class_='button-normal m--mini m--gris')
            link_href = button['href'] if button else 'No link found'
            # Extraer la información del mes usando BeautifulSoup
            mes_element = div2.find('p', class_='quater__mes')
            mes_text = mes_element.text.strip() if mes_element else 'No month found'
            curso["title"] = title
            curso["link_href"] = link_href
            curso["mes"]=mes_text
            cursos.append(curso)
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar el scraping: {e}")
    return cursos