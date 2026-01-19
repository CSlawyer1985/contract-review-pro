"""
风险评估模块
评估合同条款风险
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from review_config import ReviewConfig


class RiskAssessment:
    """风险评估器"""

    def __init__(self, data_dir: str, review_config: ReviewConfig):
        """
        初始化风险评估器

        Args:
            data_dir: 数据目录路径
            review_config: 审核配置
        """
        self.data_dir = Path(data_dir)
        self.config = review_config
        self.risk_templates = self._load_risk_templates()

    def _load_risk_templates(self) -> pd.DataFrame:
        """加载风险模板数据"""
        file_path = self.data_dir / 'risk_templates.csv'
        return pd.read_csv(file_path, encoding='utf-8')

    def assess_clause_risk(self, clause_text: str, clause_type: str, contract_type: str) -> List[Dict]:
        """
        评估单个条款的风险

        Args:
            clause_text: 条款文本
            clause_type: 条款类型
            contract_type: 合同类型

        Returns:
            风险列表
        """
        risks = []

        # 筛选相关的风险模板
        relevant_risks = self.risk_templates[
            (self.risk_templates['contract_type'].str.contains(contract_type, case=False, na=False) |
             self.risk_templates['contract_type'].str.contains('通用', case=False, na=False)) &
            (self.risk_templates['clause_name'].str.contains(clause_type, case=False, na=False) |
             self.risk_templates['clause_name'].str.contains('通用', case=False, na=False))
        ]

        for _, risk_template in relevant_risks.iterrows():
            # 检查是否需要报告该风险
            if not self.config.should_report_risk(risk_template['risk_type']):
                continue

            # 简化的风险评估：检查关键词
            risk_keywords = risk_template['risk_description'].split('、')[:3]
            matched_keywords = sum(1 for kw in risk_keywords if kw in clause_text)

            # 如果关键词匹配度较低，认为存在风险
            if matched_keywords < len(risk_keywords) / 2:
                risks.append({
                    'risk_id': risk_template['risk_id'],
                    'risk_type': risk_template['risk_type'],
                    'description': risk_template['risk_description'],
                    'legal_basis': risk_template['legal_basis'],
                    'suggestion': risk_template['modification_suggestion'],
                    'impact': risk_template['impact_analysis']
                })

        return risks

    def classify_risk_level(self, risk_score: float) -> str:
        """
        根据风险分数分类风险等级

        Args:
            risk_score: 风险分数（0-100）

        Returns:
            风险等级
        """
        if risk_score >= 80:
            return '致命风险'
        elif risk_score >= 60:
            return '重要风险'
        elif risk_score >= 40:
            return '一般风险'
        else:
            return '轻微瑕疵'

    def generate_risk_report(self, all_risks: List[Dict]) -> Dict:
        """
        生成风险报告

        Args:
            all_risks: 所有风险列表

        Returns:
            风险报告
        """
        # 按风险等级分组
        risk_by_level = {
            '致命风险': [],
            '重要风险': [],
            '一般风险': [],
            '轻微瑕疵': []
        }

        for risk in all_risks:
            risk_level = risk['risk_type']
            if risk_level in risk_by_level:
                risk_by_level[risk_level].append(risk)

        # 统计
        risk_summary = {
            level: len(risks) for level, risks in risk_by_level.items()
        }

        return {
            'summary': risk_summary,
            'risks_by_level': risk_by_level,
            'total_risks': len(all_risks)
        }
