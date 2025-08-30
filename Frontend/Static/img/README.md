# Directorio de Imágenes - ClasifiCode

Este directorio contiene las imágenes estáticas utilizadas en el frontend de ClasifiCode.

## Archivos esperados:

- `favicon.ico` - Icono del sitio web
- `logo.png` - Logo de ClasifiCode
- `hero-bg.jpg` - Imagen de fondo para la página de inicio
- `placeholder.png` - Imagen placeholder para productos sin imagen

## Notas:

- Todas las imágenes deben estar optimizadas para web
- Formatos recomendados: PNG, JPG, SVG
- Tamaños recomendados:
  - favicon.ico: 16x16, 32x32, 48x48
  - logo.png: 200x80px
  - hero-bg.jpg: 1920x1080px
  - placeholder.png: 400x300px

## Uso en las plantillas:

```html
<!-- Favicon -->
<link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='img/favicon.ico') }}">

<!-- Logo -->
<img src="{{ url_for('static', filename='img/logo.png') }}" alt="ClasifiCode Logo">

<!-- Imagen de fondo -->
<div style="background-image: url('{{ url_for('static', filename='img/hero-bg.jpg') }}')">
```

## Optimización:

Para optimizar las imágenes antes de subirlas:

1. Comprimir imágenes JPG con calidad 80-85%
2. Optimizar PNG con herramientas como TinyPNG
3. Convertir iconos simples a SVG cuando sea posible
4. Usar formatos WebP para navegadores modernos (con fallback)
