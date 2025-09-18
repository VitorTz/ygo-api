
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
                        'set_name', cs.set_name,
                        'set_code', cs.set_code,
                        'num_of_cards', cs.num_of_cards,
                        'tcg_date', cs.tcg_date,
                        'set_image', cs.set_image
                    )
                )
                FROM 
                    cards_in_sets cis
                JOIN 
                    card_sets cs ON cs.card_set_id = cis.card_set_id
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


DO $$
BEGIN
IF NOT EXISTS (
    SELECT 1
    FROM pg_matviews
    WHERE matviewname = 'card_sets_mv'
) THEN
CREATE MATERIALIZED VIEW card_sets_mv AS
SELECT    
    cs.card_set_id,
    cs.set_name,
    cs.set_code,
    cs.num_of_cards,
    to_char(cs.tcg_date, 'YYYY-MM-DD') as tcg_date,
    cs.set_image,
    COALESCE(
        (
            SELECT json_agg(
                json_build_object(
                    'card', to_jsonb(c.*),
                    'copies', cis.num_of_cards
                )
            )
            FROM 
                cards_in_sets cis
            JOIN 
                cards_mv c ON c.card_id = cis.card_id
            WHERE 
                cis.card_set_id = cs.card_set_id
        ),
        '[]'::json
    ) AS cards
FROM card_sets cs
WITH DATA;
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


CREATE UNIQUE INDEX IF NOT EXISTS idx_card_sets_mv_id ON card_sets_mv (card_set_id);

CREATE INDEX IF NOT EXISTS idx_card_sets_mv_name ON card_sets_mv (set_name);

CREATE INDEX IF NOT EXISTS idx_card_sets_mv_code ON card_sets_mv (set_code);

CREATE INDEX IF NOT EXISTS idx_card_sets_mv_name_trgm ON card_sets_mv USING gin (set_name gin_trgm_ops);


REFRESH MATERIALIZED VIEW CONCURRENTLY cards_mv;
REFRESH MATERIALIZED VIEW CONCURRENTLY card_sets_mv;