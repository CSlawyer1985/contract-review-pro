"""
为8种新合同类型生成风险点模板
"""

# 8种新合同类型及其风险点
new_contract_risks = [
    # 赠与合同
    {
        'risk_id': 'R079',
        'risk_type': '重要风险',
        'contract_type': '赠与合同',
        'clause_name': '赠与意思表示',
        'risk_description': '赠与是否为真实意思表示不明确，可能存在虚假赠与',
        'legal_basis': '民法典第657条',
        'modification_suggestion': '明确赠与为真实意思表示，可约定公证手续',
        'impact_analysis': '可能导致赠与合同无效或被撤销'
    },
    {
        'risk_id': 'R080',
        'risk_type': '致命风险',
        'contract_type': '赠与合同',
        'clause_name': '赠与物权属',
        'risk_description': '赠与物权的权属不清',
        'legal_basis': '民法典第657条',
        'modification_suggestion': '核实赠与物权的权属，确保赠与人有权处分',
        'impact_analysis': '可能导致赠与合同无法履行'
    },
    {
        'risk_id': 'R081',
        'risk_type': '重要风险',
        'contract_type': '赠与合同',
        'clause_name': '撤销权',
        'risk_description': '赠与人撤销权未约定或约定不明',
        'legal_basis': '民法典第663-666条',
        'modification_suggestion': '明确赠与人撤销权的行使条件和期限',
        'impact_analysis': '受赠人可能面临赠与人行使撤销权的风险'
    },
    {
        'risk_id': 'R082',
        'risk_type': '重要风险',
        'contract_type': '赠与合同',
        'clause_name': '瑕疵担保',
        'risk_description': '赠与物瑕疵担保责任未约定',
        'legal_basis': '民法典第662条',
        'modification_suggestion': '约定赠与物的瑕疵担保责任',
        'impact_analysis': '受赠人可能无法获得救济'
    },

    # 劳务派遣合同
    {
        'risk_id': 'R083',
        'risk_type': '致命风险',
        'contract_type': '劳务派遣合同',
        'clause_name': '派遣资质',
        'risk_description': '派遣单位无劳务派遣许可',
        'legal_basis': '劳动合同法第57条、劳务派遣暂行规定',
        'modification_suggestion': '核实派遣单位是否有劳务派遣许可',
        'impact_analysis': '劳务派遣协议无效，可能面临行政处罚'
    },
    {
        'risk_id': 'R084',
        'risk_type': '重要风险',
        'contract_type': '劳务派遣合同',
        'clause_name': '岗位性质',
        'risk_description': '派遣岗位不符合临时性、辅助性、替代性要求',
        'legal_basis': '劳动合同法第66条、劳务派遣暂行规定',
        'modification_suggestion': '确保派遣岗位为临时性、辅助性、替代性岗位',
        'impact_analysis': '可能被认定为违法派遣'
    },
    {
        'risk_id': 'R085',
        'risk_type': '重要风险',
        'contract_type': '劳务派遣合同',
        'clause_name': '劳动报酬',
        'risk_description': '同工不同酬，劳动报酬约定不明',
        'legal_basis': '劳动合同法第63条、劳务派遣暂行规定',
        'modification_suggestion': '明确劳动报酬分配和支付方式，确保同工同酬',
        'impact_analysis': '可能面临劳动争议'
    },
    {
        'risk_id': 'R086',
        'risk_type': '重要风险',
        'contract_type': '劳务派遣合同',
        'clause_name': '工伤责任',
        'risk_description': '工伤责任承担不明确',
        'legal_basis': '劳务派遣暂行规定',
        'modification_suggestion': '明确工伤责任的承担方和赔偿方式',
        'impact_analysis': '发生工伤时责任不清'
    },

    # 竞业限制协议
    {
        'risk_id': 'R087',
        'risk_type': '致命风险',
        'contract_type': '竞业限制协议',
        'clause_name': '限制范围',
        'risk_description': '竞业限制范围过宽，可能无效',
        'legal_basis': '劳动合同法第24条、竞业限制司法解释',
        'modification_suggestion': '合理界定竞业限制的地域和行业范围',
        'impact_analysis': '竞业限制条款可能被法院认定无效'
    },
    {
        'risk_id': 'R088',
        'risk_type': '重要风险',
        'contract_type': '竞业限制协议',
        'clause_name': '限制期限',
        'risk_description': '竞业限制期限超过2年',
        'legal_basis': '劳动合同法第24条',
        'modification_suggestion': '竞业限制期限不得超过2年',
        'impact_analysis': '超过部分无效'
    },
    {
        'risk_id': 'R089',
        'risk_type': '重要风险',
        'contract_type': '竞业限制协议',
        'clause_name': '补偿金',
        'risk_description': '竞业限制补偿金未约定或低于法定标准',
        'legal_basis': '劳动合同法第23条',
        'modification_suggestion': '明确补偿金，不低于离职前12个月平均工资的30%',
        'impact_analysis': '竞业限制协议可能无效，劳动者无需遵守'
    },

    # 增资扩股协议
    {
        'risk_id': 'R090',
        'risk_type': '重要风险',
        'contract_type': '增资扩股协议',
        'clause_name': '增资方式',
        'risk_description': '增资方式（定向/公开）不明确',
        'legal_basis': '公司法、证券法',
        'modification_suggestion': '明确增资方式，遵守法律法规要求',
        'impact_analysis': '可能违反公司法或证券法规定'
    },
    {
        'risk_id': 'R091',
        'risk_type': '重要风险',
        'contract_type': '增资扩股协议',
        'clause_name': '估值方法',
        'risk_description': '公司估值方法不明确或公允',
        'legal_basis': '公司法、国有资产评估管理办法',
        'modification_suggestion': '明确估值方法（市净率、PE、PB等），涉及国有资产需评估',
        'impact_analysis': '估值争议，可能影响股权比例'
    },
    {
        'risk_id': 'R092',
        'risk_type': '重要风险',
        'contract_type': '增资扩股协议',
        'clause_name': '优先认购权',
        'risk_description': '未明确原股东的优先认购权',
        'legal_basis': '公司法第34条',
        'modification_suggestion': '明确原股东的优先认购权及行使程序',
        'impact_analysis': '可能损害原股东权益'
    },

    # 对赌协议
    {
        'risk_id': 'R093',
        'risk_type': '致命风险',
        'contract_type': '对赌协议',
        'clause_name': '协议效力',
        'risk_description': '对赌协议可能违反法律、行政法规的强制性规定',
        'legal_basis': '九民纪要、公司法、合同法',
        'modification_suggestion': '确保对赌协议内容合法，不违反法律强制性规定',
        'impact_analysis': '对赌协议可能无效，无法执行'
    },
    {
        'risk_id': 'R094',
        'risk_type': '重要风险',
        'contract_type': '对赌协议',
        'clause_name': '业绩目标',
        'risk_description': '业绩目标不明确或不可量化',
        'legal_basis': '九民纪要',
        'modification_suggestion': '设定明确、可量化的业绩目标（净利润、营收、用户数等）',
        'impact_analysis': '触发条件不明确，无法执行'
    },
    {
        'risk_id': 'R095',
        'risk_type': '重要风险',
        'contract_type': '对赌协议',
        'clause_name': '估值调整',
        'risk_description': '估值调整机制不清晰',
        'legal_basis': '九民纪要',
        'modification_suggestion': '明确估值调整的具体计算公式和方法',
        'impact_analysis': '估值调整时产生争议'
    },
    {
        'risk_id': 'R096',
        'risk_type': '重要风险',
        'contract_type': '对赌协议',
        'clause_name': '股权回购',
        'risk_description': '股权回购条件、价格不明确',
        'legal_basis': '九民纪要',
        'modification_suggestion': '明确回购触发条件、回购价格计算方式',
        'impact_analysis': '回购时产生争议'
    },

    # 一致行动协议
    {
        'risk_id': 'R097',
        'risk_type': '重要风险',
        'contract_type': '一致行动协议',
        'clause_name': '一致行动范围',
        'risk_description': '一致行动范围不明确或过宽',
        'legal_basis': '公司法、公司章程',
        'modification_suggestion': '明确一致行动的范围（提案权、表决权等）',
        'impact_analysis': '行动范围不清，执行困难'
    },
    {
        'risk_id': 'R098',
        'risk_type': '重要风险',
        'contract_type': '一致行动协议',
        'clause_name': '表决权委托',
        'risk_description': '表决权委托期限过长或范围过大',
        'legal_basis': '公司法',
        'modification_suggestion': '合理约定表决权委托的期限和范围',
        'impact_analysis': '可能损害股东独立性'
    },
    {
        'risk_id': 'R099',
        'risk_type': '一般风险',
        'contract_type': '一致行动协议',
        'clause_name': '违约责任',
        'risk_description': '违约责任过重或过轻',
        'legal_basis': '合同编、公司法',
        'modification_suggestion': '合理约定违约责任，平衡各方利益',
        'impact_analysis': '违约责任不合理可能被法院调整'
    },

    # 技术转让合同
    {
        'risk_id': 'R100',
        'risk_type': '重要风险',
        'contract_type': '技术转让合同',
        'clause_name': '技术内容',
        'risk_description': '技术内容不明确、不具体',
        'legal_basis': '民法典合同编第20章',
        'modification_suggestion': '明确技术内容、技术指标、验收标准',
        'impact_analysis': '技术内容不清，交付标准不明'
    },
    {
        'risk_id': 'R101',
        'risk_type': '重要风险',
        'contract_type': '技术转让合同',
        'clause_name': '使用权限',
        'risk_description': '使用权限不明确（独占/排他/普通）',
        'legal_basis': '民法典合同编第20章、专利法',
        'modification_suggestion': '明确技术使用权限类型、地域、期限',
        'impact_analysis': '使用权限不清，可能侵犯第三方权利'
    },
    {
        'risk_id': 'R102',
        'risk_type': '重要风险',
        'contract_type': '技术转让合同',
        'clause_name': '后续改进',
        'risk_description': '后续改进的归属约定不明',
        'legal_basis': '民法典合同编第20章、专利法',
        'modification_suggestion': '明确后续技术改进的知识产权归属',
        'impact_analysis': '后续改进归属争议'
    },
    {
        'risk_id': 'R103',
        'risk_type': '重要风险',
        'contract_type': '技术转让合同',
        'clause_name': '知识产权',
        'risk_description': '可能侵犯第三方知识产权',
        'legal_basis': '专利法、技术合同法',
        'modification_suggestion': '让与人保证拥有完整知识产权，约定侵权责任承担',
        'impact_analysis': '可能面临第三方侵权诉讼'
    },

    # 保险合同
    {
        'risk_id': 'R104',
        'risk_type': '致命风险',
        'contract_type': '保险合同',
        'clause_name': '保险标的',
        'risk_description': '保险标的不具有保险利益',
        'legal_basis': '保险法第12条',
        'modification_suggestion': '核实被保险人对保险标的具有保险利益',
        'impact_analysis': '保险合同无效'
    },
    {
        'risk_id': 'R105',
        'risk_type': '重要风险',
        'contract_type': '保险合同',
        'clause_name': '免责条款',
        'risk_description': '免责条款未明确提示或过宽',
        '法律_basis': '保险法第17条',
        'modification_suggestion': '明确免责条款，以显著方式提示投保人',
        'impact_analysis': '免责条款可能无效'
    },
    {
        'risk_id': 'R106',
        'risk_id': 'R106',
        'risk_type': '重要风险',
        'contract_type': '保险合同',
        'clause_name': '如实告知义务',
        'risk_description': '投保人如实告知义务约定不明',
        'legal_basis': '保险法第16条',
        'modification_suggestion': '明确投保人如实告知义务的范围和后果',
        'impact_analysis': '未如实告知可能导致保险人解除合同'
    },
    {
        'risk_id': 'R107',
        'risk_type': '一般风险',
        'contract_type': '保险合同',
        'clause_name': '理赔程序',
        'risk_description': '理赔程序不清晰',
        'legal_basis': '保险法',
        'modification_suggestion': '明确理赔条件、程序、时限',
        'impact_analysis': '理赔时产生争议'
    },
]

# 输出为CSV格式
import csv

output_file = '/Users/CS/Trae/Claude/.trae/skills/contract-review-pro/data/risk_templates_new.csv'

with open(output_file, 'w', encoding='utf-8', newline='') as f:
    fieldnames = ['risk_id', 'risk_type', 'contract_type', 'clause_name',
                   'risk_description', 'legal_basis', 'modification_suggestion', 'impact_analysis']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(new_contract_risks)

print(f"✅ 已生成 {len(new_contract_risks)} 个新风险点模板")
print(f"📄 文件位置: {output_file}")
print("\n风险点分布:")
for i, risk in enumerate(new_contract_risks, 1):
    print(f"{i}. [{risk['contract_type']}] {risk['risk_description'][:50]}...")
