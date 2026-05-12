#!/usr/bin/env python3
"""
代码规范检查技能主入口
"""

import sys
import os
from lib.code_standard_checker import CodeStandardChecker


def run_check(file_path):
    """
    运行代码规范检查
    
    Args:
        file_path: 要检查的文件路径
    """
    # 验证文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        return
    
    # 创建检查器实例
    checker = CodeStandardChecker()
    
    # 加载代码文件
    if not checker.load_code(file_path):
        print(f"错误: 无法加载文件 - {file_path}")
        return
    
    # 运行检查
    results = checker.run_check()
    
    # 输出检查报告
    print("# 代码规范检查报告")
    print()
    print("## 文件信息")
    print(f"- 文件路径：{results['file_path']}")
    print(f"- 语言类型：{results['language']}")
    print(f"- 检查时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("## 总体评分")
    print(f"{results['level']} - {results['overall_score']}/100")
    print()
    
    if results['issues']:
        print("## 问题汇总")
        print("| 序号 | 问题类型 | 严重程度 | 位置 | 问题描述 | 改进建议 |")
        print("|------|----------|----------|------|----------|----------|")
        
        for idx, issue in enumerate(results['issues'], 1):
            print(f"| {idx} | {issue['type']} | {issue['severity']} | 第{issue['line']}行 | {issue['description']} | {issue['recommendation']} |")
        
        print()
        print("## 详细分析")
        print()
        
        # 按类型分组显示问题
        issue_types = {}
        for issue in results['issues']:
            issue_type = issue['type']
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)
        
        for issue_type, issues in issue_types.items():
            print(f"### {issue_type}检查")
            print(f"- [{'x'}] {issue_type} ({len(issues)}个问题)")
            print()
    else:
        print("## 检查结果")
        print("恭喜！未发现任何问题，您的代码符合规范要求。")
        print()


def main():
    """
    主函数
    """
    if len(sys.argv) < 2:
        print("用法: python main.py <file_path>")
        print("示例: python main.py ./src/main/java/com/example/UserService.java")
        sys.exit(1)
    
    file_path = sys.argv[1]
    run_check(file_path)


if __name__ == "__main__":
    main()