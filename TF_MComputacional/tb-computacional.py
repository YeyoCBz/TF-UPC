import streamlit as st
import random
import math
import networkx as nx
from pyvis.network import Network
import tempfile
import json

# Configuración de la página
st.set_page_config(page_title="Algoritmo de Dijkstra", layout="wide")

class AlgorithmDijkstra:
    def __init__(self, graph_dict):
        self.graph = graph_dict
        self.nodes = list(graph_dict.keys())

    def reconstruct_paths(self, current_node, start_node, predecessors):
        if current_node == start_node:
            return [[start_node]]

        paths_from_start = []
        for pred in predecessors[current_node]:
            for path in self.reconstruct_paths(pred, start_node, predecessors):
                paths_from_start.append(path + [current_node])

        return paths_from_start

    def find_short_path(self, start_node, end_node):
        distances = {node: float('inf') for node in self.graph}
        predecessors = {node: [] for node in self.graph}
        distances[start_node] = 0
        labeled_nodes = set()
        current_node = None
        min_distance = None
        while len(labeled_nodes) < len(self.graph):
            current_node = None
            min_distance = float('inf')
            for node in self.graph:
                if node not in labeled_nodes and distances[node] < min_distance:
                    min_distance = distances[node]
                    current_node = node
            if current_node is None:
                return None
            labeled_nodes.add(current_node)
            for neighbor, weight in self.graph[current_node].items():
                if neighbor not in labeled_nodes:
                    new_distance = distances[current_node] + weight
                    if new_distance < distances[neighbor]:
                        distances[neighbor] = new_distance
                        predecessors[neighbor] = [current_node]
                    elif new_distance == distances[neighbor]:
                        predecessors[neighbor].append(current_node)
        if distances[end_node] == float('inf'):
            return None
        all_shortest_paths = self.reconstruct_paths(current_node, start_node, predecessors)
        return all_shortest_paths, min_distance

def initial_environment_variables():
    # Inicializar variables de sesión para mantener estado
    if 'graph_dict' not in st.session_state:
        st.session_state.graph_dict = None
    if 'is_graph_generated' not in st.session_state:
        st.session_state.is_graph_generated = False

def generate_random_graph(n):
    graph_dict = {}
    nodes = [chr(65 + i) for i in range(n)]

    for node in nodes:
        graph_dict[node] = {}

    for i in range(n - 1):
        weight = random.randint(1, 20)
        graph_dict[nodes[i]][nodes[i + 1]] = weight

    additional_edges = random.randint(n, 2 * n)
    for _ in range(additional_edges):
        u = random.choice(nodes)
        v = random.choice(nodes)
        if u != v and v not in graph_dict[u]:
            weight = random.randint(1, 20)
            graph_dict[u][v] = weight

    return graph_dict

def pyvis_configuration():
    return """
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

def show_highlight_paths(highlight_paths, graph_dict, net):
    for u, neighbors in graph_dict.items():
        for v, weight in neighbors.items():
            net.add_edge(u, v,
                         value=weight,
                         title=f"Valor: {weight}",
                         label=str(weight),
                         color="#2B7CE9",
                         width=2)

    if highlight_paths:
        colors = ['#F00', '#0F0', '#F0F', '#FF0', '#808']

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

def create_pyvis_network(graph_dict, highlight_paths=None, start_node=None, end_node=None):
    # Crear red pyvis
    net = Network(height="1000px", width="100%", bgcolor="#0E1117", font_color="black")

    # Configuración para hacerlo interactivo pero SIN física (nodos se quedan donde los pones)
    net.set_options(pyvis_configuration())

    # Generar nuevas posiciones usando NetworkX
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


    # Resaltar caminos mínimos si existen
    net = show_highlight_paths(highlight_paths, graph_dict, net)

    return net

def load_file_json(uploaded_files):
    try:
        return json.loads(uploaded_files.getvalue())
    except Exception as e:
        st.error(f"Error: {e}")
    return None

def show_min_path(min_distance, all_short_paths, start_node, end_node):
    st.markdown("---")
    if min_distance == math.inf:
        st.error(f"No existe camino entre {start_node} y {end_node}")
    else:
        st.success(f"**Distancia mínima:** {min_distance}")
        st.subheader("Ruta")
        for i, path in enumerate(all_short_paths, 1):
            path_str = " :arrow_right: ".join(path)
            st.write(f"**Camino {i}:** {path_str} (Longitud: {min_distance})")

def steps_details_dijkstra():
    # Mostrar pasos detallados
    st.markdown("---")
    # st.subheader("Pasos Detallados del Algoritmo")
    # print("Pasos Detallados del Algoritmo en proceso")
    # Se desarolllará en futuras actualizaciones

def show_graph(all_short_paths, is_dijkstra_executed, start_node, end_node):
    net_initial = create_pyvis_network(
        st.session_state.graph_dict,
        highlight_paths=all_short_paths if is_dijkstra_executed else None,
        start_node=start_node,
        end_node=end_node
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
        net_initial.save_graph(tmp_file.name)
        with open(tmp_file.name, 'r', encoding='utf-8') as f:
            html_content = f.read()

    st.components.v1.html(html_content, height=1000)

def set_start_end_nodes(creation_type, nodes_count):
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

    if start_node == end_node:
        st.warning(f"Los nodos origen y destino son iguales")

    if creation_type == "Manual":
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 3])

        with col1:
            st.subheader("Añade una conexión")
            u = st.selectbox("Nodo origen", [chr(65 + i) for i in range(nodes_count)])
        with col2:
            st.subheader("")
            available_nodes = [chr(65 + i) for i in range(nodes_count) if chr(65 + i) != u]
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
            uploaded_files = st.file_uploader("Subir archivo", type="json")

            if uploaded_files:
                st.session_state.graph_dict = load_file_json(uploaded_files)

    return start_node, end_node

def btn_generate_graph_execute_algorithm(creation_type, nodes_count):
    is_dijkstra_executed = False
    btn1, btn2, _ = st.columns([1, 1, 2])

    if btn1.button("Crear Grafo", width="stretch", type="primary", icon=":material/network_node:"):
        st.session_state.is_graph_generated = True
        if creation_type == "Aleatorio":
            st.session_state.graph_dict = generate_random_graph(nodes_count)
        else:
            st.session_state.graph_dict = {chr(65 + i): {} for i in range(nodes_count)}

    if btn2.button("Ejecutar Dijkstra", width="stretch", icon=":material/play_circle:",
                   disabled=(not st.session_state.is_graph_generated)):
        is_dijkstra_executed = True

    return is_dijkstra_executed

def build_sidebar():
    with st.sidebar:
        st.header("Configuración del Grafo")
        nodes_count = st.slider("Número de nodos", min_value=8, max_value=16, value=8)

        creation_type = st.radio(
            "Tipo de creación:",
            ["Aleatorio", "Manual"]
        )
        # Información sobre cómo usar
        st.subheader("Leyenda", divider=True)

        st.badge("Nodo origen", color="green", icon=":material/radio_button_checked:")
        st.badge("Nodo destino", color="red", icon=":material/radio_button_checked:")
        
    return nodes_count, creation_type

def main():
    initial_environment_variables()

    st.title("Algoritmo de Dijkstra")
    st.markdown("---")

    # Sidebar
    nodes_count, creation_type = build_sidebar()

    # btn Generar grafos y ejecutar algoritmo
    is_dijkstra_executed = btn_generate_graph_execute_algorithm(creation_type, nodes_count)

    if st.session_state.is_graph_generated and st.session_state.graph_dict:
        all_short_paths = None
        start_node, end_node = set_start_end_nodes(creation_type, nodes_count)

        if is_dijkstra_executed:
            # Encontrar camino mas corto
            dijkstra = AlgorithmDijkstra(st.session_state.graph_dict)
            all_short_paths, min_distance = dijkstra.find_short_path(start_node, end_node)

            # Ruta del camino corto y detalles para encontar el camino
            show_min_path(min_distance, all_short_paths, start_node, end_node)
            steps_details_dijkstra()

        show_graph(all_short_paths, is_dijkstra_executed, start_node, end_node)

if __name__ == "__main__":
    main()