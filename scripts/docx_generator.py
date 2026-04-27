"""
Word Track Changes 生成器
基于 docx skill 的 OOXML Document 类，将审核结果转化为 Word 修订模式文档。

依赖：/Users/CS/.claude/skills/docx/ 下的 Document 类和 ooxml 工具链
"""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

# docx skill 路径
DOCX_SKILL_ROOT = Path("/Users/CS/.claude/skills/docx")

RISK_LEVEL_MAP = {
    "致命风险": "P0",
    "重要风险": "P1",
    "一般风险": "P2",
    "轻微瑕疵": "P3",
}


class DocxTrackChangesGenerator:
    """将审核结果写入 Word 文档，生成带 Track Changes 和 Comments 的 .docx"""

    def __init__(
        self,
        original_docx_path: str,
        risk_report: Dict,
        output_dir: str,
        author: str = "陈石律师",
        initials: str = "CS",
    ):
        self.original_docx = Path(original_docx_path)
        self.risk_report = risk_report
        self.output_dir = Path(output_dir)
        self.author = author
        self.initials = initials

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, contract_name: str) -> Optional[str]:
        """生成带修订标记的 Word 文档，返回输出文件路径。失败返回 None。"""
        if not self.original_docx.exists():
            print(f"[docx_generator] 原始文件不存在: {self.original_docx}")
            return None

        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp(prefix="contract_review_")
            unpacked_dir = Path(tmp_dir) / "unpacked"

            # 1. unpack 原始 docx
            self._unpack(self.original_docx, unpacked_dir)

            # 2. 注入 docx skill 路径并初始化 Document
            # 核心问题：contract-review-pro 的 scripts/ 与 docx skill 的 scripts/ 包名冲突
            # 解决方案：临时清除 sys.modules 中的 scripts 包缓存，重新加载
            docx_skill_ooxml = DOCX_SKILL_ROOT / "ooxml" / "scripts"

            saved_modules = {}
            for key in list(sys.modules.keys()):
                if key.startswith("scripts") or key.startswith("ooxml"):
                    saved_modules[key] = sys.modules.pop(key)

            try:
                # 确保 docx skill 根目录在最前面
                if str(DOCX_SKILL_ROOT) in sys.path:
                    sys.path.remove(str(DOCX_SKILL_ROOT))
                sys.path.insert(0, str(DOCX_SKILL_ROOT))

                from scripts.document import Document
            finally:
                # 恢复被清除的模块（保留新加载的）
                pass

            doc = Document(
                str(unpacked_dir),
                author=self.author,
                initials=self.initials,
                track_revisions=True,
            )

            # 3. 遍历风险项，生成修订和批注
            self._apply_all_changes(doc, self.risk_report)

            # 4. 保存（自动验证 + 写回 unpacked_dir）
            doc.save(validate=False)

            # 5. 打包为 .docx
            output_filename = f"{contract_name}-审核修订版.docx"
            output_path = self.output_dir / output_filename

            spec = importlib.util.spec_from_file_location(
                "pack_mod", docx_skill_ooxml / "pack.py"
            )
            pack_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pack_mod)
            pack_document = pack_mod.pack_document

            pack_document(str(unpacked_dir), str(output_path), validate=False)

            print(f"[docx_generator] 审核修订版已生成: {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"[docx_generator] 生成失败: {e}")
            import traceback

            traceback.print_exc()
            return None
        finally:
            if tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def _unpack(self, docx_path: Path, output_dir: Path):
        """调用 docx skill 的 unpack.py 解压 docx"""
        unpack_script = DOCX_SKILL_ROOT / "ooxml" / "scripts" / "unpack.py"
        result = subprocess.run(
            [sys.executable, str(unpack_script), str(docx_path), str(output_dir)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Unpack 失败: {result.stderr}")
        print(f"[docx_generator] Unpack 完成: {output_dir}")

    def _apply_all_changes(self, doc, risk_report: Dict):
        """遍历所有风险项，应用修订和批注"""
        risks_by_level = risk_report.get("risks_by_level", {})
        total = 0
        applied = 0

        for level in ["致命风险", "重要风险", "一般风险", "轻微瑕疵"]:
            risks = risks_by_level.get(level, [])
            for risk in risks:
                total += 1
                if self._apply_single_risk(doc, risk, level):
                    applied += 1

        print(f"[docx_generator] 风险项处理: {applied}/{total} 成功应用")

    def _apply_single_risk(self, doc, risk: Dict, level: str) -> bool:
        """对单个风险项应用修订 + 批注。返回是否成功。"""
        original_text = risk.get("original_text", "")
        suggestion = risk.get("suggestion", "")
        analysis = risk.get("analysis", "")
        legal_basis = risk.get("legal_basis", "")
        description = risk.get("description", "")

        if not original_text:
            return False

        # 构建批注内容
        priority = RISK_LEVEL_MAP.get(level, "P?")
        comment_parts = [f"[{priority}] {description}"]
        if analysis:
            comment_parts.append(f"分析: {analysis}")
        if legal_basis:
            comment_parts.append(f"依据: {legal_basis}")
        comment_text = "\n".join(comment_parts)

        try:
            editor = doc["word/document.xml"]

            # 尝试定位原文中的文本节点
            # 截取前 60 个字符用于匹配，避免全文匹配失败
            search_text = original_text.strip()[:60]
            if not search_text:
                return False

            node = editor.get_node(tag="w:r", contains=search_text)

            if node is None:
                # 尝试按段落匹配
                try:
                    node = editor.get_node(tag="w:p", contains=search_text)
                except Exception:
                    pass

            if node is None:
                print(f"[docx_generator] 未找到匹配文本: {search_text[:30]}...")
                return False

            # 如果有修改建议，生成 Track Changes
            if suggestion and suggestion.strip() not in ["无", "无建议", ""]:
                self._apply_track_change(editor, doc, node, original_text, suggestion)

                # Track Change 之后，用新插入的内容节点添加批注
                try:
                    clean_suggestion = suggestion.strip()
                    for prefix in ["修改为：", "修改为:", "建议修改为：", "建议修改为:"]:
                        if clean_suggestion.startswith(prefix):
                            clean_suggestion = clean_suggestion[len(prefix):].strip()
                    ins_node = editor.get_node(tag="w:ins", contains=clean_suggestion[:30])
                    if ins_node is not None:
                        doc.add_comment(start=ins_node, end=ins_node, text=comment_text)
                except Exception as e:
                    print(f"[docx_generator] 批注添加失败（Track Change 后）: {e}")
            else:
                # 无修改建议时，直接对原节点添加批注
                try:
                    doc.add_comment(start=node, end=node, text=comment_text)
                except Exception as e:
                    print(f"[docx_generator] 批注添加失败: {e}")

            return True

        except Exception as e:
            print(f"[docx_generator] 处理风险项失败 [{description[:20]}]: {e}")
            return False

    def _apply_track_change(self, editor, doc, node, original_text: str, suggestion: str):
        """对文本节点应用 Track Change（删除原文 + 插入建议）"""
        try:
            # 获取节点的格式信息
            rpr = ""
            try:
                rpr_nodes = node.getElementsByTagName("w:rPr")
                if rpr_nodes:
                    rpr = rpr_nodes[0].toxml()
            except Exception:
                pass

            # 清理建议文本
            clean_suggestion = suggestion.strip()
            # 如果建议中包含 "修改为：" 等前缀，提取实际内容
            for prefix in ["修改为：", "修改为:", "建议修改为：", "建议修改为:"]:
                if clean_suggestion.startswith(prefix):
                    clean_suggestion = clean_suggestion[len(prefix) :].strip()

            # 截取用于匹配的原文片段（node 中实际包含的文本）
            actual_text = self._get_node_text(node)
            if not actual_text:
                return

            replacement = (
                f'<w:del><w:r>{rpr}<w:delText>{self._escape(actual_text)}</w:delText></w:r></w:del>'
                f'<w:ins><w:r>{rpr}<w:t>{self._escape(clean_suggestion)}</w:t></w:r></w:ins>'
            )

            editor.replace_node(node, replacement)

        except Exception as e:
            print(f"[docx_generator] Track Change 应用失败: {e}")

    @staticmethod
    def _get_node_text(node) -> str:
        """提取 w:r 或 w:p 节点中的纯文本"""
        texts = []
        for t_node in node.getElementsByTagName("w:t"):
            if t_node.firstChild and t_node.firstChild.nodeType == t_node.firstChild.TEXT_NODE:
                texts.append(t_node.firstChild.data)
        return "".join(texts)

    @staticmethod
    def _escape(text: str) -> str:
        """XML 转义"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
