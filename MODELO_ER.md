# Modelo Entidade-Relacionamento (ER) - Livraria Online

---

## Diagrama ER (Mermaid)

```mermaid
erDiagram
    CATEGORIAS ||--o{ LIVROS : "possui"
    LIVROS ||--o{ ITENS_PEDIDO : "contem"
    CLIENTES ||--o{ PEDIDOS : "faz"
    PEDIDOS ||--o{ ITENS_PEDIDO : "possui"
    LIVROS ||--o{ AVALIACOES_MONGO : "recebe"

    CATEGORIAS {
        int id PK
        varchar(100) nome UK
        text descricao
    }

    LIVROS {
        int id PK
        varchar(200) titulo
        varchar(150) autor
        varchar(20) isbn UK
        decimal(10,2) preco
        int estoque
        int categoria_id FK
        timestamp created_at
    }

    CLIENTES {
        int id PK
        varchar(150) nome
        varchar(150) email UK
        varchar(20) telefone
        text endereco
        timestamp created_at
    }

    PEDIDOS {
        int id PK
        int cliente_id FK
        timestamp data_pedido
        enum status
        decimal(10,2) total
    }

    ITENS_PEDIDO {
        int pedido_id PK
        int livro_id PK
        int quantidade
        decimal(10,2) preco_unitario
    }

    AVALIACOES_MONGO {
        string _id PK
        int livro_id FK
        string email_cliente
        int nota
        string comentario
        string data
    }
```

---

## Descrição Textual das Entidades e Relacionamentos

### Entidades do MySQL (Relacional)

| Entidade | Atributos | Chaves | Constraints |
|----------|-----------|--------|-------------|
| **CATEGORIAS** | id, nome, descricao | PK: id | nome UNIQUE |
| **LIVROS** | id, titulo, autor, isbn, preco, estoque, categoria_id, created_at | PK: id, FK: categoria_id | isbn UNIQUE, preco >= 0, estoque >= 0 |
| **CLIENTES** | id, nome, email, telefone, endereco, created_at | PK: id | email UNIQUE |
| **PEDIDOS** | id, cliente_id, data_pedido, status, total | PK: id, FK: cliente_id | total >= 0, status ENUM |
| **ITENS_PEDIDO** | pedido_id, livro_id, quantidade, preco_unitario | PK composta: (pedido_id, livro_id), FKs: pedido_id, livro_id | quantidade > 0, preco_unitario >= 0 |

### Entidade do MongoDB (Documento)

| Coleção | Campos | Validações |
|---------|--------|------------|
| **avaliacoes** | _id (ObjectId), livro_id (int), email_cliente (string), nota (int), comentario (string), data (date) | $jsonSchema: required todos, pattern email, nota 1-5, maxLength 500, additionalProperties: false |

---

## Relacionamentos

### MySQL (Integridade Referencial Forte)

1. **CATEGORIAS 1:N LIVROS** — Uma categoria tem N livros; livro pertence a 1 categoria
   - FK: `livros.categoria_id` → `categorias.id`
   - ON DELETE RESTRICT (não apaga categoria com livros)

2. **CLIENTES 1:N PEDIDOS** — Um cliente faz N pedidos; pedido pertence a 1 cliente
   - FK: `pedidos.cliente_id` → `clientes.id`
   - ON DELETE RESTRICT

3. **PEDIDOS 1:N ITENS_PEDIDO** — Um pedido tem N itens; item pertence a 1 pedido
   - FK: `itens_pedido.pedido_id` → `pedidos.id`
   - ON DELETE CASCADE (apaga itens ao apagar pedido)

4. **LIVROS 1:N ITENS_PEDIDO** — Um livro aparece em N itens; item refere 1 livro
   - FK: `itens_pedido.livro_id` → `livros.id`
   - ON DELETE RESTRICT (não apaga livro em pedidos)

### MySQL ↔ MongoDB (Integridade Lógica / Aplicação)

5. **LIVROS 1:N AVALIACOES** — Um livro recebe N avaliações; avaliação refere 1 livro
   - Campo: `avaliacoes.livro_id` → `livros.id` (FK lógica, não enforced pelo banco)
   - Validação na aplicação: antes de inserir avaliação, verifica `SELECT 1 FROM livros WHERE id = ?`
   - Cascade lógico: ao excluir livro, `DELETE FROM livros` + `db.avaliacoes.deleteMany({ livro_id })`

---

## Justificativa da Divisão (Polyglot Persistence)

| Dado | Banco | Por quê |
|------|-------|---------|
| Categorias, Livros, Clientes, Pedidos, Itens | MySQL | Exigem FK, transações ACID, JOINs, constraints (preço≥0, estoque≥0, qtd>0), consistência forte |
| Avaliações | MongoDB | Texto livre, crescimento ilimitado, sem JOINs (sempre filtra por livro_id), schema flexível, validação via $jsonSchema |

---

## Índices

### MySQL (Automáticos via PK/FK)
- PKs: todas as tabelas
- FKs: indexes automáticos em `categoria_id`, `cliente_id`, `pedido_id`, `livro_id`
- UNIQUE: `categorias.nome`, `livros.isbn`, `clientes.email`

### MongoDB
```javascript
db.avaliacoes.createIndex({ livro_id: 1 }, { name: "idx_livro_id" })
```
**Justificativa:** Todas as consultas de avaliação filtram por `livro_id` (listar por livro, calcular média via `$group/$avg`). Sem índice = collection scan.

---

## Validações Específicas

### MySQL (CHECK Constraints)
- `livros.preco >= 0`
- `livros.estoque >= 0`
- `itens_pedido.quantidade > 0`
- `itens_pedido.preco_unitario >= 0`
- `pedidos.total >= 0`

### MongoDB ($jsonSchema)
```json
{
  "validationAction": "error",
  "validationLevel": "strict",
  "validator": {
    "$jsonSchema": {
      "bsonType": "object",
      "required": ["livro_id", "email_cliente", "nota", "comentario", "data"],
      "additionalProperties": false,
      "properties": {
        "_id": { "bsonType": "objectId" },
        "livro_id": { "bsonType": "int", "minimum": 1 },
        "email_cliente": { "bsonType": "string", "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$" },
        "nota": { "bsonType": "int", "minimum": 1, "maximum": 5 },
        "comentario": { "bsonType": "string", "maxLength": 500 },
        "data": { "bsonType": "date" }
      }
    }
  }
}
```

---

## Como Visualizar o Diagrama Mermaid

1. **VS Code**: Instale extensão "Markdown Preview Mermaid Support" → Ctrl+Shift+V
2. **GitHub/GitLab**: Renderiza automaticamente em `.md`
3. **Online**: Cole em https://mermaid.live/
4. **Obsidian/Notion**: Suporte nativo