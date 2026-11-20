# Livraria Online — MySQL + MongoDB

**Atividade Final — Banco de Dados II**  
**Curso: Análise e Desenvolvimento de Sistemas**

---

## 👥 Quem fez

**Integrantes:** Eduardo Heckler, Gabriel Bonow, Adrian Pety

---

## 🎯 O que é isso

Uma livraria online de terminal feita em **Python** que usa **dois bancos de dados ao mesmo tempo** — não é só "dois bancos rodando lado a lado", eles **conversam entre si** na mesma funcionalidade.

- **MySQL (relacional):** catálogo, clientes, pedidos, estoque — tudo que precisa de consistência forte, chaves estrangeiras, transações.
- **MongoDB (documentos):** avaliações dos livros — texto livre, cresce sem limite, não precisa de JOIN.

---

## 🛠 Stack

| Componente | Versão/Detalhe |
|------------|----------------|
| Python     | 3.10+          |
| MySQL/MariaDB | Via XAMPP (porta 3306) |
| MongoDB Community | Local, porta 27017 |
| Drivers    | `pymysql`, `pymongo` |

```bash
pip install pymysql pymongo
```

---

## 🗄 Como os dados estão organizados

### MySQL — banco `livraria` (5 tabelas)

| Tabela | Pra que serve | Principais constraints |
|--------|---------------|------------------------|
| `categorias` | Classificação dos livros | PK `id`, `nome` UNIQUE |
| `livros` | Catálogo (preço, estoque) | PK `id`, FK `categoria_id`, CHECK `preco>=0`, `estoque>=0` |
| `clientes` | Cadastro de compradores | PK `id`, `email` UNIQUE |
| `pedidos` | Cabeçalho do pedido | PK `id`, FK `cliente_id`, CHECK `total>=0`, ENUM `status` |
| `itens_pedido` | Linhas do pedido | PK composta (`pedido_id`, `livro_id`), FKs, CHECK `quantidade>0`, `preco_unitario>=0` |

**Por que relacional?**  
Preço, estoque e pedidos **não podem dar erro**. Um pedido não existe sem cliente, estoque não fica negativo, relatórios cruzam tabelas com JOIN. O modelo relacional garante essa consistência forte (ACID, FK, CHECK).

---

### MongoDB — banco `livraria`, coleção `avaliacoes`

```json
{
  "livro_id": 1,                    // int, FK lógica para MySQL.livros.id
  "email_cliente": "user@email.com", // string, validado por regex
  "nota": 5,                         // int, 1 a 5
  "comentario": "Ótimo livro...",    // string, máx 500 chars
  "data": ISODate("2024-01-15")      // date
}
```

**Validação (`$jsonSchema`):**
- `validationAction: "error"` — rejeita documento inválido na hora
- `validationLevel: "strict"` — vale pra insert e update
- `pattern` no email: regex RFC 5322 simplificado
- `minimum`/`maximum` na nota: 1 a 5
- `maxLength` no comentário: 500
- `additionalProperties: false` — nada de campo extra

**Índice:**
```javascript
db.avaliacoes.createIndex({ livro_id: 1 }, { name: "idx_livro_id" })
```
**Por que?** Toda busca de avaliação filtra por `livro_id` (listar, média). Sem índice = *collection scan* a cada query. Inviável quando cresce.

**Por que MongoDB?**  
Avaliação é **texto livre**, cada livro pode ter N avaliações (sem teto), sempre busca por `livro_id` (nunca faz JOIN), e o esquema pode mudar amanhã (ex.: adicionar `tags`, `recomendaria`). Documento é o modelo natural pra isso.

---

## 🔗 A integração (onde a mágica acontece)

A aplicação tem **três pontos onde os dois bancos trabalham juntos**:

1. **Relatório integrado** (`Menu Integração → Opção 1`)  
   Busca o livro no MySQL (título, autor, preço, estoque, categoria via JOIN) **e** calcula a média das notas no MongoDB via pipeline de agregação (`$match` + `$group` + `$avg`). Mostra tudo junto na tela.

2. **Validação cruzada** (ao cadastrar avaliação)  
   Antes de gravar no Mongo, o código checa se o `livro_id` existe no MySQL (`SELECT 1 FROM livros WHERE id = %s`). Não deixa criar avaliação "órfã" de livro que não existe.

3. **Cascade lógico** (ao excluir livro)  
   `DELETE FROM livros` no MySQL → `delete_many({ livro_id })` no Mongo. Remove as avaliações órfãs automaticamente.

---

## 🚀 Como rodar

### 1. Suba os bancos

**MySQL (XAMPP):**
- Abra o XAMPP, inicie **Apache** e **MySQL**
- Crie o banco e as tabelas:
  ```bash
  mysql -u root -p < schema_mysql.sql
  ```
  (Senha padrão do XAMPP é vazia — só aperte **Enter**)

**MongoDB:**
- Inicie o serviço: `mongod` (ou pelo Services do Windows)
- Rode o setup:
  ```bash
  mongosh < mongo_setup.js
  ```
  Isso cria a coleção `avaliacoes` com validação, índice e 10 avaliações de exemplo.

### 2. Ajuste credenciais (se precisar)

Se seu MySQL tiver senha, edite `app.py` na seção `MYSQL_CONFIG`:
```python
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "sua_senha_aqui",  # <-- coloque aqui
    "database": "livraria",
    ...
}
```

### 3. Rode

```bash
python app.py
```

---

## 🧪 O que testar na apresentação

| Cenário | O que mostrar |
|---------|---------------|
| **CRUD Livros** | Create, Read, Update, Delete no MySQL; JOIN com categorias |
| **CRUD Avaliações** | Create, Read, Update, Delete no Mongo |
| **Validação `$jsonSchema`** | Menu Integração → Opção 2: tenta inserir nota=6, email inválido, comentário >500 chars → **rejeitado com erro** |
| **Validação cruzada** | Tentar avaliar `livro_id=999` (não existe) → bloqueado |
| **Relatório integrado** | Menu Integração → Opção 1: dados MySQL + média Mongo na mesma tela |
| **Cascade delete** | Excluir livro que tem avaliações → ambas removidas |
| **Índice Mongo** | `db.avaliacoes.explain("executionStats").find({ livro_id: 1 })` → mostra `IXSCAN` usando `idx_livro_id` |

---

## 📁 Arquivos do projeto

```
.
├── schema_mysql.sql      # DDL MySQL + dados de exemplo
├── mongo_setup.js        # Criação coleção, $jsonSchema, índice, dados
├── app.py                # Aplicação terminal (menus, CRUDs, integração)
├── MODELO_ER.md          # Diagrama ER (Mermaid) + descrição textual
├── run_schema.bat        # Script pra recriar banco MySQL limpo
└── README.md             # Este arquivo
```

---

## 👨‍💻 O que o grupo precisa saber

Todo mundo tem que conseguir:
- Explicar **por que** dividiu os dados assim (relacional vs documento)
- Mostrar o **`$jsonSchema` rejeitando** documento inválido ao vivo
- Alterar o código na hora (ex.: mudar range da nota, adicionar campo no schema)
- Subir o projeto do zero em outra máquina

---

## 📝 Licença

Trabalho acadêmico — uso educacional.