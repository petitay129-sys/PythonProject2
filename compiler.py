# compiler.py

class JabaiScriptCompiler:
    """Class na mamamahala sa pag-run ng JabaiScript code."""

    def run(self, code: str) -> str:
        if not code.strip():
            return "Error: Empty code block."

        # Dito papasok ang Lexer -> Parser -> Interpreter ninyo.
        # Ito ay isang SIMPLENG MOCK LOGIC para sa demonstration:
        output_lines = []
        variables = {}

        lines = code.strip().split("\n")
        
        in_switch = False
        switch_val = None
        execute_block = False
        matched_any_case = False

        for line in lines:
            line = line.strip()

            if not line or line.startswith("//"):
                continue

            # Mock Variable Declaration: nambai age = 18;
            if line.startswith("nambai") and "=" in line and line.endswith(";"):
                parts = line.replace("nambai", "").replace(";", "").split("=")
                var_name = parts[0].strip()
                var_val = parts[1].strip().strip('"\'')
                variables[var_name] = var_val

            # Switch Statement: pili (day) {
            elif line.startswith("pili") and "(" in line:
                in_switch = True
                matched_any_case = False
                start_idx = line.find("(") + 1
                end_idx = line.find(")")
                expr = line[start_idx:end_idx].strip()
                switch_val = variables.get(expr, expr)
                execute_block = False

            # Switch Case: kaso 1:
            elif line.startswith("kaso") and ":" in line:
                if in_switch:
                    case_val = line.replace("kaso", "").split(":")[0].strip().strip('"\'')
                    if case_val == str(switch_val):
                        execute_block = True
                        matched_any_case = True
                    else:
                        execute_block = False

            # Default Case (Bisaya: lain:)
            elif line.startswith("default:") or line.startswith("lain:"):
                if in_switch:
                    if not matched_any_case:
                        execute_block = True
                    else:
                        execute_block = False

            # Break Statement (Bisaya: undang;)
            elif line == "undang;":
                if in_switch:
                    execute_block = False

            # Closing brace
            elif line == "}":
                execute_block = False

            # Mock Print Statement: printa(age);
            elif line.startswith("printa(") and line.endswith(");"):
                if not in_switch or execute_block:
                    content = line[7:-2].strip().strip('"\'')
                    if content in variables:
                        output_lines.append(variables[content])
                    else:
                        output_lines.append(content)

        if output_lines:
            return "\n".join(output_lines)
        return "Code executed successfully (No output)."