#!/usr/bin/env python3
"""
Livraria Online - Aplicacao Terminal (MySQL + MongoDB)
Atividade Final - Banco de Dados II

Requisitos atendidos:
- MySQL: 5 tabelas com PK, FK, CHECK, CRUD, JOIN
- MongoDB: colecao com $jsonSchema (pattern, maxLength, range), indice, validationAction: error
- Integracao: livro + preco + estoque + media notas (MySQL + Mongo $group/$avg)
- Demo: insercao de documento invalido rejeitada pelo $jsonSchema
- Validacao: livro deve existir no MySQL antes de avaliar
- Cascade: excluir livro remove avaliacoes no Mongo
"""

import sys
import pymysql
import pymongo
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any


# ===================== CONFIGURACAO =====================

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "livraria",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": False,
}

MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "livraria"
MONGO_COLLECTION = "avaliacoes"


# ===================== CONEXOES =====================

def get_mysql_conn():
    return pymysql.connect(**MYSQL_CONFIG)


def get_mongo_collection():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db[MONGO_COLLECTION]


# ===================== UTILITARIOS =====================

def input_int(prompt: str, min_val: int = None, max_val: int = None) -> int:
    while True:
        try:
            val = int(input(prompt).strip())
            if min_val is not None and val < min_val:
                print(f"  Valor deve ser >= {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"  Valor deve ser <= {max_val}")
                continue
            return val
        except ValueError:
            print("  Digite um numero inteiro valido.")


def input_float(prompt: str, min_val: float = None) -> float:
    while True:
        try:
            val = float(input(prompt).strip().replace(",", "."))
            if min_val is not None and val < min_val:
                print(f"  Valor deve ser >= {min_val}")
                continue
            return val
        except ValueError:
            print("  Digite um numero valido.")


def input_str(prompt: str, required: bool = True, max_len: int = None) -> str:
    while True:
        val = input(prompt).strip()
        if not val and required:
            print("  Campo obrigatorio.")
            continue
        if max_len and len(val) > max_len:
            print(f"  Maximo {max_len} caracteres.")
            continue
        return val


def input_email(prompt: str) -> str:
    import re
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    while True:
        val = input(prompt).strip()
        if re.match(pattern, val):
            return val
        print("  E-mail invalido. Exemplo: usuario@dominio.com")


def pause():
    input("\n  Pressione Enter para continuar...")


def print_header(titulo: str):
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}")


# ===================== CRUD LIVROS (MySQL) =====================

def listar_categorias(conn) -> List[Dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, nome FROM categorias ORDER BY nome")
        return cur.fetchall()


def criar_livro(conn):
    print_header("NOVO LIVRO")
    titulo = input_str("  Titulo: ", required=True, max_len=200)
    autor = input_str("  Autor: ", required=True, max_len=150)
    isbn = input_str("  ISBN (opcional): ", required=False, max_len=20) or None

    preco = input_float("  Preco (>= 0): ", min_val=0)
    estoque = input_int("  Estoque (>= 0): ", min_val=0)

    cats = listar_categorias(conn)
    print("\n  Categorias:")
    for c in cats:
        print(f"    [{c['id']}] {c['nome']}")
    categoria_id = input_int("  Categoria ID: ", min_val=1)

    # Valida se categoria existe
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM categorias WHERE id = %s", (categoria_id,))
        if not cur.fetchone():
            print("  [ERRO] Categoria inexistente.")
            return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO livros (titulo, autor, isbn, preco, estoque, categoria_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (titulo, autor, isbn, preco, estoque, categoria_id))
        conn.commit()
        print("  [OK] Livro cadastrado com sucesso.")
    except pymysql.IntegrityError as e:
        conn.rollback()
        print(f"  [ERRO] Erro de integridade: {e}")
    except Exception as e:
        conn.rollback()
        print(f"  [ERRO] Erro: {e}")


def listar_livros(conn, mostrar_detalhes: bool = False):
    print_header("LIVROS CADASTRADOS")
    with conn.cursor() as cur:
        cur.execute("""
            SELECT l.id, l.titulo, l.autor, l.isbn, l.preco, l.estoque,
                   c.nome AS categoria
            FROM livros l
            JOIN categorias c ON l.categoria_id = c.id
            ORDER BY l.titulo
        """)
        livros = cur.fetchall()

    if not livros:
        print("  Nenhum livro cadastrado.")
        return

    for lv in livros:
        print(f"  [{lv['id']}] {lv['titulo']} - {lv['autor']}")
        print(f"       ISBN: {lv['isbn'] or 'N/A'} | Preco: R$ {lv['preco']:.2f} | Estoque: {lv['estoque']} | Categoria: {lv['categoria']}")
        if mostrar_detalhes:
            media = calcular_media_avaliacoes(lv['id'])
            qtd = contar_avaliacoes(lv['id'])
            print(f"       * Media: {media:.1f} ({qtd} avaliacoes)")
        print()


def buscar_livro_por_id(conn, livro_id: int) -> Optional[Dict]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT l.*, c.nome AS categoria_nome
            FROM livros l
            JOIN categorias c ON l.categoria_id = c.id
            WHERE l.id = %s
        """, (livro_id,))
        return cur.fetchone()


def atualizar_livro(conn):
    print_header("ATUALIZAR LIVRO")
    livro_id = input_int("  ID do livro: ", min_val=1)
    livro = buscar_livro_por_id(conn, livro_id)
    if not livro:
        print("  [ERRO] Livro nao encontrado.")
        return

    print(f"  Atualizando: {livro['titulo']} (deixe vazio para manter)")
    titulo = input_str(f"  Titulo [{livro['titulo']}]: ", required=False, max_len=200) or livro['titulo']
    autor = input_str(f"  Autor [{livro['autor']}]: ", required=False, max_len=150) or livro['autor']
    isbn = input_str(f"  ISBN [{livro['isbn'] or ''}]: ", required=False, max_len=20) or None
    preco = input_float(f"  Preco [{livro['preco']:.2f}]: ", min_val=0)
    estoque = input_int(f"  Estoque [{livro['estoque']}]: ", min_val=0)

    cats = listar_categorias(conn)
    print("\n  Categorias:")
    for c in cats:
        print(f"    [{c['id']}] {c['nome']}")
    cat_input = input_str(f"  Categoria ID [{livro['categoria_id']}]: ", required=False)
    categoria_id = int(cat_input) if cat_input else livro['categoria_id']

    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM categorias WHERE id = %s", (categoria_id,))
        if not cur.fetchone():
            print("  [ERRO] Categoria inexistente.")
            return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE livros SET titulo=%s, autor=%s, isbn=%s, preco=%s, estoque=%s, categoria_id=%s
                WHERE id=%s
            """, (titulo, autor, isbn, preco, estoque, categoria_id, livro_id))
        conn.commit()
        print("  [OK] Livro atualizado.")
    except pymysql.IntegrityError as e:
        conn.rollback()
        print(f"  [ERRO] Erro: {e}")


def excluir_livro(conn):
    print_header("EXCLUIR LIVRO")
    livro_id = input_int("  ID do livro: ", min_val=1)
    livro = buscar_livro_por_id(conn, livro_id)
    if not livro:
        print("  [ERRO] Livro nao encontrado.")
        return

    # Verifica se ha pedidos referenciando
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM itens_pedido WHERE livro_id = %s", (livro_id,))
        if cur.fetchone():
            print("  [ERRO] Nao e possivel excluir: livro esta em pedidos.")
            return

    confirm = input_str(f"  Confirma exclusao de '{livro['titulo']}'? (s/N): ", required=False).lower()
    if confirm != 's':
        print("  Cancelado.")
        return

    try:
        # Remove avaliacoes no Mongo (cascade logico)
        col = get_mongo_collection()
        result = col.delete_many({"livro_id": livro_id})
        print(f"  [DEL]  {result.deleted_count} avaliacao(oes) removida(s) do MongoDB.")

        with conn.cursor() as cur:
            cur.execute("DELETE FROM livros WHERE id = %s", (livro_id,))
        conn.commit()
        print("  [OK] Livro excluido.")
    except Exception as e:
        conn.rollback()
        print(f"  [ERRO] Erro: {e}")


# ===================== CRUD AVALIACOES (MongoDB) =====================

def contar_avaliacoes(livro_id: int) -> int:
    col = get_mongo_collection()
    return col.count_documents({"livro_id": livro_id})


def calcular_media_avaliacoes(livro_id: int) -> float:
    col = get_mongo_collection()
    pipeline = [
        {"$match": {"livro_id": livro_id}},
        {"$group": {"_id": None, "media": {"$avg": "$nota"}}}
    ]
    result = list(col.aggregate(pipeline))
    return round(result[0]["media"], 1) if result else 0.0


def criar_avaliacao():
    print_header("NOVA AVALIACAO")
    col = get_mongo_collection()
    conn = get_mysql_conn()

    livro_id = input_int("  ID do livro: ", min_val=1)

    # Valida existencia no MySQL (requisito de integracao)
    livro = buscar_livro_por_id(conn, livro_id)
    conn.close()
    if not livro:
        print("  [ERRO] Livro nao existe no MySQL. Cadastre o livro primeiro.")
        return

    print(f"  Avaliando: {livro['titulo']} - {livro['autor']}")

    email = input_email("  E-mail do cliente: ")
    nota = input_int("  Nota (1 a 5): ", min_val=1, max_val=5)
    comentario = input_str("  Comentario (max 500 chars): ", required=True, max_len=500)

    doc = {
        "livro_id": livro_id,
        "email_cliente": email,
        "nota": nota,
        "comentario": comentario,
        "data": datetime.now()
    }

    try:
        col.insert_one(doc)
        print("  [OK] Avaliacao registrada.")
    except pymongo.errors.WriteError as e:
        if "validation failed" in str(e):
            print(f"  [ERRO] Documento invalido rejeitado pelo $jsonSchema: {e.details.get('errmsg', e)}")
        else:
            print(f"  [ERRO] Erro de escrita: {e}")
    except Exception as e:
        print(f"  [ERRO] Erro: {e}")


def listar_avaliacoes_por_livro():
    print_header("AVALIACOES POR LIVRO")
    livro_id = input_int("  ID do livro: ", min_val=1)

    conn = get_mysql_conn()
    livro = buscar_livro_por_id(conn, livro_id)
    conn.close()

    if not livro:
        print("  [ERRO] Livro nao encontrado.")
        return

    col = get_mongo_collection()
    avals = list(col.find({"livro_id": livro_id}).sort("data", -1))

    print(f"\n  Livro: {livro['titulo']} - {livro['autor']}")
    print(f"  Total: {len(avals)} avaliacao(oes) | Media: {calcular_media_avaliacoes(livro_id):.1f}\n")

    if not avals:
        print("  Nenhuma avaliacao.")
        return

    for a in avals:
        data_str = a["data"].strftime("%d/%m/%Y")
        print(f"  * {a['nota']}/5 | {a['email_cliente']} | {data_str}")
        print(f"     \"{a['comentario']}\"\n")


def atualizar_avaliacao():
    print_header("ATUALIZAR AVALIACAO")
    col = get_mongo_collection()

    livro_id = input_int("  ID do livro: ", min_val=1)
    email = input_email("  E-mail do cliente (identificador): ")

    doc = col.find_one({"livro_id": livro_id, "email_cliente": email})
    if not doc:
        print("  [ERRO] Avaliacao nao encontrada.")
        return

    print(f"  Atualizando nota {doc['nota']} e comentario (deixe vazio para manter)")
    nota_input = input_str(f"  Nova nota 1-5 [{doc['nota']}]: ", required=False)
    nota = int(nota_input) if nota_input else doc['nota']
    if nota < 1 or nota > 5:
        print("  [ERRO] Nota deve ser 1-5.")
        return

    comentario = input_str(f"  Novo comentario [{doc['comentario'][:50]}...]: ", required=False, max_len=500)
    comentario = comentario if comentario else doc['comentario']

    try:
        col.update_one(
            {"_id": doc["_id"]},
            {"$set": {"nota": nota, "comentario": comentario}}
        )
        print("  [OK] Avaliacao atualizada.")
    except pymongo.errors.WriteError as e:
        if "validation failed" in str(e):
            print(f"  [ERRO] Rejeitado pelo $jsonSchema: {e.details.get('errmsg', e)}")
        else:
            print(f"  [ERRO] Erro: {e}")


def excluir_avaliacao():
    print_header("EXCLUIR AVALIACAO")
    col = get_mongo_collection()

    livro_id = input_int("  ID do livro: ", min_val=1)
    email = input_email("  E-mail do cliente: ")

    result = col.delete_one({"livro_id": livro_id, "email_cliente": email})
    if result.deleted_count:
        print("  [OK] Avaliacao excluida.")
    else:
        print("  [ERRO] Avaliacao nao encontrada.")


# ===================== INTEGRACAO MySQL + MongoDB =====================

def relatorio_livro_com_media():
    """
    FUNCAO DE INTEGRACAO (requisito obrigatorio):
    Mostra livro + preco + estoque (MySQL) + media das notas (Mongo $group/$avg)
    """
    print_header("RELATORIO: LIVRO + MEDIA DE AVALIACOES (MySQL + Mongo)")
    livro_id = input_int("  ID do livro: ", min_val=1)

    conn = get_mysql_conn()
    livro = buscar_livro_por_id(conn, livro_id)
    conn.close()

    if not livro:
        print("  [ERRO] Livro nao encontrado no MySQL.")
        return

    media = calcular_media_avaliacoes(livro_id)
    qtd = contar_avaliacoes(livro_id)

    print(f"\n  [LIVRO] {livro['titulo']}")
    print(f"     Autor: {livro['autor']}")
    print(f"     Categoria: {livro['categoria_nome']}")
    print(f"     Preco: R$ {livro['preco']:.2f}")
    print(f"     Estoque: {livro['estoque']} unidades")
    print(f"     ISBN: {livro['isbn'] or 'N/A'}")
    print(f"\n  * Avaliacoes (MongoDB):")
    print(f"     Quantidade: {qtd}")
    print(f"     Media: {media:.1f} / 5.0")

    if qtd > 0:
        col = get_mongo_collection()
        pipeline = [
            {"$match": {"livro_id": livro_id}},
            {"$group": {"_id": "$nota", "count": {"$sum": 1}}},
            {"$sort": {"_id": -1}}
        ]
        dist = list(col.aggregate(pipeline))
        print("     Distribuicao:")
        for d in dist:
            barra = "#" * d["count"]
            print(f"       {d['_id']}*: {d['count']} {barra}")


def demonstrar_schema_invalido():
    """
    DEMO OBRIGATORIA: Tenta inserir documento invalido para mostrar
    o $jsonSchema rejeitando (validationAction: error).
    """
    print_header("DEMO: DOCUMENTO INVALIDO REJEITADO PELO $jsonSchema")
    col = get_mongo_collection()

    print("  Tentando inserir avaliacao com:")
    print("    - nota = 6 (fora do range 1-5)")
    print("    - email = 'invalido' (nao casa com pattern)")
    print("    - comentario com 600 chars (excede maxLength 500)")
    print()

    doc_invalido = {
        "livro_id": 1,
        "email_cliente": "invalido",           # falha no pattern
        "nota": 6,                              # falha no maximum
        "comentario": "x" * 600,                # falha no maxLength
        "data": datetime.now()
    }

    try:
        col.insert_one(doc_invalido)
        print("  [ERRO] INESPERADO: documento foi aceito (schema nao esta funcionando)")
    except pymongo.errors.WriteError as e:
        errmsg = e.details.get("errmsg", str(e))
        print(f"  [OK] REJEITADO PELO $jsonSchema (validationAction: error)")
        print(f"     Erro: {errmsg}")
    except Exception as e:
        print(f"  [ERRO] Erro inesperado: {e}")

    print("\n  ---")
    print("  Agora tentando com dados validos (deve funcionar):")

    doc_valido = {
        "livro_id": 1,
        "email_cliente": "teste@demo.com",
        "nota": 4,
        "comentario": "Avaliacao de teste para demonstrar que dados validos passam.",
        "data": datetime.now()
    }

    try:
        col.insert_one(doc_valido)
        print("  [OK] Documento valido aceito.")
        # Limpa o demo
        col.delete_one({"email_cliente": "teste@demo.com"})
        print("  [LIMPO] Demo removido.")
    except Exception as e:
        print(f"  [ERRO] Erro: {e}")


# ===================== MENUS =====================

def menu_livros(conn):
    while True:
        print_header("MENU LIVROS (MySQL)")
        print("  [1] Listar todos")
        print("  [2] Buscar por ID")
        print("  [3] Cadastrar")
        print("  [4] Atualizar")
        print("  [5] Excluir (remove avaliacoes no Mongo)")
        print("  [0] Voltar")
        op = input_str("  Opcao: ", required=False)

        if op == "1":
            listar_livros(conn, mostrar_detalhes=True)
        elif op == "2":
            livro_id = input_int("  ID: ", min_val=1)
            livro = buscar_livro_por_id(conn, livro_id)
            if livro:
                print(f"\n  {livro['titulo']} - {livro['autor']}")
                print(f"  Preco: R$ {livro['preco']:.2f} | Estoque: {livro['estoque']}")
                print(f"  Categoria: {livro['categoria_nome']}")
                media = calcular_media_avaliacoes(livro_id)
                qtd = contar_avaliacoes(livro_id)
                print(f"  * Media: {media:.1f} ({qtd} avaliacoes)")
            else:
                print("  [ERRO] Nao encontrado.")
        elif op == "3":
            criar_livro(conn)
        elif op == "4":
            atualizar_livro(conn)
        elif op == "5":
            excluir_livro(conn)
        elif op == "0":
            break
        else:
            print("  Opcao invalida.")
        pause()


def menu_avaliacoes():
    while True:
        print_header("MENU AVALIACOES (MongoDB)")
        print("  [1] Listar por livro")
        print("  [2] Cadastrar (valida livro no MySQL)")
        print("  [3] Atualizar")
        print("  [4] Excluir")
        print("  [0] Voltar")
        op = input_str("  Opcao: ", required=False)

        if op == "1":
            listar_avaliacoes_por_livro()
        elif op == "2":
            criar_avaliacao()
        elif op == "3":
            atualizar_avaliacao()
        elif op == "4":
            excluir_avaliacao()
        elif op == "0":
            break
        else:
            print("  Opcao invalida.")
        pause()


def menu_integracao():
    while True:
        print_header("INTEGRACAO MySQL + MongoDB")
        print("  [1] Relatorio: Livro + Preco + Estoque + Media notas")
        print("  [2] Demo: Documento invalido rejeitado pelo $jsonSchema")
        print("  [0] Voltar")
        op = input_str("  Opcao: ", required=False)

        if op == "1":
            relatorio_livro_com_media()
        elif op == "2":
            demonstrar_schema_invalido()
        elif op == "0":
            break
        else:
            print("  Opcao invalida.")
        pause()


def main():
    print_header("LIVRARIA ONLINE - MySQL + MongoDB")
    print("  Atividade Final - Banco de Dados II")

    # Testa conexoes
    try:
        conn = get_mysql_conn()
        conn.ping()
        conn.close()
        print("  [OK] MySQL conectado")
    except Exception as e:
        print(f"  [ERRO] MySQL falhou: {e}")
        print("     Verifique XAMPP/MySQL rodando e credenciais em MYSQL_CONFIG")
        sys.exit(1)

    try:
        col = get_mongo_collection()
        col.database.command("ping")
        print("  [OK] MongoDB conectado")
    except Exception as e:
        print(f"  [ERRO] MongoDB falhou: {e}")
        print("     Verifique mongod rodando na porta 27017")
        sys.exit(1)

    while True:
        print_header("MENU PRINCIPAL")
        print("  [1] Gerenciar Livros (MySQL)")
        print("  [2] Gerenciar Avaliacoes (MongoDB)")
        print("  [3] Integracao MySQL + MongoDB")
        print("  [0] Sair")
        op = input_str("  Opcao: ", required=False)

        if op == "1":
            conn = get_mysql_conn()
            try:
                menu_livros(conn)
            finally:
                conn.close()
        elif op == "2":
            menu_avaliacoes()
        elif op == "3":
            menu_integracao()
        elif op == "0":
            print("\n  Ate logo!")
            break
        else:
            print("  Opcao invalida.")
            pause()


if __name__ == "__main__":
    main()