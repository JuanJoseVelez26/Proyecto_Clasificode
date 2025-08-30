# ClasifiCode - Sistema de Clasificación Arancelaria

Sistema inteligente de clasificación arancelaria que combina reglas RGI (Reglas Generales de Interpretación) con análisis semántico y procesamiento de lenguaje natural para determinar códigos HS (Harmonized System) de manera precisa y eficiente.

## 🚀 Características

- **Clasificación por Reglas RGI**: Implementación completa de las 6 Reglas Generales de Interpretación
- **Análisis Semántico**: Búsquedas vectoriales usando pgvector y embeddings
- **Procesamiento de Lenguaje Natural**: Normalización, lematización y análisis de similitud
- **API REST**: Backend robusto con Flask y SQLAlchemy
- **Interfaz Web**: Frontend moderno con Jinja2 y Bootstrap
- **Base de Datos**: PostgreSQL con extensión pgvector para búsquedas semánticas
- **Autenticación**: Sistema JWT completo con roles y permisos
- **Auditoría**: Logging completo de todas las operaciones

## 🏗️ Arquitectura

```
ClasifiCode/
├── Backend/                 # API REST Flask
│   ├── Config/             # Configuración y settings
│   ├── Controllers/        # Endpoints de la API
│   ├── Models/             # Modelos SQLAlchemy
│   ├── Service/            # Lógica de negocio
│   │   ├── Agente/         # Motor de reglas RGI
│   │   └── modeloPln/      # Servicios de PLN
│   └── main.py             # Punto de entrada
├── Frontend/               # Interfaz web
│   ├── Static/             # CSS, JS, imágenes
│   ├── Templates/          # Plantillas Jinja2
│   └── Views/              # Vistas y rutas
└── docker-compose.yml      # Orquestación de servicios
```

## 🛠️ Tecnologías

### Backend
- **Flask**: Framework web
- **SQLAlchemy**: ORM para PostgreSQL
- **psycopg3**: Driver PostgreSQL
- **pgvector**: Extensión para embeddings
- **JWT**: Autenticación y autorización
- **Alembic**: Migraciones de base de datos

### Frontend
- **Jinja2**: Motor de plantillas
- **Bootstrap**: Framework CSS
- **JavaScript**: Interactividad del cliente

### IA/ML
- **OpenAI API**: Embeddings y análisis semántico
- **spaCy**: Procesamiento de lenguaje natural
- **RapidFuzz**: Búsqueda difusa de texto

### Infraestructura
- **PostgreSQL**: Base de datos principal
- **Redis**: Caché y sesiones
- **Docker**: Containerización
- **Docker Compose**: Orquestación

## 📋 Requisitos

- Python 3.9+
- PostgreSQL 15+
- Redis 7+
- Docker y Docker Compose

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd software_clasificode
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 3. Ejecutar con Docker (Recomendado)
```bash
# Construir e iniciar todos los servicios
make build
make run

# O usar docker-compose directamente
docker-compose up -d
```

### 4. Instalación local (Alternativa)
```bash
# Instalar dependencias
make install

# Configurar base de datos
make setup

# Ejecutar migraciones
make migrate

# Poblar datos de prueba
make seed

# Iniciar servicios
make run-backend  # En una terminal
make run-frontend # En otra terminal
```

## 📊 Uso

### Acceso a la aplicación
- **Frontend**: http://localhost:8080
- **API Backend**: http://localhost:8000
- **pgAdmin**: http://localhost:5050 (admin@clasificode.com / admin123)

### Endpoints principales

#### Autenticación
- `POST /api/auth/login` - Iniciar sesión
- `POST /api/auth/register` - Registro de usuarios
- `POST /api/auth/refresh` - Renovar token

#### Clasificación
- `POST /api/classify` - Clasificar producto
- `GET /api/classify/history` - Historial de clasificaciones
- `GET /api/classify/{id}` - Detalle de clasificación

#### Casos
- `GET /api/cases` - Listar casos
- `POST /api/cases` - Crear nuevo caso
- `GET /api/cases/{id}` - Detalle del caso
- `PUT /api/cases/{id}` - Actualizar caso

#### Administración
- `GET /api/admin/users` - Gestión de usuarios
- `GET /api/admin/stats` - Estadísticas del sistema
- `POST /api/admin/embed-catalog` - Generar embeddings

## 🔧 Configuración

### Variables de entorno importantes

```env
# Base de datos
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Seguridad
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# APIs externas
OPENAI_API_KEY=your-openai-key
HUGGINGFACE_API_KEY=your-hf-key

# Configuración de embeddings
EMBEDDING_MODEL=text-embedding-ada-002
SIMILARITY_THRESHOLD=0.8
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
make test

# Tests específicos
cd Backend && python -m pytest tests/ -v
cd Frontend && python -m pytest tests/ -v
```

## 📈 Monitoreo y Logs

```bash
# Ver logs en tiempo real
make logs

# Estado de servicios
make status

# Logs específicos
docker-compose logs backend
docker-compose logs frontend
```

## 🔄 Migraciones

```bash
# Crear nueva migración
cd Backend && alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
make migrate

# Revertir migración
cd Backend && alembic downgrade -1
```

## 🗄️ Base de Datos

### Estructura principal

- **users**: Usuarios del sistema
- **cases**: Casos de clasificación
- **hs_items**: Catálogo de códigos HS
- **hs_notes**: Notas explicativas
- **rgi_rules**: Reglas RGI
- **embeddings**: Vectores semánticos
- **audit_logs**: Log de auditoría

### Comandos útiles

```bash
# Conectar a PostgreSQL
docker exec -it clasificode_postgres psql -U clasificode_user -d clasificode_db

# Backup de base de datos
docker exec clasificode_postgres pg_dump -U clasificode_user clasificode_db > backup.sql

# Restaurar backup
docker exec -i clasificode_postgres psql -U clasificode_user -d clasificode_db < backup.sql
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Para soporte técnico o preguntas:
- Crear un issue en GitHub
- Contactar al equipo de desarrollo
- Revisar la documentación técnica

## 🔮 Roadmap

- [ ] Integración con APIs de aduanas
- [ ] Machine Learning avanzado
- [ ] API GraphQL
- [ ] Aplicación móvil
- [ ] Análisis de tendencias
- [ ] Integración con ERP
- [ ] Módulo de reportes avanzados
- [ ] Sistema de notificaciones
