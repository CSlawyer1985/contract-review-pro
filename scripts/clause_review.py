"""
条款审核模块
审核合同条款并提出修改建议，含正反两面法和条款库匹配
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ClauseReviewer:
    """条款审核器"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.clause_standards = self._load_clause_standards()
        self._workspace_library_index = None  # 外部注入

    def _load_clause_standards(self) -> pd.DataFrame:
        file_path = self.data_dir / 'clause_standards.csv'
        return pd.read_csv(file_path, encoding='utf-8')

    def set_workspace_library(self, index: Dict[str, str]):
        """注入工作区条款库索引"""
        self._workspace_library_index = index

    def review_clause(self, clause_text: str, clause_type: str, contract_type: str) -> Dict:
        """审核单个条款（兼容旧接口）"""
        standards = self.clause_standards[
            self.clause_standards['clause_type'].str.contains(clause_type, case=False, na=False) &
            (self.clause_standards['contract_type'].str.contains(contract_type, case=False, na=False) |
             self.clause_standards['contract_type'] == '通用')
        ]

        issues = []
        suggestions = []

        if not standards.empty:
            standard = standards.iloc[0]
            key_elements = standard['key_elements'].split('、')
            for element in key_elements:
                if element not in clause_text:
                    issues.append(f"缺少关键要素: {element}")
            if issues:
                suggestions.append({
                    'issue': '、'.join(issues),
                    'suggestion': f"建议参考标准模板：{standard['standard_template']}",
                    'standard_template': standard['standard_template']
                })

        return {
            'clause_type': clause_type,
            'issues': issues,
            'suggestions': suggestions,
            'has_issues': len(issues) > 0
        }

    # ============ 正反两面法 ============

    def review_clause_dual(self, clause_text: str, clause_type: str,
                           party_position: str = "我方") -> Dict:
        """
        正反两面法审核条款

        正面：正常情况下应做什么，权利义务是否明确
        反面：做不到怎么办，救济措施是否明确
        进阶：救济不被执行时怎么办
        """
        result = {
            'clause_type': clause_type,
            'positive': self._review_positive(clause_text, clause_type),
            'negative': self._review_negative(clause_text, clause_type),
            'remedy_enforcement': self._review_remedy_enforcement(clause_text),
        }
        # 综合评估
        issues_count = (len(result['positive'].get('issues', [])) +
                       len(result['negative'].get('issues', [])) +
                       len(result['remedy_enforcement'].get('issues', [])))
        result['dual_score'] = max(0, 100 - issues_count * 20)
        result['dual_level'] = '优' if result['dual_score'] >= 80 else ('良' if result['dual_score'] >= 60 else '需改进')
        return result

    def _review_positive(self, text: str, clause_type: str) -> Dict:
        """正面：正常情形"""
        issues = []
        # 检查是否有明确的权利义务表述
        has_obligation = any(kw in text for kw in ['应', '应当', '须', '必须', '负责'])
        has_right = any(kw in text for kw in ['有权', '享有', '可以要求'])
        has_standard = any(kw in text for kw in ['标准', '规格', '方式', '期限', '条件'])

        if not has_obligation: issues.append("缺少明确义务表述")
        if not has_standard: issues.append("缺少具体标准或条件")
        return {'issues': issues, 'has_obligation': has_obligation, 'has_standard': has_standard}

    def _review_negative(self, text: str, clause_type: str) -> Dict:
        """反面：违约/不履行情形"""
        issues = []
        has_remedy = any(kw in text for kw in ['违约', '赔偿', '解除', '承担', '补救', '修理', '更换'])
        has_notice = any(kw in text for kw in ['通知', '告知', '催告'])
        has_deadline = any(kw in text for kw in ['日内', '期限内', '届满'])

        if not has_remedy: issues.append("缺少违约救济措施")
        if not has_notice: issues.append("缺少通知/催告程序")
        return {'issues': issues, 'has_remedy': has_remedy, 'has_notice': has_notice}

    def _review_remedy_enforcement(self, text: str) -> Dict:
        """进阶：救济不被执行时"""
        issues = []
        has_backup = any(kw in text for kw in ['仍不', '继续', '解除', '仲裁', '诉讼', '第三方', '强制执行'])
        has_cost_allocation = any(kw in text for kw in ['费用', '实现债权', '律师费', '保全'])
        if not has_backup: issues.append("缺少救济执行失败后的二次救济")
        if not has_cost_allocation: issues.append("缺少实现债权费用承担约定")
        return {'issues': issues, 'has_backup': has_backup}

    # ============ 条款库匹配 ============

    def match_clause_from_library(self, clause_type: str, scenario_context: Dict = None) -> Optional[str]:
        """
        从工作区条款库匹配条款（三步匹配法）

        Args:
            clause_type: 条款类型（如 '实现债权费用'、'送达确认'）
            scenario_context: 场景上下文 {contract_type, amount, party_position, risk_level}

        Returns:
            匹配到的条款文本路径，或 None
        """
        if not self._workspace_library_index:
            return None

        # Step 1: 理解场景
        ct = (scenario_context or {}).get('contract_type', '')
        amount = float((scenario_context or {}).get('amount', 0) or 0)

        # Step 2: 匹配写法（基础版 vs 强化版）
        for stem, path in self._workspace_library_index.items():
            if clause_type in stem or stem in clause_type:
                # 大标的用强化版
                if amount > 1000000 and '强化' in stem:
                    return path
                return path

        # Step 3: 适配调整由调用方完成
        return None

    def generate_revised_clause(self, original_clause: str, suggestions: List[Dict]) -> str:
        if not suggestions:
            return original_clause
        if suggestions and 'standard_template' in suggestions[0]:
            return suggestions[0]['standard_template']
        return original_clause
