

CREATE TABLE IF NOT EXISTS cards (
    card_id INT PRIMARY KEY NOT NULL,
    name citext NOT NULL,
    descr TEXT NOT NULL,
    pend_descr TEXT,
    monster_descr TEXT,
    attack INT,
    defence INT,
    level INT,
    archetype archetype_enum,
    attribute attribute_enum,
    frametype frametype_enum,
    race race_enum,
    type type_enum,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS card_sets (
    card_set_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    set_name citext NOT NULL UNIQUE,
    set_code TEXT NOT NULL,
    num_of_cards INT NOT NULL CHECK (num_of_cards >= 0),
    tcg_date DATE,
    set_image TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS cards_in_sets (
    cards_in_set_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    card_id INT NOT NULL,
    card_set_id INTEGER NOT NULL,
    num_of_cards INTEGER,
    CONSTRAINT cards_in_sets_unique_cstr UNIQUE (card_id, card_set_id),
    FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (card_set_id) REFERENCES card_sets(card_set_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS linkmarkers (
    card_id INT NOT NULL,
    position position_enum NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT linkmarkers_cstr_pkey PRIMARY KEY (card_id, position)
);


CREATE TABLE IF NOT EXISTS banlist (
    ban_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    card_id INT NOT NULL,
    ban_org ban_org_enum NOT NULL,
    ban_type ban_type_enum NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT banlist_cstr_unique UNIQUE (card_id, ban_org, ban_type)
);


CREATE TABLE IF NOT EXISTS card_images (
    card_id INT PRIMARY KEY NOT NULL,
    image_url TEXT,
    image_url_cropped TEXT,
    image_url_small TEXT,
    FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS card_prices (
    card_id INT PRIMARY KEY NOT NULL,
    amazon_price INT DEFAULT 0,
    cardmarket_price INT DEFAULT 0,
    coolstuffinc_price INT DEFAULT 0,
    ebay_price INT DEFAULT 0,
    tcgplayer_price INT DEFAULT 0,
    FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS trivias (
    trivia_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    question citext NOT NULL UNIQUE,
    explanation TEXT NOT NULL,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS trivia_answers (
    trivia_answer_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trivia_id INT,
    answer TEXT NOT NULL,    
    is_correct_answer BOOLEAN NOT NULL,
    CONSTRAINT trivia_answers_cstr_unique UNIQUE (trivia_id, answer),
    FOREIGN KEY (trivia_id) REFERENCES trivias(trivia_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- set_cards
CREATE INDEX IF NOT EXISTS idx_cards_in_sets_card_id ON cards_in_sets(card_id);
CREATE INDEX IF NOT EXISTS idx_cards_in_sets_set_id ON cards_in_sets(card_set_id);

-- linkmarkers
CREATE INDEX IF NOT EXISTS idx_linkmarkers_card_id ON linkmarkers(card_id);

-- banlist
CREATE INDEX IF NOT EXISTS idx_banlist_card_id ON banlist(card_id);

-- card_images
CREATE INDEX IF NOT EXISTS idx_card_images_card_id ON card_images(card_id);

-- card_prices
CREATE INDEX IF NOT EXISTS idx_card_prices_card_id ON card_prices(card_id);

-- cards
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards (name);
CREATE INDEX IF NOT EXISTS idx_cards_name_trgm ON cards USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_cards_archetype ON cards(archetype);
CREATE INDEX IF NOT EXISTS idx_cards_attribute ON cards(attribute);
CREATE INDEX IF NOT EXISTS idx_cards_attribute ON cards(frametype);
CREATE INDEX IF NOT EXISTS idx_cards_attribute ON cards(race);
CREATE INDEX IF NOT EXISTS idx_cards_attribute ON cards(type);
