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
        'igual': '=',
        'se': 'if',  # Se para if
        'entao': '{',  # Então é apenas um bloco de código '{'
        'senao': '} else {',  # Senao é else
        'fimse': '}',  # Fimse é apenas o fechamento '}'
        'leia': 'cin >>',  # Leia para cin >>
        'escreva': 'cout <<',  # Escreva para cout <<
        'maiorigual': '>=',
        'menorigual': '<=',
        'diferente': '!=',
        'igual': '==',
        'e': '&&',
        'ou': '||',
        'verdadeiro': 'true',
        'falso': 'false',
        'enquanto': 'while',
        'fimenquanto': '}',
        'para': 'for',
        'fimpara': '}',
        'repita': 'do',
        'ate': 'while',
        'fimumrepita': '}',
        'retorne': 'return',
        'mod': '%',
        'somar': '+',
        'subtrair': '-',
        'multiplicar': '*',
        'dividir': '/',
    }

    def translate_line(line):
        line = line.replace("'", '"').strip()

        # Ignorar linhas vazias
        if not line:
            return ''
        
        # Regex para tokens (incluindo '<-')
        tokens = re.findall(r'".*?"|\w+|<-|[^\s]', line)
        translated_tokens = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            # Tratar strings literais
            if token.startswith('"') and token.endswith('"'):
                translated_tokens.append(token)
            
            # Tratar comandos especiais 'leia' e 'escreva'
            if token == 'leia':
                # Captura a variável ou lista de variáveis
                content = re.findall(r'leia\s+(.+)', line)
                if content:
                    vars_list = [v.strip() for v in content[0].split(',')]
                    translated_line = 'cin >> ' + ' >> '.join(vars_list) + ';'
                    return translated_line
                else:
                    return '/ Erro na sintaxe do comando leia /'
            
            elif token == 'escreva':
                content = re.findall(r'escreva\s+(.+)', line)
                if content:
                    items = [item.strip() for item in content[0].split(',')]
                    translated_line = 'cout << ' + ' << '.join(items) + ';'
                    return translated_line
                else:
                    return '/ Erro na sintaxe do comando escreva /'
            
            # Tratar comandos chave do dicionário
            elif token in portugol_to_cpp_dict:
                translated_tokens.append(portugol_to_cpp_dict[token])
            else:
                translated_tokens.append(token)
            
            i += 1
        
        translated_line = ' '.join(translated_tokens)
        
        # Corrigir operadores com espaços extras
        translated_line = translated_line.replace(' > =', ' >=').replace(' ! =', ' !=').replace(' < =', ' <=')
        
        # Não adicionar ponto e vírgula após '{' ou '}'
        if translated_line and translated_line[-1] not in ['{', '}', ';']:
            translated_line += ';'
        
        return translated_line

    lines = input_code.strip().split('\n')
    output_lines = ['#include <iostream>', 'using namespace std;', '']
    
    for line in lines:
        translated_line = translate_line(line)
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

    if c_code.startswith("Erro:"):
        return jsonify({"errors": [c_code]})

    return jsonify({"c_code": c_code})

if __name__ == '__main__':
    app.run(debug=True)
