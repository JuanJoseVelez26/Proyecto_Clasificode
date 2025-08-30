#!/usr/bin/env python3
"""
Seed script to populate database with initial data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import create_app
from Service.db import db
from Service.security import security_service
from Models.user import User, UserRole, UserStatus
from Models.hs_item import HSItem
from Models.rgi_rule import RGIRule
from Models.legal_source import LegalSource
import logging

def create_users():
    """Create initial users"""
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@clasificode.com',
            'password': 'Admin123!',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': UserRole.ADMIN,
            'department': 'IT',
            'position': 'System Administrator'
        },
        {
            'username': 'analyst1',
            'email': 'analyst1@clasificode.com',
            'password': 'Analyst123!',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'role': UserRole.ANALYST,
            'department': 'Clasificación',
            'position': 'Analista Senior'
        },
        {
            'username': 'analyst2',
            'email': 'analyst2@clasificode.com',
            'password': 'Analyst123!',
            'first_name': 'María',
            'last_name': 'García',
            'role': UserRole.ANALYST,
            'department': 'Clasificación',
            'position': 'Analista Junior'
        },
        {
            'username': 'viewer1',
            'email': 'viewer1@clasificode.com',
            'password': 'Viewer123!',
            'first_name': 'Carlos',
            'last_name': 'López',
            'role': UserRole.VIEWER,
            'department': 'Comercio',
            'position': 'Especialista'
        }
    ]
    
    created_users = []
    for user_data in users_data:
        # Check if user already exists
        existing_user = db.session.query(User).filter_by(username=user_data['username']).first()
        if existing_user:
            print(f"User {user_data['username']} already exists, skipping...")
            continue
        
        # Hash password
        password_hash = security_service.hash_password(user_data['password'])
        
        # Create user
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            password_hash=password_hash,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            full_name=f"{user_data['first_name']} {user_data['last_name']}",
            role=user_data['role'],
            department=user_data['department'],
            position=user_data['position'],
            status=UserStatus.ACTIVE,
            is_active=True
        )
        
        db.session.add(user)
        created_users.append(user)
        print(f"Created user: {user.username}")
    
    db.session.commit()
    return created_users

def create_rgi_rules():
    """Create RGI rules"""
    rules_data = [
        {
            'rule_number': 1,
            'title': 'Títulos de Secciones, Capítulos y Subcapítulos',
            'description': 'Los títulos de las Secciones, Capítulos y Subcapítulos tienen un valor indicativo únicamente.',
            'rule_text': 'Los títulos de las Secciones, Capítulos y Subcapítulos tienen un valor indicativo únicamente; para efectos legales, la clasificación se determina según los textos de las partidas y de las Notas de Sección o de Capítulo y, si no son contrarias a los textos de dichas partidas y Notas, según las Reglas siguientes.',
            'examples': 'Ejemplo: El título "Máquinas y aparatos mecánicos" en el Capítulo 84 es indicativo de que las máquinas y aparatos mecánicos se clasifican en ese capítulo.'
        },
        {
            'rule_number': 2,
            'title': 'Mercancías Incompletas o Sin Terminar',
            'description': 'Cualquier referencia a un artículo en una partida determinada alcanza al artículo incluso incompleto o sin terminar.',
            'rule_text': 'a) Cualquier referencia a un artículo en una partida determinada alcanza al artículo incluso incompleto o sin terminar, siempre que éste presente las características esenciales del artículo completo o terminado.\nb) Cualquier referencia a un artículo en una partida determinada alcanza también a ese artículo completo o terminado (o clasificado como completo o terminado en virtud de la Regla anterior) presentado desmontado o sin montar aún.',
            'examples': 'Ejemplo: Un automóvil sin motor se clasifica como automóvil completo.'
        },
        {
            'rule_number': 3,
            'title': 'Mercancías Mixtas o Compuestas',
            'description': 'Cuando una mercancía pueda clasificarse en dos o más partidas, se aplican las reglas de preferencia.',
            'rule_text': 'Cuando una mercancía pueda clasificarse en dos o más partidas, se aplican las reglas siguientes:\na) La partida con descripción más específica tiene prioridad sobre las partidas de descripción más genérica.\nb) Las mercancías mixtas, las mercancías compuestas de materias diferentes o constituidas por la unión de artículos diferentes y los envases que contengan mercancías se clasificarán según el material o la materia que les confiera su carácter esencial.\nc) Cuando no se pueda determinar el carácter esencial, se clasificará en la última partida por orden de numeración entre las susceptibles de tenerse razonablemente en cuenta.',
            'examples': 'Ejemplo: Una taza de porcelana con asa de metal se clasifica como porcelana.'
        },
        {
            'rule_number': 4,
            'title': 'Mercancías que no Puedan Clasificarse',
            'description': 'Las mercancías que no puedan clasificarse según las Reglas anteriores se clasifican en la partida que comprenda las mercancías más afines.',
            'rule_text': 'Las mercancías que no puedan clasificarse según las Reglas anteriores se clasifican en la partida que comprenda las mercancías más afines.',
            'examples': 'Ejemplo: Un producto nuevo que no se ajuste a ninguna partida específica se clasifica en la partida más similar.'
        },
        {
            'rule_number': 5,
            'title': 'Envases y Embalajes',
            'description': 'Los envases y embalajes se clasifican con las mercancías que contengan.',
            'rule_text': 'a) Los estuches para cámaras fotográficas, instrumentos musicales, armas, instrumentos de dibujo, collares y artículos similares, especialmente adaptados para contener un artículo determinado o un juego o surtido, susceptibles de uso prolongado y presentados con los artículos correspondientes, se clasifican con estos artículos cuando sean del tipo normalmente vendido con ellos.\nb) Salvo lo dispuesto en la Regla anterior, los envases que contengan mercancías se clasifican con ellas cuando sean del tipo normalmente utilizado para esa clase de mercancías.\nc) Las demás cajas, cajones, cajas de embalaje y similares se clasifican por separado.',
            'examples': 'Ejemplo: Una caja de cartón que contenga zapatos se clasifica con los zapatos.'
        },
        {
            'rule_number': 6,
            'title': 'Interpretación de las Partidas',
            'description': 'Para la aplicación de estas Reglas, las partidas y subpartidas se consideran mutuamente excluyentes.',
            'rule_text': 'Para la aplicación de estas Reglas, las partidas y subpartidas se consideran mutuamente excluyentes. Sin embargo, cuando una partida o subpartida se refiera a un artículo o a un material, se considera que incluye también las referencias a ese artículo o material en estado mezclado o asociado con otros artículos o materiales.',
            'examples': 'Ejemplo: Una partida que mencione "algodón" incluye también mezclas de algodón con otras fibras.'
        }
    ]
    
    created_rules = []
    for rule_data in rules_data:
        # Check if rule already exists
        existing_rule = db.session.query(RGIRule).filter_by(rule_number=rule_data['rule_number']).first()
        if existing_rule:
            print(f"RGI Rule {rule_data['rule_number']} already exists, skipping...")
            continue
        
        # Create rule
        rule = RGIRule(**rule_data)
        db.session.add(rule)
        created_rules.append(rule)
        print(f"Created RGI Rule {rule.rule_number}: {rule.title}")
    
    db.session.commit()
    return created_rules

def create_sample_hs_items():
    """Create sample HS items"""
    hs_items_data = [
        {
            'hs_code': '01',
            'chapter': '01',
            'heading': '0101',
            'subheading': '010101',
            'full_code': '0101010000',
            'description': 'Animales vivos de la especie bovina',
            'english_description': 'Live animals of the bovine species',
            'spanish_description': 'Animales vivos de la especie bovina',
            'level': 1,
            'is_leaf': False
        },
        {
            'hs_code': '0101',
            'chapter': '01',
            'heading': '0101',
            'subheading': '010101',
            'full_code': '0101010000',
            'description': 'Animales vivos de la especie bovina',
            'english_description': 'Live animals of the bovine species',
            'spanish_description': 'Animales vivos de la especie bovina',
            'level': 2,
            'parent_code': '01',
            'is_leaf': False
        },
        {
            'hs_code': '010101',
            'chapter': '01',
            'heading': '0101',
            'subheading': '010101',
            'full_code': '0101010000',
            'description': 'Animales vivos de la especie bovina, reproductores de raza pura',
            'english_description': 'Live animals of the bovine species, pure-bred breeding animals',
            'spanish_description': 'Animales vivos de la especie bovina, reproductores de raza pura',
            'level': 3,
            'parent_code': '0101',
            'is_leaf': False
        },
        {
            'hs_code': '0101010000',
            'chapter': '01',
            'heading': '0101',
            'subheading': '010101',
            'full_code': '0101010000',
            'description': 'Animales vivos de la especie bovina, reproductores de raza pura',
            'english_description': 'Live animals of the bovine species, pure-bred breeding animals',
            'spanish_description': 'Animales vivos de la especie bovina, reproductores de raza pura',
            'level': 4,
            'parent_code': '010101',
            'is_leaf': True
        },
        {
            'hs_code': '84',
            'chapter': '84',
            'heading': '8401',
            'subheading': '840101',
            'full_code': '8401010000',
            'description': 'Reactores nucleares',
            'english_description': 'Nuclear reactors',
            'spanish_description': 'Reactores nucleares',
            'level': 1,
            'is_leaf': False
        },
        {
            'hs_code': '8401',
            'chapter': '84',
            'heading': '8401',
            'subheading': '840101',
            'full_code': '8401010000',
            'description': 'Reactores nucleares',
            'english_description': 'Nuclear reactors',
            'spanish_description': 'Reactores nucleares',
            'level': 2,
            'parent_code': '84',
            'is_leaf': False
        },
        {
            'hs_code': '840101',
            'chapter': '84',
            'heading': '8401',
            'subheading': '840101',
            'full_code': '8401010000',
            'description': 'Reactores nucleares',
            'english_description': 'Nuclear reactors',
            'spanish_description': 'Reactores nucleares',
            'level': 3,
            'parent_code': '8401',
            'is_leaf': False
        },
        {
            'hs_code': '8401010000',
            'chapter': '84',
            'heading': '8401',
            'subheading': '840101',
            'full_code': '8401010000',
            'description': 'Reactores nucleares',
            'english_description': 'Nuclear reactors',
            'spanish_description': 'Reactores nucleares',
            'level': 4,
            'parent_code': '840101',
            'is_leaf': True
        }
    ]
    
    created_items = []
    for item_data in hs_items_data:
        # Check if item already exists
        existing_item = db.session.query(HSItem).filter_by(hs_code=item_data['hs_code']).first()
        if existing_item:
            print(f"HS Item {item_data['hs_code']} already exists, skipping...")
            continue
        
        # Create item
        item = HSItem(**item_data)
        db.session.add(item)
        created_items.append(item)
        print(f"Created HS Item: {item.hs_code} - {item.description}")
    
    db.session.commit()
    return created_items

def create_legal_sources():
    """Create legal sources"""
    sources_data = [
        {
            'source_type': 'LAW',
            'title': 'Ley de Comercio Exterior',
            'description': 'Ley que regula el comercio exterior en el país',
            'reference_number': 'LCE-2024',
            'publication_date': '2024-01-01',
            'effective_date': '2024-01-01',
            'content': 'Texto completo de la Ley de Comercio Exterior...'
        },
        {
            'source_type': 'REGULATION',
            'title': 'Reglamento de Clasificación Arancelaria',
            'description': 'Reglamento que establece las reglas de clasificación arancelaria',
            'reference_number': 'RCA-2024',
            'publication_date': '2024-01-15',
            'effective_date': '2024-02-01',
            'content': 'Texto completo del Reglamento de Clasificación Arancelaria...'
        }
    ]
    
    created_sources = []
    for source_data in sources_data:
        # Check if source already exists
        existing_source = db.session.query(LegalSource).filter_by(reference_number=source_data['reference_number']).first()
        if existing_source:
            print(f"Legal Source {source_data['reference_number']} already exists, skipping...")
            continue
        
        # Create source
        source = LegalSource(**source_data)
        db.session.add(source)
        created_sources.append(source)
        print(f"Created Legal Source: {source.reference_number} - {source.title}")
    
    db.session.commit()
    return created_sources

def main():
    """Main seeding function"""
    app = create_app()
    
    with app.app_context():
        print("Starting database seeding...")
        
        # Create users
        print("\n=== Creating Users ===")
        users = create_users()
        print(f"Created {len(users)} users")
        
        # Create RGI rules
        print("\n=== Creating RGI Rules ===")
        rules = create_rgi_rules()
        print(f"Created {len(rules)} RGI rules")
        
        # Create sample HS items
        print("\n=== Creating Sample HS Items ===")
        hs_items = create_sample_hs_items()
        print(f"Created {len(hs_items)} HS items")
        
        # Create legal sources
        print("\n=== Creating Legal Sources ===")
        sources = create_legal_sources()
        print(f"Created {len(sources)} legal sources")
        
        print("\n=== Seeding Complete ===")
        print("Database has been populated with initial data.")

if __name__ == '__main__':
    main()
