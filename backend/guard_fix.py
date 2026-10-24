with open('D:\\Aarakshana AI\\backend\\app\\llm.py', 'r') as f:
    content = f.read()
lines = content.splitlines()
for i, line in enumerate(lines):
    if 'def generate_paralegal_response' in line:
        lines.insert(i+1, '    try:')
        # indent body until end of function or file end
        for j in range(i+2, len(lines)):
            stripped = lines[j].lstrip()
            if stripped == '' or stripped.startswith('#'):
                continue
            if stripped.startswith('def ') or stripped.startswith('class '):
                break
            # indent existing body lines by 4 more spaces
            if lines[j].startswith('        '):
                lines[j] = '    ' + lines[j]
            elif lines[j].startswith('    '):
                lines[j] = '        ' + lines[j].lstrip()
            elif lines[j].startswith('        '):
                pass  # already indented
        # Insert except + return at very end of file (after stream function etc)
        # Instead, find the last line that is part of the function by looking for the final yield/return in stream function
        # Simpler: append at end
        lines.append('    except Exception as e:')
        lines.append('        return {"answer": "Synthesis unavailable: " + str(e), "citations": []}')
        break
with open('D:\Aarakshana AI\\backend\\app\\llm.py', 'w') as f:
    f.write('\n'.join(lines) + '\n')
print('guardrail wrapped')
