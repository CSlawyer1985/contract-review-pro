"""
风险评估模块
评估合同条款风险，含六维度评价、风险标签和雷达图数据
"""

import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from review_config import ReviewConfig


class RiskAssessment:
    """风险评估器"""

    # 8 审查维度
    RADAR_DIMENSIONS = [
        "合同效力与合规性", "价款与支付", "交付与验收", "违约责任",
        "知识产权与保密", "合同解除与终止", "争议解决", "主体授权与担保"
    ]

    # 6 维度评价标签
    SIX_DIMENSIONS = ["风险定性", "风险敞口", "发生概率", "可规避性", "商业权衡", "紧迫性"]

    def __init__(self, data_dir: str, review_config: ReviewConfig):
        self.data_dir = Path(data_dir)
        self.config = review_config
        self.risk_templates = self._load_risk_templates()
        self.risk_labels = self._load_risk_labels()

    def _load_risk_templates(self) -> pd.DataFrame:
        file_path = self.data_dir / 'risk_templates.csv'
        return pd.read_csv(file_path, encoding='utf-8')

    def _load_risk_labels(self) -> List[Dict]:
        path = self.data_dir / 'risk_labels.csv'
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        return []

    def assess_clause_risk(self, clause_text: str, clause_type: str, contract_type: str) -> List[Dict]:
        """评估单个条款的风险（含标签和维度）"""
        risks = []
        relevant_risks = self.risk_templates[
            (self.risk_templates['contract_type'].str.contains(contract_type, case=False, na=False) |
             self.risk_templates['contract_type'].str.contains('通用', case=False, na=False)) &
            (self.risk_templates['clause_name'].str.contains(clause_type, case=False, na=False) |
             self.risk_templates['clause_name'].str.contains('通用', case=False, na=False))
        ]

        for _, risk_template in relevant_risks.iterrows():
            if not self.config.should_report_risk(risk_template['risk_type']):
                continue

            risk_keywords = str(risk_template['risk_description']).split('、')[:3]
            matched_keywords = sum(1 for kw in risk_keywords if kw in clause_text)

            if matched_keywords < len(risk_keywords) / 2:
                label = risk_template.get('risk_label', self.assign_risk_label(
                    risk_template.get('risk_description', ''), clause_type))

                risks.append({
                    'risk_id': risk_template['risk_id'],
                    'risk_type': risk_template['risk_type'],
                    'description': risk_template['risk_description'],
                    'legal_basis': risk_template['legal_basis'],
                    'suggestion': risk_template['modification_suggestion'],
                    'impact': risk_template['impact_analysis'],
                    'risk_label': label,
                    'risk_dimension': risk_template.get('risk_dimension', '违约责任'),
                    'default_revision_method': risk_template.get('default_revision_method', 'comment'),
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
        """生成风险报告（含标签分布和雷达图数据）"""
        risk_by_level = {'致命风险': [], '重要风险': [], '一般风险': [], '轻微瑕疵': []}
        for risk in all_risks:
            level = risk.get('risk_type', '一般风险')
            if level in risk_by_level:
                risk_by_level[level].append(risk)

        risk_summary = {level: len(risks) for level, risks in risk_by_level.items()}

        return {
            'summary': risk_summary,
            'risks_by_level': risk_by_level,
            'total_risks': len(all_risks),
            'label_distribution': self._label_distribution(all_risks),
            'radar_data': self.generate_radar_data(all_risks),
        }

    # ============ 六维度评价 ============

    def evaluate_risk_dimensions(self, risk: Dict) -> Dict:
        """对单个风险生成六维度评价框架"""
        label = risk.get('risk_label', '违约责任')
        severity = risk.get('risk_type', '重要风险')

        severity_prob = {'致命风险': '高', '重要风险': '中高', '一般风险': '中', '轻微瑕疵': '低'}

        return {
            '风险定性': f"{label}",
            '风险敞口': self._estimate_exposure(risk),
            '发生概率': severity_prob.get(severity, '中'),
            '可规避性': '可规避' if label not in ('合同效力', '格式条款') else '需结构性调整',
            '商业权衡': '待客户评估',
            '紧迫性': '立即处理' if severity == '致命风险' else ('近期处理' if severity == '重要风险' else '持续观察'),
        }

    def _estimate_exposure(self, risk: Dict) -> str:
        """估算风险敞口"""
        desc = risk.get('description', '')
        if any(kw in desc for kw in ('无效', '不成立')):
            return '合同效力风险：合同整体可能不生效'
        if any(kw in desc for kw in ('违约金', '赔偿')):
            return '经济损失：取决于违约金计算和实际损失'
        if '全部' in desc:
            return '重大损失：可能涉及项目整体'
        return '待量化'

    # ============ 风险标签 ============

    def assign_risk_label(self, risk_description: str, clause_type: str) -> str:
        """自动匹配 15 标签体系"""
        rd = risk_description
        if any(kw in rd for kw in ("无效","不成立","违法","强制性","挂靠","无资质","权属不清")):
            return "合同效力"
        if any(kw in rd for kw in ("格式条款","免责","排除","提示说明")): return "格式条款"
        if any(kw in rd for kw in ("主体","资质","授权","签字","盖章","印章")): return "主体授权"
        if any(kw in rd for kw in ("关联","输送")): return "关联交易"
        if any(kw in rd for kw in ("社保","工资","合规","行政","监管","反商业贿赂")): return "合规审查"
        if any(kw in rd for kw in ("价款","付款","支付","报酬","费用","含税","利率","租金","补偿金")):
            return "价款与支付"
        if any(kw in rd for kw in ("交付","验收","标准不明确","质量标准")): return "交付与验收"
        if any(kw in rd for kw in ("违约","违约金","违约方","赔偿")): return "违约责任"
        if any(kw in rd for kw in ("解除","终止","回购","撤销")): return "解除与终止"
        if any(kw in rd for kw in ("担保","抵押","质押","保证","保险","增信","优先受偿")): return "担保与增信"
        if any(kw in rd for kw in ("管辖","仲裁","诉讼","送达")): return "争议解决"
        if any(kw in rd for kw in ("知识产权","保密","归属","技术成果","竞业")): return "知识产权与保密"
        if any(kw in rd for kw in ("定义","附件")): return "定义与附件"
        if any(kw in rd for kw in ("不一致","矛盾","冲突")): return "文本一致性"
        if any(kw in rd for kw in ("错别字","标点","格式","大小写")): return "文字与格式"
        return "违约责任"

    # ============ 雷达图数据 ============

    def generate_radar_data(self, risks: List[Dict]) -> Dict[str, float]:
        """生成 8 维度雷达图数据（1-5 分）"""
        dim_scores = {d: 1.0 for d in self.RADAR_DIMENSIONS}
        dim_risks = {d: [] for d in self.RADAR_DIMENSIONS}

        # 按维度分组
        for risk in risks:
            dim = risk.get('risk_dimension', '违约责任')
            if dim in dim_risks:
                dim_risks[dim].append(risk)

        # 计算每个维度分数：风险越多/越高，分数越高（意味着问题越大）
        level_weights = {'致命风险': 1.0, '重要风险': 0.7, '一般风险': 0.4, '轻微瑕疵': 0.2}
        for dim, dim_risk_list in dim_risks.items():
            if not dim_risk_list:
                dim_scores[dim] = 1.0  # 无风险 = 最低分（最好状态）
                continue
            weighted = sum(level_weights.get(r.get('risk_type', '一般风险'), 0.4) for r in dim_risk_list)
            # 映射到 1-5 分：1=良好，5=严重
            score = 1 + min(weighted * 1.5, 4)
            dim_scores[dim] = round(score, 1)

        return dim_scores

    def _label_distribution(self, risks: List[Dict]) -> Dict[str, int]:
        """按风险标签统计分布"""
        dist = {}
        for risk in risks:
            label = risk.get('risk_label', '违约责任')
            dist[label] = dist.get(label, 0) + 1
        return dist
