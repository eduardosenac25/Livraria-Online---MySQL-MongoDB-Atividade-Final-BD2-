// Livraria Online - Setup MongoDB
// Banco: livraria
// Colecao: avaliacoes
// Validacao via $jsonSchema com pattern (regex) e indice em livro_id

use livraria;

// Remove colecao se existir (para reexecucao limpa)
db.avaliacoes.drop();

// Cria colecao com validacao estrita
db.createCollection("avaliacoes", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["livro_id", "email_cliente", "nota", "comentario", "data"],
            additionalProperties: false,
            properties: {
                _id: {
                    bsonType: "objectId",
                    description: "ID automatico do MongoDB"
                },
                livro_id: {
                    bsonType: "int",
                    minimum: 1,
                    description: "ID do livro no MySQL (FK logica)"
                },
                email_cliente: {
                    bsonType: "string",
                    pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                    description: "E-mail do cliente (validado por regex RFC 5322 simplificado)"
                },
                nota: {
                    bsonType: "int",
                    minimum: 1,
                    maximum: 5,
                    description: "Nota de 1 a 5 estrelas"
                },
                comentario: {
                    bsonType: "string",
                    maxLength: 500,
                    description: "Comentario livre, maximo 500 caracteres"
                },
                data: {
                    bsonType: "date",
                    description: "Data da avaliacao"
                }
            }
        }
    },
    validationAction: "error",    // Rejeita documentos inválidos
    validationLevel: "strict"     // Aplica a inserts e updates
});

// Indice em livro_id: toda consulta de avaliacoes filtra por livro
// (listagem por livro, media de notas por livro)
// Justificativa: sem indice, scan de collection completa a cada busca
db.avaliacoes.createIndex(
    { livro_id: 1 },
    { name: "idx_livro_id" }
);

// Dados de exemplo (livro_id refere-se aos IDs do MySQL: 1 a 8)
db.avaliacoes.insertMany([
    {
        livro_id: 1,
        email_cliente: "ana.silva@email.com",
        nota: 5,
        comentario: "Obra-prima da ficcao cientifica. Construcao de mundo incrivel.",
        data: new Date("2024-01-15")
    },
    {
        livro_id: 1,
        email_cliente: "bruno.costa@email.com",
        nota: 4,
        comentario: "Muito bom, mas inicio lento. Vale a pena persistir.",
        data: new Date("2024-02-10")
    },
    {
        livro_id: 2,
        email_cliente: "carla.dias@email.com",
        nota: 5,
        comentario: "Asimov no auge. A psicohistoria e fascinante.",
        data: new Date("2024-01-20")
    },
    {
        livro_id: 3,
        email_cliente: "ana.silva@email.com",
        nota: 5,
        comentario: "Jane Austen nunca decepciona. Elizabeth Bennet e iconica.",
        data: new Date("2024-03-05")
    },
    {
        livro_id: 4,
        email_cliente: "bruno.costa@email.com",
        nota: 4,
        comentario: "Machado de Assis e genial. Narrador nao confiavel perfeito.",
        data: new Date("2024-03-12")
    },
    {
        livro_id: 5,
        email_cliente: "carla.dias@email.com",
        nota: 5,
        comentario: "Melhor livro de Python que ja li. Padroes idiomaticos claros.",
        data: new Date("2024-04-01")
    },
    {
        livro_id: 5,
        email_cliente: "ana.silva@email.com",
        nota: 4,
        comentario: "Denso, mas essencial para Python serio. Requer conhecimento previo.",
        data: new Date("2024-04-15")
    },
    {
        livro_id: 6,
        email_cliente: "bruno.costa@email.com",
        nota: 5,
        comentario: "Biblia de sistemas distribuidos. Kleppmann explica complexidade com clareza.",
        data: new Date("2024-05-01")
    },
    {
        livro_id: 7,
        email_cliente: "carla.dias@email.com",
        nota: 3,
        comentario: "Biografia detalhada, mas longa demais em partes.",
        data: new Date("2024-05-20")
    },
    {
        livro_id: 8,
        email_cliente: "ana.silva@email.com",
        nota: 5,
        comentario: "Classico atemporal. Leitura obrigatoria em qualquer idade.",
        data: new Date("2024-06-01")
    }
]);

print("Colecao 'avaliacoes' criada com validacao, indice e dados de exemplo.");
print("Indices:");
printjson(db.avaliacoes.getIndexes());