# create_db.py
import sqlite3

def create_database():
    conn = sqlite3.connect("cars.db")
    cur = conn.cursor()

    # Tabela de carros
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT NOT NULL,
        model TEXT NOT NULL,
        car_type TEXT NOT NULL,
        daily_rate REAL NOT NULL,
        seats INTEGER NOT NULL,
        fuel_type TEXT NOT NULL,
        available INTEGER NOT NULL
    );
    """)

    sample_cars = [
        ("Toyota", "Corolla", "Sedan", 100.0, 5, "Gasolina", 1),
        ("Honda", "Civic", "Sedan", 120.0, 5, "Gasolina", 1),
        ("Chevrolet", "Onix", "Hatch", 90.0, 5, "Gasolina", 1),
        ("Jeep", "Wrangler", "SUV", 150.0, 5, "Diesel", 1),
        ("Ford", "EcoSport", "SUV", 130.0, 5, "Gasolina", 1),
        ("Fiat", "Mobi", "Hatch", 80.0, 4, "Gasolina", 1)
    ]

    cur.executemany("""
    INSERT INTO cars (brand, model, car_type, daily_rate, seats, fuel_type, available)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, sample_cars)

    # Tabela de informações da empresa
    cur.execute("""
    CREATE TABLE IF NOT EXISTS business_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        info_text TEXT NOT NULL
    );
    """)

    # Insere as informações da empresa se ainda não existir nenhum registro.
    cur.execute("SELECT COUNT(*) FROM business_info;")
    count = cur.fetchone()[0]
    if count == 0:
        business_text = (
            "A CarMax é líder no mercado de aluguel de carros há mais de 20 anos. "
            "Oferece uma ampla gama de veículos, desde sedãs econômicos até SUVs de luxo. "
            "Com uma frota moderna e atendimento personalizado, a CarMax se destaca pelo comprometimento "
            "com a satisfação do cliente e pela transparência nas tarifas. "
            "A empresa conta com unidades distribuídas por todo o país, permitindo reservas online e assistência 24 horas. "
            "Investindo constantemente em tecnologia, a CarMax oferece um sistema de reservas intuitivo e políticas "
            "competitivas de preços para garantir uma experiência segura e eficiente aos clientes."
        )
        cur.execute("""
        INSERT INTO business_info (company_name, info_text)
        VALUES (?, ?);
        """, ("CarMax", business_text))

    conn.commit()
    conn.close()
    print("Banco de dados criado e dados inseridos com sucesso!")

if __name__ == "__main__":
    create_database()
