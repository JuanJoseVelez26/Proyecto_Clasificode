.PHONY: help install setup run build clean test migrate seed

# Default target
help:
	@echo "ClasifiCode - Sistema de Clasificación Arancelaria"
	@echo ""
	@echo "Comandos disponibles:"
	@echo "  install     - Instalar dependencias"
	@echo "  setup       - Configurar base de datos y variables de entorno"
	@echo "  run         - Ejecutar el proyecto completo"
	@echo "  run-backend - Ejecutar solo el backend"
	@echo "  run-frontend- Ejecutar solo el frontend"
	@echo "  build       - Construir imágenes Docker"
	@echo "  clean       - Limpiar contenedores y volúmenes"
	@echo "  test        - Ejecutar tests"
	@echo "  migrate     - Ejecutar migraciones de base de datos"
	@echo "  seed        - Poblar base de datos con datos de prueba"

# Instalar dependencias
install:
	@echo "Instalando dependencias del backend..."
	cd Backend && pip install -r requirements.txt
	@echo "Instalando dependencias del frontend..."
	cd Frontend && pip install -r requirements.txt

# Configurar proyecto
setup:
	@echo "Configurando proyecto..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Archivo .env creado. Por favor, edita las variables de entorno."; \
	fi
	@echo "Creando directorio de logs..."
	mkdir -p logs
	@echo "Configuración completada."

# Ejecutar proyecto completo
run:
	@echo "Iniciando ClasifiCode..."
	docker-compose up -d

# Ejecutar solo backend
run-backend:
	@echo "Iniciando backend..."
	cd Backend && python main.py

# Ejecutar solo frontend
run-frontend:
	@echo "Iniciando frontend..."
	cd Frontend && python app.py

# Construir imágenes Docker
build:
	@echo "Construyendo imágenes Docker..."
	docker-compose build

# Limpiar contenedores y volúmenes
clean:
	@echo "Deteniendo contenedores..."
	docker-compose down
	@echo "Limpiando volúmenes..."
	docker-compose down -v
	@echo "Limpiando imágenes no utilizadas..."
	docker system prune -f

# Ejecutar tests
test:
	@echo "Ejecutando tests del backend..."
	cd Backend && python -m pytest tests/ -v
	@echo "Ejecutando tests del frontend..."
	cd Frontend && python -m pytest tests/ -v

# Ejecutar migraciones
migrate:
	@echo "Ejecutando migraciones..."
	cd Backend && python -m alembic upgrade head

# Poblar base de datos
seed:
	@echo "Poblando base de datos con datos de prueba..."
	cd Backend && python scripts/seed.py

# Generar embeddings del catálogo HS
embed-catalog:
	@echo "Generando embeddings del catálogo HS..."
	cd Backend && python scripts/embed_hs_catalog.py

# Logs en tiempo real
logs:
	docker-compose logs -f

# Reiniciar servicios
restart:
	docker-compose restart

# Estado de los servicios
status:
	docker-compose ps
