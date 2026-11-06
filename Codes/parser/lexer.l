%{
#include "parser.tab.h"
%}

%%

int     { return INT; }

[a-zA-Z_][a-zA-Z0-9_]* { return ID; }

[0-9]+  { return NUM; }

"="      { return '='; }

";"      { return ';'; }

[ \t\n] ;

. ;

%%

int yywrap()
{
    return 1;
}
