"""
条款提取模块
自动扫描值得入库的条款，输出到工作区 candidates/ 目录
"""
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ClauseExtractor:
    """条款提取器 — 每次审核后自动触发"""

    def __init__(self, workspace_clause_dir: Optional[str] = None):
        """
        Args:
            workspace_clause_dir: 工作区条款库路径（.claude/clauses/）
        """
        self.workspace_dir = Path(workspace_clause_dir) if workspace_clause_dir else None
        self.candidates_dir = self.workspace_dir / "candidates" if self.workspace_dir else None
        self.existing_index = self._build_index() if self.workspace_dir else {}

    def _build_index(self) -> Dict[str, str]:
        """构建现有条款库索引"""
        idx = {}
        if not self.workspace_dir or not self.workspace_dir.exists():
            return idx
        for f in self.workspace_dir.glob("*.md"):
            if f.name != "README.md":
                # 用文件名（去扩展名）作为 key
                idx[f.stem] = str(f)
        return idx

    def scan_for_candidates(self, parsed_clauses: List[Dict],
                            contract_type: str) -> List[Dict]:
        """
        扫描合同条款，识别值得入库的候选条款

        提取标准：
        1. 条款类型在现有库中无覆盖
        2. 条款写法有新意或更精准
        3. 覆盖了新的风险场景

        Args:
            parsed_clauses: 已解析的条款列表 [{type, text, ...}, ...]
            contract_type: 合同类型

        Returns:
            候选条款列表 [{type, text, reason, score}, ...]
        """
        candidates = []
        for clause in parsed_clauses:
            clause_type = clause.get('type', '')
            clause_text = clause.get('text', '')
            if not clause_text or len(clause_text) < 50:
                continue

            score = 0
            reasons = []

            # 标准 1：库中无覆盖
            covered = any(clause_type in k or k in clause_type for k in self.existing_index)
            if not covered:
                score += 3
                reasons.append(f"条款类型「{clause_type}」在现有库中无覆盖")

            # 标准 2：条款文本质量（长度适当、结构清晰）
            if 100 < len(clause_text) < 2000:
                score += 1
            if any(kw in clause_text for kw in ['应', '应当', '有权', '不得']):
                score += 1

            # 标准 3：包含具体救济措施
            if any(kw in clause_text for kw in ['违约金', '赔偿', '解除', '承担', '保证']):
                score += 1
                reasons.append("包含具体救济措施")

            if score >= 3:
                candidates.append({
                    'type': clause_type,
                    'text': clause_text,
                    'score': score,
                    'reason': '; '.join(reasons),
                    'source_contract_type': contract_type,
                })

        return sorted(candidates, key=lambda c: c['score'], reverse=True)

    def generate_candidate_file(self, candidate: Dict, source_contract_name: str) -> Optional[str]:
        """
        生成候选条款文件（适用条件 → 标准文本 → 法律依据 → 使用说明）

        Returns:
            生成的文件路径，无可写目标则返回 None
        """
        if not self.candidates_dir:
            return None

        self.candidates_dir.mkdir(parents=True, exist_ok=True)

        clause_type = candidate['type']
        date_str = datetime.now().strftime('%Y%m%d')
        safe_name = source_contract_name.replace('/', '-')[:30]
        filename = f"{clause_type}-{safe_name}-{date_str}.md"
        filepath = self.candidates_dir / filename

        # 检查是否与已有条款同类型
        existing_note = ""
        for k, v in self.existing_index.items():
            if clause_type in k or k in clause_type:
                existing_note = f"\n## 与现有版本差异\n同类型条款「{k}」已存在（{v}），本版本与之差异：[待人工对比]\n"

        content = f"""# {clause_type}

> 来源：{source_contract_name} | 提取日期：{date_str} | 评分：{candidate['score']}/5

## 适用条件
- 合同类型：{candidate.get('source_contract_type', '通用')}
- 提取理由：{candidate['reason']}

## 标准文本
{candidate['text']}

## 法律依据
[待补充]

## 使用说明
- 入库评分：{candidate['score']}/5
- 建议入库级别：{'P0 - 强烈建议' if candidate['score'] >= 4 else 'P1 - 建议入库' if candidate['score'] >= 3 else 'P2 - 可选入库'}
{existing_note}
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return str(filepath)

    def compare_with_existing(self, candidate: Dict) -> Optional[str]:
        """与现有条款比较，返回差异说明"""
        for k in self.existing_index:
            if candidate['type'] in k or k in candidate['type']:
                return f"同类型条款「{k}」已存在于 {self.existing_index[k]}"
        return None


if __name__ == '__main__':
    print("=== 条款提取器测试 ===\n")
    ws = "/Users/CS/Trae/个人工作/合同审核/.claude/clauses"
    extractor = ClauseExtractor(ws)

    # 模拟条款
    test_clauses = [
        {'type': '数据安全', 'text': '数据处理方应采取不低于ISO 27001标准的安全措施，发生数据泄露时应在24小时内通知数据提供方，并承担由此产生的全部损失及第三方索赔。' * 2, 'line': 1},
        {'type': '违约责任', 'text': '违约方应支付违约金。', 'line': 2},
    ]
    candidates = extractor.scan_for_candidates(test_clauses, '服务合同')
    print(f"发现 {len(candidates)} 个候选条款")
    for c in candidates:
        print(f"  {c['type']}: 评分{c['score']}/5 - {c['reason']}")
