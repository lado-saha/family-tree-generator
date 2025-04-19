import json
import networkx as nx
import random
from datetime import datetime
import os
try:
    import pyvis
    from pyvis.network import Network
    HAVE_PYVIS = True
except ImportError:
    HAVE_PYVIS = False
    print("Pyvis not available. Interactive visualization disabled.")

def load_family_data(json_file):
    """Load family data from JSON file"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

def build_family_graph(people_data, max_people=None):
    """
    Build a NetworkX graph from family data
    Nodes are people, edges represent parent-child relationships
    """
    G = nx.DiGraph()
    
    # Limit the dataset for visualization if needed
    if max_people is not None and len(people_data) > max_people:
        # Take a random sample of people
        people_sample = random.sample(people_data, max_people)
    else:
        people_sample = people_data
    
    # Create a dictionary for quick lookups
    people_dict = {person['id']: person for person in people_data}
    
    # Add nodes (people)
    for person in people_sample:
        # Calculate age or years lived
        birth_year = int(person['date_of_birth'].split('-')[0])
        if person['is_deceased'] and person['date_of_death']:
            death_year = int(person['date_of_death'].split('-')[0])
            years_lived = death_year - birth_year
            age_text = f"{years_lived} years"
        else:
            current_year = datetime.now().year
            age = current_year - birth_year
            age_text = f"{age} years"
        
        # Format name
        name = f"{person['first_name']} {person['last_name']}"
        if person['is_deceased']:
            name += " ✝"
        
        # Create label
        label = f"{name}\n({birth_year}-{death_year if person['is_deceased'] and person['date_of_death'] else 'Present'})"
        
        # Store complete info in the node for tooltips later
        node_info = {
            'id': person['id'],
            'label': label,
            'name': name,
            'sex': person['sex'],
            'birth': birth_year,
            'age': age_text,
            'is_deceased': person['is_deceased'],
            'father_id': person['father_id'],
            'mother_id': person['mother_id'],
            'first_name': person['first_name'],
            'last_name': person['last_name'],
            'nationality': person['nationality'],
            'occupation': person['occupation'],
            'education': person['education'],
            'blood_type': person['blood_type'],
        }
        
        # Add node with gender-based color
        color = '#ADD8E6' if person['sex'] == 'M' else '#FFCCCB'  # Light blue for males, light red for females
        if person['first_name'] == 'Unknown':
            color = '#D3D3D3'  # Grey for unknown people
        
        G.add_node(person['id'], **node_info, color=color)
    
    # Add edges (parent-child relationships)
    for person in people_sample:
        # Add edge from father to child if father exists and is in our sample
        if person['father_id'] and person['father_id'] in G:
            G.add_edge(person['father_id'], person['id'], relationship='father')
        
        # Add edge from mother to child if mother exists and is in our sample
        if person['mother_id'] and person['mother_id'] in G:
            G.add_edge(person['mother_id'], person['id'], relationship='mother')
    
    return G

def visualize_with_pyvis(G, output_file='family_tree.html', height="800px", width="100%"):
    """
    Create an interactive family tree visualization using pyvis
    This allows for dynamic exploration of large family trees
    """
    if not HAVE_PYVIS:
        print("Pyvis is not available. Cannot create interactive visualization.")
        return

    # Create a new network
    net = Network(height=height, width=width, directed=True, notebook=False)

    # Add all nodes
    for node_id, node_data in G.nodes(data=True):
        # Create plain text label without HTML tags
        name = node_data.get('name', 'Unknown')
        birth = node_data.get('birth', 'Unknown')
        age = node_data.get('age', 'Unknown')

        # Simple multi-line label without HTML tags
        label = f"{name}\nBorn: {birth}\nAge: {age}"

        # Create title (tooltip) with more detailed information
        title = f"{node_data.get('label', 'Unknown person')}"

        # Add the node - using circles for everyone
        color = node_data.get('color', '#CCCCCC')
        shape = 'circle'  # Same shape for everyone

        # Only use a different shape for unknown people
        if node_data.get('first_name') == 'Unknown':
            shape = 'diamond'

        net.add_node(node_id, label=label, title=title,
                     color=color, shape=shape)

    # Add edges (relationships)
    for source, target, edge_data in G.edges(data=True):
        if edge_data.get('relationship') == 'father':
            color = 'blue'
        elif edge_data.get('relationship') == 'mother':
            color = 'red'
        else:
            color = 'gray'

        net.add_edge(source, target, color=color)

    # Configure physics for better layout
    net.barnes_hut(
        gravity=-3000,
        central_gravity=0.5,
        spring_length=150,
        spring_strength=0.05,
        damping=0.09
    )

    # Handle different pyvis versions
    try:
        # Newer pyvis versions
        net.show_buttons(filter_=['physics'])
    except (AttributeError, TypeError):
        try:
            # Older pyvis versions
            net.show_buttons()
        except Exception as e:
            print(f"Warning: Could not add buttons due to version incompatibility: {e}")
            # Continue without buttons

    # Save to HTML file
    net.save_graph(output_file)
    print(f"Interactive family tree visualization saved to {output_file}")

    return output_file