from fastapi import FastAPI, HTTPException, Query, Path
import pyodbc

# ==============================
# CONFIGURAÇÃO DA API
# ==============================
app = FastAPI(title="API Acadêmica", version="1.0", description="API para consulta de dados acadêmicos.")

# ==============================
# CONEXÃO SQL SERVER
# ==============================
def get_connection():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=;"
        "DATABASE=;"
        "UID=;"
        "PWD=;"
    )
    return pyodbc.connect(conn_str)

# ==============================
# UTILITÁRIOS
# ==============================
def row_to_dict(columns, row):
    return {col: getattr(row, col) for col in columns}

# ==============================
# ROTA PRINCIPAL
# ==============================
@app.get("/", summary="Status da API")
def raiz():
    return {"status": "API rodando com sucesso 🚀"}

# ==============================
# ROTA: Alunos por Curso
# ==============================
@app.get("/curso/alunos", summary="Consultar alunos por curso")
def consultar_alunos_por_curso(
    codcurso: str | None = Query(None, description="Código do curso"),
    nomecurso: str | None = Query(None, description="Nome parcial do curso")
):
    if not codcurso and not nomecurso:
        raise HTTPException(status_code=400, detail="Informe 'codcurso' ou 'nomecurso'.")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    SALUNO.RA,
                    PPESSOA.NOME,
                    PPESSOA.CPF,
                    SCURSO.CODCURSO,
                    SCURSO.NOME AS CURSO
                FROM SMATRICULA 
                INNER JOIN SALUNO WITH (NOLOCK) 
                    ON SALUNO.RA = SMATRICULA.RA
                INNER JOIN PPESSOA WITH (NOLOCK) 
                    ON PPESSOA.CODIGO = SALUNO.CODPESSOA
                INNER JOIN STURMADISC WITH (NOLOCK) 
                    ON STURMADISC.IDHABILITACAOFILIAL = SMATRICULA.IDHABILITACAOFILIAL
                    AND STURMADISC.IDTURMADISC = SMATRICULA.IDTURMADISC
                INNER JOIN SHABILITACAOFILIAL WITH (NOLOCK) 
                    ON STURMADISC.IDHABILITACAOFILIAL = SHABILITACAOFILIAL.IDHABILITACAOFILIAL
                INNER JOIN SCURSO WITH (NOLOCK) 
                    ON SCURSO.CODCURSO = SHABILITACAOFILIAL.CODCURSO
                WHERE 1=1
            """
            params = []
            if codcurso:
                query += " AND SCURSO.CODCURSO = ?"
                params.append(codcurso)
            if nomecurso:
                query += " AND SCURSO.NOME LIKE ?"
                params.append(f"%{nomecurso}%")

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="Nenhum aluno encontrado para este curso.")

        alunos = [
            {
                "RA": row.RA,
                "Nome": row.NOME,
                "CPF": row.CPF,
                "Curso": row.CURSO,
                "CodCurso": row.CODCURSO
            }
            for row in rows
        ]

        return {"TotalAlunos": len(alunos), "Alunos": alunos}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

# ==============================
# ROTA: Alunos por Turma
# ==============================
@app.get("/alunos/turma/{idturmadisc}", summary="Consultar alunos por turma")
def get_alunos_por_turma(
    idturmadisc: str = Path(..., description="ID da turma/disciplina"),
    status: str | None = Query(None, description="Filtrar por status da matrícula (ex: 1=Ativo)")
):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT 
                    SALUNO.RA,
                    PPESSOA.NOME,
                    PPESSOA.CPF,
                    SCURSO.CODCURSO,
                    SCURSO.NOME AS CURSO, 
                    STURMADISC.CODDISC,
                    STURMADISC.IDPERLET,
                    SMATRICULA.CODSTATUS
                FROM SMATRICULA 
                INNER JOIN SALUNO WITH (NOLOCK)
                    ON SALUNO.RA = SMATRICULA.RA
                INNER JOIN PPESSOA WITH (NOLOCK)
                    ON PPESSOA.CODIGO = SALUNO.CODPESSOA
                INNER JOIN STURMADISC WITH (NOLOCK) 
                    ON STURMADISC.IDHABILITACAOFILIAL = SMATRICULA.IDHABILITACAOFILIAL
                    AND STURMADISC.IDTURMADISC = SMATRICULA.IDTURMADISC
                INNER JOIN SHABILITACAOFILIAL WITH (NOLOCK) 
                    ON STURMADISC.IDHABILITACAOFILIAL = SHABILITACAOFILIAL.IDHABILITACAOFILIAL
                INNER JOIN SCURSO WITH (NOLOCK) 
                    ON SCURSO.CODCURSO = SHABILITACAOFILIAL.CODCURSO
                WHERE STURMADISC.IDTURMADISC = ?
            """
            params = [idturmadisc]
            if status:
                sql += " AND SMATRICULA.CODSTATUS = ?"
                params.append(status)

            cursor.execute(sql, params)
            rows = cursor.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="Nenhum aluno encontrado para esta turma/disciplina.")

        columns = ["RA", "NOME", "CPF", "CODCURSO", "CURSO", "CODDISC", "IDPERLET", "CODSTATUS"]
        result = [row_to_dict(columns, r) for r in rows]

        return {"TotalAlunos": len(result), "Alunos": result, "FiltroStatus": status}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

# ==============================
# ROTA: Disciplinas do Aluno por Período Letivo
# ==============================
@app.get("/aluno/{ra}/disciplinas", summary="Consultar disciplinas de um aluno")
def get_disciplinas_aluno(
    ra: str = Path(..., description="RA do aluno"),
    idperlet: str = Query(..., description="ID do Período Letivo")
):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT 
                    SALUNO.RA,
                    PPESSOA.NOME AS NOMEALUNO,
                    STURMADISC.CODDISC,
                    SDISCIPLINA.NOME AS NOMEDISCIPLINA,
                    STURMADISC.IDPERLET,
                    SMATRICULA.CODSTATUS
                FROM SMATRICULA
                INNER JOIN SALUNO WITH (NOLOCK)
                    ON SALUNO.RA = SMATRICULA.RA
                INNER JOIN PPESSOA WITH (NOLOCK)
                    ON PPESSOA.CODIGO = SALUNO.CODPESSOA
                INNER JOIN STURMADISC WITH (NOLOCK)
                    ON STURMADISC.IDHABILITACAOFILIAL = SMATRICULA.IDHABILITACAOFILIAL
                    AND STURMADISC.IDTURMADISC = SMATRICULA.IDTURMADISC
                INNER JOIN SDISCIPLINA WITH (NOLOCK)
                    ON SDISCIPLINA.CODDISC = STURMADISC.CODDISC
                WHERE SALUNO.RA = ?
                  AND STURMADISC.IDPERLET = ?
            """
            params = [ra, idperlet]
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="Nenhuma disciplina encontrada para este aluno e período letivo.")

        disciplinas = [
            {
                "RA": row.RA,
                "Aluno": row.NOMEALUNO,
                "CodDisc": row.CODDISC,
                "Disciplina": row.NOMEDISCIPLINA,
                "PeriodoLetivo": row.IDPERLET,
                "StatusMatricula": row.CODSTATUS
            }
            for row in rows
        ]

        return {"TotalDisciplinas": len(disciplinas), "Disciplinas": disciplinas}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

# ==============================
# ROTA: Quantidade de Alunos por Curso (Semestre Atual)
# ==============================
@app.get("/curso/alunos/quantidade", summary="Quantidade de alunos por curso")
def get_quantidade_alunos_por_curso(
    codcurso: str = Query(..., description="Código do curso"),
    idperlet: str = Query(..., description="ID do Período Letivo")
):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            sql = """
                SELECT 
                    SCURSO.CODCURSO,
                    SCURSO.NOME AS CURSO,
                    COUNT(DISTINCT SALUNO.RA) AS TOTAL_ALUNOS
                FROM SMATRICULA
                INNER JOIN SALUNO WITH (NOLOCK) 
                    ON SALUNO.RA = SMATRICULA.RA
                INNER JOIN PPESSOA WITH (NOLOCK) 
                    ON PPESSOA.CODIGO = SALUNO.CODPESSOA
                INNER JOIN STURMADISC WITH (NOLOCK) 
                    ON STURMADISC.IDHABILITACAOFILIAL = SMATRICULA.IDHABILITACAOFILIAL
                    AND STURMADISC.IDTURMADISC = SMATRICULA.IDTURMADISC
                INNER JOIN SHABILITACAOFILIAL WITH (NOLOCK) 
                    ON STURMADISC.IDHABILITACAOFILIAL = SHABILITACAOFILIAL.IDHABILITACAOFILIAL
                INNER JOIN SCURSO WITH (NOLOCK) 
                    ON SCURSO.CODCURSO = SHABILITACAOFILIAL.CODCURSO
                INNER JOIN SHABILITACAOALUNO WITH (NOLOCK) 
                    ON SHABILITACAOALUNO.RA = SMATRICULA.RA
                    AND SHABILITACAOALUNO.IDHABILITACAOFILIAL = SMATRICULA.IDHABILITACAOFILIAL
                INNER JOIN SMATRICPL WITH (NOLOCK) 
                    ON SMATRICPL.RA = SMATRICULA.RA
                    AND SMATRICPL.IDHABILITACAOFILIAL = SMATRICULA.IDHABILITACAOFILIAL
                    AND SMATRICPL.IDPERLET = SMATRICULA.IDPERLET
                WHERE SCURSO.CODCURSO = ?
                  AND STURMADISC.IDPERLET = ?
                  AND SMATRICPL.CODSTATUS = '1'
                GROUP BY SCURSO.CODCURSO, SCURSO.NOME
            """

            params = [codcurso, idperlet]
            cursor.execute(sql, params)
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Nenhum curso encontrado para os parâmetros informados.")

        return {
            "CodCurso": row.CODCURSO,
            "Curso": row.CURSO,
            "TotalAlunos": row.TOTAL_ALUNOS
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")
# ==============================
# ROTA: CONSULTA ALUNO POR RA, IDPERLET e CODCURSO
# ==============================
@app.get("/aluno", summary="Dados do aluno com disciplinas")
def get_aluno(
    ra: str = Query(..., description="RA do aluno"),
    idperlet: str = Query(..., description="ID do período letivo"),
    codcurso: str = Query(..., description="Código do curso")
):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
             SELECT 
              DISTINCT
              CASE WHEN SHABILITACAOALUNO.CODSTATUS = '1' THEN 'MATRICULADO' END AS SIT_CURSO,
	          SALUNO.RA,
	          PPESSOA.NOME,
              PPESSOA.CPF,
              SCURSO.CODCURSO,
              SCURSO.NOME AS CURSO,
	          CASE WHEN SMATRICPL.CODSTATUS = '1' THEN 'MATRICULADO' END AS SIT_PERIODO_LETIVO,
              STURMADISC.IDPERLET,
              SMATRICPL.CODTURMA,
	          SUBSTRING (SMATRICPL.CODTURMA, 1,5) AS CODTURMA_REDUZIDO,
	          SCURSO.NOME AS CURSO,
	          STURMADISC.CODDISC,
	          SDISCIPLINA.NOME AS DISCIPLINA,
	          SMATRICULA.IDTURMADISC,
	          CASE WHEN SMATRICULA.CODSTATUS = '13' THEN 'CURSANDO'
	          WHEN SMATRICULA.CODSTATUS = '3' THEN 'MATRICULADO DEP'
		      WHEN SMATRICULA.CODSTATUS = '30' THEN 'REPETENTE C/ COBRANCA'
              END SITUACAO_DISCIPLINA
                FROM SMATRICULA
                INNER JOIN SALUNO (NOLOCK) 
                    ON SALUNO.RA = SMATRICULA.RA
                INNER JOIN PPESSOA (NOLOCK) 
                    ON PPESSOA.CODIGO = SALUNO.CODPESSOA
                INNER JOIN STURMADISC (NOLOCK) 
                    ON STURMADISC.IDHABILITACAOFILIAL = SMATRICULA.IDHABILITACAOFILIAL
                    AND STURMADISC.IDTURMADISC = SMATRICULA.IDTURMADISC
                INNER JOIN SHABILITACAOFILIAL (NOLOCK) 
                    ON STURMADISC.IDHABILITACAOFILIAL = SHABILITACAOFILIAL.IDHABILITACAOFILIAL
                INNER JOIN SCURSO (NOLOCK) 
                    ON SCURSO.CODCURSO = SHABILITACAOFILIAL.CODCURSO
                INNER JOIN SHABILITACAOALUNO (NOLOCK) 
                    ON SHABILITACAOALUNO.RA = SMATRICULA.RA
                    AND SHABILITACAOALUNO.IDHABILITACAOFILIAL = SMATRICULA.IDHABILITACAOFILIAL
                INNER JOIN SMATRICPL (NOLOCK) 
                    ON SMATRICPL.RA = SMATRICULA.RA
                    AND SMATRICPL.IDHABILITACAOFILIAL = SMATRICULA.IDHABILITACAOFILIAL
                    AND SMATRICPL.IDPERLET = SMATRICULA.IDPERLET
                INNER JOIN SDISCIPLINA (NOLOCK) 
                    ON STURMADISC.CODDISC = SDISCIPLINA.CODDISC           
                WHERE SCURSO.CODCURSO = ?
                  AND STURMADISC.IDPERLET = ?
                  AND SALUNO.RA = ?
                  AND SMATRICPL.CODSTATUS = '1'
                  AND SMATRICULA.CODSTATUS NOT IN ('16', '6')
                  AND SHABILITACAOALUNO.CODSTATUS NOT IN ('12','15','18','21','22','24')
                ORDER BY PPESSOA.NOME
            """, (codcurso, idperlet, ra))

            rows = cursor.fetchall()

            if not rows:
                return {"erro": "Aluno não encontrado"}

            # Dados gerais do aluno (primeira linha)
            aluno = {
                "RA": rows[0].RA,
                "NOME": rows[0].NOME,
                "CPF": rows[0].CPF,
                "CODCURSO": rows[0].CODCURSO,
                "CURSO": rows[0].CURSO,
                "SIT_CURSO": rows[0].SIT_CURSO,
                "IDPERLET": rows[0].IDPERLET,
                "SIT_PERIODO_LETIVO": rows[0].SIT_PERIODO_LETIVO,
                "DISCIPLINAS": []
            }

            # Preenche disciplinas
            for row in rows:
                aluno["DISCIPLINAS"].append({
                    "CODTURMA": row.CODTURMA,
                    "CODTURMA_REDUZIDO": row.CODTURMA_REDUZIDO,
                    "IDTURMADISC": row.IDTURMADISC,
                    "CODDISC": row.CODDISC,
                    "NOME": row.DISCIPLINA,
                    "SITUACAO_DISCIPLINA": row.SITUACAO_DISCIPLINA
                })

            return aluno

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
