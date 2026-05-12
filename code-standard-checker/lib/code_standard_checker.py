#!/usr/bin/env python3
"""
代码规范检查器
用于检查多种编程语言的代码是否符合项目规范和最佳实践
"""

import re
import sys
import json
from typing import Dict, List, Tuple, Optional


class CodeStandardChecker:
    """
    代码规范检查器类
    支持多种编程语言的代码规范检查
    """
    
    def __init__(self):
        self.check_results = []
        self.file_path = ""
        self.code_lines = []
        
    def load_code(self, file_path: str) -> bool:
        """
        加载代码文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否成功加载文件
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.code_lines = content.splitlines()
                self.file_path = file_path
                return True
        except Exception as e:
            print(f"Error loading file {file_path}: {str(e)}")
            return False
    
    def detect_language(self) -> str:
        """
        检测编程语言类型
        
        Returns:
            str: 编程语言类型
        """
        if self.file_path.endswith('.java'):
            return 'java'
        elif self.file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
            return 'javascript'
        elif self.file_path.endswith('.py'):
            return 'python'
        elif self.file_path.endswith(('.html', '.htm')):
            return 'html'
        elif self.file_path.endswith('.css'):
            return 'css'
        else:
            return 'unknown'
    
    def check_naming_conventions(self, language: str) -> List[Dict]:
        """
        检查命名规范
        
        Args:
            language: 编程语言类型
            
        Returns:
            List[Dict]: 发现的问题列表
        """
        issues = []
        
        for i, line in enumerate(self.code_lines, 1):
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith(('/*', '*', '//', '/*')):
                continue
            
            # 检查类名是否符合UpperCamelCase
            if language == 'java':
                # 检查类声明
                class_match = re.search(r'class\s+([A-Za-z0-9_]+)', line)
                if class_match:
                    class_name = class_match.group(1)
                    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', class_name):
                        issues.append({
                            'line': i,
                            'type': '命名规范',
                            'severity': '高',
                            'description': f'类名 "{class_name}" 不符合UpperCamelCase规范',
                            'recommendation': f'类名应该以大写字母开头，如 "{class_name.capitalize()}"'
                        })
                
                # 检查接口声明
                interface_match = re.search(r'interface\s+([A-Za-z0-9_]+)', line)
                if interface_match:
                    interface_name = interface_match.group(1)
                    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', interface_name):
                        issues.append({
                            'line': i,
                            'type': '命名规范',
                            'severity': '高',
                            'description': f'接口名 "{interface_name}" 不符合UpperCamelCase规范',
                            'recommendation': f'接口名应该以大写字母开头，如 "{interface_name.capitalize()}"'
                        })
                
                # 检查枚举声明
                enum_match = re.search(r'enum\s+([A-Za-z0-9_]+)', line)
                if enum_match:
                    enum_name = enum_match.group(1)
                    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', enum_name):
                        issues.append({
                            'line': i,
                            'type': '命名规范',
                            'severity': '高',
                            'description': f'枚举名 "{enum_name}" 不符合UpperCamelCase规范',
                            'recommendation': f'枚举名应该以大写字母开头，如 "{enum_name.capitalize()}"'
                        })
                
                # 检查方法名是否符合lowerCamelCase
                method_match = re.search(r'(?:public|private|protected)?\s*(?:static)?\s+\w+\s+([a-z][A-Za-z0-9_]*)\s*\(', line)
                if method_match:
                    method_name = method_match.group(1)
                    if not re.match(r'^[a-z][a-zA-Z0-9]*$', method_name):
                        issues.append({
                            'line': i,
                            'type': '命名规范',
                            'severity': '中',
                            'description': f'方法名 "{method_name}" 不符合lowerCamelCase规范',
                            'recommendation': f'方法名应该以小写字母开头，如 "{method_name.lower()}"'
                        })
                
                # 检查常量名是否符合UPPER_SNAKE_CASE
                const_match = re.search(r'static\s+final\s+\w+\s+([A-Za-z0-9_]+)', line)
                if const_match:
                    const_name = const_match.group(1)
                    if not re.match(r'^[A-Z][A-Z0-9_]*$', const_name):
                        issues.append({
                            'line': i,
                            'type': '命名规范',
                            'severity': '中',
                            'description': f'常量名 "{const_name}" 不符合UPPER_SNAKE_CASE规范',
                            'recommendation': f'常量名应该全部大写并用下划线分隔，如 "{const_name.upper()}"'
                        })
                
                # 检查变量名是否符合lowerCamelCase
                var_match = re.search(r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s+\w+\s+([a-z][A-Za-z0-9_]*)\s*=\s*', line)
                if var_match:
                    var_name = var_match.group(1)
                    if not re.match(r'^[a-z][a-zA-Z0-9]*$', var_name):
                        issues.append({
                            'line': i,
                            'type': '命名规范',
                            'severity': '中',
                            'description': f'变量名 "{var_name}" 不符合lowerCamelCase规范',
                            'recommendation': f'变量名应该以小写字母开头，如 "{var_name.lower()}"'
                        })
            elif language == 'javascript':
                # 检查函数名
                func_match = re.search(r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)', line)
                if func_match:
                    func_name = func_match.group(1)
                    if not re.match(r'^[a-z][a-zA-Z0-9]*$', func_name):
                        issues.append({
                            'line': i,
                            'type': '命名规范',
                            'severity': '中',
                            'description': f'函数名 "{func_name}" 不符合camelCase规范',
                            'recommendation': f'函数名应该以小写字母开头，如 "{func_name.lower()}"'
                        })
                
                # 检查变量声明
                let_var_match = re.search(r'(let|const|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)', line)
                if let_var_match:
                    var_name = let_var_match.group(2)
                    if not re.match(r'^[a-z][a-zA-Z0-9]*$', var_name):
                        issues.append({
                            'line': i,
                            'type': '命名规范',
                            'severity': '中',
                            'description': f'变量名 "{var_name}" 不符合camelCase规范',
                            'recommendation': f'变量名应该以小写字母开头，如 "{var_name.lower()}"'
                        })
            elif language == 'python':
                # 检查类名
                py_class_match = re.search(r'class\s+([A-Za-z0-9_]+)', line)
                if py_class_match:
                    class_name = py_class_match.group(1)
                    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', class_name):
                        issues.append({
                            'line': i,
                            'type': '命名规范',
                            'severity': '中',
                            'description': f'类名 "{class_name}" 不符合CapWords规范',
                            'recommendation': f'类名应该以大写字母开头，如 "{class_name.capitalize()}"'
                        })
                
                # 检查函数名
                py_func_match = re.search(r'def\s+([a-z_][a-z0-9_]*)', line)
                if py_func_match:
                    func_name = py_func_match.group(1)
                    if not re.match(r'^[a-z_][a-z0-9_]*$', func_name):
                        issues.append({
                            'line': i,
                            'type': '命名规范',
                            'severity': '中',
                            'description': f'函数名 "{func_name}" 不符合snake_case规范',
                            'recommendation': f'函数名应该使用下划线分隔小写字母，如 "{func_name.lower()}"'
                        })
                
                # 检查常量
                py_const_match = re.search(r'([A-Z][A-Z0-9_]*)\s+=\s+', line)
                if py_const_match:
                    const_name = py_const_match.group(1)
                    if not re.match(r'^[A-Z][A-Z0-9_]*$', const_name):
                        issues.append({
                            'line': i,
                            'type': '命名规范',
                            'severity': '中',
                            'description': f'常量名 "{const_name}" 不符合UPPER_CASE规范',
                            'recommendation': f'常量名应该全部大写并用下划线分隔，如 "{const_name.upper()}"'
                        })
        
        return issues
    
    def check_comment_standards(self, language: str) -> List[Dict]:
        """
        检查注释规范
        
        Args:
            language: 编程语言类型
            
        Returns:
            List[Dict]: 发现的问题列表
        """
        issues = []
        in_multiline_comment = False
        multiline_comment_started = False
        
        for i, line in enumerate(self.code_lines, 1):
            stripped_line = line.strip()
            
            # 检查是否有行尾注释
            if language in ['java', 'javascript']:
                # 检查Java和JavaScript的行尾注释
                if '//' in stripped_line and not stripped_line.startswith('//'):
                    parts = stripped_line.split('//', 1)
                    code_part = parts[0]
                    comment_part = parts[1]
                    
                    # 如果代码部分不为空，且注释不是在字符串内，则认为是行尾注释
                    if code_part and not self._is_in_string(stripped_line, '//'):
                        issues.append({
                            'line': i,
                            'type': '注释规范',
                            'severity': '中',
                            'description': f'第{i}行存在行尾注释',
                            'recommendation': '将注释移到单独的行上，便于阅读和维护'
                        })
            elif language == 'python':
                # 检查Python的行尾注释
                if '#' in stripped_line and not stripped_line.startswith('#'):
                    parts = stripped_line.split('#', 1)
                    code_part = parts[0]
                    comment_part = parts[1]
                    
                    # 如果代码部分不为空，且注释不是在字符串内，则认为是行尾注释
                    if code_part and not self._is_in_string(stripped_line, '#'):
                        issues.append({
                            'line': i,
                            'type': '注释规范',
                            'severity': '中',
                            'description': f'第{i}行存在行尾注释',
                            'recommendation': '将注释移到单独的行上，便于阅读和维护'
                        })
        
        # 检查类和方法注释是否完整
        if language == 'java':
            for i, line in enumerate(self.code_lines, 1):
                # 检查类定义是否有注释
                if re.search(r'public\s+class\s+|class\s+', line):
                    # 向前查找是否有Javadoc注释
                    has_javadoc = False
                    for j in range(max(0, i-5), i):
                        if j < len(self.code_lines) and ('/**' in self.code_lines[j] or '@see' in self.code_lines[j] or '@param' in self.code_lines[j]):
                            has_javadoc = True
                            break
                    if not has_javadoc:
                        issues.append({
                            'line': i,
                            'type': '注释规范',
                            'severity': '中',
                            'description': f'第{i}行的类定义缺少Javadoc注释',
                            'recommendation': '为类添加Javadoc注释，说明类的功能、作者、日期等信息'
                        })
                
                # 检查公共方法是否有注释
                if re.search(r'public\s+\w+\s+\w+\s*\(', line):
                    # 向前查找是否有Javadoc注释
                    has_javadoc = False
                    for j in range(max(0, i-3), i):
                        if j < len(self.code_lines) and ('/**' in self.code_lines[j] or '@see' in self.code_lines[j] or '@param' in self.code_lines[j] or '@return' in self.code_lines[j]):
                            has_javadoc = True
                            break
                    if not has_javadoc:
                        issues.append({
                            'line': i,
                            'type': '注释规范',
                            'severity': '中',
                            'description': f'第{i}行的公共方法缺少Javadoc注释',
                            'recommendation': '为公共方法添加Javadoc注释，说明参数、返回值和异常等信息'
                        })
        
        return issues
    
    def _is_in_string(self, code_line: str, comment_symbol: str) -> bool:
        """
        检查代码行中的注释是否在字符串内部
            
        Args:
            code_line: 代码行
            comment_symbol: 注释符号（如'//'或'#'）
                
        Returns:
            bool: 是否在字符串内
        """
        # 分割代码行为注释前和注释后的部分
        parts = code_line.split(comment_symbol, 1)
        if len(parts) < 2:
            return False
            
        code_part = parts[0]
            
        # 检查代码部分是否在字符串内
        in_single_quote_str = False
        in_double_quote_str = False
        i = 0
        while i < len(code_part):
            char = code_part[i]
            if char == '"' and (i == 0 or code_part[i-1] != '\\\\'):
                in_double_quote_str = not in_double_quote_str
            elif char == "'" and (i == 0 or code_part[i-1] != '\\\\'):
                in_single_quote_str = not in_single_quote_str
            i += 1
            
        return in_single_quote_str or in_double_quote_str
    
    def check_security_issues(self, language: str) -> List[Dict]:
        """
        检查安全问题
            
        Args:
            language: 编程语言类型
                
        Returns:
            List[Dict]: 发现的问题列表
        """
        issues = []
            
        for i, line in enumerate(self.code_lines, 1):
            # 检查SQL注入风险
            if re.search(r'\bexecuteQuery\b|\bexecuteUpdate\b|SELECT|INSERT|UPDATE|DELETE', line, re.IGNORECASE) and '?' not in line and 'WHERE' in line:
                issues.append({
                    'line': i,
                    'type': '安全问题',
                    'severity': '高',
                    'description': f'第{i}行可能存在SQL注入风险',
                    'recommendation': '使用PreparedStatement替代字符串拼接，防止SQL注入'
                })
                
            # 检查硬编码密码
            if re.search(r'password|pwd|pass', line, re.IGNORECASE) and '=' in line:
                if re.search(r'[\'\"][^\'\"]*[\'\"]', line):  # 检查是否是字符串赋值
                    issues.append({
                        'line': i,
                        'type': '安全问题',
                        'severity': '高',
                        'description': f'第{i}行可能存在硬编码密码',
                        'recommendation': '将敏感信息存储在配置文件中，不要硬编码在代码中'
                    })
                
            # 检查硬编码API密钥
            if re.search(r'api[_\-]?key|secret|token', line, re.IGNORECASE) and '=' in line:
                if re.search(r'[\'\"][^\'\"]*[\'\"]', line):
                    issues.append({
                        'line': i,
                        'type': '安全问题',
                        'severity': '高',
                        'description': f'第{i}行可能存在硬编码API密钥或令牌',
                        'recommendation': '将敏感信息存储在配置文件或环境变量中，不要硬编码在代码中'
                    })
                
            # 检查未经验证的重定向
            if re.search(r'Response\.sendRedirect|redirect\(', line):
                issues.append({
                    'line': i,
                    'type': '安全问题',
                    'severity': '中',
                    'description': f'第{i}行可能存在未经验证的重定向漏洞',
                    'recommendation': '验证重定向目标URL的安全性，避免开放重定向漏洞'
                })
                
            # 检查跨站脚本(XSS)风险
            if language == 'java':
                if re.search(r'getParameter\(', line) and (re.search(r'println|write', line) or any(re.search(r'println|write', l) for l in self.code_lines[max(0, i-3):i])):
                    issues.append({
                        'line': i,
                        'type': '安全问题',
                        'severity': '高',
                        'description': f'第{i}行可能存在跨站脚本(XSS)风险',
                        'recommendation': '对用户输入进行适当的转义和验证，防止XSS攻击'
                    })
            elif language == 'javascript':
                if re.search(r'document\.write|innerHTML', line) and (re.search(r'location|params|query', line) or any(re.search(r'location|params|query', l) for l in self.code_lines[max(0, i-3):i])):
                    issues.append({
                        'line': i,
                        'type': '安全问题',
                        'severity': '高',
                        'description': f'第{i}行可能存在跨站脚本(XSS)风险',
                        'recommendation': '对用户输入进行适当的转义和验证，防止XSS攻击'
                    })
            
        return issues
    
    def check_performance_issues(self, language: str) -> List[Dict]:
        """
        检查性能问题
        
        Args:
            language: 编程语言类型
            
        Returns:
            List[Dict]: 发现的问题列表
        """
        issues = []
        
        for i, line in enumerate(self.code_lines, 1):
            # 检查循环中的数据库操作
            if re.search(r'for\s*\(.*\)|while\s*\(.*\)|\.forEach\(|\.stream\(\)', line):
                # 查找接下来几行是否有数据库操作
                for j in range(i, min(i+15, len(self.code_lines))):
                    if re.search(r'\.find\(|\.save\(|\.query\(|executeQuery|executeUpdate|\.get\(\)', self.code_lines[j]):
                        issues.append({
                            'line': j,
                            'type': '性能问题',
                            'severity': '中',
                            'description': f'第{j}行在循环中执行数据库操作可能影响性能',
                            'recommendation': '考虑批量操作或预加载数据以提高性能'
                        })
                        break
            
            # 检查可能的内存泄漏
            if language == 'java':
                if re.search(r'StringBuilder', line) and not re.search(r'new StringBuilder\(\d+\)', line):
                    # 检查StringBuilder是否指定了初始容量
                    issues.append({
                        'line': i,
                        'type': '性能问题',
                        'severity': '低',
                        'description': f'第{i}行StringBuilder未指定初始容量可能影响性能',
                        'recommendation': '为StringBuilder指定初始容量以避免多次扩容'
                    })
                
                # 检查集合初始化未指定大小
                if re.search(r'new ArrayList<>|new HashMap<>|new HashSet<>', line):
                    issues.append({
                        'line': i,
                        'type': '性能问题',
                        'severity': '低',
                        'description': f'第{i}行集合初始化未指定初始大小可能影响性能',
                        'recommendation': '为集合指定预期的初始大小以避免多次扩容'
                    })
            
            # 检查不必要的字符串操作
            if language in ['java', 'javascript']:
                if re.search(r'"\s*\+\s*"', line) or re.search(r"'\s*\+\s*'", line):
                    issues.append({
                        'line': i,
                        'type': '性能问题',
                        'severity': '中',
                        'description': f'第{i}行存在不必要的字符串拼接操作',
                        'recommendation': '考虑使用模板字符串或字符串构建器来提高性能'
                    })
            
            # 检查未使用的导入或变量
            if re.search(r'import\s+', line):
                # 这里只是标记可能的未使用导入，实际检测需要更复杂的分析
                pass
        
        return issues
    
    def run_check(self) -> Dict:
        """
        运行完整的代码规范检查
        
        Returns:
            Dict: 检查结果
        """
        if not self.code_lines:
            return {'error': '没有加载任何代码文件'}
        
        language = self.detect_language()
        all_issues = []
        
        # 执行各项检查
        all_issues.extend(self.check_naming_conventions(language))
        all_issues.extend(self.check_comment_standards(language))
        all_issues.extend(self.check_security_issues(language))
        all_issues.extend(self.check_performance_issues(language))
        
        # 计算总体评分
        severity_score_map = {'高': 10, '中': 5, '低': 2}
        total_deduction = sum(severity_score_map.get(issue['severity'], 2) for issue in all_issues)
        score = max(0, 100 - total_deduction)
        
        if score >= 90:
            level = '优秀'
        elif score >= 75:
            level = '良好'
        elif score >= 60:
            level = '一般'
        else:
            level = '需改进'
        
        return {
            'file_path': self.file_path,
            'language': language,
            'overall_score': score,
            'level': level,
            'issues': all_issues,
            'issue_summary': self._generate_issue_summary(all_issues)
        }
    
    def _generate_issue_summary(self, issues: List[Dict]) -> Dict:
        """
        生成问题摘要
        
        Args:
            issues: 问题列表
            
        Returns:
            Dict: 问题摘要
        """
        summary = {
            'total_issues': len(issues),
            'high_severity': len([i for i in issues if i['severity'] == '高']),
            'medium_severity': len([i for i in issues if i['severity'] == '中']),
            'low_severity': len([i for i in issues if i['severity'] == '低'])
        }
        return summary


def main():
    """
    主函数，处理命令行输入
    """
    if len(sys.argv) < 2:
        print("Usage: python code_standard_checker.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    checker = CodeStandardChecker()
    if not checker.load_code(file_path):
        print(f"Failed to load file: {file_path}")
        sys.exit(1)
    
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
    print("## 问题汇总")
    print("| 序号 | 问题类型 | 严重程度 | 位置 | 问题描述 | 改进建议 |")
    print("|------|----------|----------|------|----------|----------|")
    
    for idx, issue in enumerate(results['issues'], 1):
        print(f"| {idx} | {issue['type']} | {issue['severity']} | 第{issue['line']}行 | {issue['description']} | {issue['recommendation']} |")
    
    print()
    print("## 详细分析")
    print()
    print("### 代码风格检查")
    naming_issues = [i for i in results['issues'] if i['type'] == '命名规范']
    print(f"- [{'x' if naming_issues else ' '}] 命名规范 ({len(naming_issues)}个问题)")
    
    comment_issues = [i for i in results['issues'] if i['type'] == '注释规范']
    print(f"- [{'x' if comment_issues else ' '}] 注释完整性 ({len(comment_issues)}个问题)")
    
    print()
    print("### 安全规范检查")
    security_issues = [i for i in results['issues'] if i['type'] == '安全问题']
    print(f"- [{'x' if security_issues else ' '}] 输入验证 ({len(security_issues)}个问题)")
    
    print()
    print("### 性能规范检查")
    perf_issues = [i for i in results['issues'] if i['type'] == '性能问题']
    print(f"- [{'x' if perf_issues else ' '}] 数据库查询 ({len(perf_issues)}个问题)")


if __name__ == "__main__":
    main()