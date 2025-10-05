import streamlit as st
import random
import math
import networkx as nx
from pyvis.network import Network
import tempfile
import json
import re

# Configuración de la página
st.set_page_config(page_title="Algoritmo de Dijkstra", layout="wide")


class DijkstraManual:
    def __init__(self, graph_dict):
        """
        graph_dict: diccionario donde las claves son nodos y los valores son
                   diccionarios de vecinos con pesos {vecino: peso}
        """
        self.graph = graph_dict
        self.nodes = list(graph_dict.keys())

    def find_shortest_paths(self, start, end):
        # Inicializar estructuras
        distances = {node: math.inf for node in self.nodes}
        previous = {node: [] for node in self.nodes}
        visited = {node: False for node in self.nodes}
        distances[start] = 0

        steps = []

        # Algoritmo de Dijkstra
        for _ in range(len(self.nodes)):
            # Encontrar nodo no visitado con menor distancia
            min_distance = math.inf
            current_node = None

            for node in self.nodes:
                if not visited[node] and distances[node] < min_distance:
                    min_distance = distances[node]
                    current_node = node

            if current_node is None:
                break

            # Marcar como visitado
            visited[current_node] = True

            # Guardar información del paso actual
            step_info = {
                'current_node': current_node,
                'distances': distances.copy(),
                'visited': {k: v for k, v in visited.items()},
                'previous': {k: v.copy() for k, v in previous.items()}
            }
            steps.append(step_info)

            # Actualizar distancias de vecinos
            for neighbor, weight in self.graph[current_node].items():
                if not visited[neighbor]:
                    new_distance = distances[current_node] + weight

                    if new_distance < distances[neighbor]:
                        distances[neighbor] = new_distance
                        previous[neighbor] = [current_node]
                    elif new_distance == distances[neighbor]:
                        previous[neighbor].append(current_node)

            if current_node == end:
                break

        return steps, distances, previous


def find_all_paths(previous, start, end):
    """Encuentra todos los caminos mínimos usando backtracking - VERSIÓN CORREGIDA"""

    def backtrack(node):
        if node == start:
            return [[start]]

        paths = []
        for prev_node in previous[node]:
            partial_paths = backtrack(prev_node)
            for path in partial_paths:
                paths.append(path + [node])

        return paths

    all_paths = backtrack(end)
    return all_paths


def generate_random_graph(n):
    """Genera un grafo aleatorio con n nodos"""
    graph_dict = {}

    # Crear nodos
    nodes = [chr(65 + i) for i in range(n)]

    # Inicializar grafo
    for node in nodes:
        graph_dict[node] = {}

    # Asegurar que el grafo sea conexo
    for i in range(n - 1):
        weight = random.randint(1, 20)
        graph_dict[nodes[i]][nodes[i + 1]] = weight

    # Agregar aristas adicionales aleatorias
    additional_edges = random.randint(n, 2 * n)
    for _ in range(additional_edges):
        u = random.choice(nodes)
        v = random.choice(nodes)
        if u != v and v not in graph_dict[u]:
            weight = random.randint(1, 20)
            graph_dict[u][v] = weight

    return graph_dict

def create_pyvis_network(graph_dict, highlight_paths=None, start_node=None, end_node=None):
    # Crear red pyvis
    net = Network(height="1000px", width="100%", bgcolor="#0E1117", font_color="black")

    # Configuración para hacerlo interactivo pero SIN física (nodos se quedan donde los pones)
    options = """
    {
      "physics": {
        "enabled": false
      },
      "interaction": {
        "dragNodes": true,
        "dragView": true,
        "zoomView": true,
        "keyboard": {
          "enabled": true,
          "speed": {"x": 10, "y": 10, "zoom": 0.02}
        }
      },
      "nodes": {
        "font": { "size": 40 },
        "scaling": {"min": 20, "max": 60},
        "size": 50
      },
      "edges": {
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 1,
            "type": "arrow"
          }
        },
        "font": {
          "size": 30,
          "align": "top"
        },
        "smooth": {
          "enabled": false
        },
        "width": 2,
        "scaling": {
          "min": 4,
          "max": 4,
          "label": {
            "enabled": false
          }
        },
        "color": {
          "color": "#2B7CE9",
          "highlight": "#FFA500",
          "hover": "#FFA500"
        }
      },
      "layout": {
        "improvedLayout": true,
        "hierarchical": {
          "enabled": false
        }
      }
    }
    """

    net.set_options(options)

    # Generar nuevas posiciones usando NetworkX
    print("------NUEVOOOOO------------")
    G_nx = nx.DiGraph()

    # Agregar todos los nodos primero (incluso si no tienen aristas)
    for node in graph_dict.keys():
        G_nx.add_node(node)

    # Agregar aristas
    for u, neighbors in graph_dict.items():
        for v, weight in neighbors.items():
            G_nx.add_edge(u, v, weight=weight)

    # Usar spring layout para posiciones iniciales
    pos_nx = nx.spring_layout(G_nx, seed=42, k=3, iterations=100)

    # Convertir a formato pyvis (escalar)
    pos = {}
    for node, (x, y) in pos_nx.items():
        pos[node] = {"x": x * 1000, "y": y * 1000}


    # Agregar nodos con posiciones
    for node in graph_dict.keys():
        color = "#97c2fc"  # Color por defecto (azul claro)
        size = 25

        # Resaltar nodo origen y destino
        if node == start_node:
            color = "#4CAF50"  # Verde
            size = 50
        elif node == end_node:
            color = "#FF6B6B"  # Rojo
            size = 50

        # Usar posición guardada o generada
        node_pos = pos.get(node, {"x": 0, "y": 0})

        net.add_node(node,
                     label=node,
                     color=color,
                     size=size,
                     shape="ellipse",
                     x=node_pos["x"],
                     y=node_pos["y"])

    # Agregar aristas normales primero
    for u, neighbors in graph_dict.items():
        for v, weight in neighbors.items():
            net.add_edge(u, v,
                         value=weight,
                         title=f"Valor: {weight}",
                         label=str(weight),
                         color="#2B7CE9",
                         width=2)

    # Resaltar caminos mínimos si existen
    if highlight_paths:
        colors = ['#FF0000', '#00AA00', '#FF00FF', '#FFA500', '#800080']

        for i, path in enumerate(highlight_paths):
            color = colors[i % len(colors)]
            for j in range(len(path) - 1):
                u, v = path[j], path[j + 1]
                weight = graph_dict[u][v]

                for edge in net.edges:
                    if (edge['from'] == u and edge['to'] == v) or (edge['from'] == v and edge['to'] == u):
                        edge['color'] = color
                        edge['width'] = 4
                        edge['title'] = f"Camino {i + 1} - Valor: {weight}"
                        break

    return net


def load_file_json(uploaded_files):
    try:
        return json.loads(uploaded_files.getvalue())
    except Exception as e:
        st.error(f"Error: {e}")
    return None


def show_min_path(min_distance, start_node, end_node, all_paths):
    # Mostrar resultados
    st.markdown("---")

    # Distancia mínima
    if min_distance == math.inf:
        st.error(f"No existe camino entre {start_node} y {end_node}")
    else:
        st.success(f"**Distancia mínima:** {min_distance}")
        st.subheader("Ruta")
        for i, path in enumerate(all_paths, 1):
            path_str = " → ".join(path)
            st.write(f"**Camino {i}:** {path_str} (Longitud: {min_distance})")

def steps_details_dijkstra():
    # Mostrar pasos detallados
    st.markdown("---")
    st.subheader("Pasos Detallados del Algoritmo")
    # print("Pasos Detallados del Algoritmo en proceso")
    # Se desarolllará en futuras actualizaciones


def main():
    st.title("Algoritmo de Dijkstra")
    st.markdown("---")

    # Sidebar para configuración
    with st.sidebar:
        st.header("Configuración del Grafo")
        n = st.slider("Número de nodos", min_value=8, max_value=16, value=8)

        generation_type = st.radio(
            "Tipo de generación del grafo:",
            ["Aleatorio", "Manual"]
        )
        # Información sobre cómo usar
        st.subheader("Leyenda", divider=True)

        st.badge("Nodo origen", color="green", icon=":material/radio_button_checked:")
        st.badge("Nodo destino", color="red", icon=":material/radio_button_checked:")

    # Inicializar variables de sesión para mantener estado
    if 'graph_dict' not in st.session_state:
        st.session_state.graph_dict = None
    if 'generate_graph' not in st.session_state:
        st.session_state.generate_graph = False
    if 'graph_generated' not in st.session_state:
        st.session_state.graph_generated = False

    # Mostrar interfaz para grafo manual
    if generation_type == "Manual":
        # Inicializar grafo vacío si no existe
        if st.session_state.graph_dict is None:
            st.session_state.graph_dict = {chr(65 + i): {} for i in range(n)}

        col1, col2, col3, col4, col5= st.columns([2,2,2,1,3])
        with col1:
            st.subheader("Añade una conexión")
            u = st.selectbox("Nodo origen", [chr(65 + i) for i in range(n)])
        with col2:
            st.subheader("")
            available_nodes = [chr(65 + i) for i in range(n) if chr(65 + i) != u]
            v = st.selectbox("Nodo destino", available_nodes)
        with col3:
            st.subheader("")
            weight = st.number_input("valor", min_value=1, max_value=100, value=5)
        with col4:
            st.subheader("")
            st.write("")
            if st.button("", icon=":material/add:"):
                st.session_state.graph_dict[u][v] = weight
        with col5:
            st.subheader("Carga tu grafo")
            uploaded_files = st.file_uploader("Subir Archivo", type="json")

            if uploaded_files:
                st.session_state.graph_dict = load_file_json(uploaded_files)



    is_dijkstra_executed = False

    btn1, btn2, _ = st.columns([1,1,2])

    # Botón para generar/crear grafo
    if btn1.button("Generar/Crear Grafo", width="stretch", type="primary", icon=":material/network_node:"):
        if generation_type == "Aleatorio":
            st.session_state.graph_dict = generate_random_graph(n)

        st.session_state.graph_generated = True

    if btn2.button("Ejecutar Dijkstra", disabled=(not st.session_state.graph_generated), width="stretch",
                   icon=":material/play_circle:"):
        is_dijkstra_executed = True

    # Solo mostrar la interfaz si el grafo fue generado
    if st.session_state.graph_generated and st.session_state.graph_dict:
        # Selección de nodos para Dijkstra
        all_paths = None
        min_distance = None

        col1, col2 = st.columns(2)
        with col1:
            start_node = st.selectbox(
                "Nodo origen",
                list(st.session_state.graph_dict.keys()),
                key="start_node"
            )
        with col2:
            end_node = st.selectbox(
                "Nodo destino",
                list(st.session_state.graph_dict.keys()),
                len(list(st.session_state.graph_dict.keys())) - 1,
                key="end_node"
            )

        # Crear grafo interactivo
        if start_node == end_node:
            st.warning(f"Los nodos origen y destino son iguales")

        if is_dijkstra_executed:
            # Crear instancia del algoritmo manual
            dijkstra = DijkstraManual(st.session_state.graph_dict)

            # Ejecutar algoritmo
            steps, distances, previous = dijkstra.find_shortest_paths(start_node, end_node)
            # Distancia mínima
            min_distance = distances[end_node]
            if min_distance != math.inf:
                all_paths = find_all_paths(previous, start_node, end_node)


        net_initial = create_pyvis_network(
            st.session_state.graph_dict,
            highlight_paths=all_paths if is_dijkstra_executed else None,
            start_node=start_node,
            end_node=end_node
        )

        # Guardar y mostrar el grafo
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
            net_initial.save_graph(tmp_file.name)
            with open(tmp_file.name, 'r', encoding='utf-8') as f:
                html_content = f.read()

        st.components.v1.html(html_content, height=1000)

        if is_dijkstra_executed:
            with st.spinner("Ejecutando algoritmo de Dijkstra..."):
                show_min_path(min_distance, start_node, end_node, all_paths)
                steps_details_dijkstra()


if __name__ == "__main__":
    main()