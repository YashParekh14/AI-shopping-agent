"""
Database setup — creates tables and seeds them with products and reviews.

Works with both SQLite (local dev) and PostgreSQL/Supabase (production).
Run once after setting up a new environment:
    python setup_db.py
"""

import os
import config

# ── Detect backend ────────────────────────────────────────────────────────────
USE_PG = bool(config.DATABASE_URL)

if USE_PG:
    import psycopg2
    def get_raw_conn():
        return psycopg2.connect(config.DATABASE_URL)
    PH = "%s"          # PostgreSQL placeholder
    SERIAL = "SERIAL"  # PostgreSQL auto-increment
    TEXT_TYPE = "TEXT"
    REAL_TYPE = "REAL"
    INT_TYPE = "INTEGER"
else:
    import sqlite3
    def get_raw_conn():
        return sqlite3.connect(config.DB_PATH)
    PH = "?"
    SERIAL = "INTEGER"
    TEXT_TYPE = "TEXT"
    REAL_TYPE = "REAL"
    INT_TYPE = "INTEGER"


def create_database():
    conn = get_raw_conn()
    cur = conn.cursor()

    # Products table
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS products (
            id {INT_TYPE} PRIMARY KEY,
            name {TEXT_TYPE} NOT NULL,
            category {TEXT_TYPE},
            price {REAL_TYPE},
            description {TEXT_TYPE},
            is_organic {INT_TYPE} DEFAULT 0
        )
    """)

    # Reviews table
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS reviews (
            id {SERIAL} {'PRIMARY KEY' if USE_PG else 'PRIMARY KEY AUTOINCREMENT'},
            product_id {INT_TYPE},
            rating {REAL_TYPE},
            reviewer_name {TEXT_TYPE},
            review_text {TEXT_TYPE},
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """) if not USE_PG else cur.execute(f"""
        CREATE TABLE IF NOT EXISTS reviews (
            id SERIAL PRIMARY KEY,
            product_id INTEGER,
            rating REAL,
            reviewer_name TEXT,
            review_text TEXT
        )
    """)

    # Orders table
    if USE_PG:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                ordered_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                ordered_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

    # ── Products ──────────────────────────────────────────────────────────────
    products = [
        (1,  "Organic Raw Honey",             "honey",     14.99, "Pure organic raw honey, unfiltered and cold-pressed",               1),
        (2,  "Wildflower Honey",              "honey",     12.99, "Natural wildflower honey from local beekeepers",                    0),
        (3,  "Organic Manuka Honey",          "honey",     29.99, "Premium organic Manuka honey from New Zealand",                     1),
        (4,  "Clover Honey",                  "honey",      8.99, "Classic clover honey, smooth and sweet",                            0),
        (5,  "Organic Buckwheat Honey",       "honey",     18.99, "Dark and robust organic buckwheat honey, antioxidant-rich",         1),
        (6,  "Orange Blossom Honey",          "honey",     15.99, "Light and floral orange blossom honey",                             0),
        (7,  "Organic Acacia Honey",          "honey",     17.99, "Light and mild organic acacia honey, low glycemic index",           1),
        (8,  "Creamed Honey",                 "honey",     11.99, "Smooth creamed honey with spreadable texture",                      0),
        (9,  "Organic Extra Virgin Olive Oil","oil",        16.99, "Cold-pressed organic EVOO from Mediterranean olives",              1),
        (10, "Coconut Oil",                   "oil",        12.49, "Refined coconut oil, great for high-heat cooking",                 0),
        (11, "Organic Flaxseed Oil",          "oil",        14.99, "Cold-pressed organic flaxseed oil, rich in omega-3",               1),
        (12, "Avocado Oil",                   "oil",        18.99, "Cold-pressed avocado oil, high smoke point",                       0),
        (13, "Organic Almonds",               "nuts",       11.99, "Raw organic almonds, unsalted, non-GMO certified",                 1),
        (14, "Roasted Cashews",               "nuts",        9.99, "Lightly salted dry-roasted cashews",                               0),
        (15, "Organic Chia Seeds",            "seeds",       8.49, "Organic black chia seeds, high in fiber and omega-3",              1),
        (16, "Mixed Nuts",                    "nuts",       13.99, "Premium mix of walnuts, pecans, almonds and Brazil nuts",          0),
        (17, "Organic Quinoa",                "grains",     10.99, "Organic white quinoa, complete protein, gluten-free",              1),
        (18, "Rolled Oats",                   "grains",      5.49, "Whole grain rolled oats, great for porridge and baking",           0),
        (19, "Organic Brown Rice",            "grains",      7.99, "Long-grain organic brown rice, naturally gluten-free",             1),
        (20, "Steel-Cut Oats",                "grains",      6.99, "Traditional steel-cut oats, low GI, hearty texture",               0),
        (21, "Organic Green Tea",             "tea",        12.99, "Japanese organic sencha green tea, 50 bags",                       1),
        (22, "Chamomile Tea",                 "tea",         8.99, "Dried chamomile flowers, caffeine-free, soothing",                 0),
        (23, "Organic Ethiopian Coffee",      "coffee",     16.99, "Single-origin organic Arabica, medium roast whole bean",           1),
        (24, "Dark Roast Espresso Blend",     "coffee",     14.49, "Bold dark roast espresso blend, ground",                           0),
        (25, "Organic Granola",               "snacks",      9.99, "Organic oat granola with honey, almonds and dried cranberries",    1),
        (26, "Rice Cakes",                    "snacks",      4.49, "Lightly salted brown rice cakes, low calorie",                     0),
        (27, "Organic Dried Mango",           "snacks",      7.99, "Unsweetened organic dried mango slices, no preservatives",         1),
        (28, "Trail Mix",                     "snacks",      8.49, "Classic trail mix with raisins, M&Ms, peanuts and sunflower seeds",0),
        (29, "Organic Almond Milk",           "dairy-alt",   4.99, "Unsweetened organic almond milk, fortified with calcium",          1),
        (30, "Oat Milk",                      "dairy-alt",   4.49, "Barista-style oat milk, great for coffee",                         0),
        (31, "Organic Coconut Milk",          "dairy-alt",   3.99, "Full-fat organic coconut milk, great for curries",                 1),
        (32, "Soy Milk",                      "dairy-alt",   3.49, "Unsweetened soy milk, high protein",                               0),
    ]

    if USE_PG:
        cur.execute("TRUNCATE TABLE reviews, orders, products RESTART IDENTITY CASCADE")
        cur.executemany(
            f"INSERT INTO products (id,name,category,price,description,is_organic) "
            f"VALUES ({PH},{PH},{PH},{PH},{PH},{PH}) ON CONFLICT (id) DO NOTHING",
            products,
        )
    else:
        cur.executemany(
            "INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?)", products
        )

    # ── Reviews ───────────────────────────────────────────────────────────────
    reviews = [
        (1,5.0,"Alice","Amazing honey!"),(1,4.0,"Bob","Good quality."),(1,5.0,"Carol","Excellent flavor."),
        (1,4.5,"Dave","Very good, unfiltered."),(2,4.0,"Eve","Decent for price."),(2,3.5,"Frank","Average."),
        (2,4.0,"Grace","Good everyday honey."),(3,5.0,"Henry","Worth every penny."),(3,4.5,"Iris","Excellent."),
        (3,5.0,"Jack","Best honey ever."),(4,3.5,"Kate","Okay for cooking."),(4,3.5,"Leo","Nothing special."),
        (4,3.5,"Mia","Average clover honey."),(5,5.0,"Noah","Rich bold flavor."),(5,4.0,"Olivia","Good strong honey."),
        (5,5.0,"Paul","Love the dark color."),(5,4.5,"Quinn","Great organic option."),(6,4.0,"Rachel","Nice floral flavor."),
        (6,4.5,"Sam","Lovely and delicate."),(6,4.0,"Tina","Good for baking."),(7,5.0,"Uma","Perfect mild flavor!"),
        (7,4.5,"Victor","Excellent light honey."),(7,4.5,"Wendy","Very pure taste."),(7,5.0,"Xavier","Wonderful."),
        (8,4.0,"Yvonne","Nice spreadable texture."),(8,4.0,"Zack","Good on toast."),(8,4.0,"Amy","Decent creamed honey."),
        (9,5.0,"Brian","Best olive oil."),(9,4.5,"Clara","Great flavor."),(9,4.5,"Derek","Excellent quality."),
        (10,4.0,"Elena","Good for frying."),(10,3.5,"Felix","Does the job."),(10,3.5,"Gina","Decent."),
        (11,5.0,"Harry","Great for smoothies."),(11,4.0,"Isla","Good omega-3."),(11,4.5,"James","Love for dressings."),
        (12,4.5,"Karen","Excellent smoke point."),(12,4.0,"Liam","Good all-purpose."),(12,4.5,"Maya","Great for cooking."),
        (13,5.0,"Nate","Crunchy and fresh."),(13,4.5,"Olivia","Love organic raw."),(13,4.5,"Peter","Very fresh."),
        (13,5.0,"Rita","Best almonds online."),(14,4.0,"Steve","Good cashews."),(14,4.0,"Tara","Slightly over-salted."),
        (14,4.0,"Ursula","Good value."),(15,4.5,"Vince","Easy in smoothies."),(15,4.5,"Wanda","Great fiber source."),
        (15,4.5,"Xena","Good quality seeds."),(16,4.0,"Yuri","Good mix."),(16,3.5,"Zara","Too many peanuts."),
        (16,4.0,"Alex","Nice for snacking."),(16,3.5,"Blake","Too many raisins."),(17,5.0,"Chloe","Cooks perfectly."),
        (17,4.5,"Dylan","Excellent protein."),(17,4.5,"Ella","Best quinoa."),(18,4.5,"Finn","Great oats."),
        (18,4.0,"Gabi","Good texture."),(18,4.5,"Hugo","Reliable oats."),(19,4.5,"Irene","Nice chewy texture."),
        (19,4.5,"Jake","Good quality."),(19,4.5,"Kara","Love the organic cert."),(20,4.0,"Lars","Great texture."),
        (20,3.5,"Mona","Takes long to cook."),(20,4.0,"Ned","Hearty and filling."),(21,5.0,"Opal","Delicate flavor."),
        (21,4.5,"Phil","Best green tea."),(21,4.5,"Quinn","Great quality."),(22,4.0,"Rose","Very soothing."),
        (22,4.5,"Seth","Lovely floral notes."),(22,4.0,"Tess","Good chamomile."),(23,5.0,"Uri","Best coffee ever."),
        (23,4.5,"Vera","Amazing single-origin."),(23,4.5,"Will","Very smooth."),(23,5.0,"Xara","Exceptional quality."),
        (24,4.0,"Yael","Strong and bold."),(24,4.0,"Zion","Good dark roast."),(24,4.0,"Abe","Solid espresso."),
        (25,4.5,"Beth","Delicious granola."),(25,4.5,"Cole","Great texture."),(25,4.5,"Dana","My go-to breakfast."),
        (26,4.0,"Earl","Light and crispy."),(26,3.5,"Faye","A bit bland."),(26,4.0,"Glen","Good value."),
        (27,5.0,"Hope","So sweet and chewy!"),(27,4.5,"Ivan","No added sugar."),(27,4.5,"Jade","Natural taste."),
        (28,4.0,"Kent","Great for hiking."),(28,3.5,"Luna","Too many M&Ms."),(28,3.5,"Marc","Not my favorite."),
        (29,4.5,"Nina","Great in coffee."),(29,4.5,"Omar","Love organic cert."),(29,4.5,"Pam","Tastes great."),
        (30,4.5,"Rex","Perfect for lattes."),(30,4.0,"Sara","Good oat milk."),(30,4.5,"Tom","Best barista oat milk."),
        (31,4.5,"Una","Creamy and rich."),(31,4.5,"Vito","Full fat delicious."),(31,4.5,"Wren","Perfect coconut milk."),
        (32,4.0,"Xio","Good protein."),(32,3.5,"Yosef","Slightly thin."),(32,3.5,"Zola","Decent soy milk."),
    ]

    if USE_PG:
        cur.executemany(
            f"INSERT INTO reviews (product_id,rating,reviewer_name,review_text) "
            f"VALUES ({PH},{PH},{PH},{PH})",
            reviews,
        )
    else:
        cur.execute("DELETE FROM reviews")
        cur.executemany(
            "INSERT INTO reviews (product_id,rating,reviewer_name,review_text) VALUES (?,?,?,?)",
            reviews,
        )

    conn.commit()
    conn.close()
    backend = "PostgreSQL/Supabase" if USE_PG else f"SQLite at {config.DB_PATH}"
    print(f"Database created successfully on {backend}")


if __name__ == "__main__":
    create_database()
