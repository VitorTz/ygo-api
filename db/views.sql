
DO $$
BEGIN
IF NOT EXISTS (
    SELECT 1
    FROM pg_matviews
    WHERE matviewname = 'cards_mv'
) THEN
    CREATE MATERIALIZED VIEW cards_mv AS
    SELECT
        c.card_id,
        c.name,
        c.descr,
        c.pend_descr,
        c.monster_descr,
        c.attack,
        c.defence,
        c.level,
        c.archetype,
        c.attribute,
        c.frametype,
        c.race,
        c.type,

        -- sets
        COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'code', cs.card_set_code,
                        'name', cs.name,
                        'rarity', sr.name,
                        'rarity_code', sr.code,
                        'price', COALESCE(cs.price, 0)::float / 100
                    )
                )
                FROM 
                    cards_in_sets cis
                JOIN 
                    card_sets cs ON cs.card_set_code = cis.card_set_code
                JOIN 
                    set_rarity sr ON sr.set_rarity_id = cs.set_rarity_id
                WHERE 
                    cis.card_id = c.card_id
            ),
            '[]'::jsonb
        ) AS card_sets,

        -- linkmarkers
        COALESCE(
            (
                SELECT 
                    jsonb_agg(position)
                FROM 
                    linkmarkers lm
                WHERE 
                    lm.card_id = c.card_id
            ),
            '[]'::jsonb
        ) AS linkmarkers,

        -- banlists
        COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'ban_org', b.ban_org,
                        'ban_type', b.ban_type
                    )
                )
                FROM 
                    banlist b
                WHERE 
                    b.card_id = c.card_id
            ),
            '[]'::jsonb
        ) AS banlists,

        -- images
        COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'image_url', ci.image_url,
                        'image_url_cropped', ci.image_url_cropped,
                        'image_url_small', ci.image_url_small
                    )
                )
                FROM 
                    card_images ci
                WHERE 
                    ci.card_id = c.card_id
            ),
            '[]'::jsonb
        ) AS images,

        -- prices
        COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'amazon_price', COALESCE(cp.amazon_price, 0)::float / 100,
                        'cardmarket_price', COALESCE(cp.cardmarket_price, 0)::float / 100,
                        'coolstuffinc_price', COALESCE(cp.coolstuffinc_price, 0)::float / 100,
                        'ebay_price', COALESCE(cp.ebay_price, 0)::float / 100,
                        'tcgplayer_price', COALESCE(cp.tcgplayer_price, 0)::float / 100
                    )
                )
                FROM 
                    card_prices cp
                WHERE 
                    cp.card_id = c.card_id
            ),
            '[]'::jsonb
        ) AS card_prices

    FROM cards c;
END IF;
END$$;


CREATE UNIQUE INDEX IF NOT EXISTS idx_cards_mv_card_id ON cards_mv(card_id);

CREATE INDEX IF NOT EXISTS idx_cards_mv_name ON cards_mv(name);

CREATE INDEX IF NOT EXISTS idx_cards_mv_name_trgm ON cards_mv USING gin (name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_cards_mv_attack ON cards_mv(attack DESC);

CREATE INDEX IF NOT EXISTS idx_cards_mv_defence ON cards_mv(defence DESC);

CREATE INDEX IF NOT EXISTS idx_cards_mv_level ON cards_mv(level DESC);

CREATE INDEX IF NOT EXISTS idx_cards_archetype_attack ON cards(archetype, attack);

CREATE INDEX IF NOT EXISTS idx_cards_archetype_defence ON cards(archetype, defence);

CREATE INDEX IF NOT EXISTS idx_cards_archetype_level ON cards(archetype, level);

CREATE INDEX IF NOT EXISTS idx_cards_mv_archetype ON cards_mv(archetype);

CREATE INDEX IF NOT EXISTS idx_cards_mv_attribute ON cards_mv(attribute);

CREATE INDEX IF NOT EXISTS idx_cards_mv_frametype ON cards_mv(frametype);

CREATE INDEX IF NOT EXISTS idx_cards_mv_race ON cards_mv(race);

CREATE INDEX IF NOT EXISTS idx_cards_mv_type ON cards_mv(type);