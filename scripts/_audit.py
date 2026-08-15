import ast
src = open('bot.py', encoding='utf-8').read()
tree = ast.parse(src)
issues = []
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        s = node.value
        if len(s) > 10 and any(ch in s for ch in '⚠️💳🛒🔗💰📦⭐🏦🔐'):
            # Check it's not in a comment/docstring context that references lang
            issues.append((node.lineno, s[:45]))
print("UI-like literals in bot.py:", len(issues))
for ln, s in issues[:20]:
    print(f"  line {ln}: {s!r}")