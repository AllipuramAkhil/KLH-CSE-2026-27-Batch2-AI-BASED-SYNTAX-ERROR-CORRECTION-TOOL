%{
#include <stdio.h>

extern FILE *yyin;
%}

%option noyywrap

ID      [a-zA-Z_][a-zA-Z0-9_]*
NUMBER  (0[xX][0-9a-fA-F]+|[0-9]+(\.[0-9]*)?([eE][+-]?[0-9]+)?)[uUlLfF]*
STRING  \"([^\\\n]|\\.)*\"
CHAR    \'([^\\\n]|\\.)*\'

%%

#[ \t]*[a-zA-Z_][a-zA-Z0-9_]* { printf("PREPROCESSOR : %s\n", yytext); }

\<[^>\r\n]+\> { printf("HEADER       : %s\n", yytext); }

"//"[^\r\n]* ;

"/*"([^*]|\*+[^*/])*\*+"/" ;

{STRING} { printf("STRING       : %s\n", yytext); }

{CHAR} { printf("CHARACTER    : %s\n", yytext); }

auto|break|case|char|const|continue|default|do|double|else|enum|extern|float|for|goto|if|inline|int|long|register|restrict|return|short|signed|sizeof|static|struct|switch|typedef|union|unsigned|void|volatile|while|class|namespace|public|private|protected|template|typename|using|virtual|bool|true|false|new|delete|this|try|catch|throw|nullptr { printf("KEYWORD      : %s\n", yytext); }

printf|scanf|main { printf("FUNCTION     : %s\n", yytext); }

{NUMBER} { printf("NUMBER       : %s\n", yytext); }

{ID} { printf("IDENTIFIER   : %s\n", yytext); }

"=="|"!="|"<="|">="|"++"|"--"|"+="|"-="|"*="|"/="|"%="|"&&"|"||"|"<<"|">>"|"->"|"="|"+"|"-"|"*"|"/"|"%"|"!"|"&"|"|"|"^"|"~"|"<"|">" { printf("OPERATOR     : %s\n", yytext); }

";"|","|"("|")"|"{"|"}"|"["|"]"|":"|"." { printf("SYMBOL       : %s\n", yytext); }

[ \t\r\n]+ ;

. { printf("UNKNOWN      : %s\n", yytext); }

%%

int main()
{
    FILE *file = fopen("input.c", "r");

    if(file == NULL)
    {
        printf("Cannot open input.c\n");
        return 1;
    }

    yyin = file;

    yylex();

    fclose(file);

    return 0;
}
