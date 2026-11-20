-- Livraria Online - Schema MySQL
-- Banco: livraria
-- 5 tabelas com PK, FK, CHECK constraints

CREATE DATABASE IF NOT EXISTS livraria
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE livraria;

-- 1. Categorias
CREATE TABLE categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    descricao TEXT
) ENGINE=InnoDB;

-- 2. Livros
CREATE TABLE livros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    autor VARCHAR(150) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    preco DECIMAL(10,2) NOT NULL,
    estoque INT NOT NULL DEFAULT 0,
    categoria_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_preco CHECK (preco >= 0),
    CONSTRAINT chk_estoque CHECK (estoque >= 0),
    CONSTRAINT fk_livros_categoria
        FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 3. Clientes
CREATE TABLE clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    telefone VARCHAR(20),
    endereco TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 4. Pedidos
CREATE TABLE pedidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pendente','pago','enviado','entregue','cancelado') DEFAULT 'pendente',
    total DECIMAL(10,2) NOT NULL DEFAULT 0,

    CONSTRAINT chk_total CHECK (total >= 0),
    CONSTRAINT fk_pedidos_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 5. Itens do Pedido (PK composta)
CREATE TABLE itens_pedido (
    pedido_id INT NOT NULL,
    livro_id INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,

    PRIMARY KEY (pedido_id, livro_id),
    CONSTRAINT chk_quantidade CHECK (quantidade > 0),
    CONSTRAINT chk_preco_unitario CHECK (preco_unitario >= 0),
    CONSTRAINT fk_itens_pedido
        FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_itens_livro
        FOREIGN KEY (livro_id) REFERENCES livros(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Dados de exemplo (sem acentos para compatibilidade terminal Windows)
INSERT INTO categorias (nome, descricao) VALUES
('Ficcao Cientifica', 'Livros de ficcao cientifica e fantasia'),
('Romance', 'Romances contemporaneos e classicos'),
('Tecnico', 'Livros tecnicos, programacao, ciencia de dados'),
('Biografia', 'Biografias e memorias'),
('Infantil', 'Literatura infantil e juvenil');

INSERT INTO livros (titulo, autor, isbn, preco, estoque, categoria_id) VALUES
('Duna', 'Frank Herbert', '978-85-7657-123-4', 59.90, 15, 1),
('Fundacao', 'Isaac Asimov', '978-85-7657-124-1', 54.90, 10, 1),
('Orgulho e Preconceito', 'Jane Austen', '978-85-7657-125-8', 42.90, 20, 2),
('Dom Casmurro', 'Machado de Assis', '978-85-7657-126-5', 38.90, 25, 2),
('Python Fluente', 'Luciano Ramalho', '978-85-7657-127-2', 129.90, 8, 3),
('Designing Data-Intensive Applications', 'Martin Kleppmann', '978-85-7657-128-9', 149.90, 5, 3),
('Steve Jobs', 'Walter Isaacson', '978-85-7657-129-6', 69.90, 12, 4),
('O Pequeno Principe', 'Antoine de Saint-Exupery', '978-85-7657-130-2', 34.90, 30, 5);

INSERT INTO clientes (nome, email, telefone, endereco) VALUES
('Ana Silva', 'ana.silva@email.com', '(11) 99999-1111', 'Rua A, 123 - Sao Paulo/SP'),
('Bruno Costa', 'bruno.costa@email.com', '(21) 98888-2222', 'Av. B, 456 - Rio de Janeiro/RJ'),
('Carla Dias', 'carla.dias@email.com', '(31) 97777-3333', 'Rua C, 789 - Belo Horizonte/MG');

-- Pedido de exemplo
INSERT INTO pedidos (cliente_id, status, total) VALUES
(1, 'entregue', 114.80);

INSERT INTO itens_pedido (pedido_id, livro_id, quantidade, preco_unitario) VALUES
(1, 1, 1, 59.90),
(1, 3, 1, 54.90);