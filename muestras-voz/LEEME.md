# Muestras de voz para el video de Monty Hall

Las 8 voces leen el mismo texto (el inicio del guion), así que se pueden comparar directamente.
Todas salen de Piper (gratis, funciona sin internet). Para que no suenen genéricas, a cada una le cambié
el ritmo, el tono y la variación al hablar, y le agregué ecualización, compresión y a veces un poco de eco.

| # | Archivo | Acento | Estilo |
|---|---------|--------|--------|
| 1 | 01-daniela-argentina-cercana.mp3 | Argentina (mujer) | Cercana, como un amigo que te cuenta algo |
| 2 | 02-daniela-argentina-intriga.mp3 | Argentina (mujer, más grave) | Lenta y misteriosa |
| 3 | 03-claude-mexico-documental.mp3 | México (hombre) | Documental, con algo de sala (la voz actual del video, mejorada) |
| 4 | 04-ald-mexico-grave-radio.mp3 | México (hombre, más grave) | Locutor de radio, con mucho cuerpo |
| 5 | 05-davefx-espana-narrador.mp3 | España (hombre) | Narrador clásico |
| 6 | 06-sharvard-espana-mujer-energica.mp3 | España (mujer) | Rápida y con energía, tipo YouTube |
| 7 | 07-sharvard-espana-hombre-calido.mp3 | España (hombre) | Cálida y tranquila |
| 8 | 08-carlfm-espana-lofi-misterio.mp3 | España (hombre) | Lo-fi, como una radio vieja o un podcast de misterio |

Notas:
- Daniela (1 y 2) es la única voz argentina, pero pronuncia algunas palabras un poco borrosas.
- Las voces 4, 6 y 7 son las que pasaron la prueba de transcripción automática casi sin errores.
- Cuando elijas una, se puede regenerar el video entero con esa voz: `python3 monty_sync.py voz salida`.
