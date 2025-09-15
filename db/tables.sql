

CREATE TABLE IF NOT EXISTS set_rarity (
    set_rarity_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name citext NOT NULL UNIQUE,
    code TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


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
    card_set_code citext PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    set_rarity_id INT,
    price INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (set_rarity_id) REFERENCES set_rarity(set_rarity_id) ON DELETE SET NULL ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS cards_in_sets (
    card_id INT NOT NULL,
    card_set_code citext NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT set_cards_cstr_pkey PRIMARY KEY (card_id, card_set_code),
    FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (card_set_code) REFERENCES card_sets(card_set_code) ON DELETE CASCADE ON UPDATE CASCADE
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


-- set_cards
CREATE INDEX IF NOT EXISTS idx_cards_in_sets_card_id ON cards_in_sets(card_id);
CREATE INDEX IF NOT EXISTS idx_cards_in_sets_set_code ON cards_in_sets(card_set_code);
CREATE INDEX IF NOT EXISTS idx_card_sets_rarity ON card_sets(set_rarity_id);

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
