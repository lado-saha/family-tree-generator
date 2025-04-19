import json
import random
import uuid
import names
from faker import Faker

fake = Faker()

# Constants
START_YEAR = 1900
CURRENT_YEAR = 2025
MAX_AGE = 100
MARRIAGE_MIN_AGE = 18
FERTILITY_START_AGE = 16
FERTILITY_END_AGE_FEMALE = 45
FERTILITY_END_AGE_MALE = 70

# Probabilities
PROB_UNKNOWN_FATHER = 0.15
PROB_UNKNOWN_MOTHER = 0.05
PROB_REMARRIAGE = 0.3
PROB_DIVORCE = 0.35
PROB_POLYGAMY = 0.03  # (for older generations)
PROB_OUT_OF_WEDLOCK = 0.2
PROB_DEATH_YEARLY = 0.01  # Base probability increases with age
PROB_MIGRATION = 0.1

# Diversity parameters
BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
BLOOD_TYPE_DIST = [0.34, 0.06, 0.08, 0.02, 0.03, 0.01,
                   0.38, 0.08]  # Approximate global distribution
EYE_COLORS = ['Brown', 'Blue', 'Green', 'Hazel', 'Grey', 'Amber']
HAIR_COLORS = ['Black', 'Brown', 'Blonde', 'Red', 'Grey', 'White']
NATIONALITIES = ['American', 'British', 'French', 'German', 'Italian',
                 'Spanish', 'Chinese', 'Indian', 'Japanese', 'Nigerian', 'Brazilian', 'Mexican']
ETHNICITIES = ['Caucasian', 'African', 'Hispanic',
               'Asian', 'Middle Eastern', 'Mixed']
RELIGIONS = ['Christianity', 'Islam', 'Hinduism',
             'Buddhism', 'Judaism', 'None', 'Other']

# For storing people
people = {}
# For tracking relationships
marriages = []
children_map = {}  # Maps parent IDs to their children


def create_date(year, randomize=True):
    """Create a date with optional randomization within the year"""
    if randomize:
        month = random.randint(1, 12)
        max_day = 28 if month == 2 else 30 if month in [4, 6, 9, 11] else 31
        day = random.randint(1, max_day)
    else:
        month, day = 1, 1

    return f"{year}-{month:02d}-{day:02d}"


def random_age_death(birth_year, is_deceased=None):
    """Calculate if a person has died based on their birth year and determine death details"""
    age = CURRENT_YEAR - birth_year

    # Force death for very old people
    if age > MAX_AGE:
        is_deceased = True

    # If we don't know if they're deceased, calculate probability
    if is_deceased is None:
        yearly_prob = PROB_DEATH_YEARLY
        # Increase probability for older people
        if age > 70:
            yearly_prob += (age - 70) * 0.01

        is_deceased = random.random() < yearly_prob * age

    if is_deceased and age > 0:
        # Most likely to die in later years
        if age > 75:
            death_age = random.randint(
                max(birth_year + 75, START_YEAR), min(birth_year + age, CURRENT_YEAR))
        else:
            # Some chance of early death
            death_age = random.randint(
                birth_year + 1, min(birth_year + age, CURRENT_YEAR))

        death_date = create_date(death_age)
        cause = random.choice([
            "Natural causes", "Heart disease", "Cancer", "Accident",
            "Respiratory disease", "Stroke", "Complications from surgery",
            "Unknown", "Infectious disease", "War/conflict"
        ])
        return is_deceased, death_date, cause

    return is_deceased, None, None


def create_person(
    birth_year=None,
    father_id=None,
    mother_id=None,
    forced_gender=None,
    is_deceased=None,
    first_name=None,
    last_name=None
):
    """Create a person with given or random attributes"""

    person_id = str(uuid.uuid4())

    # Generate or use provided birth year
    if birth_year is None:
        birth_year = random.randint(START_YEAR, CURRENT_YEAR - 5)

    # Generate sex/gender
    sex = forced_gender if forced_gender else random.choice(['M', 'F'])

    # Generate names
    if not first_name:
        first_name = names.get_first_name(
            gender='male' if sex == 'M' else 'female')

    # For last name, use father's if available, otherwise generate
    if not last_name and father_id and father_id in people:
        last_name = people[father_id]['last_name']
    elif not last_name:
        last_name = names.get_last_name()

    middle_name = names.get_first_name(
        gender='male' if sex == 'M' else 'female') if random.random() < 0.7 else None

    # Determine maiden name for females
    maiden_name = None
    if sex == 'F' and random.random() < 0.8:
        maiden_name = last_name  # Will be updated if the person marries

    # Create birth date
    date_of_birth = create_date(birth_year)

    # Determine death information
    is_deceased, date_of_death, cause_of_death = random_age_death(
        birth_year, is_deceased)

    # Physical characteristics - with some genetic influence
    blood_type = random.choices(BLOOD_TYPES, weights=BLOOD_TYPE_DIST)[0]

    # Eye and hair color influenced by parents
    eye_color = None
    hair_color = None

    if father_id in people and mother_id in people and random.random() < 0.8:
        # 80% chance to inherit from parents
        eye_color = random.choice(
            [people[father_id]['eye_color'], people[mother_id]['eye_color']])
        hair_color = random.choice(
            [people[father_id]['hair_color'], people[mother_id]['hair_color']])

    if not eye_color:
        eye_color = random.choice(EYE_COLORS)
    if not hair_color:
        hair_color = random.choice(HAIR_COLORS)

    # Other attributes
    height_cm = random.randint(
        150, 200) if sex == 'M' else random.randint(145, 185)

    # Generate plausible contact info based on birth year (older people less likely to have email)
    email = None
    age = CURRENT_YEAR - birth_year
    if age >= 10 and age <= 90 and random.random() < (0.9 - (age / 100)):
        email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com'])}"

    # Phone more common than email
    phone = None
    if age >= 12 and random.random() < (0.95 - (age / 200)):
        phone = f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"

    # Cultural background - with some family influence
    nationality = None
    ethnicity = None
    religion = None

    if father_id in people and mother_id in people and random.random() < 0.9:
        # 90% chance to have same nationality as parents if both known
        nationality = random.choice(
            [people[father_id]['nationality'], people[mother_id]['nationality']])
        ethnicity = random.choice(
            [people[father_id]['ethnicity'], people[mother_id]['ethnicity']])
        # 80% chance to follow parents' religion
        if random.random() < 0.8:
            religion = random.choice(
                [people[father_id]['religion'], people[mother_id]['religion']])

    if not nationality:
        nationality = random.choice(NATIONALITIES)
    if not ethnicity:
        ethnicity = random.choice(ETHNICITIES)
    if not religion:
        religion = random.choice(RELIGIONS)

    # Location data
    place_of_birth = fake.city() + ", " + fake.country()
    address = fake.address() if not is_deceased and age >= 18 else None

    # Education and occupation based on age
    education = None
    occupation = None

    if age >= 18:
        edu_levels = [
            "High School", "Some College", "Bachelor's Degree",
            "Master's Degree", "Ph.D.", "Trade School", "None"
        ]
        education = random.choice(edu_levels)

        if not is_deceased or (is_deceased and age >= 22):
            occupation = fake.job()

    person = {
        "id": person_id,
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "maiden_name": maiden_name,
        "date_of_birth": date_of_birth,
        "sex": sex,
        "blood_type": blood_type,
        "nationality": nationality,
        "ethnicity": ethnicity,
        "place_of_birth": place_of_birth,
        "date_of_death": date_of_death,
        "is_deceased": is_deceased,
        "cause_of_death": cause_of_death,
        "height_cm": height_cm,
        "eye_color": eye_color,
        "hair_color": hair_color,
        "email": email,
        "phone": phone,
        "address": address,
        "occupation": occupation,
        "education": education,
        "religion": religion,
        "notes": None,
        # 30% have legacy content
        "legacy_bucket_id": str(uuid.uuid4()) if random.random() < 0.3 else None,
        "father_id": father_id,
        "mother_id": mother_id
    }

    people[person_id] = person
    return person_id


def simulate_marriage(person1_id, person2_id, year):
    """Register a marriage between two people"""
    if person1_id not in people or person2_id not in people:
        return False

    p1 = people[person1_id]
    p2 = people[person2_id]

    # Make sure they're of age
    p1_birth_year = int(p1['date_of_birth'].split('-')[0])
    p2_birth_year = int(p2['date_of_birth'].split('-')[0])

    if (year - p1_birth_year < MARRIAGE_MIN_AGE) or (year - p2_birth_year < MARRIAGE_MIN_AGE):
        return False

    # Update maiden name for female spouse
    if p1['sex'] == 'F' and p1['maiden_name'] is None:
        p1['maiden_name'] = p1['last_name']
        p1['last_name'] = p2['last_name']
    elif p2['sex'] == 'F' and p2['maiden_name'] is None:
        p2['maiden_name'] = p2['last_name']
        p2['last_name'] = p1['last_name']

    # Record the marriage
    marriages.append({
        'person1_id': person1_id,
        'person2_id': person2_id,
        'year': year,
        'current': True
    })

    return True


def find_spouse_candidates(person_id, year):
    """Find suitable candidates for marriage based on age and availability"""
    if person_id not in people:
        return []

    person = people[person_id]
    birth_year = int(person['date_of_birth'].split('-')[0])

    # Person must be of marriageable age
    if year - birth_year < MARRIAGE_MIN_AGE:
        return []

    # Person must be alive
    if person['is_deceased'] and int(person['date_of_death'].split('-')[0]) < year:
        return []

    gender_preference = 'F' if person['sex'] == 'M' else 'M'

    # Find candidates of appropriate gender and age
    candidates = []
    for pid, p in people.items():
        if p['sex'] != gender_preference:
            continue

        p_birth_year = int(p['date_of_birth'].split('-')[0])

        # Skip if too young
        if year - p_birth_year < MARRIAGE_MIN_AGE:
            continue

        # Skip if deceased
        if p['is_deceased'] and int(p['date_of_death'].split('-')[0]) < year:
            continue

        # Age difference check (more flexible for older generations)
        age_diff = abs(birth_year - p_birth_year)
        if year < 1970 and age_diff > 20:
            continue
        elif year >= 1970 and age_diff > 15:
            continue

        # Check if already married (and not polygamous)
        already_married = False
        for marriage in marriages:
            if year < 1970 and person['sex'] == 'M' and random.random() < PROB_POLYGAMY:
                # Allow polygamy for males in older times
                continue

            if ((marriage['person1_id'] == pid or marriage['person2_id'] == pid) and
                    marriage['current'] and marriage['year'] <= year):
                already_married = True
                break

        if not already_married:
            candidates.append(pid)

    return candidates


def simulate_child(father_id, mother_id, year):
    """Create a child with the given parents in the given year"""
    if mother_id not in people:
        return None

    mother = people[mother_id]

    # Calculate mother's age
    mother_birth_year = int(mother['date_of_birth'].split('-')[0])
    mother_age = year - mother_birth_year

    # Check if mother is of reproductive age
    if mother_age < FERTILITY_START_AGE or mother_age > FERTILITY_END_AGE_FEMALE:
        return None

    # Check if mother is alive
    if mother['is_deceased'] and int(mother['date_of_death'].split('-')[0]) < year:
        return None

    # Check if father is of reproductive age and alive (if known)
    if father_id and father_id in people:
        father = people[father_id]
        father_birth_year = int(father['date_of_birth'].split('-')[0])
        father_age = year - father_birth_year

        if father_age < FERTILITY_START_AGE or father_age > FERTILITY_END_AGE_MALE:
            return None

        if father['is_deceased'] and int(father['date_of_death'].split('-')[0]) < year:
            return None

    # Create the child with randomized gender
    child_id = create_person(
        birth_year=year,
        father_id=father_id,
        mother_id=mother_id,
        last_name=people[father_id]['last_name'] if father_id and father_id in people else mother['last_name']
    )

    # Register child with parents
    if father_id:
        if father_id not in children_map:
            children_map[father_id] = []
        children_map[father_id].append(child_id)

    if mother_id not in children_map:
        children_map[mother_id] = []
    children_map[mother_id].append(child_id)

    return child_id


def create_unknown_parent(is_male, birth_year=None):
    """Create a placeholder for an unknown parent"""
    if birth_year is None:
        # Estimate a plausible birth year
        birth_year = random.randint(START_YEAR, CURRENT_YEAR - 20)

    parent_id = create_person(
        birth_year=birth_year,
        forced_gender='M' if is_male else 'F',
        is_deceased=random.random() < 0.8,  # Likely deceased if unknown
        first_name="Unknown",
        last_name="Unknown" if is_male else "Unknown"
    )

    # Mark as unknown in notes
    people[parent_id]['notes'] = "Placeholder for unknown parent"

    return parent_id


def build_initial_population(num_families=15, family_max_size=20):
    """Create initial population with several distinct family lines"""

    family_patriarchs = []
    for _ in range(num_families):
        # Create a patriarch for each family line (born in early 1900s)
        birth_year = random.randint(START_YEAR, START_YEAR + 30)
        patriarch_id = create_person(birth_year=birth_year, forced_gender='M')
        family_patriarchs.append(patriarch_id)

        # Create a spouse for the patriarch
        birth_year_spouse = random.randint(birth_year - 5, birth_year + 5)
        spouse_id = create_person(
            birth_year=birth_year_spouse, forced_gender='F')

        # Register marriage at appropriate year
        marriage_year = max(birth_year, birth_year_spouse) + \
            random.randint(18, 25)
        simulate_marriage(patriarch_id, spouse_id, marriage_year)

        # Generate children
        # Larger families in older generations
        num_children = random.randint(2, 8)
        for _ in range(num_children):
            child_birth_year = random.randint(
                marriage_year + 1, min(marriage_year + 20, CURRENT_YEAR - 20))
            simulate_child(patriarch_id, spouse_id, child_birth_year)

    return family_patriarchs


def simulate_generations(num_generations=3):
    """Simulate multiple generations with relationships, marriages, etc."""

    for current_year in range(START_YEAR + 20, CURRENT_YEAR):
        # Find eligible people for events in this year
        eligible_for_marriage = []
        eligible_for_childbirth = []

        for pid, person in people.items():
            birth_year = int(person['date_of_birth'].split('-')[0])

            # Skip if person is deceased before this year
            if person['is_deceased'] and int(person['date_of_death'].split('-')[0]) < current_year:
                continue

            age = current_year - birth_year

            # Eligible for marriage
            if age >= MARRIAGE_MIN_AGE:
                # Check if already married
                already_married = False
                for marriage in marriages:
                    if ((marriage['person1_id'] == pid or marriage['person2_id'] == pid) and
                            marriage['current'] and marriage['year'] <= current_year):
                        already_married = True
                        break

                if not already_married:
                    eligible_for_marriage.append(pid)

            # Eligible for having children
            if ((person['sex'] == 'F' and FERTILITY_START_AGE <= age <= FERTILITY_END_AGE_FEMALE) or
                    (person['sex'] == 'M' and FERTILITY_START_AGE <= age <= FERTILITY_END_AGE_MALE)):
                eligible_for_childbirth.append(pid)

        # Process marriages
        for pid in eligible_for_marriage.copy():
            if random.random() < 0.1:  # Not everyone gets married in a given year
                candidates = find_spouse_candidates(pid, current_year)
                if candidates:
                    spouse_id = random.choice(candidates)
                    if simulate_marriage(pid, spouse_id, current_year):
                        # This is where the error occurs - need to check if still in list
                        if pid in eligible_for_marriage:  # Add this check
                            eligible_for_marriage.remove(pid)
                        if spouse_id in eligible_for_marriage:
                            eligible_for_marriage.remove(spouse_id)

        # Process divorces
        for marriage in marriages:
            if marriage['current'] and marriage['year'] < current_year:
                if random.random() < PROB_DIVORCE / 50:  # Yearly probability
                    marriage['current'] = False

        # Process childbirths
        # First for married couples
        for marriage in marriages:
            if marriage['current'] and marriage['year'] < current_year:
                p1_id = marriage['person1_id']
                p2_id = marriage['person2_id']

                # Determine which is male/female
                father_id = p1_id if people[p1_id]['sex'] == 'M' else p2_id
                mother_id = p1_id if people[p1_id]['sex'] == 'F' else p2_id

                # 20% chance of having a child in a given year if conditions are right
                if (mother_id in eligible_for_childbirth and
                        (not children_map.get(mother_id) or len(children_map.get(mother_id, [])) < 10)):

                    if random.random() < 0.2:
                        simulate_child(father_id, mother_id, current_year)

        # Then for out-of-wedlock births
        for mother_id in eligible_for_childbirth:
            if people[mother_id]['sex'] == 'F' and random.random() < PROB_OUT_OF_WEDLOCK / 10:
                # Decide if father is known or unknown
                if random.random() < PROB_UNKNOWN_FATHER:
                    # Create unknown father with estimated birth year
                    mother_birth_year = int(
                        people[mother_id]['date_of_birth'].split('-')[0])
                    father_birth_year = mother_birth_year + \
                        random.randint(-5, 5)
                    father_id = create_unknown_parent(
                        is_male=True, birth_year=father_birth_year)
                else:
                    # Find random male father
                    father_candidates = [
                        pid for pid, p in people.items()
                        if p['sex'] == 'M' and
                        FERTILITY_START_AGE <= (current_year - int(p['date_of_birth'].split('-')[0])) <= FERTILITY_END_AGE_MALE and
                        not (p['is_deceased'] and int(
                            p['date_of_death'].split('-')[0]) < current_year)
                    ]

                    if father_candidates:
                        father_id = random.choice(father_candidates)
                    else:
                        # Create unknown father
                        mother_birth_year = int(
                            people[mother_id]['date_of_birth'].split('-')[0])
                        father_birth_year = mother_birth_year + \
                            random.randint(-5, 5)
                        father_id = create_unknown_parent(
                            is_male=True, birth_year=father_birth_year)

                simulate_child(father_id, mother_id, current_year)

        # Create orphans and children with unknown parents
        if random.random() < 0.05:  # 5% chance each year to add an orphan
            # Create child
            birth_year = current_year

            # Decide if parents are known
            has_known_father = random.random() > PROB_UNKNOWN_FATHER
            has_known_mother = random.random() > PROB_UNKNOWN_MOTHER

            father_id = None
            mother_id = None

            if has_known_father:
                # Find or create father
                father_birth_year = birth_year - random.randint(20, 40)
                father_id = create_person(
                    birth_year=father_birth_year, forced_gender='M')
            else:
                father_id = create_unknown_parent(
                    is_male=True, birth_year=birth_year - random.randint(20, 40))

            if has_known_mother:
                # Find or create mother
                mother_birth_year = birth_year - random.randint(18, 35)
                mother_id = create_person(
                    birth_year=mother_birth_year, forced_gender='F')
            else:
                mother_id = create_unknown_parent(
                    is_male=False, birth_year=birth_year - random.randint(18, 35))

            # Create the child
            create_person(birth_year=birth_year,
                          father_id=father_id, mother_id=mother_id)


def create_family_tree(output_file='family_tree.json', num_families=15, num_generations=4):
    """Generate a complete family tree dataset"""
    build_initial_population(num_families)
    simulate_generations(num_generations)

    # Output the family tree data as JSON
    output = {
        "people": list(people.values())
    }

    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Generated family tree with {len(people)} people")

    # Generate some statistics
    num_males = sum(1 for p in people.values() if p['sex'] == 'M')
    num_females = sum(1 for p in people.values() if p['sex'] == 'F')
    num_deceased = sum(1 for p in people.values() if p['is_deceased'])

    print(
        f"Males: {num_males}, Females: {num_females}, Deceased: {num_deceased}")
    print(
        f"Marriages: {len(marriages)}, Current marriages: {sum(1 for m in marriages if m['current'])}")

    return output_file


# Example usage
if __name__ == "__main__":
    # You would need to pip install names, pandas, numpy, and faker first
    output_file = create_family_tree(num_families=15, num_generations=4)
    print(f"Family tree data saved to {output_file}")
