"""
OOXML Lite — skill 内置的 docx Track Changes / Comments 引擎

设计目标：
- 零外部依赖（仅标准库 zipfile + xml.dom.minidom），skill 可独立生成批注版合同
- 接口形态对齐 Anthropic docx skill 的 Document library（doc[rel_path] / get_node /
  replace_node / insert_after / add_comment / save），调用方代码双引擎可互换
- 跨 <w:t> 分片匹配：Word/WPS 常把一段文本拆进多个 <w:t>，匹配一律走"节点内全部
  w:t 文本拼接"，不做单 run 字符串假设

纪律（来自批注版合同制作规范）：
- 修订标记 del+ins 配对：先 <w:del>（w:delText）后 <w:ins>（w:t）
- 新增条款必须是独立 <w:p> 段落并携带 <w:pPr>，不得行内追加
- 修订/批注必须携带 w:author / w:date / w:id
"""

import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from xml.dom import minidom
from xml.dom.minidom import Document as DomDocument
from xml.dom.minidom import Element, Node

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CT_COMMENTS = "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"
REL_COMMENTS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"

_CONTENT_TYPES = "[Content_Types].xml"
_DOCUMENT = "word/document.xml"
_COMMENTS = "word/comments.xml"
_RELS = "word/_rels/document.xml.rels"


# ---------------------------------------------------------------------------
# unpack / pack
# ---------------------------------------------------------------------------

def unpack_docx(src: str, dest: str) -> None:
    """解压 docx（zip）到目录，dest 存在则先清空（clean-unpack 纪律）"""
    dest_path = Path(dest)
    if dest_path.exists():
        shutil.rmtree(dest_path)
    dest_path.mkdir(parents=True)
    with zipfile.ZipFile(src, "r") as zf:
        zf.extractall(dest_path)


def pack_docx(src_dir: str, dest: str) -> None:
    """把目录打包为 docx（zip）。压缩集内顺序对 Word 无影响"""
    src_path = Path(src_dir)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(src_path.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(src_path).as_posix())


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _node_text(node: Node) -> str:
    """拼接节点内全部 w:t 文本（跨分片）"""
    if node.nodeType != Node.ELEMENT_NODE:
        return ""
    parts = [
        t.firstChild.data
        for t in node.getElementsByTagName("w:t")
        if t.firstChild and t.firstChild.nodeType == Node.TEXT_NODE
    ]
    return "".join(parts)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# LiteEditor — 单个 XML 部件的编辑器（默认 word/document.xml）
# ---------------------------------------------------------------------------

class LiteEditor:
    """对应 doc["word/document.xml"] 返回的 editor 对象"""

    def __init__(self, owner: "LiteDocument", rel_path: str):
        self._owner = owner
        self.rel_path = rel_path
        self.dom: DomDocument = owner._load_dom(rel_path)

    # -- 查询 ---------------------------------------------------------------

    def get_node(self, tag: Optional[str] = None, contains: Optional[str] = None) -> Optional[Element]:
        """按标签 + 拼接文本定位第一个匹配节点（跨 <w:t> 分片匹配）"""
        if not tag:
            return None
        for node in self.dom.getElementsByTagName(tag):
            if contains is None or contains in _node_text(node):
                return node
        return None

    # -- 修改 ---------------------------------------------------------------

    def _fragment_nodes(self, xml_str: str) -> List[Node]:
        """把 XML 片段字符串解析为本文档的节点列表（自动补命名空间声明）"""
        wrapped = f'<w:_fragment xmlns:w="{W_NS}">{xml_str}</w:_fragment>'
        frag = minidom.parseString(wrapped)
        return [self.dom.importNode(c, deep=True) for c in frag.documentElement.childNodes]

    def replace_node(self, node: Node, xml_str: str) -> None:
        """用 XML 片段替换节点"""
        parent = node.parentNode
        if parent is None:
            raise ValueError("目标节点无父节点，无法替换")
        for new_node in self._fragment_nodes(xml_str):
            parent.insertBefore(new_node, node)
        parent.removeChild(node)

    def insert_after(self, node: Node, xml_str: str) -> None:
        """在节点之后插入 XML 片段"""
        parent = node.parentNode
        if parent is None:
            raise ValueError("目标节点无父节点，无法插入")
        ref = node.nextSibling
        for new_node in self._fragment_nodes(xml_str):
            parent.insertBefore(new_node, ref)

    def insert_before(self, node: Node, xml_str: str) -> None:
        parent = node.parentNode
        if parent is None:
            raise ValueError("目标节点无父节点，无法插入")
        for new_node in self._fragment_nodes(xml_str):
            parent.insertBefore(new_node, node)


# ---------------------------------------------------------------------------
# LiteDocument — 对应 docx skill 的 Document
# ---------------------------------------------------------------------------

class LiteDocument:
    """最小化 Document：多部件缓存、comments 管理、写回"""

    def __init__(self, unpacked_dir: str, author: str, initials: str, track_revisions: bool = True):
        self.root = Path(unpacked_dir)
        self.author = author
        self.initials = initials
        self.track_revisions = track_revisions
        self._doms = {}          # rel_path -> DomDocument
        self._editors = {}       # rel_path -> LiteEditor
        self._comment_id = None  # 延迟初始化

    # -- 部件加载/访问 -------------------------------------------------------

    def _load_dom(self, rel_path: str) -> DomDocument:
        if rel_path not in self._doms:
            file_path = self.root / rel_path
            if file_path.exists():
                self._doms[rel_path] = minidom.parse(str(file_path))
            else:
                self._doms[rel_path] = None
        return self._doms[rel_path]

    def __getitem__(self, rel_path: str) -> LiteEditor:
        if rel_path not in self._editors:
            self._editors[rel_path] = LiteEditor(self, rel_path)
        return self._editors[rel_path]

    # -- 批注 ---------------------------------------------------------------

    def _next_comment_id(self) -> int:
        if self._comment_id is None:
            dom = self._load_dom(_COMMENTS)
            max_id = -1
            if dom is not None:
                for c in dom.getElementsByTagName("w:comment"):
                    try:
                        max_id = max(max_id, int(c.getAttribute("w:id")))
                    except (TypeError, ValueError):
                        continue
            self._comment_id = max_id + 1
        cid = self._comment_id
        self._comment_id += 1
        return cid

    def _ensure_comments_part(self) -> DomDocument:
        """确保 comments.xml 存在并在 [Content_Types].xml / rels 中登记"""
        dom = self._load_dom(_COMMENTS)
        if dom is None:
            dom = minidom.parseString(
                f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:comments xmlns:w="{W_NS}"></w:comments>'
            )
            self._doms[_COMMENTS] = dom
            if _COMMENTS in self._editors:
                self._editors[_COMMENTS].dom = dom

        # [Content_Types].xml 登记
        ct = self._load_dom(_CONTENT_TYPES)
        if ct is not None and not any(
            o.getAttribute("PartName") == "/word/comments.xml"
            for o in ct.getElementsByTagName("Override")
        ):
            override = ct.createElement("Override")
            override.setAttribute("PartName", "/word/comments.xml")
            override.setAttribute("ContentType", CT_COMMENTS)
            ct.documentElement.appendChild(override)

        # document.xml.rels 登记
        rels = self._load_dom(_RELS)
        if rels is not None and not any(
            r.getAttribute("Type") == REL_COMMENTS
            for r in rels.getElementsByTagName("Relationship")
        ):
            existing_ids = {
                r.getAttribute("Id") for r in rels.getElementsByTagName("Relationship")
            }
            n = 1
            while f"rId{n}" in existing_ids:
                n += 1
            rel = rels.createElement("Relationship")
            rel.setAttribute("Id", f"rId{n}")
            rel.setAttribute("Type", REL_COMMENTS)
            rel.setAttribute("Target", "comments.xml")
            rels.documentElement.appendChild(rel)

        return dom

    def add_comment(self, start: Node, end: Node, text: str) -> None:
        """在 start..end 节点范围上添加批注（锚点包裹 + comments.xml 追加）"""
        comments_dom = self._ensure_comments_part()
        doc_dom = self._load_dom(_DOCUMENT)
        cid = self._next_comment_id()

        # 1. comments.xml 追加批注正文
        comment = comments_dom.createElement("w:comment")
        comment.setAttribute("w:id", str(cid))
        comment.setAttribute("w:author", self.author)
        comment.setAttribute("w:initials", self.initials)
        comment.setAttribute("w:date", _now_iso())
        for para in text.split("\n"):
            p = comments_dom.createElement("w:p")
            r = comments_dom.createElement("w:r")
            t = comments_dom.createElement("w:t")
            t.setAttribute("xml:space", "preserve")
            t.appendChild(comments_dom.createTextNode(para))
            r.appendChild(t)
            p.appendChild(r)
            comment.appendChild(p)
        comments_dom.documentElement.appendChild(comment)

        # 2. document.xml 锚点包裹
        range_start = doc_dom.createElement("w:commentRangeStart")
        range_start.setAttribute("w:id", str(cid))
        range_end = doc_dom.createElement("w:commentRangeEnd")
        range_end.setAttribute("w:id", str(cid))
        ref_run = doc_dom.createElement("w:r")
        rpr = doc_dom.createElement("w:rPr")
        rstyle = doc_dom.createElement("w:rStyle")
        rstyle.setAttribute("w:val", "CommentReference")
        rpr.appendChild(rstyle)
        ref_run.appendChild(rpr)
        cref = doc_dom.createElement("w:commentReference")
        cref.setAttribute("w:id", str(cid))
        ref_run.appendChild(cref)

        start_parent = start.parentNode
        end_parent = end.parentNode
        if start_parent is None or end_parent is None:
            raise ValueError("批注锚点节点无父节点")
        start_parent.insertBefore(range_start, start)
        end_ref = end.nextSibling
        end_parent.insertBefore(range_end, end_ref)
        end_parent.insertBefore(ref_run, end_ref)

    # -- 写回 ---------------------------------------------------------------

    def save(self, validate: bool = False) -> None:  # noqa: ARG002 - 对齐 docx skill 签名
        """把内存中修改过的部件写回 unpacked 目录"""
        for rel_path, dom in self._doms.items():
            if dom is None:
                continue
            file_path = self.root / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(dom.toxml(encoding="utf-8"))
