import pinecone
from langchain_core.documents import Document
def asegurarNamespace(index, namespace):
    try:
        # Intenta insertar un vector dummy para crear el namespace si no existe
        dummy_id = "dummy_vector_id"
        dummy_vector = [0.1] * 3072  # Vector dummy con 10 dimensiones de ejemplo
        index.upsert(vectors=[(dummy_id, dummy_vector)], namespace=namespace)
        print(f"Namespace '{namespace}' asegurado.")
    except Exception as e:
        print(f"Error al asegurar el namespace '{namespace}': {e}")
def obtenerIndexTodosCursos():
    api_key = "78e19e89-ca6f-4057-bc03-0c0ff6330e61"
    pc = pinecone.Pinecone(api_key=api_key)
    index_name = "todos-cursos"
    index = pc.Index(index_name)
    asegurarNamespace(index,"cursos")
    return index

def existeNamespace(codigoCRM, index):
    try:
        # Intentar obtener un vector de un ID específico en el namespace
        response = index.fetch(ids=[codigoCRM], namespace="cursos")
        # Verificar si el response contiene vectores
        if response["vectors"]:
            return True
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
def hayCambiosEnNamespace(curso, index):
    # Verifica si hay cambios en la metadata "infoCrudaPDF" o "infoCrudaWEB" y la fecha de inicio
    try:
        response = index.fetch(ids=[curso["codigoCRM"]], namespace="cursos")
        if response.get("vectors"):
            vector_metadata = list(response["vectors"].values())[0].get("metadata", {})
            if len(curso["infoCrudaPDF"]) != vector_metadata.get("infoCrudaPDF", "") or \
                len(curso["infoCrudaWEB"]) != vector_metadata.get("infoCrudaWEB", "") or \
                curso["Fecha inicio"] != vector_metadata.get("Fecha inicio", ""):
                    return True
        return False
    except Exception as e:
        return False
def ObtenerTodosLosCodigosCRMPinecone(index,namespace="cursos"):
    try:
        query_vector = [0.0] * 3072  # Vector de consulta dummy con dimensiones que coinciden con tus vectores
        response = index.query(
        vector=query_vector,  # Usamos el argumento con nombre 'vector'
        namespace=namespace,  # Especificamos el namespace
        top_k=300,            # Número de resultados deseados
        include_values=False  # No necesitamos los valores de los vectores, solo los IDs
        )
        ids = [match['id'] for match in response.get('matches', [])]
        ids = [id for id in ids if id not in ["dummy_vector_id"]]
        return ids
    except Exception as e:
        print(f"Error: {e}")
        return []

def EncontrarNamespacesAEliminar(todosProgramasActuales, codigosCrmPinecone):
    # Compara los dos arreglos y devuelve los códigos que no están en todosProgramasActuales
    return [codigo for codigo in codigosCrmPinecone if codigo not in todosProgramasActuales]


def obtenerArreglosParaActualizarPinecone(cursos):
    index=obtenerIndexTodosCursos()
    crearNamespace=[]
    actualizarNamespace=[]
    todosProgramasActuales=[]
    eliminarNamespace=[]
    for curso in cursos:
        if existeNamespace(curso["codigoCRM"],index)==False: #Si no existe se debera crear
            crearNamespace.append(curso)
        elif hayCambiosEnNamespace(curso,index)==True: #Si existe y hay cambios en la info cruda, se debe actualizar
            actualizarNamespace.append(curso)
        else: #Si no existe y no hay cambios no se debe hacer nada.
            pass
        todosProgramasActuales.append(curso["codigoCRM"])
        codigosCrmPinecone=ObtenerTodosLosCodigosCRMPinecone(index)
        eliminarNamespace=EncontrarNamespacesAEliminar(todosProgramasActuales,codigosCrmPinecone)
    return crearNamespace,actualizarNamespace,eliminarNamespace