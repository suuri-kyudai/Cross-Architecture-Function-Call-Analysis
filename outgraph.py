import networkx as nx
from IPython.display import SVG, display
import sys
from processargs import Pkfile
import pathlib


def graphviz(g: nx.DiGraph, output_path):
    G = nx.nx_agraph.to_agraph(g)
    svg = SVG(G.draw(prog='dot', format='svg'))
    # display(svg)
    graph = nx.nx_agraph.to_agraph(g)
    graph.draw(output_path, format='svg', prog='dot')


if __name__ == "__main__":
    output_path = sys.argv[1]
    input_path_list = sys.argv[2:]
    size = len(input_path_list)
    for pkindex, input_path in enumerate(input_path_list, 1):
        pkfile = Pkfile(input_path, output_path)
        pkfile.load(pkfile.path)
        graph = pkfile.content[0][1]
        pkfile.extension = ".svg"
        pkfile.setoutput()
        # グラフ画像を保存
        print(f'{pkindex}/{size}', end=' ')
        print(pkfile.name)
        # もう画像があるならとばす
        if pathlib.Path(output_path).joinpath(f"{pkfile.stem}.svg").is_file():
            print("skipped")
            continue
        try:
            graphviz(graph, pkfile.output)
        except AttributeError:
            print('NoneType Object cannot convert into svg.')
