import re
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Dicionário de tradução de palavras reservadas do Portugol para C++
portugol_to_cpp_dict = {
    'inicio': 'int main() {',
    'fim': '}',
    'inteiro': 'int',
    'real': 'float',
    'caracter': 'char',
    'string': 'string',
    'se': 'if',
    'entao': '{',
    'senaose': '} else if',
    'senao': '} else {',
    'fimse': '}',
    'faça': '{',
    'maiorigual': '>=',
    'menorigual': '<=',
    'menor': '<',
    'maior': '>',
    'diferente': '!=',
    'igual': '=',
    'e': '&&',
    'ou': '||',
    'verdadeiro': 'true',
    'falso': 'false',
    'enquanto': 'while',
    'fimenquanto': '}',
    'fimpara': '}',
    'repita': 'do {',
    'ate': '} while',
    'fimumrepita': ';',
    'retorne': 'return',
    'mod': '%',
    'somar': '+',
    'subtrair': '-',
    'multiplicar': '*',
    'dividir': '/',
    'saia': 'break',
}

# Lista de tokens para a biblioteca
token_library = sorted(portugol_to_cpp_dict.keys())

# Conjunto de palavras reservadas do C++
cpp_reserved_words = {
    'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do', 'double',
    'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'int', 'long',
    'register', 'return', 'short', 'signed', 'sizeof', 'static', 'struct',
    'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while',
    'asm', 'bool', 'catch', 'class', 'const_cast', 'delete', 'dynamic_cast',
    'explicit', 'export', 'false', 'friend', 'inline', 'mutable', 'namespace',
    'new', 'operator', 'private', 'protected', 'public', 'reinterpret_cast',
    'static_cast', 'template', 'this', 'throw', 'true', 'try', 'typeid',
    'typename', 'using', 'virtual', 'wchar_t', 'and', 'and_eq', 'bitand',
    'bitor', 'compl', 'not', 'not_eq', 'or', 'or_eq', 'xor', 'xor_eq',
    'override', 'final', 'import', 'module', 'requires',
}

# Combina palavras reservadas do Portugol e do C++ em um único conjunto
reserved_words = set(portugol_to_cpp_dict.keys()).union(cpp_reserved_words)

token_library = sorted([
    {'token': key, 'translation': value}
    for key, value in portugol_to_cpp_dict.items()
], key=lambda x: x['token'])

def portugol_to_cpp(input_code):
    """Função que converte código em Portugol para C++ com indentação adequada"""

    variables = {}  # Dicionário para armazenar variáveis e seus tipos

    def validate_tokens(line):
        """Valida cada token em uma linha de código"""
        # Atualização da regex para capturar strings, caracteres, números de ponto flutuante e inteiros
        tokens = re.findall(r'".*?"|\'.*?\'|\d+\.\d+|\d+|\w+|<-|[^\s]', line)  # Tokeniza a linha
        for token in tokens:
            # Ignora literais de string e caracteres, números e alguns símbolos
            if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
                continue
            if re.match(r'^-?\d+(\.\d+)?$', token):  # Permite inteiros, reais e negativos
                continue
            if token in {',', '(', ')'}:
                continue
            # Verifica se o token é válido
            if token not in portugol_to_cpp_dict and not re.match(r'^[a-zA-Z_]\w*$', token):
                return f"/ Erro: Token '{token}' não reconhecido no código Portugol. /"
        return None  # Nenhum erro encontrado

    def translate_condition(condition):
        """Traduza uma condição usando condition_operator_dict"""
        for key, val in sorted(condition_operator_dict.items(), key=lambda x: len(x[0]), reverse=True):
            condition = re.sub(r'\b{}\b'.format(re.escape(key)), val, condition)
        return condition

    def translate_line(line):
        """Traduz uma única linha de código"""
        line = line.strip()  # Apenas remove espaços em branco
        if not line:
            return ''  # Ignora linhas vazias

        error = validate_tokens(line)  # Valida tokens na linha
        if error:
            return error  # Retorna o erro encontrado

        # Tradução de declarações de variáveis
        var_decl_match = re.match(r'^(inteiro|real|caracter)\b\s+(.+)', line)
        if var_decl_match:
            tipo = var_decl_match.group(1)  # Tipo da variável
            vars_list = [v.strip() for v in var_decl_match.group(2).split(',')]  # Lista de variáveis
            for var in vars_list:
                # Verifica se o nome da variável é válido
                if var in reserved_words:
                    return f"/ Erro: Nome de variável '{var}' é uma palavra reservada. /"
                if not re.match(r'^[a-zA-Z_]\w*$', var):
                    return f"/ Erro: Nome de variável inválido '{var}'. /"
                variables[var] = tipo  # Armazena o tipo da variável
            translated_type = portugol_to_cpp_dict[tipo]  # Traduz o tipo
            return f"{translated_type} " + ', '.join(vars_list) + ';'  # Retorna a declaração traduzida

        # Tradução do comando 'leia'
        if line.startswith('leia'):
            content = re.findall(r'leia\s+(.+)', line)
            if content:
                vars_list = [v.strip() for v in content[0].split(',')]  # Lista de variáveis a serem lidas
                for var in vars_list:
                    # Verifica se o nome da variável é válido
                    if var in reserved_words:
                        return f"/ Erro: Nome de variável '{var}' é uma palavra reservada. /"
                    if not re.match(r'^[a-zA-Z_]\w*$', var):
                        return f"/ Erro: Nome de variável inválido '{var}'. /"
                return 'cin >> ' + ' >> '.join(vars_list) + ';'  # Retorna o comando 'cin' traduzido
            else:
                return '/ Erro na sintaxe do comando leia /'

        # Tradução do comando 'escreva'
        if line.startswith('escreva'):
            # Permitir 'escreva "texto", variavel' sem parênteses
            content = re.findall(r'escreva\s+(.+)', line)
            if content:
                items = [item.strip() for item in content[0].split(',')]  # Itens a serem impressos
                return 'cout << ' + ' << '.join(items) + ';'  # Retorna o comando 'cout' traduzido
            else:
                return '/ Erro na sintaxe do comando escreva /'

        # Tradução de loops 'para'
        if line.startswith('para'):
            match = re.match(r'para\s+(\w+)\s+de\s+(\d+)\s+ate\s+(\w+)\s+faça', line)
            if match:
                var = match.group(1)    # Variável de controle
                start = match.group(2)  # Valor inicial
                end = match.group(3)    # Valor final
                return f"for (int {var} = {start}; {var} <= {end}; {var}++) {{"

        # Tradução de condições 'se', 'senaose', 'senao'
        if line.startswith('se ') or line.startswith('senaose ') or line.startswith('senao '):
            # Tradução de 'se (cond) entao' para 'if (cond) {'
            if line.startswith('se '):
                match = re.match(r'se\s*\((.*?)\)\s*entao', line)
                if match:
                    condition = translate_condition(match.group(1).strip())
                    return f"if ({condition}) {{"
            # Tradução de 'senaose (cond) entao' para '} else if (cond) {'
            elif line.startswith('senaose '):
                match = re.match(r'senaose\s*\((.*?)\)\s*entao', line)
                if match:
                    condition = translate_condition(match.group(1).strip())
                    return f"}} else if ({condition}) {{"
            # Tradução de 'senao' para '} else {'
            elif line.startswith('senao'):
                return "} else {"

        # Tradução de 'fimse'
        if line.startswith('fimse'):
            return '}'

        # Tradução de 'repita'
        if line.startswith('repita'):
            return 'do {'

        # Tradução de 'ate'
        if line.startswith('ate'):
            # Traduz 'ate (cond)' para '} while (cond);'
            match = re.match(r'ate\s*\((.*?)\)', line)
            if match:
                condition = translate_condition(match.group(1).strip())
                return f"}} while ({condition});"
            else:
                return '/ Erro na sintaxe do comando ate /'

        # Tradução de 'enquanto' (loop 'enquanto cond faca')
        if line.startswith('enquanto'):
            match = re.match(r'enquanto\s*\((.*?)\)\s*faca', line)
            if match:
                condition = translate_condition(match.group(1).strip())
                return f"while ({condition}) {{"

        # Tradução de 'fimpara' e 'fimenquanto'
        if line.startswith('fimpara') or line.startswith('fimenquanto'):
            return '}'

        # Tradução de atribuições
        assign_match = re.match(r'^(\w+)\s+igual\s+(.+)', line)
        if assign_match:
            var = assign_match.group(1)
            value = assign_match.group(2).strip()

            # Verifica se a variável foi declarada
            if var not in variables:
                return f"/ Erro: Variável '{var}' não declarada. /"

            tipo = variables[var]

            # Trata a atribuição com base no tipo da variável
            if tipo == 'caracter':
                # Verifica se o valor está entre aspas simples e possui apenas um caractere
                char_match = re.match(r"^'([^'\s])'$", value)
                if not char_match:
                    return f"/ Erro: Atribuição inválida para variável 'caracter'. Use aspas simples e apenas um caractere. /"
                return f"{var} = {value};"
            else:
                # Substitui operadores no 'value' ordenando por comprimento decrescente para evitar conflitos
                for key, val in sorted(operator_dict.items(), key=lambda x: len(x[0]), reverse=True):
                    value = re.sub(r'\b{}\b'.format(re.escape(key)), val, value)
                # Substitui aspas simples por duplas para strings, se houver
                value = value.replace("'", '"')
                return f"{var} = {value};"

        # Tradução genérica usando o dicionário
        for portugol_key, cpp_value in sorted(portugol_to_cpp_dict.items(), key=lambda x: len(x[0]), reverse=True):
            # Evita substituir 'igual' dentro de palavras maiores (usando bordas de palavra)
            line = re.sub(r'\b{}\b'.format(re.escape(portugol_key)), cpp_value, line)  # Substitui palavras-chave

        # Tokeniza a linha novamente para substituições finais
        tokens = re.findall(r'".*?"|\'.*?\'|\d+\.\d+|\d+|\w+|<-|[^\s]', line)  # Atualizada para incluir floats e caracteres
        translated_tokens = []
        for token in tokens:
            if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
                translated_tokens.append(token)  # Mantém literais de string e caracteres
            elif token in portugol_to_cpp_dict:
                translated_tokens.append(portugol_to_cpp_dict[token])  # Traduz tokens
            else:
                translated_tokens.append(token)  # Mantém outros tokens inalterados

        translated_line = ' '.join(translated_tokens)  # Reconstrói a linha

        # Adiciona ponto e vírgula se necessário
        if translated_line and translated_line[-1] not in ['{', '}', ';']:
            translated_line += ';'
        return translated_line  # Retorna a linha traduzida

    # Define os dicionários de operadores (mantenha do seu código original)
    operator_dict = {
        'igual igual': '==',
        'diferente': '!=',
        'maior igual': '>=',
        'menor igual': '<=',
        'somar': '+',
        'subtrair': '-',
        'multiplicar': '*',
        'dividir': '/',
        'mod': '%',
        'e': '&&',
        'ou': '||',
        'maior': '>',
        'menor': '<',
    }

    # Dicionário separado para operadores usados em condições
    condition_operator_dict = {
        'igual igual': '==',
        'igual': '==',
        'diferente': '!=',
        'maior igual': '>=',
        'menor igual': '<=',
        'somar': '+',
        'subtrair': '-',
        'multiplicar': '*',
        'dividir': '/',
        'mod': '%',
        'e': '&&',
        'ou': '||',
        'maior': '>',
        'menor': '<',
    }

    # Divide o código de entrada em linhas e inicializa a saída
    lines = input_code.strip().split('\n')
    output_lines = ['#include <iostream>', 'using namespace std;']  # Cabeçalho do código C++
    indent_level = 0  # Nível inicial de indentação

    for line in lines:
        translated_line = translate_line(line)  # Traduz cada linha
        if "/ Erro:" in translated_line:
            return translated_line  # Retorna o erro imediatamente

        stripped_line = translated_line.strip()

        # Aumenta ou diminui o nível de indentação com base nas chaves
        if stripped_line.startswith('}'):
            indent_level = max(indent_level - 1, 0)  # Decrementa indentação antes da linha

        # Aplica a indentação atual à linha traduzida
        indented_line = ('    ' * indent_level) + translated_line  # Usa 4 espaços por nível de indentação
        output_lines.append(indented_line)

        # Incrementa o nível de indentação se a linha terminar com '{'
        if stripped_line.endswith('{'):
            indent_level += 1

    return '\n'.join(output_lines)  # Retorna o código traduzido completo

@app.route('/')
def index():
    print("Tokens disponíveis:", token_library)  # Adicionado para depuração
    return render_template('index.html', tokens=token_library)  # Passa os tokens para o template

@app.route('/compile', methods=['POST'])
def compile_code():
    portugol_code = request.form['portugol_code']

    if not portugol_code.strip():
        return jsonify({"errors": ["Erro: Código em Portugol não pode estar vazio."]})

    c_code = portugol_to_cpp(portugol_code)

    # Substituições adicionais para operadores que podem ter sido separados por espaços
    c_code = c_code.replace('= =','==')
    c_code = c_code.replace('> =','>=')
    c_code = c_code.replace('< =','<=')
    c_code = c_code.replace('! =','!=')
    c_code = c_code.replace('< <','<<')
    c_code = c_code.replace('> >','>>')

    if "/ Erro:" in c_code:
        return jsonify({"errors": [c_code]})

    return jsonify({"c_code": c_code})

if __name__ == '__main__':
    app.run(debug=True)
