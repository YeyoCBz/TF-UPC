import streamlit as st
import random
import math
import networkx as nx
from pyvis.network import Network
import tempfile
import json

st.set_page_config(page_title="Algoritmo de Dijkstra", layout="wide")

class AlgorithmDijkstra:
    def __init__(self, graph_dict):
        self.graph = graph_dict
        self.nodes = list(graph_dict.keys())
        self.steps = []

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
        hop_depth = {node: float('inf') for node in self.graph}  # Profundidad en saltos
        distances[start_node] = 0
        hop_depth[start_node] = 0
        labeled_nodes = set()
        iteration = 1
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
            step_updates = []
            for neighbor, weight in self.graph[current_node].items():
                if neighbor not in labeled_nodes:
                    new_distance = distances[current_node] + weight
                    new_hop = hop_depth[current_node] + 1
                    if new_distance < distances[neighbor]:
                        distances[neighbor] = new_distance
                        hop_depth[neighbor] = new_hop
                        predecessors[neighbor] = [current_node]
                        step_updates.append({
                            "nodo": neighbor,
                            "desde": current_node,
                            "distancia": new_distance,
                            "iteracion_salto": new_hop
                        })
                    elif new_distance == distances[neighbor]:
                        predecessors[neighbor].append(current_node)
                        step_updates.append({
                            "nodo": neighbor,
                            "desde": current_node,
                            "distancia": new_distance,
                            "iteracion_salto": new_hop,
                            "empate": True
                        })
            self.steps.append({
                "iteracion": iteration,
                "seleccionado": current_node,
                "actualizaciones": step_updates
            })
            iteration += 1
        if distances[end_node] == float('inf'):
            return None
        all_shortest_paths = self.reconstruct_paths(end_node, start_node, predecessors)
        return all_shortest_paths, distances[end_node]

def initial_environment_variables():
    if 'graph_dict' not in st.session_state:
        st.session_state.graph_dict = None
    if 'is_graph_generated' not in st.session_state:
        st.session_state.is_graph_generated = False
    if 'dijkstra_steps' not in st.session_state:
        st.session_state.dijkstra_steps = []

def _manual_graph_complete(graph_dict, nodes_count):
    if not graph_dict:
        return False
    end_node = st.session_state.get('end_node')
    for i in range(nodes_count):
        node = chr(65 + i)
        if node == end_node:
            continue
        if node not in graph_dict or len(graph_dict[node]) == 0:
            return False
    return True

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
          "align": "top",
          "color": "#FFF"
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
                         color="#2CF",
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
    net = Network(height="1000px", width="100%", bgcolor="#0E1117", font_color="black")

    net.set_options(pyvis_configuration())

    G_nx = nx.DiGraph()

    for node in graph_dict.keys():
        G_nx.add_node(node)

    for u, neighbors in graph_dict.items():
        for v, weight in neighbors.items():
            G_nx.add_edge(u, v, weight=weight)

    pos_nx = nx.spring_layout(G_nx, seed=42, k=3, iterations=100)

    pos = {}
    for node, (x, y) in pos_nx.items():
        pos[node] = {"x": x * 1000, "y": y * 1000}

    for node in graph_dict.keys():
        color = "#9CF"
        size = 25

        if node == start_node:
            color = "#0F0"
            size = 50
        elif node == end_node:
            color = "#F00"
            size = 50

        node_pos = pos.get(node, {"x": 0, "y": 0})

        net.add_node(node,
                     label=node,
                     color=color,
                     size=size,
                     shape="ellipse",
                     x=node_pos["x"],
                     y=node_pos["y"])

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
    if not st.session_state.get('dijkstra_steps'):
        return
    st.subheader("Resumen de pasos (Dijkstra)")
    for step in st.session_state['dijkstra_steps']:
        st.write(f"Paso {step['iteracion']}: Nodo seleccionado {step['seleccionado']}")
        if step['actualizaciones']:
            for upd in step['actualizaciones']:
                etiqueta = f"[{upd['distancia']}, {upd['desde']}]`({upd['iteracion_salto']})`"
                if upd.get('empate'):
                    st.write(f"- Empate: {upd['nodo']} {etiqueta}")
                else:
                    st.write(f"- {upd['nodo']} {etiqueta}")

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
        is_edge_already_created = False
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
                if v in st.session_state.graph_dict.get( u, {}):
                    st.session_state.graph_dict[u][v] = weight
                else:
                    if u in st.session_state.graph_dict.get(v, {}):
                        is_edge_already_created = True
                    else:
                        st.session_state.graph_dict[u][v] = weight
        with col5:
            st.subheader("Carga tu grafo")
            uploaded_files = st.file_uploader("Subir archivo", type="json")

            if uploaded_files:
                json_graph = load_file_json(uploaded_files)
                if nodes_count == len(json_graph):
                    st.session_state.graph_dict = json_graph
                else:
                    st.warning(f"El json debe tener {nodes_count} nodos")

        if is_edge_already_created:
            col_warning, _ = st.columns([2, 1])
            with col_warning:
                st.warning(f"No se puede cambiar la dirección de la arista {v} -> {u}")


    return start_node, end_node

def btn_generate_graph_execute_algorithm(creation_type, nodes_count):
    is_dijkstra_executed = False
    btn1, btn2, btn3, btn4 = st.columns([1, 1, 1, 1])

    if btn1.button("Crear Grafo", width="stretch", type="primary", icon=":material/network_node:"):
        st.session_state.is_graph_generated = True
        if creation_type == "Aleatorio":
            st.session_state.graph_dict = generate_random_graph(nodes_count)
        else:
            st.session_state.graph_dict = {chr(65 + i): {} for i in range(nodes_count)}

    if btn2.button("Ejecutar Dijkstra", width="stretch", icon=":material/play_circle:",
                   disabled=(not st.session_state.is_graph_generated)):
        if creation_type == "Manual" and not _manual_graph_complete(st.session_state.graph_dict, nodes_count):
            st.warning("Completa las conexiones antes de ejecutar Dijkstra")
        else:
            is_dijkstra_executed = True

    if st.session_state.is_graph_generated and st.session_state.graph_dict:
        graph_json = json.dumps(st.session_state.graph_dict, indent=2)
        btn3.download_button(
            label="Descargar Grafo",
            data=graph_json,
            file_name="grafo.json",
            mime="application/json",
            icon=":material/download:",
            disabled=(not st.session_state.is_graph_generated)
        )

    if btn4.button("Reiniciar", width="stretch", icon=":material/restart_alt:"):
        st.session_state.graph_dict = None
        st.session_state.is_graph_generated = False
        st.session_state.dijkstra_steps = []

    return is_dijkstra_executed

def build_sidebar():
    with st.sidebar:
        st.header("Configuración del Grafo")
        nodes_count = st.slider("Número de nodos", min_value=8, max_value=16, value=8)

        creation_type = st.radio(
            "Tipo de creación:",
            ["Aleatorio", "Manual"]
        )

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

            steps, graph = st.columns({1, 3})
            with steps:
                st.session_state.dijkstra_steps = dijkstra.steps
                steps_details_dijkstra()
            with graph:
                show_graph(all_short_paths, is_dijkstra_executed, start_node, end_node)

            # Ruta del camino corto y detalles para encontar el camino
            # show_min_path(min_distance, all_short_paths, start_node, end_node)
        else:
            show_graph(all_short_paths, is_dijkstra_executed, start_node, end_node)


if __name__ == "__main__":
    main()