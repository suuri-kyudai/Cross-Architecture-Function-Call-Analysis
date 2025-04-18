import networkx as nx
import sys
from processargs import Pkfile
import re
import itertools
import searchlibroot as slr
import openpyxl
import pathlib
import copy


def add_nodes_and_edge(graph, node1, node2):
    if not graph.has_edge(node1, node2):
        graph.add_node(node1, label=node1)
        graph.add_node(node2, label=node2)
        graph.add_edge(node1, node2)
    return


def ismipsandftext(pkfile, s):
    # グラフ元のバイナリのアーキテクチャがmipsで最適化レベルがo1以上でかつ
    # 呼び出す関数が_ftextだったとき，それをmainに変更
    # そのための判定関数
    # 憶測に基づいて大胆なことをやっているので処理については要検討
    pattern = re.compile(r"_{0,2}ftext")
    m = re.search(pattern, s)
    if pkfile.opt >= 2 and pkfile.arch == "mips" and m:
        return True


def calluserfunction(cl):
    # ツールチェインや最適化度によってmain関数の呼び出しが_ftextの呼び出しになる
    # _ftext内での関数呼び出しでライブラリ関数でない関数を呼び出していたら
    # それは_ftextではなくmain関数での呼び出しということにする
    cs = set([f[0] for f in cl] + [f[1] for f in cl])
    return any([slr.is_userfunc(f) for f in cs])


def modifymain(nl):
    # _ftext関数の呼び出しをmain関数の呼び出しということにする
    cf = [f[0] for f in nl]
    pattern = re.compile(r"_{0,2}ftext")
    ml = [re.search(pattern, f) for f in cf]
    # name_listの中にmain関数と_ftextの呼び出しがあるかどうかを判定
    # main関数がなくて_ftextがある場合，_ftextがmain関数である可能性高い
    if "main" not in cf and any(ml):
        index = ml.index([i for i in ml if i][0])
        cf, cl = nl[index]
        # _ftextがユーザー定義関数を呼び出すかチェック
        if calluserfunction(cl):
            nl[index][0] = "main"
            for index_ftext, cll in enumerate(nl[index][1]):
                mf = [re.search(pattern, f) for f in cll]
                if any(mf):
                    index_tuple = mf.index([i for i in mf if i][0])
                    nl[index][1][index_ftext][index_tuple] = "main"
    return nl


# アーキテクチャ固有の関数が存在するか確認する関数
# リストの呼び出された関数にアーキテクチャ固有の関数があったら
# Trueを返す
def hasarchfunc(namelist, specnodes):
    for name in namelist:
        if any([node in specnodes for node in sum(name[1], [])]):
            return True
    else:
        return False


# アーキテクチャ固有のノードをリストから削除する関数
def rmnode(namelist, specnodes):
    # 走査用のリストをコピー
    namelistc = copy.deepcopy(namelist)
    for i, name in enumerate(namelistc):
        callfunc_from, callfunc_to_list = name
        length = len(callfunc_to_list)
        for j, callfunc in enumerate(callfunc_to_list):
            node_from, node_to = callfunc
            if node_to in specnodes:
                node_via_list = []
                # [node1, specnode]が見つかったものから後ろに走査
                # [specnode, node2]となっているものを探す
                for k in range(j+1, length):
                    pair = callfunc_to_list[k]
                    if pair[0] == node_to:
                        node_via_list.append(pair[1])
                    if pair[1] == node_to:
                        break
                # [node1, specnode]と[specnode, node2]を消して
                # [node1, node2]を挿入
                namelist[i][1].remove([node_from, node_to])
                for node in node_via_list:
                    namelist[i][1].insert(j, [node_from, node])
                    namelist[i][1].remove([node_to, node])
                break
    return namelist


# グラフ(networkx)作成関数
# ノード名にその関数を呼び出した関数名を付与
# 関数A内で関数Bが呼ばれているとしたらノード名はB/A
# 関数の呼び出し順序は維持する
# new_analyze_fromidaで作成したname_listにしか使えません
def makenxgraph_kawasoe(name_list):
    # name_list = [['func_name_callee',
    #               [['func_name1', 'func_name2'],
    #                ['func_name1', 'func_name2'],
    #                ['func_name1', 'func_name2']...]]]
    name_list = modifymain(name_list)
    graph = nx.DiGraph()
    for name in name_list:
        # nameから呼び出す関数とリストをアンパック
        callfunc_from, callfunc_list = name
        attr_node = callfunc_from
        for callfunc in callfunc_list:
            # callfunc_listが空なら飛ばす
            if not callfunc_list:
                continue
            # callfunc_to_listから関数の呼び出し元と呼び出し先をアンパック
            node_from, node_to = callfunc
            if node_from == "":
                node_from = "empty_string"
            if node_to == "":
                node_to = "empty_string"
            node_from = f'{node_from}/{attr_node}'
            node_to = f'{node_to}/{attr_node}'
            if not graph.has_edge(node_from, node_to):
                graph.add_node(node_from, label=node_from)
                graph.add_node(node_to, label=node_to)
                graph.add_edge(node_from, node_to)
    return graph


def makenxgraph_kawasoe_noattr(name_list):
    # name_list = [['func_name_callee',
    #               [['func_name1', 'func_name2'],
    #                ['func_name1', 'func_name2'],
    #                ['func_name1', 'func_name2']...]]]
    name_list = modifymain(name_list)
    graph = nx.DiGraph()
    for name in name_list:
        # nameから呼び出す関数とリストをアンパック
        callfunc_from, callfunc_list = name
        for lc, callfunc in enumerate(callfunc_list):
            # callfunc_listが空なら飛ばす
            if not callfunc_list:
                continue
            # callfunc_to_listから関数の呼び出し元と呼び出し先をアンパック
            node_from, node_to = callfunc
            if node_from == "":
                node_from = "empty_string"
            if node_to == "":
                node_to = "empty_string"
            # call_func_fromからnode_fromにエッジを追加する
            if lc == 0 and callfunc_from != node_from:
                add_nodes_and_edge(graph, callfunc_from, node_from)
            add_nodes_and_edge(graph, node_from, node_to)
    return graph


# アーキテクチャ固有の関数シンボルのリスト
wbarch = openpyxl.load_workbook("path/to/archspecificsym_list.xlsx")

if __name__ == "__main__":
    input_path_list = sys.argv[2:]
    output_path = sys.argv[1]
    for input_path in input_path_list:
        pkfile = Pkfile(input_path, output_path)

        pkfile.load(pkfile.path)
        if not pkfile.content:
            continue
        print(pkfile.name)
        malware_fcsg = []

        arch = pkfile.arch + pkfile.tool
        # アーキテクチャ固有と判定されたノード集合(specnodes)
        archsheet = wbarch[f"{arch}"]
        specnodes = set()
        for row in archsheet.iter_rows(min_col=1, max_col=1, values_only=True):
            specnodes.add(row[0])

        # アーキテクチャ固有の関数を削除
        # アーキテクチャ固有の関数内で呼び出される関数シーケンスの削除
        namelist = [name for name in pkfile.content
                    if not name[0] in specnodes]
        # ライブラリ関数やユーザー定義関数内で呼び出される
        # アーキテクチャ固有の関数の削除
        while hasarchfunc(namelist, specnodes):
            namelist = rmnode(namelist, specnodes)

        # attributeあり
        graph = makenxgraph_kawasoe(namelist)
        malware_fcsg.append([pkfile.stem, graph])
        pkfile.suffix = "ma"
        pkfile.extension = ".list.pk"
        pkfile.setoutput()
        pkfile.dump(pkfile.output, malware_fcsg)

        malware_fcsg.clear()
        # attributeなし
        graph = makenxgraph_kawasoe_noattr(namelist)
        malware_fcsg.append([pkfile.stem, graph])
        pkfile.suffix = "ma_noattr"
        pkfile.extension = ".list.pk"
        pkfile.setoutput()
        pkfile.dump(pkfile.output, malware_fcsg)
