from fastapi import FastAPI, HTTPException, Query
import pyodbc

# ==============================
# CONFIGURAÇÃO DA API
# ==============================
app = FastAPI(title="API Acadêmica", version="1.0")

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
# ROTA PRINCIPAL (SAÚDE DA API)
# ==============================
@app.get("/")
def raiz():
    return {"status": "API rodando com sucesso 🚀"}

# ==============================
# ROTA: Alunos por Curso
# ==============================
@app.get("/curso/alunos")
def consultar_alunos_por_curso(codcurso: str = None, nomecurso: str = None):
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
                INNER JOIN SALUNO ON SALUNO.RA = SMATRICULA.RA
                INNER JOIN PPESSOA ON PPESSOA.CODIGO = SALUNO.CODPESSOA
                INNER JOIN STURMADISC ON STURMADISC.IDHABILITACAOFILIAL = SMATRICULA.IDHABILITACAOFILIAL
                     AND STURMADISC.IDTURMADISC = SMATRICULA.IDTURMADISC
                INNER JOIN SHABILITACAOFILIAL ON STURMADISC.IDHABILITACAOFILIAL = SHABILITACAOFILIAL.IDHABILITACAOFILIAL
                INNER JOIN SCURSO ON SCURSO.CODCURSO = SHABILITACAOFILIAL.CODCURSO
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
@app.get("/alunos/turma/{idturmadisc}")
def get_alunos_por_turma(
    idturmadisc: str,
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
                INNER JOIN SALUNO ON SALUNO.RA = SMATRICULA.RA
                INNER JOIN PPESSOA ON PPESSOA.CODIGO = SALUNO.CODPESSOA
                INNER JOIN STURMADISC ON STURMADISC.IDHABILITACAOFILIAL = SMATRICULA.IDHABILITACAOFILIAL
                     AND STURMADISC.IDTURMADISC = SMATRICULA.IDTURMADISC
                INNER JOIN SHABILITACAOFILIAL ON STURMADISC.IDHABILITACAOFILIAL = SHABILITACAOFILIAL.IDHABILITACAOFILIAL
                INNER JOIN SCURSO ON SCURSO.CODCURSO = SHABILITACAOFILIAL.CODCURSO
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

        columns = ["RA", "NOME", "CPF", "CODCURSO", "CURSO", "CODDISC", "IDPERLET"]
        result = [row_to_dict(columns, r) for r in rows]

        return {"TotalAlunos": len(result), "Alunos": result, "FiltroStatus": status}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

# ==============================
# ROTA: Disciplinas do Aluno por Período Letivo
# ==============================
@app.get("/aluno/{ra}/disciplinas")
def get_disciplinas_aluno(
    ra: str,
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
                INNER JOIN SALUNO 
                    ON SALUNO.RA = SMATRICULA.RA
                INNER JOIN PPESSOA 
                    ON PPESSOA.CODIGO = SALUNO.CODPESSOA
                INNER JOIN STURMADISC 
                    ON STURMADISC.IDHABILITACAOFILIAL = SMATRICULA.IDHABILITACAOFILIAL
                   AND STURMADISC.IDTURMADISC = SMATRICULA.IDTURMADISC
                INNER JOIN SDISCIPLINA 
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
