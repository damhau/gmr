#!/usr/bin/env python3
"""Writes app/static/themes/*.json. Edit a theme here (or the JSON directly) and run: python3 app/tools_make_themes.py

Theme format (all keys optional except name):
  name, emoji            shown in /admin
  colors                 sky/dawn/horizon (background gradient top/mid/bottom), ground, path, pathDone, ink, cloud,
                         mist (target times), accent (flag, streak, late), ok (done time), sun, discDone
  texts                  title, subtitle, msgs[5] (0..4 steps done), win, late  - placeholders {goal} {time}
  icons                  emoji per task: wake clothes breakfast teeth
  sky                    {"type":"sun"} | {"type":"emoji","emoji":"🌙","size":56} | {"type":"none"}
  clouds                 true/false
  decor                  [{"emoji":"⭐","x":120,"y":50,"size":22}, {"circle":1,"x":..,"y":..,"r":..,"fill":".."},
                          {"rect":1,"x":..,"y":..,"w":..,"h":..,"fill":".."}]   (SVG coords, 1000x338 scene, sky is y<250)
                         Free spots: sky y<110 anywhere; on the ground, x~220 or x~700 with y=246 (the road is high there).
                         Stations sit at x~90, 320, 560, 800 (discs y 170-255, labels y 266-335); avoid them.
  confetti               emoji list for the celebration
  rider                  SVG fragment drawn in an 80x80 box, facing right, feet at y~76; placed on the trail
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "static" / "themes"
OUT.mkdir(parents=True, exist_ok=True)

SHADOW = '<ellipse cx="38" cy="79" rx="16" ry="4" fill="rgba(0,0,0,.14)"/>'

THEMES = {
"licorne": {
  "name": "Licorne", "emoji": "🦄",
  "colors": {"sky": "#D6ECFF", "dawn": "#FFE6CB", "horizon": "#FFF6EA", "ground": "#6ED39E", "path": "#F7C88C", "pathDone": "#FF8A65",
             "ink": "#22304F", "cloud": "#ffffff", "mist": "#8FA8C6", "accent": "#FF6F59", "ok": "#1F9E63", "sun": "#FFD23F", "discDone": "#FFF1EC"},
  "texts": {"title": "En route pour l'école, Romane !", "subtitle": "Quatre étapes, puis le drapeau. Tu y arrives avant {goal} ?",
            "msgs": ["En selle, c'est parti !", "Super départ !", "À mi-chemin !", "Presque au drapeau…", "Tu as réussi ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! 🎉 Bravo Romane !", "late": "Arrivée à {time}. Demain avant {goal} ?"},
  "icons": {"wake": "☀️", "clothes": "👕", "breakfast": "🥣", "teeth": "🪥"},
  "sky": {"type": "sun"}, "clouds": True, "confetti": ["🌟", "⭐", "🦄", "🎉", "✨"],
  "rider": SHADOW + '''<rect x="14" y="52" width="8" height="24" rx="4" fill="#fff"/><rect x="38" y="52" width="8" height="24" rx="4" fill="#fff"/>
<ellipse cx="30" cy="48" rx="26" ry="17" fill="#fff"/><path d="M6 44 C -10 34, -8 60, 6 56" fill="#C58BFF"/>
<ellipse cx="54" cy="30" rx="15" ry="13" fill="#fff"/><ellipse cx="66" cy="34" rx="8" ry="6" fill="#FFD9E8"/><circle cx="56" cy="27" r="2.6" fill="#22304F"/>
<path d="M40 22 C 38 6, 56 8, 52 20 C 60 4, 72 14, 62 24" fill="#7DD8FF"/><path d="M50 18 L54 -2 L58 18 Z" fill="#FFD23F"/>'''},

"shrek": {
  "name": "Shrek", "emoji": "🧅",
  "colors": {"sky": "#CFE8C9", "dawn": "#E9EFC2", "horizon": "#F5F1D6", "ground": "#5E9E3E", "path": "#B98A5A", "pathDone": "#7B4F2A",
             "ink": "#2E3B1E", "cloud": "#ffffff", "mist": "#7F9A6D", "accent": "#E0592B", "ok": "#2B7A2B", "sun": "#F7D64A", "discDone": "#E8F3D6"},
  "texts": {"title": "Direction le marais, Romane !", "subtitle": "Quatre étapes avant l'école. Les ogres sont à l'heure avant {goal} ?",
            "msgs": ["Debout, l'ogre !", "Comme un oignon : couche par couche !", "L'Âne suit, à mi-chemin !", "Le marais est en vue…", "Bravo, digne de Fiona ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! 🎉 Même Dragon est impressionnée !", "late": "Arrivée à {time}. Demain, on bat l'Âne avant {goal} ?"},
  "icons": {"wake": "🌅", "clothes": "🧥", "breakfast": "🥞", "teeth": "🪥"},
  "sky": {"type": "sun"}, "clouds": True, "confetti": ["🧅", "🐸", "🌿", "🎉", "💚"],
  "decor": [{"emoji": "🌳", "x": 220, "y": 246, "size": 44}, {"emoji": "🐸", "x": 700, "y": 246, "size": 26}, {"emoji": "🦋", "x": 420, "y": 110, "size": 22}],
  "rider": SHADOW + '''<rect x="24" y="58" width="10" height="20" rx="4" fill="#4A2E14"/><rect x="42" y="58" width="10" height="20" rx="4" fill="#4A2E14"/>
<path d="M18 40 h40 l5 22 h-50 z" fill="#8B5A2B"/><rect x="30" y="40" width="16" height="22" fill="#F1E3B4"/>
<ellipse cx="38" cy="26" rx="18" ry="16" fill="#8DC63F"/>
<path d="M20 22 c-8 -2 -12 -10 -6 -12 c4 -1 6 6 8 10z" fill="#8DC63F"/><path d="M56 22 c8 -2 12 -10 6 -12 c-4 -1 -6 6 -8 10z" fill="#8DC63F"/>
<circle cx="14" cy="11" r="2.5" fill="#6FA832"/><circle cx="62" cy="11" r="2.5" fill="#6FA832"/>
<circle cx="32" cy="24" r="3.4" fill="#fff"/><circle cx="45" cy="24" r="3.4" fill="#fff"/><circle cx="33" cy="24" r="1.6" fill="#222"/><circle cx="46" cy="24" r="1.6" fill="#222"/>
<path d="M30 33 q9 7 18 0" stroke="#3E6B1D" stroke-width="2" fill="none" stroke-linecap="round"/><ellipse cx="38" cy="29" rx="3" ry="2" fill="#7FB236"/>'''},

"harry-potter": {
  "name": "Harry Potter", "emoji": "⚡",
  "colors": {"sky": "#141A3A", "dawn": "#2B2F63", "horizon": "#4A3A6B", "ground": "#2F4A3A", "path": "#C9A24A", "pathDone": "#F3D57A",
             "ink": "#F5ECD3", "cloud": "#3C4577", "mist": "#B9B0D9", "accent": "#E5B84A", "ok": "#8FE39A", "sun": "#F5ECD3", "discDone": "#3B3560"},
  "texts": {"title": "Direction Poudlard, Romane !", "subtitle": "Quatre sortilèges, puis le drapeau. Le Poudlard Express part à {goal} !",
            "msgs": ["Accio réveil !", "Un sortilège réussi !", "À mi-chemin du château !", "La tour d'astronomie est en vue…", "10 points pour Romane ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! ⚡ Le Choixpeau est fier de toi !", "late": "Arrivée à {time}. Demain, on attrape le train avant {goal} ?"},
  "icons": {"wake": "🦉", "clothes": "🧣", "breakfast": "🍫", "teeth": "🪄"},
  "sky": {"type": "emoji", "emoji": "🌙", "size": 58}, "clouds": False, "confetti": ["⚡", "🦉", "✨", "🪄", "⭐"],
  "decor": [{"circle": 1, "x": 90, "y": 40, "r": 2, "fill": "#fff"}, {"circle": 1, "x": 210, "y": 90, "r": 1.5, "fill": "#fff"}, {"circle": 1, "x": 330, "y": 30, "r": 2.2, "fill": "#fff"},
            {"circle": 1, "x": 480, "y": 70, "r": 1.6, "fill": "#fff"}, {"circle": 1, "x": 600, "y": 25, "r": 2, "fill": "#fff"}, {"circle": 1, "x": 720, "y": 95, "r": 1.4, "fill": "#fff"},
            {"circle": 1, "x": 810, "y": 40, "r": 2.4, "fill": "#fff"}, {"circle": 1, "x": 160, "y": 140, "r": 1.3, "fill": "#fff"}, {"circle": 1, "x": 560, "y": 130, "r": 1.8, "fill": "#fff"},
            {"emoji": "🏰", "x": 700, "y": 118, "size": 64}, {"emoji": "🦉", "x": 250, "y": 118, "size": 26}],
  "rider": SHADOW + '''<line x1="4" y1="64" x2="66" y2="44" stroke="#8B5A2B" stroke-width="4" stroke-linecap="round"/>
<path d="M8 62 L-4 72 M9 65 L0 78 M12 66 L6 78 M6 60 L-8 66" stroke="#C9A24A" stroke-width="3" stroke-linecap="round"/>
<path d="M28 30 l-9 28 h30 l-7 -28 z" fill="#1F1F2E"/>
<circle cx="35" cy="22" r="10" fill="#F5D0B0"/><path d="M24 20 q11 -14 22 -1 q-3 -6 -11 -8 q-8 1 -11 9z" fill="#3A2718"/>
<circle cx="31" cy="24" r="3.5" fill="none" stroke="#222" stroke-width="1.5"/><circle cx="40" cy="24" r="3.5" fill="none" stroke="#222" stroke-width="1.5"/><line x1="34.5" y1="24" x2="36.5" y2="24" stroke="#222" stroke-width="1.5"/>
<path d="M25 32 h20 v5 h-20 z" fill="#7B1E22"/><rect x="25" y="34" width="20" height="1.6" fill="#E5B84A"/><path d="M43 33 l8 10 l-4 1 l-6 -8z" fill="#7B1E22"/>
<path d="M35 10 l4 -1 l-2 3 l3 -1 l-4 5 l1 -3 l-3 1 z" fill="#E5B84A"/>'''},

"kpop-demon-hunters": {
  "name": "KPop Demon Hunters", "emoji": "🎤",
  "colors": {"sky": "#2A1140", "dawn": "#6A1B9A", "horizon": "#C2185B", "ground": "#3B1A5C", "path": "#FF6FB5", "pathDone": "#7CF5FF",
             "ink": "#FFF3FB", "cloud": "#8E44AD", "mist": "#D9B3FF", "accent": "#FF3FA4", "ok": "#7CF5FF", "sun": "#FF3FA4", "discDone": "#4B2072"},
  "texts": {"title": "Huntr/x en scène, Romane !", "subtitle": "Quatre étapes pour sceller le Honmoon avant {goal} !",
            "msgs": ["Le concert commence !", "Golden ! Premier couplet réussi !", "À mi-chemin, les démons reculent !", "Dernier refrain avant le drapeau…", "Le Honmoon est scellé ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! 🎤 Rumi, Mira et Zoey t'applaudissent !", "late": "Arrivée à {time}. Demain, on chante plus vite qu'avant {goal} ?"},
  "icons": {"wake": "🎵", "clothes": "👘", "breakfast": "🍜", "teeth": "✨"},
  "sky": {"type": "emoji", "emoji": "🌟", "size": 54}, "clouds": False, "confetti": ["🎤", "💜", "✨", "🐯", "🎶"],
  "decor": [{"emoji": "✨", "x": 130, "y": 60, "size": 24}, {"emoji": "🎶", "x": 300, "y": 40, "size": 26}, {"emoji": "💜", "x": 560, "y": 70, "size": 22},
            {"emoji": "✨", "x": 760, "y": 100, "size": 20}, {"emoji": "🎵", "x": 660, "y": 30, "size": 22}, {"emoji": "🌆", "x": 460, "y": 118, "size": 60}],
  "rider": SHADOW + '''<ellipse cx="36" cy="52" rx="26" ry="18" fill="#6FB7E9"/><ellipse cx="36" cy="58" rx="16" ry="11" fill="#FFFFFF"/>
<path d="M18 44 q4 -8 8 0 M28 40 q4 -8 8 0 M40 40 q4 -8 8 0 M50 44 q4 -8 8 0" stroke="#1F2A44" stroke-width="3" fill="none" stroke-linecap="round"/>
<rect x="16" y="62" width="9" height="16" rx="4" fill="#6FB7E9"/><rect x="46" y="62" width="9" height="16" rx="4" fill="#6FB7E9"/>
<path d="M10 52 c-12 -2 -14 -14 -6 -16" stroke="#6FB7E9" stroke-width="5" fill="none" stroke-linecap="round"/>
<circle cx="56" cy="34" r="17" fill="#6FB7E9"/><path d="M42 24 l-2 -12 l10 6z M70 24 l2 -12 l-10 6z" fill="#6FB7E9"/>
<circle cx="50" cy="32" r="7" fill="#fff"/><circle cx="63" cy="32" r="7" fill="#fff"/><circle cx="52" cy="33" r="3.2" fill="#111"/><circle cx="61" cy="31" r="3.2" fill="#111"/>
<ellipse cx="57" cy="41" rx="3" ry="2" fill="#E0559A"/><path d="M52 45 q5 4 10 0" stroke="#1F2A44" stroke-width="1.5" fill="none"/>
<path d="M46 20 l3 -6 M66 20 l-3 -6" stroke="#1F2A44" stroke-width="2.5" stroke-linecap="round"/>'''},

"totoro": {
  "name": "Totoro", "emoji": "🌰",
  "colors": {"sky": "#CDE9E0", "dawn": "#E8F1D7", "horizon": "#F6F3E4", "ground": "#6BAF6B", "path": "#C9B58E", "pathDone": "#8C6E4A",
             "ink": "#2F3A2F", "cloud": "#ffffff", "mist": "#8AA08A", "accent": "#E07B39", "ok": "#2E7D4F", "sun": "#F8D66D", "discDone": "#EAF3E4"},
  "texts": {"title": "Sur le chemin de l'école, Romane !", "subtitle": "Quatre étapes avant le Chat-bus. Il passe à {goal} !",
            "msgs": ["Totoro t'attend au camphrier !", "Un gland ramassé !", "À mi-chemin, sous le parapluie !", "Le Chat-bus arrive…", "Le Chat-bus est là ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! 🌰 Les Noiraudes dansent !", "late": "Arrivée à {time}. Demain avant {goal}, promis à Totoro ?"},
  "icons": {"wake": "🌱", "clothes": "☂️", "breakfast": "🍙", "teeth": "🪥"},
  "sky": {"type": "sun"}, "clouds": True, "confetti": ["🌰", "🍃", "☂️", "🌱", "✨"],
  "decor": [{"emoji": "🌳", "x": 700, "y": 246, "size": 64}, {"emoji": "🌿", "x": 220, "y": 246, "size": 28}, {"emoji": "🍃", "x": 420, "y": 110, "size": 22}],
  "rider": SHADOW + '''<ellipse cx="38" cy="50" rx="25" ry="28" fill="#8C8C8C"/><ellipse cx="38" cy="58" rx="16" ry="18" fill="#DCDCD2"/>
<path d="M29 50 l4 3 l4 -3 M41 50 l4 3 l4 -3 M35 58 l4 3 l4 -3" stroke="#8C8C8C" stroke-width="1.6" fill="none"/>
<path d="M22 28 l4 -16 l9 13 z" fill="#8C8C8C"/><path d="M54 28 l-4 -16 l-9 13 z" fill="#8C8C8C"/>
<circle cx="30" cy="34" r="3.6" fill="#fff"/><circle cx="46" cy="34" r="3.6" fill="#fff"/><circle cx="30" cy="34" r="1.6" fill="#222"/><circle cx="46" cy="34" r="1.6" fill="#222"/>
<ellipse cx="38" cy="39" rx="3" ry="2" fill="#333"/>
<path d="M12 36 h11 M12 41 h11 M53 36 h11 M53 41 h11" stroke="#333" stroke-width="1.2" stroke-linecap="round"/>
<ellipse cx="42" cy="14" rx="9" ry="4" fill="#5FAF4B" transform="rotate(-20 42 14)"/>
<ellipse cx="27" cy="77" rx="9" ry="3" fill="#7A7A7A"/><ellipse cx="49" cy="77" rx="9" ry="3" fill="#7A7A7A"/>'''},

"espace": {
  "name": "Espace", "emoji": "🚀",
  "colors": {"sky": "#0B1026", "dawn": "#1B2A5C", "horizon": "#2E3F7A", "ground": "#8D8FA3", "path": "#B8C0E0", "pathDone": "#FFB347",
             "ink": "#F2F5FF", "cloud": "#3A4A80", "mist": "#A9B4D8", "accent": "#FF7A3D", "ok": "#7CFFB2", "sun": "#FFD23F", "discDone": "#2B3A6E"},
  "texts": {"title": "Décollage pour l'école, Romane !", "subtitle": "Quatre étapes de la check-list. Mise en orbite avant {goal} ?",
            "msgs": ["Compte à rebours lancé !", "Moteurs allumés !", "À mi-chemin de la Lune !", "Approche finale…", "Mission accomplie ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! 🚀 Houston est fier de toi !", "late": "Arrivée à {time}. Demain, orbite avant {goal} ?"},
  "icons": {"wake": "🌍", "clothes": "👩‍🚀", "breakfast": "🥣", "teeth": "🪐"},
  "sky": {"type": "emoji", "emoji": "🌕", "size": 60}, "clouds": False, "confetti": ["🚀", "⭐", "🪐", "🌟", "👩‍🚀"],
  "decor": [{"circle": 1, "x": 80, "y": 50, "r": 2, "fill": "#fff"}, {"circle": 1, "x": 260, "y": 30, "r": 1.6, "fill": "#fff"}, {"circle": 1, "x": 400, "y": 90, "r": 2.2, "fill": "#fff"},
            {"circle": 1, "x": 640, "y": 40, "r": 1.5, "fill": "#fff"}, {"circle": 1, "x": 760, "y": 110, "r": 2, "fill": "#fff"}, {"circle": 1, "x": 180, "y": 130, "r": 1.4, "fill": "#fff"},
            {"emoji": "🪐", "x": 330, "y": 70, "size": 40}, {"emoji": "🛸", "x": 700, "y": 60, "size": 30}],
  "rider": SHADOW + '''<path d="M40 6 C 58 24, 58 52, 40 66 C 22 52, 22 24, 40 6z" fill="#F4F4F4"/>
<path d="M40 6 C 48 14, 52 22, 53 28 L 27 28 C 28 22, 32 14, 40 6z" fill="#E53935"/>
<circle cx="40" cy="38" r="7" fill="#64B5F6" stroke="#37474F" stroke-width="2.5"/>
<path d="M24 50 l-10 16 l14 -4z" fill="#E53935"/><path d="M56 50 l10 16 l-14 -4z" fill="#E53935"/>
<path d="M33 64 h14 l-7 16z" fill="#FFB300"/><path d="M36 64 h8 l-4 9z" fill="#FFF176"/>'''},

"pirates": {
  "name": "Pirates", "emoji": "🏴‍☠️",
  "colors": {"sky": "#BFE3F5", "dawn": "#FFE9C7", "horizon": "#FFF3E0", "ground": "#2E86C1", "path": "#E8D3A2", "pathDone": "#C0392B",
             "ink": "#1F2D3D", "cloud": "#ffffff", "mist": "#6F8FA8", "accent": "#C0392B", "ok": "#1E8449", "sun": "#FFD23F", "discDone": "#FFF1E0"},
  "texts": {"title": "À l'abordage de l'école, Romane !", "subtitle": "Quatre étapes sur la carte au trésor. Le trésor est à {goal} !",
            "msgs": ["Tous sur le pont !", "Hissez les voiles !", "À mi-chemin de l'île !", "Terre en vue…", "Le trésor est à toi ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! 🏴‍☠️ Capitaine Romane !", "late": "Arrivée à {time}. Demain, on accoste avant {goal} ?"},
  "icons": {"wake": "🦜", "clothes": "🧢", "breakfast": "🍌", "teeth": "🦷"},
  "sky": {"type": "sun"}, "clouds": True, "confetti": ["🏴‍☠️", "💰", "🦜", "⚓", "🪙"],
  "decor": [{"emoji": "🏝️", "x": 700, "y": 246, "size": 50}, {"emoji": "🐚", "x": 220, "y": 246, "size": 22}, {"emoji": "🐟", "x": 440, "y": 300, "size": 20}],
  "rider": '''<path d="M4 56 q36 16 72 0 l-8 18 h-56 z" fill="#7A4A21"/><path d="M8 58 q32 12 64 0" stroke="#5A3416" stroke-width="2" fill="none"/>
<line x1="40" y1="56" x2="40" y2="8" stroke="#4E342E" stroke-width="3"/>
<path d="M42 14 q24 16 0 34 z" fill="#F6EFD8"/><path d="M38 18 q-18 14 0 28 z" fill="#E8DCC0"/>
<text x="42" y="12" font-size="12">🏴‍☠️</text>'''},

"dinosaures": {
  "name": "Dinosaures", "emoji": "🦕",
  "colors": {"sky": "#FFE0B2", "dawn": "#FFCC80", "horizon": "#FFF3E0", "ground": "#7CB342", "path": "#D7B98E", "pathDone": "#8D6E63",
             "ink": "#3E2723", "cloud": "#ffffff", "mist": "#A1887F", "accent": "#E64A19", "ok": "#2E7D32", "sun": "#FFB300", "discDone": "#FFF1DC"},
  "texts": {"title": "Vers l'école, Romane-saure !", "subtitle": "Quatre étapes dans la jungle avant {goal}. Rugis !",
            "msgs": ["Le volcan gronde, debout !", "Un dino de réveillé !", "À mi-chemin de la jungle !", "Le nid est en vue…", "RAAAWR ! Tu as réussi ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! 🦖 Reine des dinos !", "late": "Arrivée à {time}. Demain, on court avant {goal} ?"},
  "icons": {"wake": "🌋", "clothes": "🦖", "breakfast": "🥚", "teeth": "🦷"},
  "sky": {"type": "sun"}, "clouds": True, "confetti": ["🦕", "🦖", "🌴", "🥚", "🎉"],
  "decor": [{"emoji": "🌋", "x": 700, "y": 246, "size": 60}, {"emoji": "🌴", "x": 220, "y": 246, "size": 44}],
  "rider": SHADOW + '''<ellipse cx="34" cy="54" rx="26" ry="16" fill="#66BB6A"/>
<path d="M8 58 c-10 2 -14 12 -8 16 c4 -8 8 -8 12 -10z" fill="#66BB6A"/>
<rect x="16" y="62" width="10" height="16" rx="4" fill="#4CAF50"/><rect x="42" y="62" width="10" height="16" rx="4" fill="#4CAF50"/>
<path d="M52 50 c6 -18 4 -30 14 -34" stroke="#66BB6A" stroke-width="10" fill="none" stroke-linecap="round"/>
<ellipse cx="68" cy="14" rx="10" ry="7" fill="#66BB6A"/><circle cx="70" cy="12" r="1.8" fill="#222"/>
<circle cx="28" cy="50" r="3" fill="#2E7D32"/><circle cx="40" cy="56" r="2.5" fill="#2E7D32"/><circle cx="20" cy="58" r="2" fill="#2E7D32"/>
<path d="M22 40 l4 -6 l4 6 M32 39 l4 -6 l4 6 M42 41 l4 -6 l4 6" fill="#A5D6A7"/>'''},

"sirene": {
  "name": "Sirène", "emoji": "🧜‍♀️",
  "colors": {"sky": "#BFEAF5", "dawn": "#9FD8E8", "horizon": "#7CC5DA", "ground": "#1E88A8", "path": "#F6E7B2", "pathDone": "#FF8AAE",
             "ink": "#12384A", "cloud": "#ffffff", "mist": "#5E93A6", "accent": "#FF6F9C", "ok": "#0E8A6A", "sun": "#FFD23F", "discDone": "#FFF0F5"},
  "texts": {"title": "Vers l'école sous la mer, Romane !", "subtitle": "Quatre coquillages, puis le drapeau. Marée haute à {goal} !",
            "msgs": ["Les vagues t'appellent !", "Un coquillage trouvé !", "À mi-chemin du lagon !", "Le récif est en vue…", "Tu as traversé l'océan ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! 🐚 Reine du lagon !", "late": "Arrivée à {time}. Demain, on nage avant {goal} ?"},
  "icons": {"wake": "🐚", "clothes": "👗", "breakfast": "🍓", "teeth": "🪥"},
  "sky": {"type": "sun"}, "clouds": True, "confetti": ["🐚", "🐠", "🫧", "💗", "⭐"],
  "decor": [{"emoji": "🐠", "x": 200, "y": 300, "size": 22}, {"emoji": "🐙", "x": 680, "y": 302, "size": 24}, {"emoji": "🫧", "x": 440, "y": 298, "size": 18}, {"emoji": "⛵", "x": 840, "y": 120, "size": 30}],
  "rider": '''<path d="M6 76 q18 -6 30 -22 q-4 20 -12 26 z" fill="#26A69A"/><path d="M2 78 l14 -10 l-2 14 z" fill="#26A69A"/>
<path d="M32 56 q10 -4 14 -20 q6 14 4 26 q-10 4 -18 -6z" fill="#26A69A"/>
<ellipse cx="46" cy="36" rx="9" ry="12" fill="#F5D0B0"/><path d="M38 34 h16 v6 h-16z" fill="#7E57C2"/>
<circle cx="47" cy="20" r="10" fill="#F5D0B0"/>
<path d="M36 18 q10 -14 22 -2 q2 14 -2 22 q-4 -8 -2 -14 q-8 2 -14 8 q-4 -4 -4 -14z" fill="#E53935"/>
<circle cx="44" cy="20" r="1.6" fill="#222"/><circle cx="51" cy="20" r="1.6" fill="#222"/><path d="M45 25 q3 2 6 0" stroke="#B3405A" stroke-width="1.4" fill="none"/>
<text x="54" y="12" font-size="10">⭐</text>'''},

"pokemon": {
  "name": "Pokémon", "emoji": "⚡",
  "colors": {"sky": "#CDEBFF", "dawn": "#FFF3B0", "horizon": "#FFFBE6", "ground": "#66BB6A", "path": "#F5D75E", "pathDone": "#EF5350",
             "ink": "#1F2A44", "cloud": "#ffffff", "mist": "#7F8FA8", "accent": "#EF5350", "ok": "#2E7D32", "sun": "#FFD23F", "discDone": "#FFF8DC"},
  "texts": {"title": "En route vers l'arène, Romane !", "subtitle": "Quatre badges à gagner avant {goal}. Pikachu, go !",
            "msgs": ["Un nouveau dresseur se réveille !", "Premier badge !", "À mi-chemin de l'arène !", "Le dernier badge est proche…", "Champion·ne de la ligue ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! ⚡ Pika-pika !", "late": "Arrivée à {time}. Demain, tous les badges avant {goal} ?"},
  "icons": {"wake": "⚡", "clothes": "🧢", "breakfast": "🍎", "teeth": "🪥"},
  "sky": {"type": "sun"}, "clouds": True, "confetti": ["⚡", "⭐", "🔴", "🎉", "💛"],
  "decor": [{"emoji": "🌲", "x": 220, "y": 246, "size": 44}, {"emoji": "🏟️", "x": 700, "y": 246, "size": 44}],
  "rider": SHADOW + '''<path d="M10 60 l-8 -4 l6 -8 l-8 -4 l12 -8 l2 10 l8 -2z" fill="#8D6E63"/><path d="M6 54 l-2 -8 l8 -4 l-2 8z" fill="#FFD54F"/>
<ellipse cx="38" cy="54" rx="20" ry="18" fill="#FFD54F"/><rect x="24" y="66" width="9" height="12" rx="4" fill="#FFD54F"/><rect x="42" y="66" width="9" height="12" rx="4" fill="#FFD54F"/>
<circle cx="42" cy="30" r="17" fill="#FFD54F"/>
<path d="M30 18 l-8 -16 l14 10z" fill="#FFD54F"/><path d="M22 2 l4 8 l-6 2z" fill="#222"/>
<path d="M54 18 l8 -16 l-14 10z" fill="#FFD54F"/><path d="M62 2 l-4 8 l6 2z" fill="#222"/>
<circle cx="36" cy="28" r="3" fill="#222"/><circle cx="48" cy="28" r="3" fill="#222"/><circle cx="37" cy="27" r="1" fill="#fff"/><circle cx="49" cy="27" r="1" fill="#fff"/>
<circle cx="30" cy="36" r="4" fill="#E53935"/><circle cx="54" cy="36" r="4" fill="#E53935"/>
<path d="M40 34 q2 2 4 0" stroke="#222" stroke-width="1.4" fill="none"/><path d="M38 38 q4 4 8 0" stroke="#222" stroke-width="1.4" fill="none"/>
<path d="M22 50 h8 M22 56 h6" stroke="#8D6E63" stroke-width="3" stroke-linecap="round"/>'''},

"minecraft": {
  "name": "Minecraft", "emoji": "⛏️",
  "colors": {"sky": "#7EC0EE", "dawn": "#A9D7F5", "horizon": "#CDE8F7", "ground": "#5D8A3C", "path": "#8B6F47", "pathDone": "#D6B36B",
             "ink": "#1E2A1E", "cloud": "#ffffff", "mist": "#6E8B6E", "accent": "#E04B3A", "ok": "#2E7D32", "sun": "#FFF176", "discDone": "#EAF1DA"},
  "texts": {"title": "Vers l'école, bloc par bloc, Romane !", "subtitle": "Quatre blocs à miner avant {goal}. Attention aux creepers !",
            "msgs": ["Le soleil se lève sur le monde !", "Un bloc de miné !", "À mi-chemin du village !", "Le portail est en vue…", "Tu as vaincu l'Ender Dragon ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! 💎 Diamant pour Romane !", "late": "Arrivée à {time}. Demain, on mine avant {goal} ?"},
  "icons": {"wake": "🌅", "clothes": "🛡️", "breakfast": "🍞", "teeth": "⛏️"},
  "sky": {"type": "none"}, "clouds": False, "confetti": ["💎", "⛏️", "🟩", "🎉", "🧱"],
  "decor": [{"rect": 1, "x": 880, "y": 30, "w": 60, "h": 60, "fill": "#FFF176"}, {"rect": 1, "x": 120, "y": 50, "w": 90, "h": 24, "fill": "#ffffff"}, {"rect": 1, "x": 150, "y": 36, "w": 40, "h": 14, "fill": "#ffffff"},
            {"rect": 1, "x": 540, "y": 40, "w": 80, "h": 22, "fill": "#ffffff"}, {"rect": 1, "x": 560, "y": 26, "w": 36, "h": 14, "fill": "#ffffff"},
            {"emoji": "🌳", "x": 700, "y": 246, "size": 40}, {"emoji": "🏠", "x": 220, "y": 246, "size": 40}],
  "rider": '''<rect x="22" y="36" width="32" height="30" fill="#4CAF50"/><rect x="22" y="36" width="8" height="8" fill="#388E3C"/><rect x="42" y="50" width="8" height="8" fill="#388E3C"/><rect x="30" y="58" width="6" height="6" fill="#81C784"/>
<rect x="18" y="66" width="12" height="12" fill="#388E3C"/><rect x="46" y="66" width="12" height="12" fill="#388E3C"/>
<rect x="26" y="8" width="26" height="26" fill="#5CB85C"/><rect x="26" y="8" width="6" height="6" fill="#7BD37B"/><rect x="44" y="26" width="6" height="6" fill="#4A9A4A"/>
<rect x="30" y="14" width="6" height="6" fill="#111"/><rect x="42" y="14" width="6" height="6" fill="#111"/>
<rect x="36" y="20" width="6" height="8" fill="#111"/><rect x="33" y="24" width="3" height="8" fill="#111"/><rect x="42" y="24" width="3" height="8" fill="#111"/>'''},

"mandalorian": {
  "name": "Star Wars – Mandalorian", "emoji": "🛸",
  "colors": {"sky": "#1B1F3F", "dawn": "#6E3F6A", "horizon": "#E8955A", "ground": "#C9A06B", "path": "#EAD6AE", "pathDone": "#8FE39A",
             "ink": "#F5EFE3", "cloud": "#3B3F66", "mist": "#BDB6D4", "accent": "#FF9B3D", "ok": "#8FE39A", "sun": "#FFD9A0", "discDone": "#3E3455"},
  "texts": {"title": "Telle est la voie, Romane !", "subtitle": "Quatre missions avant {goal}. Grogu compte sur toi !",
            "msgs": ["Debout, Mando !", "Première mission accomplie !", "À mi-chemin de la galaxie !", "Le Razor Crest est en vue…", "Telle est la voie ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! 🛸 Grogu applaudit avec ses grandes oreilles !", "late": "Arrivée à {time}. Demain, hyperespace avant {goal} ?"},
  "icons": {"wake": "🌌", "clothes": "🪖", "breakfast": "🍲", "teeth": "🪥"},
  "sky": {"type": "sun"}, "clouds": False, "confetti": ["🛸", "⭐", "💚", "🌌", "✨"],
  "decor": [{"circle": 1, "x": 880, "y": 70, "r": 16, "fill": "#FFB870"},
            {"circle": 1, "x": 90, "y": 40, "r": 2, "fill": "#fff"}, {"circle": 1, "x": 230, "y": 90, "r": 1.5, "fill": "#fff"}, {"circle": 1, "x": 340, "y": 30, "r": 2.2, "fill": "#fff"},
            {"circle": 1, "x": 470, "y": 60, "r": 1.6, "fill": "#fff"}, {"circle": 1, "x": 620, "y": 25, "r": 2, "fill": "#fff"}, {"circle": 1, "x": 760, "y": 100, "r": 1.4, "fill": "#fff"},
            {"emoji": "🛸", "x": 560, "y": 90, "size": 34}, {"emoji": "🌵", "x": 220, "y": 246, "size": 40}, {"emoji": "🪨", "x": 700, "y": 246, "size": 34}],
  "rider": SHADOW + '''<ellipse cx="40" cy="74" rx="18" ry="3.5" fill="#8FE39A" opacity=".5"/>
<ellipse cx="40" cy="58" rx="28" ry="17" fill="#8A9199"/>
<path d="M22 60 q18 -14 36 0 v6 h-36z" fill="#8B6A4A"/>
<path d="M29 33 C 19 27, 6 29, 2 39 C 1 43, 5 46, 10 45 C 16 44, 22 45, 29 45 Z" fill="#8DBF7A"/><path d="M27 36 C 19 32, 10 34, 7 40 C 7 43, 11 44, 15 43 C 20 42, 24 43, 27 43 Z" fill="#C4DEA8"/>
<path d="M51 33 C 61 27, 74 29, 78 39 C 79 43, 75 46, 70 45 C 64 44, 58 45, 51 45 Z" fill="#8DBF7A"/><path d="M53 36 C 61 32, 70 34, 73 40 C 73 43, 69 44, 65 43 C 60 42, 56 43, 53 43 Z" fill="#C4DEA8"/>
<ellipse cx="40" cy="40" rx="14" ry="12" fill="#8DBF7A"/>
<circle cx="34" cy="41" r="4.5" fill="#111"/><circle cx="47" cy="41" r="4.5" fill="#111"/><circle cx="35.5" cy="39.5" r="1.4" fill="#fff"/><circle cx="48.5" cy="39.5" r="1.4" fill="#fff"/>
<path d="M37 49 q3 2 6 0" stroke="#3E5E2E" stroke-width="1.4" fill="none" stroke-linecap="round"/>
<path d="M36 29 q0 -4 2 -4 M40 28 q0 -4 2 -4 M44 29 q0 -4 2 -3" stroke="#D7E3BF" stroke-width="1" fill="none" stroke-linecap="round"/>
<path d="M12 58 a28 17 0 0 0 56 0z" fill="#C4CAD2"/><path d="M15 63 q25 8 50 0" stroke="#9AA1AB" stroke-width="2" fill="none"/>'''},

"vice-versa": {
  "name": "Vice-Versa (Joie)", "emoji": "😄",
  "colors": {"sky": "#FFF3B0", "dawn": "#FFD6E8", "horizon": "#FFFBEA", "ground": "#7FD8A8", "path": "#FFC3E1", "pathDone": "#FFD23F",
             "ink": "#3A2E5C", "cloud": "#ffffff", "mist": "#8E7BB0", "accent": "#FF5FA2", "ok": "#1F9E63", "sun": "#FFD23F", "discDone": "#FFF6E0"},
  "texts": {"title": "Joie t'accompagne à l'école, Romane !", "subtitle": "Quatre souvenirs à créer avant {goal}. Tout en jaune !",
            "msgs": ["Le Quartier Général se réveille !", "Un souvenir tout doré !", "À mi-chemin, Joie saute partout !", "Le train de la pensée arrive…", "Souvenir essentiel créé ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! 😄 Une journée en or !", "late": "Arrivée à {time}. Demain, Joie gagne avant {goal} ?"},
  "icons": {"wake": "🌞", "clothes": "👗", "breakfast": "🥞", "teeth": "🪥"},
  "sky": {"type": "sun"}, "clouds": True, "confetti": ["💛", "💙", "💚", "❤️", "💜"],
  "decor": [{"circle": 1, "x": 150, "y": 60, "r": 10, "fill": "#FFD23F"}, {"circle": 1, "x": 300, "y": 40, "r": 8, "fill": "#5AA9FF"}, {"circle": 1, "x": 450, "y": 80, "r": 9, "fill": "#FF5A5A"},
            {"circle": 1, "x": 600, "y": 35, "r": 8, "fill": "#7ED957"}, {"circle": 1, "x": 760, "y": 75, "r": 9, "fill": "#B57BFF"},
            {"emoji": "🌈", "x": 700, "y": 246, "size": 50}, {"emoji": "🎈", "x": 220, "y": 246, "size": 30}],
  "rider": SHADOW + '''<circle cx="40" cy="42" r="34" fill="#FFF176" opacity=".35"/>
<rect x="30" y="60" width="7" height="17" rx="3" fill="#FFE082"/><rect x="43" y="60" width="7" height="17" rx="3" fill="#FFE082"/>
<path d="M30 36 h20 l8 28 h-36z" fill="#7ED957"/><circle cx="38" cy="50" r="1.8" fill="#C8F79A"/><circle cx="47" cy="57" r="1.8" fill="#C8F79A"/><circle cx="33" cy="59" r="1.4" fill="#C8F79A"/>
<path d="M30 40 l-12 -14" stroke="#FFE082" stroke-width="5" stroke-linecap="round"/><path d="M50 40 l12 -14" stroke="#FFE082" stroke-width="5" stroke-linecap="round"/>
<circle cx="40" cy="24" r="13" fill="#FFE082"/>
<path d="M27 21 q2 -15 14 -15 q12 0 13 12 q-3 -5 -8 -6 q-2 6 -8 3 q-4 5 -11 6z" fill="#3FA9F5"/>
<circle cx="35" cy="25" r="2.8" fill="#1E5AA8"/><circle cx="45" cy="25" r="2.8" fill="#1E5AA8"/><circle cx="36" cy="24" r="1" fill="#fff"/><circle cx="46" cy="24" r="1" fill="#fff"/>
<path d="M34 30 q6 6 12 0" stroke="#C76A2E" stroke-width="1.6" fill="none" stroke-linecap="round"/>'''},

"lego": {
  "name": "Lego", "emoji": "🧱",
  "colors": {"sky": "#BFE3FF", "dawn": "#E3F2FF", "horizon": "#FFFFFF", "ground": "#4CAF50", "path": "#FFD500", "pathDone": "#E3000B",
             "ink": "#1E2A44", "cloud": "#ffffff", "mist": "#7F8FA8", "accent": "#E3000B", "ok": "#2E7D32", "sun": "#FFD500", "discDone": "#FFF7CC"},
  "texts": {"title": "Construis ta journée, Romane !", "subtitle": "Quatre briques à assembler avant {goal}. Tout est super génial !",
            "msgs": ["Première brique : debout !", "Une brique posée !", "À mi-chemin de la tour !", "Dernière brique en vue…", "Tout est super génial ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! 🧱 Maître constructrice !", "late": "Arrivée à {time}. Demain, on construit avant {goal} ?"},
  "icons": {"wake": "🌅", "clothes": "👕", "breakfast": "🧇", "teeth": "🪥"},
  "sky": {"type": "sun"}, "clouds": True, "confetti": ["🧱", "🟥", "🟨", "🟦", "🟩"],
  "decor": [{"rect": 1, "x": 196, "y": 232, "w": 48, "h": 18, "fill": "#E3000B"}, {"rect": 1, "x": 204, "y": 214, "w": 32, "h": 18, "fill": "#1E64C8"},
            {"rect": 1, "x": 208, "y": 208, "w": 8, "h": 6, "fill": "#1E64C8"}, {"rect": 1, "x": 224, "y": 208, "w": 8, "h": 6, "fill": "#1E64C8"},
            {"rect": 1, "x": 676, "y": 232, "w": 48, "h": 18, "fill": "#FFD500"}, {"rect": 1, "x": 684, "y": 214, "w": 32, "h": 18, "fill": "#2E7D32"},
            {"rect": 1, "x": 688, "y": 208, "w": 8, "h": 6, "fill": "#2E7D32"}, {"rect": 1, "x": 704, "y": 208, "w": 8, "h": 6, "fill": "#2E7D32"}],
  "rider": SHADOW + '''<rect x="24" y="50" width="32" height="6" fill="#1E64C8"/><rect x="24" y="54" width="14" height="22" fill="#1E64C8"/><rect x="42" y="54" width="14" height="22" fill="#1E64C8"/>
<rect x="22" y="72" width="16" height="5" fill="#174E9C"/><rect x="42" y="72" width="16" height="5" fill="#174E9C"/>
<path d="M26 28 h28 l4 24 h-36z" fill="#E3000B"/><rect x="34" y="34" width="12" height="12" fill="#FFD500"/><rect x="37" y="37" width="6" height="6" fill="#E3000B"/>
<path d="M30 33 l-12 15" stroke="#E3000B" stroke-width="8" stroke-linecap="round"/><path d="M50 33 l12 15" stroke="#E3000B" stroke-width="8" stroke-linecap="round"/>
<circle cx="17" cy="50" r="4.5" fill="#FFD500"/><circle cx="63" cy="50" r="4.5" fill="#FFD500"/>
<rect x="36" y="24" width="8" height="5" fill="#FFD500"/>
<rect x="29" y="6" width="22" height="20" rx="5" fill="#FFD500"/><rect x="35" y="1" width="10" height="6" rx="1" fill="#FFD500"/>
<circle cx="37" cy="14" r="1.8" fill="#111"/><circle cx="45" cy="14" r="1.8" fill="#111"/><path d="M35 19 q6 4 12 0" stroke="#111" stroke-width="1.5" fill="none" stroke-linecap="round"/>'''},

"rock-star": {
  "name": "Rock star", "emoji": "🎸",
  "colors": {"sky": "#1A0F2E", "dawn": "#5B1E5E", "horizon": "#E63E7B", "ground": "#2B2140", "path": "#FFB84C", "pathDone": "#FF3D7F",
             "ink": "#FFF4F8", "cloud": "#4A2F6E", "mist": "#C9B3E0", "accent": "#FFB84C", "ok": "#7CFFB2", "sun": "#FFD23F", "discDone": "#3E2A5E"},
  "texts": {"title": "En scène, Romane !", "subtitle": "Quatre morceaux avant le grand concert de {goal} !",
            "msgs": ["Le public t'attend !", "Premier riff réussi !", "À mi-chemin du concert !", "Le solo final approche…", "Standing ovation ! 🎉"],
            "win": "Arrivée à {time}, avant {goal} ! 🎸 Rock star !", "late": "Arrivée à {time}. Demain, le concert commence avant {goal} ?"},
  "icons": {"wake": "🎵", "clothes": "🕶️", "breakfast": "🥣", "teeth": "🎤"},
  "sky": {"type": "emoji", "emoji": "⚡", "size": 56}, "clouds": False, "confetti": ["🎸", "⭐", "🎶", "🔥", "🤘"],
  "decor": [{"emoji": "🎤", "x": 130, "y": 60, "size": 24}, {"emoji": "🎶", "x": 300, "y": 40, "size": 26}, {"emoji": "⭐", "x": 560, "y": 70, "size": 22},
            {"emoji": "🎵", "x": 660, "y": 30, "size": 22}, {"emoji": "✨", "x": 800, "y": 100, "size": 20},
            {"emoji": "🔊", "x": 220, "y": 246, "size": 36}, {"emoji": "🥁", "x": 700, "y": 246, "size": 40}],
  "rider": SHADOW + '''<rect x="26" y="52" width="9" height="24" rx="3" fill="#222"/><rect x="41" y="52" width="9" height="24" rx="3" fill="#222"/>
<rect x="24" y="72" width="12" height="6" rx="2" fill="#5D4037"/><rect x="40" y="72" width="12" height="6" rx="2" fill="#5D4037"/>
<path d="M27 30 h22 l3 24 h-28z" fill="#1C1C24"/><path d="M35 30 h6 v22 h-6z" fill="#E53935"/>
<line x1="46" y1="50" x2="74" y2="30" stroke="#8B5A2B" stroke-width="4" stroke-linecap="round"/>
<line x1="47" y1="49" x2="73" y2="30" stroke="#E8DCC0" stroke-width="1"/>
<rect x="69" y="24" width="9" height="9" rx="2" fill="#222" transform="rotate(-35 73.5 28.5)"/>
<ellipse cx="44" cy="54" rx="13" ry="9" fill="#E53935" transform="rotate(-20 44 54)"/><circle cx="46" cy="53" r="3" fill="#fff"/><circle cx="41" cy="56" r="1.5" fill="#222"/>
<path d="M30 36 l26 -6" stroke="#1C1C24" stroke-width="6" stroke-linecap="round"/><circle cx="57" cy="29" r="3.5" fill="#F5D0B0"/>
<path d="M48 36 l-2 14" stroke="#1C1C24" stroke-width="6" stroke-linecap="round"/><circle cx="46" cy="51" r="3.5" fill="#F5D0B0"/>
<circle cx="38" cy="20" r="11" fill="#F5D0B0"/>
<path d="M27 18 l-4 -12 l7 6 l2 -10 l5 7 l4 -9 l3 9 l6 -7 l-1 10 l6 -4 l-4 10z" fill="#2B1B12"/>
<rect x="29" y="17" width="8" height="5" rx="2" fill="#111"/><rect x="39" y="17" width="8" height="5" rx="2" fill="#111"/><line x1="37" y1="19" x2="39" y2="19" stroke="#111" stroke-width="1.5"/>
<ellipse cx="39" cy="27" rx="2.5" ry="2" fill="#B3405A"/>'''},
}

for tid, t in THEMES.items():
    (OUT / f"{tid}.json").write_text(json.dumps(t, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"wrote {len(THEMES)} themes to {OUT}")
