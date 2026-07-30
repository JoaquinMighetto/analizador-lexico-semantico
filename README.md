# Analizador de expresiones

Este proyecto implementa una calculadora con interfaz grafica en Tkinter que evalua expresiones aritmeticas, variables y funciones matematicas.

## Como funciona

El programa procesa cada entrada en cuatro etapas:

1. Analisis lexico: `Lexer` convierte el texto en tokens como numeros, operadores, parentesis, identificadores y comas.
2. Analisis sintactico: `Parser` toma los tokens y construye un AST con nodos como `Number`, `Variable`, `BinOp`, `UnaryOp`, `Assign` y `FunctionCall`.
3. Analisis semantico: `SemanticAnalyzer` recorre el AST antes de ejecutar la expresion y verifica que las variables existan, que las funciones sean validas y que la cantidad de argumentos sea razonable.
4. Interpretacion: `Interpreter` evalua el AST y produce el resultado final.

## Modulos

- `t4.py`: contiene el lexer, parser, interprete y la interfaz grafica.
- `semantic_analyzer.py`: contiene la validacion semantica separada del resto del flujo.

## Caracteristicas

- Variables persistentes durante la ejecucion.
- Constantes matematicas `pi` y `e`.
- Funciones como `sqrt`, `sin`, `cos`, `tan`, `log`, `ln`, `exp`, `abs`, `floor`, `ceil`, `round`, `pow`, `max` y `min`.
- Historial de expresiones en la interfaz.

## Ejemplos

- `2 + 3 * 4`
- `x = 10`
- `y = sqrt(x) + 2`
- `sin(pi / 2)`

## Errores que detecta

- Uso de variables no definidas.
- Llamadas a funciones inexistentes.
- Numero incorrecto de argumentos en funciones con firma conocida.
- Errores aritmeticos como division por cero durante la ejecucion.

## Ejecucion

Ejecuta `t4.py` con Python para abrir la ventana de la calculadora.