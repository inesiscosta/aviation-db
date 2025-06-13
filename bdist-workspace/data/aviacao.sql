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

-- RI-1: Garante que, ao fazer check-in (atribuição de assento), a classe do bilhete corresponde à classe do assento e o avião do assento corresponde ao avião do voo
CREATE OR REPLACE FUNCTION validate_checkin()
RETURNS TRIGGER AS $$
DECLARE
    assento_classe BOOLEAN;
    voo_serie VARCHAR(80);
BEGIN
    -- Verifica se lugar e no_serie estão definidos na operação de (check-in)
    IF NEW.lugar IS NOT NULL AND NEW.no_serie IS NOT NULL THEN
        -- Classe do bilhete = classe do assento
        SELECT prim_classe INTO assento_classe
        FROM assento
        WHERE lugar = NEW.lugar AND no_serie = NEW.no_serie;
        IF assento_classe IS NULL OR assento_classe <> NEW.prim_classe THEN
            RAISE EXCEPTION 'Classe do bilhete (%) não corresponde à do lugar (%) atribuído.', NEW.prim_classe, assento_classe;
        END IF;
        -- Avião do assento = avião do voo
        SELECT no_serie INTO voo_serie FROM voo WHERE id = NEW.voo_id;
        IF voo_serie IS NULL OR voo_serie <> NEW.no_serie THEN
            RAISE EXCEPTION 'O assento atribuído (lugar: %, avião: %) não pertence ao avião (%) que realiza o voo (voo_id: %).', NEW.lugar, NEW.no_serie, voo_serie, NEW.voo_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_validate_checkin
BEFORE INSERT OR UPDATE OF lugar, no_serie ON bilhete
FOR EACH ROW
EXECUTE FUNCTION validate_checkin();

-- RI-1: Garante que, ao fazer check-in (atribuição de assento), a classe do bilhete corresponde à classe do assento e o avião do assento corresponde ao avião do voo
CREATE OR REPLACE FUNCTION validate_checkin()
RETURNS TRIGGER AS $$
DECLARE
    assento_classe BOOLEAN;
    voo_serie VARCHAR(80);
BEGIN
    -- Verifica se lugar e no_serie estão definidos na operação de (check-in)
    IF NEW.lugar IS NOT NULL AND NEW.no_serie IS NOT NULL THEN
        -- Classe do bilhete = classe do assento
        SELECT prim_classe INTO assento_classe
        FROM assento
        WHERE lugar = NEW.lugar AND no_serie = NEW.no_serie;
        IF assento_classe IS NULL OR assento_classe <> NEW.prim_classe THEN
            RAISE EXCEPTION 'Classe do bilhete (%) não corresponde à do lugar (%) atribuído.', NEW.prim_classe, assento_classe;
        END IF;
        -- Avião do assento = avião do voo
        SELECT no_serie INTO voo_serie FROM voo WHERE id = NEW.voo_id;
        IF voo_serie IS NULL OR voo_serie <> NEW.no_serie THEN
            RAISE EXCEPTION 'O assento atribuído (lugar: %, avião: %) não pertence ao avião (%) que realiza o voo (voo_id: %).', NEW.lugar, NEW.no_serie, voo_serie, NEW.voo_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_validate_checkin
BEFORE INSERT OR UPDATE OF lugar, no_serie ON bilhete
FOR EACH ROW
EXECUTE FUNCTION validate_checkin();

-- RI-3: Garante que a hora da venda é anterior à hora de partida de todos os voos associados aos bilhetes dessa venda
CREATE OR REPLACE FUNCTION validate_sale_time()
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
        RAISE EXCEPTION 'Hora da venda % não pode ser posterior ou igual à hora de partida do voo (id: %, partida: %).', venda_hora, NEW.voo_id, partida;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_validate_sale_time
BEFORE INSERT ON bilhete
FOR EACH ROW
EXECUTE FUNCTION validate_sale_time();