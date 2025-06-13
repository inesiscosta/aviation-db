DROP TABLE IF EXISTS aeroporto CASCADE;
DROP TABLE IF EXISTS aviao CASCADE;
DROP TABLE IF EXISTS assento CASCADE;
DROP TABLE IF EXISTS voo CASCADE;
DROP TABLE IF EXISTS venda CASCADE;
DROP TABLE IF EXISTS bilhete CASCADE;

CREATE TABLE aeroporto(
	codigo CHAR(3) PRIMARY KEY CHECK (codigo ~ '^[A-Z]{3}$'),
	nome VARCHAR(80) NOT NULL,
	cidade VARCHAR(255) NOT NULL,
	pais VARCHAR(255) NOT NULL,
	UNIQUE (nome, cidade)
);

CREATE TABLE aviao(
	no_serie VARCHAR(80) PRIMARY KEY,
	modelo VARCHAR(80) NOT NULL
);

CREATE TABLE assento (
	lugar VARCHAR(3) CHECK (lugar ~ '^[0-9]{1,2}[A-Z]$'),
	no_serie VARCHAR(80) REFERENCES aviao,
	prim_classe BOOLEAN NOT NULL DEFAULT FALSE,
	PRIMARY KEY (lugar, no_serie)
);

CREATE TABLE voo (
	id SERIAL PRIMARY KEY,
	no_serie VARCHAR(80) REFERENCES aviao,
	hora_partida TIMESTAMP,
	hora_chegada TIMESTAMP, 
	partida CHAR(3) REFERENCES aeroporto(codigo),
	chegada CHAR(3) REFERENCES aeroporto(codigo),
	UNIQUE (no_serie, hora_partida),
	UNIQUE (no_serie, hora_chegada),
	UNIQUE (hora_partida, partida, chegada),
	UNIQUE (hora_chegada, partida, chegada),
	CHECK (partida!=chegada),
	CHECK (hora_partida<=hora_chegada)
);

CREATE TABLE venda (
	codigo_reserva SERIAL PRIMARY KEY,
	nif_cliente CHAR(9) NOT NULL,
	balcao CHAR(3) REFERENCES aeroporto(codigo),
	hora TIMESTAMP
);

CREATE TABLE bilhete (
	id SERIAL PRIMARY KEY,
	voo_id INTEGER REFERENCES voo,
	codigo_reserva INTEGER REFERENCES venda,
	nome_passegeiro VARCHAR(80),
	preco NUMERIC(7,2) NOT NULL,
	prim_classe BOOLEAN NOT NULL DEFAULT FALSE,
	lugar VARCHAR(3),
	no_serie VARCHAR(80),
	UNIQUE (voo_id, codigo_reserva, nome_passegeiro),
	FOREIGN KEY (lugar, no_serie) REFERENCES assento
);


------------------------JUPYTER CENAS------------------------------

-- RI-1: Classe do bilhete = classe do assento E avião do assento = avião do voo
CREATE OR REPLACE FUNCTION checkin_ri1()
RETURNS TRIGGER AS $$
DECLARE
    assento_classe BOOLEAN;
    voo_serie VARCHAR(80);
BEGIN
    -- Verifica se lugar e no_serie estão a ser definidos (check-in)
    IF NEW.lugar IS NOT NULL AND NEW.no_serie IS NOT NULL THEN
        -- Classe do bilhete = classe do assento
        SELECT prim_classe INTO assento_classe
        FROM assento
        WHERE lugar = NEW.lugar AND no_serie = NEW.no_serie;
        IF assento_classe IS NULL OR assento_classe <> NEW.prim_classe THEN
            RAISE EXCEPTION 'Classe do bilhete não corresponde à classe do assento';
        END IF;
        -- Avião do assento = avião do voo
        SELECT no_serie INTO voo_serie FROM voo WHERE id = NEW.voo_id;
        IF voo_serie IS NULL OR voo_serie <> NEW.no_serie THEN
            RAISE EXCEPTION 'Avião do assento não corresponde ao avião do voo';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_checkin_ri1
BEFORE INSERT OR UPDATE OF lugar, no_serie ON bilhete
FOR EACH ROW
EXECUTE FUNCTION checkin_ri1();

-- RI-2: Nº bilhetes vendidos por classe ≤ nº assentos disponíveis por classe no avião do voo
CREATE OR REPLACE FUNCTION venda_ri2()
RETURNS TRIGGER AS $$
DECLARE
    bilhetes_1c INT;
    bilhetes_2c INT;
    assentos_1c INT;
    assentos_2c INT;
    serie VARCHAR(80);
BEGIN
    -- Só verifica em inserção de bilhete
    SELECT no_serie INTO serie FROM voo WHERE id = NEW.voo_id;
    -- Bilhetes já vendidos para este voo
    SELECT COUNT(*) INTO bilhetes_1c FROM bilhete WHERE voo_id = NEW.voo_id AND prim_classe = TRUE;
    SELECT COUNT(*) INTO bilhetes_2c FROM bilhete WHERE voo_id = NEW.voo_id AND prim_classe = FALSE;
    -- Assentos disponíveis por classe no avião
    SELECT COUNT(*) INTO assentos_1c FROM assento WHERE no_serie = serie AND prim_classe = TRUE;
    SELECT COUNT(*) INTO assentos_2c FROM assento WHERE no_serie = serie AND prim_classe = FALSE;
    -- Considera o novo bilhete
    IF NEW.prim_classe THEN
        bilhetes_1c := bilhetes_1c + 1;
    ELSE
        bilhetes_2c := bilhetes_2c + 1;
    END IF;
    IF bilhetes_1c > assentos_1c THEN
        RAISE EXCEPTION 'Excedida a capacidade de 1ª classe para este voo'; -- Pass flight id in error message.
    END IF;
    IF bilhetes_2c > assentos_2c THEN
        RAISE EXCEPTION 'Excedida a capacidade de 2ª classe para este voo';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_venda_ri2
BEFORE INSERT OR UPDATE OF prim_classe ON bilhete
FOR EACH ROW
EXECUTE FUNCTION venda_ri2();

-- RI-3: Hora da venda < hora de partida de todos os voos dos bilhetes da venda
CREATE OR REPLACE FUNCTION venda_ri3()
RETURNS TRIGGER AS $$
DECLARE
    venda_hora TIMESTAMP;
    partida TIMESTAMP;
BEGIN
    -- Hora da venda
    SELECT hora INTO venda_hora FROM venda WHERE codigo_reserva = NEW.codigo_reserva;
    -- Hora de partida do voo deste bilhete
    SELECT hora_partida INTO partida FROM voo WHERE id = NEW.voo_id;
    IF venda_hora IS NOT NULL AND partida IS NOT NULL AND venda_hora >= partida THEN
        RAISE EXCEPTION 'Hora da venda não pode ser posterior ou igual à hora de partida do voo'; -- TODO: More descriptive error messages.
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_venda_ri3
BEFORE INSERT ON bilhete
FOR EACH ROW
EXECUTE FUNCTION venda_ri3();