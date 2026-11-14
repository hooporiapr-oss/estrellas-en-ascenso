# Estrellas en Ascenso · Cognitivo Gym

Online lessons for kids ages 5 to 6 and their parents. Each lesson is a short
video spoken to the child by a coach's voice, a game to play on a tablet, and
an activity to do at home with mom or dad.

## Lessons

| # | Lesson | Video |
|---|--------|-------|
| 1 | La Zona 2-1-2 | `videos/leccion1-zona-212.mp4` (59 s, cover `videos/leccion1-portada.jpg`) |

## Making the videos

The tools are in `herramientas/` (Python with Pillow and NumPy, plus ffmpeg):

- `leccion1.py` builds Lección 1. The voice is generated with Piper and its
  male Spanish voice `es-carlfm-x-low`; point `PIPER` and `VOZ` at them:

  ```
  PIPER=/path/to/piper VOZ=/path/to/es-carlfm-x-low.onnx python3 herramientas/leccion1.py videos/leccion1-zona-212.mp4
  ```

- `zona212.py` is the same drill without a voice (its pieces, cones and court are shared with `leccion1.py`).
- `sigue.py` (court, text, closing card) and `musica.py` (music) are shared helpers; the fonts are under the SIL Open Font License (`OFL-*.txt`).

© 2026 Gostar Digital LLC
