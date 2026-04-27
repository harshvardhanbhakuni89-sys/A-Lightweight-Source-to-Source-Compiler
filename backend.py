from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

temp_count = 0

def new_temp():
    global temp_count
    temp_count += 1
    return f"t{temp_count}"


# ---------------------------
# LEXICAL
# ---------------------------
def lexical_analysis(code_lines):
    tokens = []
    pattern = r"[A-Za-z_]\w*|\d+|[=+\-*/()]"

    for line in code_lines:
        matches = re.findall(pattern, line)

        for token in matches:
            if token.isidentifier():
                if token == "print":
                    tokens.append("PRINT")
                else:
                    tokens.append(f"IDENT({token})")
            elif token.isdigit():
                tokens.append(f"NUM({token})")
            elif token == "=":
                tokens.append("ASSIGN")
            else:
                tokens.append(f"OP({token})")

    return tokens


# ---------------------------
# SYNTAX
# ---------------------------
def parse_expression(expr):
    if "+" in expr:
        left, right = expr.split("+", 1)
        return {
            "type": "binary",
            "op": "+",
            "left": left.strip(),
            "right": right.strip()
        }
    return expr.strip()


def syntax_analysis(code_lines):
    ast = []

    for line in code_lines:
        line = line.strip()

        if "=" in line:
            left, right = line.split("=")

            ast.append({
                "type": "assign",
                "left": left.strip(),
                "right": parse_expression(right.strip())
            })

    return ast


# ---------------------------
# SEMANTIC
# ---------------------------
def is_number(x):
    try:
        float(x)
        return True
    except:
        return False


def semantic_analysis(ast):
    table = {}
    errors = []

    for node in ast:
        table[node["left"]] = "int"

        right = node["right"]

        if isinstance(right, dict):
            for op in [right["left"], right["right"]]:
                if not is_number(op) and op not in table:
                    errors.append(f"Undeclared variable: {op}")

    return table, errors


# ---------------------------
# TAC
# ---------------------------
def generate_TAC(ast):
    tac = []

    for node in ast:
        right = node["right"]

        if isinstance(right, dict):
            t = new_temp()
            tac.append(f"{t} = {right['left']} {right['op']} {right['right']}")
            tac.append(f"{node['left']} = {t}")
        else:
            tac.append(f"{node['left']} = {right}")

    return tac


# ---------------------------
# C CODE
# ---------------------------
def generate_c_code(code_lines, ast):
    code = ["#include <stdio.h>", "int main() {"]

    for node in ast:
        right = node["right"]

        if isinstance(right, dict):
            expr = f"{right['left']} + {right['right']}"
        else:
            expr = right

        code.append(f"    int {node['left']} = {expr};")

    for line in code_lines:
        if line.startswith("print"):
            val = line[line.find("{")+1:line.find("}")]
            code.append(f'    printf("Result = %d", {val});')

    code.append("    return 0;")
    code.append("}")

    return "\n".join(code)


# ---------------------------
# API
# ---------------------------
@app.route('/compile', methods=['POST'])
def compile_code():
    global temp_count
    temp_count = 0

    data = request.get_json()
    code_lines = data.get("code", "").split("\n")

    tokens = lexical_analysis(code_lines)
    ast = syntax_analysis(code_lines)
    table, errors = semantic_analysis(ast)
    tac = generate_TAC(ast)
    c_code = generate_c_code(code_lines, ast)

    return jsonify({
        "tokens": tokens,
        "ast": ast,
        "symbol_table": table,
        "errors": errors,
        "tac": tac,
        "c_code": c_code
    })


if __name__ == "__main__":
    app.run(debug=True)