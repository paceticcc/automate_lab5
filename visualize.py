import networkx as nx
from pyvis.network import Network

def readFile(file):
    f = open(file, 'r')
    original = []
    lineCount = 0

    for line in f:
        splited = line.split(';')
        original.append([0] * len(splited))
        for i in range(len(splited)):
            item = splited[i].strip('\n').strip('\t')
            original[lineCount][i] = item

        lineCount += 1

    for line in original:
        print(line)

    G = nx.DiGraph()
    for i in range(1, len(original[1])):
        isFinal = original[0][i] == 'F'
        state = original[1][i]
        G.add_node(state, is_final=isFinal)
        for j in range(2, len(original)):
            if original[j][i] != "":
                nextStates = original[j][i].split(",")
                terminal = original[j][0]
                for nextState in nextStates:
                    if G.has_edge(state, nextState):
                        current_label = G.edges[state, nextState]['label']
                        new_label = f"{current_label},{terminal}"
                        G.edges[state, nextState]['label'] = new_label
                    else:
                        G.add_edge(state, nextState, label=terminal)

    return G

def visualizeGraph(G):
    net = Network(notebook=True, directed=True)

    for node, attr in G.nodes(data=True):
        color = 'green' if attr.get('is_final', False) else 'blue'
        net.add_node(node, color=color)

    for edge in G.edges(data=True):
        src = edge[0]
        dst = edge[1]
        label = edge[2].get('label', '')
        net.add_edge(src, dst, arrows='to', label=label)

    net.show('graph.html')

def visualize(file):
    G = readFile(file)
    visualizeGraph(G)