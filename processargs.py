import sys
import pickle
import pathlib
import re


def getfilestem(filename):
    # ファイル名の拡張子を除いた文字列を返す
    # 最初の.(dot)の直前の文字までを返す
    pattern = re.compile(r"([\w-]+)")
    m = re.search(pattern, filename)
    return m.group(1)


def getfileattributes(filename):
    # ファイル名のソースファイル名，アーキテクチャ，最適化レベルを辞書にして返す
    # ファイル名はf"{source}{architecture}{optimization}"
    pattern = re.compile(r"([\w-]+?)"
                         "(armv4l|armv5l|armv6l|armv4tl|arm720t|arm|"
                         "mipsel|mips64|mips|"
                         "m68k|i486|i586|i686|x86)"
                         "(bl|al|fl)?(O|o)([0-3])")
    m = re.search(pattern, filename)
    if m:
        return {"source": m.group(1),
                "architecture": m.group(2),
                "tool": m.group(3),
                "optimization": int(m.group(5))}
    else:
        return {"source": "",
                "architecture": "",
                "tool": "",
                "optimization": 0}


# pickleファイルのクラス
class Pkfile():
    def __init__(self, path, output_path=None):
        self.path = pathlib.Path(path)
        self.name = self.path.name
        self.stem = getfilestem(self.name)
        if output_path:
            self.output_dir = pathlib.Path(output_path)
        self.suffix = ""
        self.extension = ".list.pk"
        attrdict = getfileattributes(self.name)
        self.source = attrdict["source"]
        self.arch = attrdict["architecture"]
        self.tool = attrdict["tool"]
        self.opt = attrdict["optimization"]

    def load(self, path):
        if path:
            try:
                with open(self.path, mode="rb") as f:
                    self.content = pickle.load(f)
                return self.content
            except pickle.UnpicklingError as e:
                self.content = []
                print(f"{e}:{self.name}")

    def dump(self, path, store):
        # パスを指定してリストや辞書をローカルに保存
        if path or self.content != []:
            extension = self.extension
            if extension == ".pk" or extension == ".list.pk":
                with open(path, mode="wb") as f:
                    pickle.dump(store, f)
            elif extension == ".gexf":
                print("実装中ですがなにもダンプ出来ていません")
                pass

    def setoutput(self):
        stem = self.stem
        suffix = self.suffix
        extension = self.extension
        if suffix:
            suffix = "_" + suffix
        self.output = self.output_dir / f"{stem}{suffix}{extension}"


class ProcessArgs():
    def __init__(self, input_path, output_path=None):
        self.input = input_path
        self.output = output_path

    # 入力ファイル1つあたりに行う処理
    def process(self, pkfile):
        return

    def iterationforinput(self):
        output_path_dir = self.output
        for input_path in self.input:
            fcsg = Pkfile(input_path, output_path_dir)
            fcsg.load(fcsg.path)
            ret = self.process(fcsg)
            fcsg.setoutput()
            fcsg.dump(fcsg.output, ret)


class DecoratorforArgs():
    def iteration_pkfiles(self, input_path_list, output_path_dir):
        def _deco(func):
            def _wrapper(fcsg, *args, **kwargs):
                for input_path in input_path_list:
                    fcsg = Pkfile(input_path, output_path_dir)
                    fcsg.load(fcsg.path)
                    ret = func(fcsg, *args, **kwargs)
                    fcsg.setoutput()
                    fcsg.dump(fcsg.output, ret)
                return ret
            return _wrapper
        return _deco
