import json
import sqlite3
import os


def create_database_schema(db_path):
    """Create SQLite database with the Person table schema"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create the Person table
    c.execute('''
    CREATE TABLE IF NOT EXISTS Person (
        id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        middle_name TEXT,
        last_name TEXT NOT NULL,
        maiden_name TEXT,
        date_of_birth TEXT,
        sex TEXT CHECK (sex IN ('M', 'F', 'Other')),
        blood_type TEXT CHECK (blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
        nationality TEXT,
        ethnicity TEXT,
        place_of_birth TEXT,
        date_of_death TEXT,
        is_deceased INTEGER DEFAULT 0,
        cause_of_death TEXT,
        height_cm INTEGER,
        eye_color TEXT,
        hair_color TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        occupation TEXT,
        education TEXT,
        religion TEXT,
        notes TEXT,
        legacy_bucket_id TEXT,
        father_id TEXT,
        mother_id TEXT,
        FOREIGN KEY (father_id) REFERENCES Person(id),
        FOREIGN KEY (mother_id) REFERENCES Person(id)
    )
    ''')

    # Create indexes
    c.execute('CREATE INDEX IF NOT EXISTS idx_person_father ON Person(father_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_person_mother ON Person(mother_id)')
    c.execute(
        'CREATE INDEX IF NOT EXISTS idx_person_name ON Person(last_name, first_name)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_person_birth ON Person(date_of_birth)')
    c.execute(
        'CREATE INDEX IF NOT EXISTS idx_legacy_bucket ON Person(legacy_bucket_id)')

    conn.commit()
    conn.close()

    print(f"Database schema created at {db_path}")
    return db_path


def import_from_json(json_path, db_path):
    """Import family tree data from JSON into SQLite database"""
    # Load the JSON data
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Connect to the database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Insert each person
    for person in data['people']:
        # Convert boolean is_deceased to integer for SQLite
        is_deceased = 1 if person['is_deceased'] else 0

        c.execute('''
        INSERT OR REPLACE INTO Person (
            id, first_name, middle_name, last_name, maiden_name,
            date_of_birth, sex, blood_type, nationality, ethnicity,
            place_of_birth, date_of_death, is_deceased, cause_of_death,
            height_cm, eye_color, hair_color, email, phone,
            address, occupation, education, religion, notes,
            legacy_bucket_id, father_id, mother_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            person['id'], person['first_name'], person['middle_name'], person['last_name'], person['maiden_name'],
            person['date_of_birth'], person['sex'], person['blood_type'], person['nationality'], person['ethnicity'],
            person['place_of_birth'], person['date_of_death'], is_deceased, person['cause_of_death'],
            person['height_cm'], person['eye_color'], person['hair_color'], person['email'], person['phone'],
            person['address'], person['occupation'], person['education'], person['religion'], person['notes'],
            person['legacy_bucket_id'], person['father_id'], person['mother_id']
        ))

    conn.commit()

    # Verify import
    c.execute("SELECT COUNT(*) FROM Person")
    count = c.fetchone()[0]

    conn.close()

    print(f"Successfully imported {count} people into the database")
    return count


def export_to_json(db_path, json_path):
    """Export family tree data from SQLite database to JSON"""
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    c = conn.cursor()

    # Get all people
    c.execute("SELECT * FROM Person")
    rows = c.fetchall()

    # Convert to list of dictionaries
    people = []
    for row in rows:
        person = dict(row)
        # Convert integer is_deceased back to boolean for JSON
        person['is_deceased'] = bool(person['is_deceased'])
        people.append(person)

    # Create JSON structure
    data = {
        'people': people
    }

    # Write to file
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

    conn.close()

    print(f"Successfully exported {len(people)} people to {json_path}")
    return len(people)


def run_sample_queries(db_path):
    """Run some sample queries to demonstrate database functionality"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    results = {}

    # 1. Count total people
    c.execute("SELECT COUNT(*) FROM Person")
    results['total_people'] = c.fetchone()[0]

    # 2. Gender distribution
    c.execute("SELECT sex, COUNT(*) FROM Person GROUP BY sex")
    results['gender_distribution'] = {
        sex: count for sex, count in c.fetchall()}

    # 3. Age distribution (living people)
    c.execute("""
    SELECT 
        CASE 
            WHEN (strftime('%Y', 'now') - strftime('%Y', date_of_birth)) < 18 THEN 'Under 18'
            WHEN (strftime('%Y', 'now') - strftime('%Y', date_of_birth)) BETWEEN 18 AND 30 THEN '18-30'
            WHEN (strftime('%Y', 'now') - strftime('%Y', date_of_birth)) BETWEEN 31 AND 50 THEN '31-50'
            WHEN (strftime('%Y', 'now') - strftime('%Y', date_of_birth)) BETWEEN 51 AND 70 THEN '51-70'
            ELSE 'Over 70'
        END as age_group,
        COUNT(*) as count
    FROM Person
    WHERE is_deceased = 0
    GROUP BY age_group
    ORDER BY 
        CASE age_group
            WHEN 'Under 18' THEN 1
            WHEN '18-30' THEN 2
            WHEN '31-50' THEN 3
            WHEN '51-70' THEN 4
            ELSE 5
        END
    """)
    results['age_distribution'] = {
        age_group: count for age_group, count in c.fetchall()}

    # 4. Top family names
    c.execute("""
    SELECT last_name, COUNT(*) as count 
    FROM Person 
    GROUP BY last_name 
    ORDER BY count DESC 
    LIMIT 10
    """)
    results['top_family_names'] = {name: count for name, count in c.fetchall()}

    # 5. People with unknown parents
    c.execute("""
    SELECT 
        SUM(CASE WHEN father_id IS NULL THEN 1 ELSE 0 END) as unknown_father,
        SUM(CASE WHEN mother_id IS NULL THEN 1 ELSE 0 END) as unknown_mother,
        SUM(CASE WHEN father_id IS NULL AND mother_id IS NULL THEN 1 ELSE 0 END) as unknown_both
    FROM Person
    """)
    unknown_stats = c.fetchone()
    results['unknown_parents'] = {
        'unknown_father': unknown_stats[0],
        'unknown_mother': unknown_stats[1],
        'unknown_both': unknown_stats[2]
    }

    # 6. Distribution by decade of birth
    c.execute("""
    SELECT 
        (CAST(strftime('%Y', date_of_birth) AS INTEGER) / 10) * 10 as decade,
        COUNT(*) as count
    FROM Person
    GROUP BY decade
    ORDER BY decade
    """)
    results['birth_by_decade'] = {
        f"{decade}s": count for decade, count in c.fetchall()}

    # 7. Find people with the most children
    c.execute("""
    SELECT p.id, p.first_name, p.last_name, COUNT(*) as num_children
    FROM Person p
    JOIN Person c ON c.father_id = p.id OR c.mother_id = p.id
    GROUP BY p.id
    ORDER BY num_children DESC
    LIMIT 5
    """)
    results['most_children'] = [
        {'id': row[0], 'name': f"{row[1]} {row[2]}", 'children': row[3]}
        for row in c.fetchall()
    ]

    # Close connection
    conn.close()

    print("Sample queries executed successfully")
    return results


def process_family_data(json_path='family_tree.json', db_path='family_tree.db'):
    """Complete workflow to process family tree data"""
    # Make sure we have a fresh database
    if os.path.exists(db_path):
        os.remove(db_path)

    # Create database schema
    create_database_schema(db_path)

    # Import data from JSON
    import_from_json(json_path, db_path)

    # Run sample queries
    results = run_sample_queries(db_path)

    # Export back to JSON to verify round-trip
    export_json_path = 'family_tree_exported.json'
    export_to_json(db_path, export_json_path)

    return {
        'db_path': db_path,
        'query_results': results,
        'exported_json': export_json_path
    }


if __name__ == "__main__":
    # Example usage
    results = process_family_data()
    print(f"Database created at: {results['db_path']}")
    print(
        f"Total people in database: {results['query_results']['total_people']}")
    print(f"Top family names: {results['query_results']['top_family_names']}")
