# Livraria Online -- MySQL + MongoDB

**Atividade Final -- Banco de Dados II**  
**Curso: Analise e Desenvolvimento de Sistemas**

---

## [INFORMACOES PARA APRESENTACAO]

**Integrantes:** Eduardo Heckler, Gabriel Bonow, Adrian Pety

**Tema da aplicacao:** Livraria online com catalogo de livros, gestao de clientes/pedidos e sistema de avaliacoes.

**Linguagem utilizada:** Python 3.10+

**SGBD relacional escolhido:** MySQL/MariaDB (via XAMPP)

**SGBD NoSQL:** MongoDB Community Edition

**Como executar a aplicacao:**
1. Suba o MySQL (XAMPP) e MongoDB (mongod)
2. Crie o banco MySQL: `mysql -u root -p < schema_mysql.sql` (senha vazia, aperte Enter)
3. Crie a colecao MongoDB: `mongosh < mongo_setup.js`
4. Instale dependencias: `pip install pymysql pymongo`
5. Rode: `python app.py`

**Como os dois bancos sao utilizados:**
- **MySQL:** Armazena dados transacionais e estruturados (categorias, livros, clientes, pedidos, itens_pedido). Usa PK/FK, CHECK constraints, ENUM, JOINs. Garante integridade referencial e consistencia ACID.
- **MongoDB:** Armazena avaliacoes (texto livre, crescimento ilimitado). Colecao `avaliacoes` validada por `$jsonSchema` com pattern (email), range (nota 1-5), maxLength (comentario 500 chars). Indice em `livro_id` para consultas rapidas.
- **Integracao real:** (1) Relatorio mostra livro+preco+estoque (MySQL) + media de notas (MongoDB $group/$avg). (2) Ao avaliar, valida se livro existe no MySQL antes de inserir no Mongo. (3) Ao excluir livro, remove avaliacoes no Mongo (cascade logico).

**Por que essa divisao?**
- **Relacional (MySQL):** Preco, estoque, pedidos exigem integridade referencial (FK), transacoes ACID (estoque nao fica negativo, pedido so existe com cliente valido), consultas com JOIN (relatorios cruzando tabelas). Modelo relacional garante consistencia forte.
- **MongoDB:** Avaliacoes sao texto livre, crescem sem limite pre-definido, nao precisam de JOINs (sempre consultadas por livro_id), esquema pode variar futuramente (tags, recomendaria). Documentos sao modelo natural.

---

## [OBJETIVO]

Aplicacao de terminal em Python que usa **dois bancos de dados simultaneamente**, complementando-se na mesma funcionalidade (nao apenas coexistindo).

- **MySQL** (relacional): dados transacionais, integridade referencial, consultas com JOIN
- **MongoDB** (documentos): avaliacoes livres, crescimento ilimitado, validacao por `$jsonSchema`

---

## [STACK]

| Componente | Versao/Detalhe |
|------------|----------------|
| Python     | 3.10+          |
| MySQL/MariaDB | Via XAMPP (porta 3306) |
| MongoDB Community | Local, porta 27017 |
| Drivers    | `pymysql`, `pymongo` |

Instale as dependencias:
```bash
pip install pymysql pymongo
```

---

## [ESTRUTURA DOS BANCOS]

### MySQL -- Banco `livraria` (5 tabelas)

| Tabela | Finalidade | Constraints |
|--------|------------|-------------|
| `categorias` | Classificacao dos livros | PK `id`, `nome` UNIQUE |
| `livros` | Catalogo (preco, estoque) | PK `id`, FK `categoria_id`, CHECK `preco>=0`, `estoque>=0` |
| `clientes` | Cadastro de compradores | PK `id`, `email` UNIQUE |
| `pedidos` | Cabecalho do pedido | PK `id`, FK `cliente_id`, CHECK `total>=0`, ENUM `status` |
| `itens_pedido` | Linhas do pedido | PK composta (`pedido_id`, `livro_id`), FKs, CHECK `quantidade>0`, `preco_unitario>=0` |

**Por que relacional?**  
Preco, estoque e pedidos exigem **integridade referencial** (FKs), **transacoes ACID** (estoque nao pode ficar negativo, pedido nao pode existir sem cliente) e **consultas com JOIN** (relatorios cruzando tabelas). O modelo relacional garante consistencia forte nesses cenarios.

---

### MongoDB -- Banco `livraria`, Colecao `avaliacoes`

```json
{
  "livro_id": 1,                    // int, FK logica para MySQL.livros.id
  "email_cliente": "user@email.com", // string, pattern RFC 5322 simplificado
  "nota": 5,                         // int, 1 a 5
  "comentario": "Otimo livro...",    // string, maxLength 500
  "data": ISODate("2024-01-15")      // date
}
```

**Validacao (`$jsonSchema`):**
- `validationAction: "error"` -- rejeita documento invalido
- `validationLevel: "strict"` -- aplica em insert e update
- `pattern` no `email_cliente`: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- `minimum`/`maximum` na `nota`: 1 a 5
- `maxLength` no `comentario`: 500
- `additionalProperties: false` -- proibe campos extras

**Indice:**
```javascript
db.avaliacoes.createIndex({ livro_id: 1 }, { name: "idx_livro_id" })
```
**Justificativa:** Toda consulta de avaliacoes filtra por `livro_id` (listagem por livro, calculo de media via `$group/$avg`). Sem indice, haveria *collection scan* a cada busca -- inviavel conforme a colecao cresce.

**Por que MongoDB?**  
Avaliacoes sao **texto livre**, **crescem sem limite pre-definido** (cada livro pode ter N avaliacoes), **nao precisam de JOINs** (sempre consultadas por `livro_id`) e o esquema pode variar (ex.: futuramente adicionar `tags`, `recomendaria`). Documentos sao o modelo natural.

---

## [INTEGRACAO (MEIO A MEIO)]

A aplicacao implementa **duas funcionalidades que usam os dois bancos juntos**:

1. **Relatorio integrado** (`menu_integracao` -> opcao 1)  
   Busca livro no MySQL (titulo, autor, preco, estoque, categoria via JOIN) **e** calcula media de notas no MongoDB via pipeline de agregacao (`$match` + `$group` + `$avg`). Exibe tudo junto.

2. **Validacao cruzada** (ao cadastrar avaliacao)  
   Antes de inserir no Mongo, o codigo verifica se `livro_id` existe no MySQL (`SELECT 1 FROM livros WHERE id = %s`). Garante que nao ha avaliacao "orfas" de livro inexistente.

3. **Cascade logico** (ao excluir livro)  
   `DELETE FROM livros` no MySQL -> `delete_many({ livro_id })` no Mongo. Remove avaliacoes orfas automaticamente.

---

## [COMO EXECUTAR]

### 1. Suba os bancos

**MySQL (XAMPP):**
- Inicie Apache + MySQL no painel do XAMPP
- Crie o banco e tabelas:
  ```bash
  mysql -u root -p < schema_mysql.sql
  ```
  (Senha padrao do XAMPP costuma ser vazia; aperte Enter)

**MongoDB:**
- Inicie o servico: `mongod` (ou via Services do Windows)
- Execute o setup:
  ```bash
  mongosh < mongo_setup.js
  ```
  Isso cria a colecao `avaliacoes` com validacao, indice e dados de exemplo.

### 2. Configure credenciais (se necessario)

Edite `app.py` na secao `MYSQL_CONFIG` se seu MySQL tiver senha:
```python
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "sua_senha_aqui",  # <-- altere se needed
    "database": "livraria",
    ...
}
```

### 3. Rode a aplicacao

```bash
python app.py
```

---

## [O QUE TESTAR (PARA A APRESENTACAO)]

| Cenario | O que Demonstrar |
|---------|------------------|
| **CRUD Livros** | Create, Read, Update, Delete no MySQL; JOIN com categorias |
| **CRUD Avaliacoes** | Create, Read, Update, Delete no Mongo |
| **Validacao $jsonSchema** | Menu Integracao -> Opcao 2: tenta inserir nota=6, email invalido, comentario >500 chars -> **rejeitado com erro** |
| **Validacao cruzada** | Tentar avaliar livro_id=999 (nao existe) -> bloqueado |
| **Relatorio integrado** | Menu Integracao -> Opcao 1: mostra dados MySQL + media Mongo na mesma tela |
| **Cascade delete** | Excluir livro que tem avaliacoes -> ambas removidas |
| **Indice Mongo** | `db.avaliacoes.explain("executionStats").find({ livro_id: 1 })` -> mostra `IXSCAN` usando `idx_livro_id` |

---

## [ARQUIVOS DO PROJETO]

```
.
├── schema_mysql.sql      # DDL MySQL + dados de exemplo
├── mongo_setup.js        # Criacao colecao, $jsonSchema, indice, dados
├── app.py                # Aplicacao terminal (menus, CRUDs, integracao)
└── README.md             # Este arquivo
```

---

## [GRUPO]

Todos os integrantes devem saber:
- Explicar a divisao de dados entre MySQL e MongoDB
- Mostrar o `$jsonSchema` rejeitando documento invalido
- Alterar o codigo na hora (ex.: mudar range da nota, adicionar campo no schema)
- Rodar o projeto do zero em outra maquina

---

## [LICENCA]

Trabalho academico -- uso educacional.