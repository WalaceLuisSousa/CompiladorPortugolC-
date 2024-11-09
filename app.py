import re
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Função que traduz o código de Portugol para C++
def portugol_to_cpp(input_code):
    portugol_to_cpp_dict = {
        'inicio': 'int main() {',
        'fim': '}',
        'inteiro': 'int',
        'real': 'float',
        'caracter': 'char',
        'se': 'if',  # Se para if
        'entao': '{',  # Então é apenas um bloco de código '{'
        'senao': '} else {',  # Senao é else
        'fimse': '}',  # Fimse é apenas o fechamento '}'
        'faca': '{',  # Faca indica início do bloco de código '{'
        'maiorigual': '>=',  # Maior ou igual
        'menorigual': '<=',  # Menor ou igual
        'menor': '<',  # Menor 
        'maior': '>',  # maior
        'diferente': '!=',  # Diferente
        'igual': '=',  # Igualdade
        'e': '&&',  # Operador lógico "e"
        'ou': '||',  # Operador lógico "ou"
        'verdadeiro': 'true',  # Valor booleano verdadeiro
        'falso': 'false',  # Valor booleano falso
        'enquanto': 'while',  # Laço enquanto
        'fimenquanto': '}',  # Fim do laço enquanto
        'fimpara': '}',  # Fim do laço para
        'repita': 'do',  # Início do laço "faça ... enquanto"
        'ate': 'while',  # Condição de parada do laço "faça ... enquanto"
        'fimumrepita': '}',  # Fim do laço "faça ... enquanto"
        'retorne': 'return',  # Retorna valor de função
        'mod': '%',  # Operador de módulo (resto de divisão)
        'somar': '+',  # Operador de soma
        'subtrair': '-',  # Operador de subtração
        'multiplicar': '*',  # Operador de multiplicação
        'dividir': '/',  # Operador de divisão
        'saia': 'break',
        'diferente': '<>',
    }

    def validate_tokens(line):
        # Dividir a linha em tokens, incluindo palavras, números, vírgulas e símbolos
        tokens = re.findall(r'".*?"|\w+|<-|[^\s]', line)

        for token in tokens:
            # Ignorar strings literais, números, vírgulas, e parênteses
            if token.startswith('"') and token.endswith('"'):
                continue
            if re.match(r'^\d+$', token):
                continue
            if token in {',', '(', ')'}:  # Permitir vírgulas e parênteses
                continue
            # Verificar se o token está no dicionário de tradução ou é uma variável válida
            if token not in portugol_to_cpp_dict and not re.match(r'^[a-zA-Z_]\w*$', token):
                return f"/ Erro: Token '{token}' não reconhecido no código Portugol. /"
        
        return None  # Se todos os tokens são válidos, retorna None

    def translate_line(line):
        line = line.replace("'", '"').strip()

        # Ignorar linhas vazias
        if not line:
            return ''
        
        # Validar tokens da linha antes de traduzir
        error = validate_tokens(line)
        if error:
            return error  # Retorna o erro imediatamente se houver um token inválido

        # Tratar comandos específicos 'leia' e 'escreva' antes de aplicar o dicionário completo
        if line.startswith('leia'):
            content = re.findall(r'leia\s+(.+)', line)
            if content:
                vars_list = [v.strip() for v in content[0].split(',')]
                translated_line = 'cin >> ' + ' >> '.join(vars_list) + ';'
                return translated_line
            else:
                return '/ Erro na sintaxe do comando leia /'

        elif line.startswith('escreva'):
            content = re.findall(r'escreva\s+(.+)', line)
            if content:
                items = [item.strip() for item in content[0].split(',')]
                translated_line = 'cout << ' + ' << '.join(items) + ';'
                return translated_line
            else:
                return '/ Erro na sintaxe do comando escreva /'
        
        # Traduzir o loop 'para ... de ... ate ... faca' para a estrutura de 'for' do C++
        if line.startswith('para'):
            match = re.search(r'para\s+(\w+)\s+de\s+(\d+)\s+ate\s+(\w+)\s+faca', line)
            if match:
                var = match.group(1)  # variável de controle
                start = match.group(2)  # valor inicial
                end = match.group(3)  # valor final
                return f"for (int {var} = {start}; {var} <= {end}; {var}++) {{"

        # Traduzir todos os tokens no dicionário
        for portugol_key, cpp_value in portugol_to_cpp_dict.items():
            line = re.sub(rf'\b{portugol_key}\b', cpp_value, line)

        # Traduzir 'se' e 'enquanto' com validação de parênteses
        if line.startswith('se') or line.startswith('enquanto'):
            # Extraindo a condição entre 'se'/'enquanto' e 'entao'/'faca'
            condition_match = re.search(r'(se|enquanto)\s+(.+?)\s+(entao|faca)', line)
            if condition_match:
                keyword = condition_match.group(1)  # se ou enquanto
                condition = condition_match.group(2).strip()
                
                # Verificar se a condição já está entre parênteses
                if not (condition.startswith('(') and condition.endswith(')')):
                    return f"/ Erro: Condição '{keyword}' requer parênteses ao redor da expressão. /"

                translated_keyword = portugol_to_cpp_dict[keyword]
                return f"{translated_keyword} {condition} {{"

        # Regex para tokens (incluindo '<-')
        tokens = re.findall(r'".*?"|\w+|<-|[^\s]', line)
        translated_tokens = []
        
        for token in tokens:
            # Tratar strings literais
            if token.startswith('"') and token.endswith('"'):
                translated_tokens.append(token)
                continue
            
            # Traduzir comandos do dicionário ou manter variáveis
            if token in portugol_to_cpp_dict:
                translated_tokens.append(portugol_to_cpp_dict[token])
            else:
                translated_tokens.append(token)
        
        translated_line = ' '.join(translated_tokens)
        
        # Corrigir operadores com espaços extras
        translated_line = translated_line.replace(' > =', ' >=').replace(' ! =', ' !=').replace(' < =', ' <=').replace('= =','==').replace('< <','<<').replace('> >','>>').replace('< >','!=')
        
        # Não adicionar ponto e vírgula após '{' ou '}'
        if translated_line and translated_line[-1] not in ['{', '}', ';']:
            translated_line += ';'
        
        return translated_line

    lines = input_code.strip().split('\n')
    output_lines = ['#include <iostream>', 'using namespace std;', '']
    
    for line in lines:
        translated_line = translate_line(line)
        if "/ Erro:" in translated_line:
            return translated_line  # Retorna erro imediatamente
        output_lines.append(translated_line)
    
    output_code = '\n'.join(output_lines)
    return output_code

# Rota principal que exibe a página HTML
@app.route('/')
def index():
    return render_template('index.html')

# Rota para processar o código em Portugol e gerar o código C++
@app.route('/compile', methods=['POST'])
def compile():
    portugol_code = request.form['portugol_code']
    
    if not portugol_code.strip():
        return jsonify({"errors": ["Erro: Código em Portugol não pode estar vazio."]})

    c_code = portugol_to_cpp(portugol_code)

    if "/ Erro:" in c_code:
        return jsonify({"errors": [c_code]})

    return jsonify({"c_code": c_code})

if __name__ == '__main__':
    app.run(debug=True)
