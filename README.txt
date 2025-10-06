**** Descritivo de consumo das rota da API ACADEMICA ****

#### Consultar alunos por curso (todos NO TOTVS Educacional) ####

http://localhost:8000/curso/alunos?codcurso=06
http://localhost:8000/curso/alunos?nomecurso=Administração
http://localhost:8000/curso/alunos?nomecurso=DIRETO

#### Consultar alunos por curso (idturmadisc) ####

http://localhost:8000/alunos/turma/325

#### Consultar disciplinas do alunos por periodo letivo (aluno/MATRICULA_ALUNO/disciplinas?idperlet=81(ID PERIDO LETIDO)) ####

http://localhost:8000/aluno/23250162/disciplinas?idperlet=81

#### Pagina inicial API ACADEMICA ####
http://localhost:8000/docs#/default

#### Consultar total de alunos por curso no periodo letivo (todos NO TOTVS Educacional) ####
http://localhost:8000/curso/alunos/quantidade?codcurso={?}&idperlet={?}

#### Consultar de alunos por curso no periodo letivo e disciplinas (todos NO TOTVS Educacional) ####
http://localhost:8000/aluno?ra=22290003&idperlet=82&codcurso=29

#### Consultar dados de turmas por alunos matriculados no período letivo/curso (todos NO TOTVS Educacional) ####
http://localhost:8000/turma?codcurso=29&idperlet=82
