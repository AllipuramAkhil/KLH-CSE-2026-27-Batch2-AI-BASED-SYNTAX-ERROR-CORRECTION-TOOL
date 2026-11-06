%{
#include <stdio.h>
#include <stdlib.h>

void yyerror(const char *s);
int yylex();
%}

%token INT ID NUM

%%

statement:
      INT ID '=' NUM ';'
      {
          printf("Valid Statement\n");
      }
      ;

%%

void yyerror(const char *s)
{
    printf("Syntax Error Detected!\n");
}

int main()
{
    printf("Enter Statement:\n");
    yyparse();
    return 0;
}
