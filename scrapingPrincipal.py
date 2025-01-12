import json
import fitz
import requests
from bs4 import BeautifulSoup
import re
from servicios import obtenerInfoProgramaCRM,ScrapearInfoLinksHijos,ScrapearInformacionCursosCategoria
def obtenerLinksDelLinkHijo(url):
    urls = []
    urls.append({"El curso": url})
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        elements = soup.find_all(class_='submenu-enlaces__item')
        for element in elements:
            link = element.find('a')
            if link:
                text = link.get_text().strip()
                href = link['href']

                if href and href.startswith(('http://', 'https://')) and "Inscríbete" not in text:
                    urls.append({text: href})
    else:
        print(f"Error al realizar la solicitud: {response.status_code}")
    return urls
def obtenerInformacion(url):
    # Hacer una solicitud GET a la URL
    informacion=""
    response = requests.get(url)
    # Asegurarse de que la solicitud fue exitosa
    if response.status_code == 200:
        # Parsear el contenido HTML con BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        # Lista de etiquetas HTML a eliminar
        etiquetas_a_eliminar = ['form','head']
        clases_a_eliminar = ["limit header__main","limit footer_bottom__container","jh-banner__breadcrumb","header__title"]
        # Eliminar elementos por etiqueta
        for etiqueta in etiquetas_a_eliminar:
            elementos = soup.find_all(etiqueta)
            for elemento in elementos:
                elemento.decompose()
        for clase in clases_a_eliminar:
            elementos = soup.find_all(class_=clase)
            for elemento in elementos:
                elemento.decompose()
        # Extraer todo el texto después de eliminar los elementos
        text = soup.get_text(separator='\n', strip=True)
        informacion+=text
        # Imprimir el texto
        # Encontrar el <figcaption> con la clase específica
        figcaption = soup.find('figcaption', class_='footer_faq-center section')
        if figcaption:
            # Encontrar el enlace <a> dentro del <figcaption>
            link = figcaption.find('a')
            if link:
                # Extraer la URL del enlace
                href = link.get('href')
                informacion+=href
            else:
                print("No se encontró el enlace en el <figcaption>")
        else:
            print("No se encontró el <figcaption> con la clase especificada")
    else:
        print(f"Error al acceder a la página. Código de estado: {response.status_code}")
    return informacion
def ScrapearInfoCurso(link):
    links = obtenerLinksDelLinkHijo(link)
    texto_largo=""
    for link in links:
        for key, value in link.items():
            texto_largo+= "Descripcion de Fuente de Datos:" + key  + "\n"
            texto_largo+="Link de Fuente de Datos:"+value + "\n"
            texto_largo+="Informacion\n" + obtenerInformacion(value) + "\n"
    # Dividir el texto en frases usando saltos de línea
    frases = texto_largo.split('\n')
    # Usar un conjunto para rastrear frases vistas y una lista para mantener el orden
    vistas = set()
    frases_unicas = []
    for frase in frases:
        if frase not in vistas:
            vistas.add(frase)
            frases_unicas.append(frase)
    # Volver a unir las frases únicas en un solo texto con saltos de línea
    texto_sin_repetidos = '\n'.join(frases_unicas)
    # Mostrar el resultado
    return texto_sin_repetidos
def buscarPDF(link):
    response = requests.get(link)
    soup = BeautifulSoup(response.content, 'html.parser')
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Verificar que el enlace termine en .pdf y no contenga la palabra "normativa"
        if href.endswith('.pdf') and 'normativa' not in href.lower():
            return href
    return None

def leerPDF(linkpdf):
    respuesta = requests.get(linkpdf)
    doc = fitz.open(stream=respuesta.content, filetype="pdf")
    extracted_text = ""
    for page in doc:
        extracted_text += page.get_text()
    doc.close()
    return extracted_text

def BuscarLeerPdf(link):
    links = obtenerLinksDelLinkHijo(link)
    texto_largo=""
    for link in links:
        for key, link in link.items():
            linkpdf=buscarPDF(link)
            if linkpdf:
                return leerPDF(linkpdf)
    return ""
def mapeo(Titulo,results,infoCruda_pdf,inforHijoCruda_web,info):
    if(len(results[0])>2):
        results=results[0]
    return {
        "Titulo": Titulo,
        "codigoCRM": results,
        "infoCrudaPDF": infoCruda_pdf,
        "infoCrudaWEB": inforHijoCruda_web,
        "Precio de lista": info.get('Precio de lista', 'No disponible'),
        "Edad mínima": info.get("RangoDeEdad_c", 'No disponible'),
        "Fecha inicio": info.get("CTRFechadeinicio_c", 'No disponible'),
        "Modalidad": info.get("Modalidad", 'No disponible'),
        "Componente internacional": info.get("CTRComponenteInternacional_c", 'No disponible'),
        "Días y horario de dictado": info.get("Dias y horario de dictado", 'No disponible'),
        "Duración del programa": info.get("Duracion del programa", 'No disponible'),
        "Lugar de dictado": info.get("Lugar de dictado", 'No disponible')
    }
def obtenerPDFsArreglo(link):
    response = requests.get(link)
    soup = BeautifulSoup(response.content, 'html.parser')
    pdf_links = []

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Verificar que el enlace termine en .pdf y no contenga la palabra "normativa"
        if href.endswith('.pdf') and 'normativa' not in href.lower():
            pdf_links.append(href)
    return pdf_links

def obtnerLinksCursosEdex(url):
    urls = []
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        elements = soup.find_all(class_='submenu-enlaces__item')

        for element in elements:
            link = element.find('a')
            if not link:
                link = element.find('span')
            if link:
                text = link.get_text().strip()
                href = link['href']
                if "Cursos" in text:
                    urls.append({text: href})
    else:
        print(f"Error al realizar la solicitud: {response.status_code}")
    return urls
def scrapingPrincipal(Titulo,link):
    cursos=[]
    curso={}
    if "edex" not in link and "centrumx" not in link and link:
        result = re.sub(r'/cursos-[^/]+/?$', '', link)
        response_detalle = requests.get(result+"#showform")
        response_detalle.raise_for_status()
        soup_detalle = BeautifulSoup(response_detalle.text, 'html.parser')
        inforHijoCruda_web = ScrapearInfoLinksHijos(link)
        codigos = soup_detalle.select('select[name="programa"] option[value]')
        codigos += soup_detalle.select('input[type="hidden"][name="programa"]')
        pattern_input = re.compile(r'value="(\d+)"')
        pattern_option = re.compile(r'value="(\d+)#([^"]+)"')
        inputs = pattern_input.findall(str(codigos))
        options = pattern_option.findall(str(codigos))
        results = []
        results.extend(inputs)
        results.extend([f"{code}#{name}" for code, name in options])
        if inputs:
            infoCruda_pdf=BuscarLeerPdf(link)
            codigoCRM=results[0]
            info=obtenerInfoProgramaCRM(codigoCRM)
            curso=mapeo(Titulo,results,infoCruda_pdf,inforHijoCruda_web,info)
            cursos.append(curso)
            return cursos
        else:
            print("Curso atipico")
            inforHijoCruda_web = ScrapearInfoLinksHijos(link)
            if codigos:
                infoCruda_pdf = BuscarLeerPdf(link)
                diccionario = {item.split('#')[0]: item.split('#')[1] for item in results}
                for codigo, value in diccionario.items():
                    print(codigo)
                    print(value)
                    info = obtenerInfoProgramaCRM(codigo)
                    curso_leido = mapeo(Titulo+str(value), str(codigo), infoCruda_pdf, "Curso:" + Titulo+str(value)+ "|" +inforHijoCruda_web, info)
                    print(curso_leido)
                    cursos.append(curso_leido)
                return cursos
            else:
                cursos=[]
                print("No se pudo procesar el link:",link)
                cursos_links=ScrapearInformacionCursosCategoria(link)
                for nieto in cursos_links:
                    link=nieto["link_href"]
                    result = re.sub(r'/cursos-[^/]+/?$', '', link)
                    response_detalle = requests.get(result+"#showform")
                    response_detalle.raise_for_status()
                    soup_detalle = BeautifulSoup(response_detalle.text, 'html.parser')
                    inforHijoCruda_web = ScrapearInfoLinksHijos(link)
                    codigos = soup_detalle.select('select[name="programa"] option[value]')
                    codigos += soup_detalle.select('input[type="hidden"][name="programa"]')
                    pattern_input = re.compile(r'value="(\d+)"')
                    pattern_option = re.compile(r'value="(\d+)#([^"]+)"')
                    inputs = pattern_input.findall(str(codigos))
                    options = pattern_option.findall(str(codigos))
                    results = []
                    results.extend(inputs)
                    results.extend([f"{code}#{name}" for code, name in options])
                    if inputs:
                        infoCruda_pdf=BuscarLeerPdf(link)
                        codigoCRM=results[0]
                        info=obtenerInfoProgramaCRM(codigoCRM)
                        curso=mapeo(Titulo,results,infoCruda_pdf,inforHijoCruda_web,info)
                        cursos.append(curso)
                print(cursos)
                return cursos
    elif link:
        if "edex" in link:
            link=obtnerLinksCursosEdex(link)[0]["Cursos"]
            cursos =[]
            pdfs = obtenerPDFsArreglo(link)
            for pdf in pdfs:
                patternCodigoCRM = r'-(\d+)\.pdf'
                patternTitulo = r'/([\w-]+)-\d{15}\.pdf'
                if(re.search(patternCodigoCRM, pdf) and re.search(patternTitulo, pdf)):
                    codigoCRM = re.search(patternCodigoCRM, pdf).group(1)
                    Titulo = re.search(patternTitulo, pdf).group(1)
                else:
                    print("No se enontro codigo CRM en:",pdf)
                    continue
                info=obtenerInfoProgramaCRM(codigoCRM)
                infoCruda_pdf=BuscarLeerPdf(link)
                curso=mapeo(Titulo,codigoCRM,infoCruda_pdf,"",info)
                cursos.append(curso)
            return cursos
        if "centrumx" in link:
            #Proocesar en una funcion ProcesarCentrumX()
            #Aun no se tiene los datos ncesarios para poder realizar este scraping
            pass
def obtenerInformacion(url):
    # Hacer una solicitud GET a la URL
    informacion = ""
    response = requests.get(url)

    # Asegurarse de que la solicitud fue exitosa
    if response.status_code == 200:
        # Parsear el contenido HTML con BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Lista de etiquetas HTML a eliminar
        etiquetas_a_eliminar = ['form', 'head']
        clases_a_eliminar = ["limit header__main", "limit footer_bottom__container", "jh-banner__breadcrumb", "header__title"]

        # Eliminar elementos por etiqueta
        for etiqueta in etiquetas_a_eliminar:
            elementos = soup.find_all(etiqueta)
            for elemento in elementos:
                elemento.decompose()

        # Eliminar elementos por clase
        for clase in clases_a_eliminar:
            elementos = soup.find_all(class_=clase)
            for elemento in elementos:
                elemento.decompose()

        # Extraer todo el texto después de eliminar los elementos
        text = soup.get_text(separator='\n', strip=True)

        # Crear un diccionario para almacenar los enlaces encontrados
        enlaces = {}

        # Buscar todos los enlaces en el HTML
        for enlace in soup.find_all('a', href=True):
            texto_enlace = enlace.get_text(strip=True)
            href = enlace['href']
            if texto_enlace:  # Solo añadir si el texto del enlace no está vacío
                enlaces[texto_enlace] = href

        # Reemplazar referencias de enlaces en el texto
        for texto_enlace, href in enlaces.items():
            text = text.replace(texto_enlace, f"{texto_enlace} ({href})")

        # Agregar el texto procesado a la variable de información
        informacion += text

        # Encontrar el <figcaption> con la clase específica
        figcaption = soup.find('figcaption', class_='footer_faq-center section')
        if figcaption:
            # Encontrar el enlace <a> dentro del <figcaption>
            link = figcaption.find('a')
            if link:
                # Extraer la URL del enlace
                href = link.get('href')
                informacion += f"\n{href}"
            else:
                print("No se encontró el enlace en el <figcaption>")
        else:
            print("No se encontró el <figcaption> con la clase especificada")
    else:
        print(f"Error al acceder a la página. Código de estado: {response.status_code}")

    return informacion
obtenerInformacion("https://centrum.pucp.edu.pe/programas/mba/mba-centrum/")