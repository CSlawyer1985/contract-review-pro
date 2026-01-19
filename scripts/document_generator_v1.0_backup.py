"""
文档生成模块
生成法律审核意见书和批注版合同
"""

from pathlib import Path
from typing import Dict, List
from datetime import datetime


class DocumentGenerator:
    """文档生成器"""

    def __init__(self, output_dir: str):
        """
        初始化文档生成器

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.opinions_dir = self.output_dir / 'opinions'
        self.annotated_dir = self.output_dir / 'annotated_contracts'

        # 创建输出目录
        self.opinions_dir.mkdir(parents=True, exist_ok=True)
        self.annotated_dir.mkdir(parents=True, exist_ok=True)

    def generate_legal_opinion(self, contract_name: str, analysis_result: Dict,
                              risk_report: Dict, user_context: Dict) -> str:
        """
        生成法律审核意见书（Markdown格式）

        Args:
            contract_name: 合同名称
            analysis_result: 合同分析结果
            risk_report: 风险报告
            user_context: 用户上下文信息

        Returns:
            生成的文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{contract_name}_法律审核意见书_{timestamp}.md"
        filepath = self.opinions_dir / filename

        # 生成 Markdown 内容
        content = self._generate_opinion_content(
            contract_name, analysis_result, risk_report, user_context
        )

        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(filepath)

    def _generate_opinion_content(self, contract_name: str, analysis_result: Dict,
                                 risk_report: Dict, user_context: Dict) -> str:
        """生成意见书内容"""
        content = f"""# {contract_name} 法律审核意见书

---

## 一、合同基本信息

- **合同类型**: {analysis_result.get('identified_type', '未知')}
- **识别置信度**: {analysis_result.get('type_confidence', 0):.2%}
- **审核时间**: {datetime.now().strftime('%Y年%m月%d日')}

---

## 二、用户确认信息

- **代表方**: {user_context.get('party', '未指定')}
- **市场地位**: {user_context.get('position', '未指定')}
- **过往交易**: {user_context.get('history', '无')}
- **关注点**: {user_context.get('focus', '未指定')}

---

## 三、审核配置

- **审核深度**: {user_context.get('review_depth', '标准审核')}
- **审核范围**: {user_context.get('review_scope', '主要条款')}
- **风险等级**: {', '.join(user_context.get('risk_levels', ['致命', '重要', '一般']))}

---

## 四、风险汇总

"""

        # 风险汇总
        summary = risk_report.get('summary', {})
        content += "| 风险等级 | 数量 |\n"
        content += "|---------|------|\n"
        for level, count in summary.items():
            content += f"| {level} | {count} |\n"
        content += f"| **合计** | **{risk_report.get('total_risks', 0)}** |\n\n"

        # 按风险等级详细列出
        content += "## 五、详细审核意见\n\n"

        risks_by_level = risk_report.get('risks_by_level', {})

        for level in ['致命风险', '重要风险', '一般风险', '轻微瑕疵']:
            risks = risks_by_level.get(level, [])
            if not risks:
                continue

            content += f"### {level}（{len(risks)}项）\n\n"

            for i, risk in enumerate(risks, 1):
                content += f"#### {i}. {risk['description']}\n\n"
                content += f"- **风险等级**: {risk['risk_type']}\n"
                content += f"- **法律依据**: {risk['legal_basis']}\n"
                content += f"- **修改建议**: {risk['suggestion']}\n"
                content += f"- **影响分析**: {risk['impact']}\n\n"

        # 条款审核结果
        clauses = analysis_result.get('clauses', {})
        if clauses:
            content += "## 六、条款审核结果\n\n"
            for clause_type, clause_list in clauses.items():
                content += f"### {clause_type}（{len(clause_list)}条）\n\n"
                for clause in clause_list[:3]:  # 只显示前3条
                    content += f"**{clause['number']}**: {clause['content'][:100]}...\n\n"

        # 总体建议
        content += """---

## 七、总体建议

1. **优先处理**: 建议优先修改"致命风险"和"重要风险"相关条款
2. **风险对冲**: 对于无法修改的风险，建议通过其他措施进行对冲（如担保、保险）
3. **后续跟进**: 建议在合同履行过程中密切关注已识别的风险点

---

*本意见书由 AI 辅助生成，仅供参考，具体请以专业律师意见为准。*

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return content

    def generate_annotated_contract(self, contract_name: str, original_contract: str,
                                   revisions: List[Dict]) -> str:
        """
        生成批注版合同（简化的Markdown格式）

        注意：完整版需要使用 python-docx 生成 Word 文档

        Args:
            contract_name: 合同名称
            original_contract: 原合同文本
            revisions: 修订列表

        Returns:
            生成的文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{contract_name}_批注版_{timestamp}.md"
        filepath = self.annotated_dir / filename

        # 生成带批注的内容
        content = f"# {contract_name}（批注版）\n\n"
        content += "## 批注说明\n\n"
        content += "- ~~删除线~~ 表示删除的内容\n"
        content += "- **下划线** 或红色文字表示新增的内容\n"
        content += "- [批注] 表示审核意见和修改建议\n\n"
        content += "---\n\n"

        # 添加原合同内容（简化版，实际应该逐行处理并添加修订标记）
        content += "## 合同正文\n\n"
        content += original_contract

        # 添加修订汇总
        if revisions:
            content += "\n\n---\n\n"
            content += "## 修订汇总\n\n"
            for i, revision in enumerate(revisions, 1):
                content += f"### 修订 {i}\n\n"
                content += f"- **位置**: {revision.get('location', '未知')}\n"
                content += f"- **风险等级**: {revision.get('risk_level', '未知')}\n"
                content += f"- **原内容**: {revision.get('original', '未知')}\n"
                content += f"- **建议修改**: {revision.get('suggested', '未知')}\n"
                content += f"- **修改理由**: {revision.get('reason', '未知')}\n\n"

        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(filepath)
