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
        for line in lines:
            line = line.strip()

            # Mock Variable Declaration: nambai age = 18;
            if line.startswith("nambai") and "=" in line and line.endswith(";"):
                parts = line.replace("nambai", "").replace(";", "").split("=")
                var_name = parts[0].strip()
                var_val = parts[1].strip()
                variables[var_name] = var_val

            # Mock Print Statement: printa(age);
            elif line.startswith("printa(") and line.endswith(");"):
                content = line[7:-2].strip()
                if content in variables:
                    output_lines.append(variables[content])
                else:
                    output_lines.append(content)

        if output_lines:
            return "\n".join(output_lines)
        return "Code executed successfully (No output)."